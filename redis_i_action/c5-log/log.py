import logging
import time
from datetime import datetime
import redis
import bisect
import uuid
import contextlib
import json
import csv
from functools import wraps
QUIT = False
SAMPPLE_COUNT = 10
config_connection = None

SEVERTITY = {
	logging.DEBUG:'debug',
	logging.INFO:'info',
	logging.WARNING:'warning',
	logging.ERROR:'error',
	logging.CRITICAL:'critical',
}
PRECISION = [1,5,60,300,900,3600,1800,86400]
LAST_CHECKED = None
IS_UNDER_MAINTENANCE = False
CONFIGS = {}
CHECKED = {}
REDIS_CONNECTIONS = {}
SEVERTITY.update((name,name) for name in SEVERTITY.values())


class request:
	pass

# def redis_connection(component,wait=1):
# 	key = 'config:redis:' + component
# 	def f(function):
# 		@wraps(function)
# 		def callback(*args,**kwargs):
# 			old_config = CONFIGS.get(key,object())
# 			_config = get_config(
# 				config_connection,'redis',component,wait
# 			)
# 			config = {}
# 			for key,value in _config.iteritems():
# 				config[k.encode('utf-8')] = v

# 			if config != old_config:
# 				REDIS_CONNECTIONS[key] = redis.Redis(**config)

# 			return function(REDIS_CONNECTIONS.get(key),*args,**kwargs)
# 		return callback
# 	return f

def redis_connection(component, wait=1):                        #A
    key = 'config:redis:' + component                           #B
    def wrapper(function):                                      #C
        @wraps(function)                              #D
        def call(*args, **kwargs):                              #E
            old_config = CONFIGS.get(key, object())             #F
            _config = get_config(                               #G
                config_connection, 'redis', component, wait)    #G

            config = {}
            for k, v in _config.iteritems():                    #L
                config[k.encode('utf-8')] = v                   #L

            if config != old_config:                            #H
                REDIS_CONNECTIONS[key] = redis.Redis(**config)  #H

            return function(                                    #I
                REDIS_CONNECTIONS.get(key), *args, **kwargs)    #I
        return call                                             #J
    return wrapper

# @redis_connection('logs')
def log_recent(conn,name,message,severity=logging.INFO,pipe=None):
	severity = str(SEVERTITY.get(severity,severity)).lower()
	destination = 'recent:%s:%s'%(name,severity)

	message = time.asctime() + ' ' + message

	pipe = pipe or conn.pipeline()
	pipe.lpush(destination,message)
	pipe.ltrim(destination,0,99)
	pipe.save()


def log_common(conn,name,message,severity=logging.INFO,timeout=5):
	severity = str(SEVERTITY.get(severity,severity)).lower()
	destination = 'common:%s:%s' % (name,severity)

	start_key = destination +':start'
	pipe = conn.pipeline()

	end = time.time() + timeout

	while time.time() < end:
		try:
			pipe.watch(start_key)
			now = datetime.utcnow().timetuple()

			hour_start = datetime(*now[:4]).isoformat()
			existing = pipe.get(start_key)
			pipe.multi()
			if existing and existing < hour_start:
				pipe.rename(destination,destination+':last')
				pipe.rename(destination,destination+':pstart')
				pipe.set(start_key,hour_start)
			pipe.zincrby(destination,message)
			log_recent(pipe,name,message,severity,pipe)
			return
		except redis.exceptions.WatchError:
			continue


def update_counter(conn,name,count=1,now=None):
	now = now or time.time()
	pipe = conn.pipeline()
	for prec in PRECISION:
		pnow = int(now/prec) * prec
		hash = '%s:%s' % (prec,name)
		pipe.zadd('known:',hash,0)
		pipe.hincrby('count:'+hash,pnow,count)
	pipe.execute()

def get_counter(conn,name,precision):
	hash = '%s:%s' % (precision,name)
	data = conn.hgetall('count:'+hash)
	to_return = []
	for key,value in data.iteritems():
		to_return.append((int(key),int(value)))
	to_return.sort()
	return to_return

