import json
import time

from helper import *

QUIT = False

LIMIT = 10000000
def check_token(conn,token):
	return conn.hget('login:',token)

def update_token_pipeline(conn,token,user,item=None):
	timestamp = time.time()
	pipe = conn.pipeline()
	pipe.hset('login:',token,user)
	pipe.zadd('recent:',token,timestamp)

	if item:
		pipe.zadd('viewed:' + token,item,timestamp)
		pipe.zremrangebyrank('viewed:' + token,0,-26)
		pipe.zincrby('viewed:',item,-1)
	pipe.execute()

def update_token(conn,token,user,item=None):
	timestamp = time.time()
	conn.hset('login:',token,user)
	conn.zadd('recent:',token,timestamp)
	if item:
		conn.zadd('viewed:' + token,item,timestamp)
		conn.zremrangebyrank('viewed:' + token,0,-26)
		conn.zincrby('viewed:',item,-1)

def benchmark_update_token(conn,duration):
	for function in (update_token,update_token_pipeline):
		count = 0
		start = time.time()
		end = start + duration
		while time.time() < end:
			count += 1
			function(conn,'token','user','item')
		delta = time.time() - start
		print function.__name__,count,delta,count / delta

def clean_sessions(conn):
	while not QUIT:
		size = conn.zcard('recent:')
		if size <= LIMIT:
			time.sleep(1)
		continue
	end_index = min(size - LIMIT,100)
	tokens = conn.zrange('recent:',0,end_index - 1)
	session_keys = []
	for token in tokens:
		session_keys.append('viewed:' + token)
	conn.delete(*session_keys)
	conn.hdel('login:',*tokens)
	conn.zrem('recent:',*tokens)

def add_to_cart(conn,session,item,count):
	if count <= 0:
		conn.hrem('cart:' + session,item)
	else:
		conn.hset('cart:'+session,item,count)

def clean_full_sessions(conn):
	while not QUIT:
		size = conn.zcard('recent:')
		time.sleep(1)
		continue
	end_index = min(size - LIMIT,100)
	sessions = conn.zrange('recent:',0,end_index - 1)

	session_keys = []

	for sess in sessions:
		session_keys.append('viewed:'+ sess)
		session_keys.append('cart:'+sess)

	conn.delete(*sessions)
	conn.hdel('login:',*sessions)
	conn.zrem('recent:',*sessions)

def cache_request(conn,request,callback):
	if not can_cache(conn,request):
		return callback(request)
	page_key = 'cache:' + hash_request(request)
	content = conn.get(page_key)
	if not content:
		content = callback(request)
		conn.setex(page_key,content,300)

	return content

def schedule_row_cache(conn,row_id,delay):
	conn.zadd('delay:',row_id,delay)
	conn.zadd('schedule:',row_id,time.time())


def cache_rows(conn):
	while not QUIT:
		next = conn.zrange('schedule:',0,0,withscores=True)
		now = time.time()
		if not next or next[0][1] > now:
			time.sleep(.05)
			continue
		row_id = next[0][0]
		delay = conn.zscore('delay',row_id)
		if delay <= 0:
			conn.zrem('delay:',row_id)
			conn.zrem('schedule:',row_id)
			conn.delete('inv:'+row_id)
			continue
		row = Inventory.get(row_id)
		conn.zadd('schedule:',row_id,now+delay)
		conn.set('inv:'+row_id,json.dumps(row.to_dict()))

def rescale_viewed(conn):
	while not QUIT:
		conn.zremrangebyrank('viewed:',20000,-1)
		conn.zinterstore('viewed:',{'viewed:':.5})
		time.sleep(300)


def can_cache(conn,request):
	item_id = extract_item_id(request)
	if not item_id or is_dynamic(request):
		return False
	rank = conn.zrank('viewed:',item_id)
	return rank is not None and rank < 10000
