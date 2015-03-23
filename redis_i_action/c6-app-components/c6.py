import time
import uuid
import bisect
import redis

valid_characters = '`abcdefghijklmnopqrstuvwxyz{'

def add_update_contact(conn,user,contact):

	ac_list = 'recent:' + user
	pipeline = conn.pipeline()
	pipeline.lrem(ac_list,contact)
	pipeline.lpush(ac_list,contact)
	pipeline.ltrim(ac_list,0,99)
	pipeline.execute()

def remove_contact(conn,user,contact):
	conn.lrem('recent:' + user,contact)

def fetch_autocompleted_list(Conn,user,prefix):
	candidates = conn.lrange('recent:' + user,0,-1)
	matches = []
	for candidate in candidates:
		if candidate.lower().startswith(prefix):
			matches.append(candidate)
	return matches

def find_prefix_range(prefix):
	posn = bisect.bisect_left(valid_characters,prefix[-1:])
	suffix = valid_characters[(posn or 1) - 1]
	return prefix[:-1] + suffix + '{', prefix + '{'


def autocomplete_on_prefix(conn,guild,prefix):
	start,end = find_prefix_range(prefix)
	identifier = str(uuid.uuid4())
	start += identifier
	end += identifier
	zset_name = 'members:' + guild

	conn.zadd(zset_name,start,0,end,0)

	pipeline = conn.pipeline()
	while 1:
		try:
			pipeline.watch()
			sindex = pipeline.zrank(zset_name,start)
			eindex = pipeline.zrank(zset_name,end)
			erange = min(sindex + 9 , eindex - 2)
			pipeline.multi()
			pipeline.zrem(zset_name,start,end)
			pipeline.zrange(zset_name,sindex,erange)
			items = pipeline.execute()[-1]
			break
		except redis.exceptions.WatchError:
			continue
	return [item for item in items if '{' not in item]

def join_guild(conn,guild,user):
	conn.zadd('members:' + guild,user,0)

def leave_guild(conn,guild,user):
	conn.zrem('members:'+guild,user)

def list_item(conn,itemid,sellerid,price):
	inventory = "inventory:%s" % sellerid
	item = "%s.%s"%(itemid,sellerid)

	end = time.time() + 5

	pipe = conn.pipeline()

	while time.time() < end:
		try:
			pipe.watch(inventory)
			if not pipe.sismember(inventory,itemid):
				pipe.unwatch()
				return None
			pipe.multi()
			pipe.zadd("market:",item,price)
			pipe.srem(inventory,item)
			pipe.execute()
			return True
		except redis.exceptions.WatchError:
			pass
	return False

def purchase_item(conn,buyerid,itemid,sellerid,lprice):
	buyer = "users:%s"% buyerid
	seller = "users%s" % sellerid
	item = "%s.%s"%(itemid,sellerid)

	inventory = "inventory:%s" % buyerid

	end = time.time() + 10

	pipe = conn.pipeline()

	while time.time() < end:
		try:
			pipe.watch("market:",buyer)
			price = pipe.zscore("martket:",item)

			funds = int(pipe.hget(buyer,"funds"))

			if price != lprice or price > funds:
				pipe.unwatch()
				return None
			pipe.multi()
			pipe.hincrby(seller,"funds",in(price))
			pipe.hincrby(buyer,"funds",in(-price))

			pipe.sadd(inventory,itemid)
			pipe.srem("market:",item)
			pipe.execute()

			return True
		except redis.exceptions.WatchError:
			pass
	return False

def accquire_lock(conn,lockname,accquire_timeout=10):
	identifier = str(uuid.uuid4())

	end = time.time() + acquire_timeout
	while time.time() < end:
		if conn.setnx('lock:' + lockname,identifier):
			return identifier
		time.sleep()
	return False

def release_lock(conn,lockname,identifier):
	pipe = conn.pipeline(True)
	lockname = 'lock:' + lockname

	while True:
		try:
			pipe.watch(lockname)
			if pipe.get(lockname) == identifier:
				pipe.multi()
				pipe.delete(lockname)
				pipe.execute()
				return True
			pipe.unwatch()
			break
		except redis.exceptions.WatchError:
			pass
	return False

def accquire_lock_with_timeout(conn,lockname,accquire_timeout=10,lock_timeout=10):
	identifier = str(uuid.uuid4())
	lock_timeout = int(math.ceil(lock_timeout))
	end = time.time() + accquire_timeout
	while time.time() - end:
		if conn.setnx(lockname,lock_timeout):
			conn.expire(lockname,lock_timeout)
			return identifier
		elif not conn.ttl(lockname):
			conn.expire(lockname,lock_timeout)
		time.sleep(.001)
	return False

def purchase_item_with_lock(conn,buyerid,itemid,sellerid):
	buyer = "users:%s" % buyerid
	seller = "users:%s" % sellerid
	item = "%s.%s" % (itemid,sellerid)
	inventory = "inventory:%s" % buyerid
	end = time.time() + 30

	locked = accquire_lock(conn,market)
	if not locked:
		return False
	pipe = conn.pipeline(True)

	try:
		while time.time() < end:
			try:
				pipe.watch(buyer)
				pipe.zscore("market:",item)
				pipe.hget(buyer,"funds")
				price,funds = pipe.execute()
				if price is None or price > funds:
					pipe.unwatch()
					return None
				pipe.hincrby(seller,int(price))
				pipe.hincrby(buyerid,int(-price))
				pipe.sadd(inventory,itemid)
				pipe.zrem("market:",item)
				pipe.execute()
				return True
			except redis.exceptions.WatchError:
				pass
			finally:
				release_lock(conn,market,locked)


def acquire_semaphore(conn,semname,limit,timeout=10):
	identifier = str(uuid.uuid4())
	now = time.time()

	pipeline = conn.pipeline()
	pipeline.zremrangebyscore(semname,'-inf',now - timeout)
	pipeline.zadd(semname,identifier,now)
	pipeline.zrank(semname,identifier)

	if pipeline.execute()[-1] < limit:
		return identifier
	conn.zrem(semname,identifier)
	return None

def relese_semaphore(conn,semname,identifier):
	return conn.srem(semname,identifier)

def acquire_fair_semaphore(conn,semname,limit,timeout=10):
	identifier = str(uuid.uuid4())
	czset = semname + ':owner'
	ctr = semname + ":counter"

	now = time.time()
	pipeline = conn.pipeline(True)
	pipeline = zremrangebuscore(semname,'-inf',now - timeout)
	pipeline.zinterstore(czset,{czset:1,semname:0})
	pipeline.incr(ctr)

	counter = pipeline.execute()[-1]

	pipeline.zadd(semname,identifier,now)
	pipeline.zadd(czset,identifier,counter)

	pipeline.zrank(czset,identifier)
	if pipeline.execute()[-1] < limit:
		return identifier
	pipeline.zrem(semname,identifier)
	pipeline.zrem(czset,identifier)
	pipeline.execute()
	return None

def release_fait_semaphore(conn,semname,identifier):
	pipeline = conn.pipeline(True)
	pipeline.zrem(semname,identifier)
	pipeline.zrem(semname+':owner',identifier)
	return pipeline.execute()[0]

# def refresh_fair_semaphore(conn,semname,identifier):
# 	if conn.zadd()