def clean_counters(conn):
	pipe = conn.pipeline()
	passes = 0
	while not QUIT:
		start = time.time()
		index = 0
		while index < conn.zcard('known:'):
			hash = conn.zrange('known:',index,index)
			index += 1
			if not hash:
				break
			hash = hash[0]
			prec = int(hash.partition(':')[0])
			bprec = int(prec // 60) or 1
			if passes % bprec:
				continue
			hkey = 'count:' + hash
			cutoff = time.time() - SAMPPLE_COUNT*prec
			samples = map(int,conn.hkeys(hkey))
			samples.sort()
			remove = bisect.bisect_right(samples,cutoff)
			if remove:
				conn.hdel(hkey,*samples[:remove])
				if remove == len(samples):
					try:
						pipe.watch(hkey)
						if not pipe.hlen(hkey):
							pipe.multi()
							pipe.zrem('known:',hash)
							pipe.execute()
							index -= 1
						else:
							pipe.unwatch()
					except redis.exceptions.WatchError:
						pass
		passes += 1
		duration = min(int(time.time() - start) + 1, 60)
		time.sleep(max(60 - duration,1))

def update_stats(conn,context,type,value,timeout=5):
	destination = 'stats:%s:%s' % (context,type)
	start_key = destination + ':start'
	pipe = conn.pipeline(True)
	end = time.time() + timeout

	while time.time() < end:
		try:
			pipe.watch(start_key)
			now = datetime.utcnow().timetuple()
			hour_start = datetime(*now[:4]).isoformat()

			existing = pipe.get(start_key)
			pipe.multi()
			if existing and existing < hour_start:
				pipe.rename(destination,destination+':last')
				pipe.rename(start_key,destination+':pstart')
				pipe.set(start_key,hour_start)

			tkey1 = str(uuid.uuid4())
			tkey2 = str(uuid.uuid4())

			pipe.zadd(tkey1,'min',value)
			pipe.zadd(tkey2,'max',value)
			pipe.zunionstore(destination,[destination,tkey1],aggregate='min')
			pipe.zunionstore(destination,[destination,tkey2],aggregate='max')

			pipe.delete(tkey2,tkey1)

			pipe.zincrby(destination,'count')
			pipe.zincrby(destination,'sum',value)
			pipe.zincrby(destination,'sumsq',value*value)

			return pipe.execute()[-3:]
		except redis.exceptions.WatchError:
			continue


def get_stats(conn,context,type):
	key = 'stats:%s:%s' % (context,type)
	data = dict(conn.zrange(key,0,-1,withscores=True))
	data['average'] = data['sum'] / data['count']
	numerator = data['sumsq'] - data['sum'] ** 2 / data['count']
	data['stddev'] = (numerator / (data['count'] - 1 or 1)) ** .5
	return data


@contextlib.contextmanager
def access_time(conn,context):
	start = time.time()
	yield
	delta = time.time() - start
	stats = update_stats(conn,context,'AccessTime',delta)

	average = stats[1] / stats[0]

	pipe = conn.pipeline()

	pipe.zadd('slowest:AccessTime',context,average)
	pipe.zremrangebyrank('slowest:AccessTime',0,-101)
	pipe.execute()

def process_view(conn,callback):
	with access_time(conn,request.path):
		return callback()


def ip_to_score(ip_address):
	score = 0
	for v in ip_address.split('.'):
		score = score * 256 + int(v,10)
	return score

def import_ips_to_redis(conn,filename):
	csv_file = csv.reader(open(filename,'rb'))
	for count,row in enumerate(csv_file):
		start_ip = row[0] if row else ''
		if 'i' in start_ip.lower():
			continue
		if '.' in start_ip:
			start_ip = ip_to_score(start_ip)
		elif start_ip.isdigit():
			start_ip = int(start_ip,10)
		else:
			continue
		city_id = row[2] + '_' + str(count)
		conn.zadd('ip2cityid:',city_id,start_ip)

def import_cities_to_redis(conn, filename):
    for row in csv.reader(open(filename, 'rb')):
        if len(row) < 4 or not row[0].isdigit():
            continue
        row = [i.decode('latin-1') for i in row]
        city_id = row[0]
        country = row[1]
        region = row[2]
        city = row[3]
        conn.hset('cityid2city:', city_id,
            json.dumps([city, region, country]))

def find_city_by_ip(conn,ip_address):
	if isinstance(ip_address,str):
		ip_address = ip_to_score(ip_address)

	city_id = conn.zrevrangebyscore(
		'ip2cityid:',ip_address,0,start=0,num=1
		)
	if not city_id:
		return None
	city_id = city_id[0].partition('_')[0]
	return json.loads(conn.hget('cityid2city',city_id))

def is_under_maintenance(conn):
	global LAST_CHECKED,IS_UNDER_MAINTENANCE

	if LAST_CHECKED < time.time() - 1:
		LAST_CHECKED = time.time()
		IS_UNDER_MAINTENANCE = bool(
			conn.get('is-under-maintenance')
			)
		return IS_UNDER_MAINTENANCE

def set_config(conn,type,component,config):
	conn.set('config:%s:%s' % (type,component),json.dumps(config))

def get_config(conn,type,component,wait=1):
	key = 'config:%s:%s' % (type,component)
	config = json.loads(conn.get(key) or '{}')
	config = dict((str(k),config[k]) for k in config)
	old_config = CONFIGS.get(key)

	if config != old_config:
		CONFIGS[key] = config
	return CONFIGS.get(key)

