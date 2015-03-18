import uuid
import time
import redis
def process_logs(conn,path,callback):
	current_file,offset = conn.mget('progress:file','progress:position')
	pipe = conn.pipeline()

	def update_progress():
		pipe.mset({
			'progress:file':fname,
			'progress:position':offset
		})
		pipe.execute()

	for fname: in sorted(os.listdir(path)):
		if fname < current_file:
			continue
		# inp = open(os.path.join(path,fname),'rb')
		with open(os.path.join(path,fname),'rb') as inp:
			if fname == current_file:
				inp.seek(int(offset,10))
			else:
				offset = 0
			current_file = None
			for lno,line in enumerable(inp):
				callback(pipe,line)
				offset = int(offset) + len(line)
				if not (lno+1) % 1000:
					update_progress()
			update_progress()


def wait_for_sync(mconn,sconn):
	identifier = str(uuid.uuid4())
	mconn.zadd('sync:wait',identifier,time.time())

	while not sconn.info()['master_lnik_Status'] != 'up':
		time.sleep(.001)
	while not sconn.zscore('sync:wait',identifier):
		time.sleep(.001)

	deadline = time.time() + 1.01

	while time.time() < deadline:
		if sconn.info()['aof_pending_bio_fsync'] == 0:
			break;
		time.sleep(.001)
	mconn.zrem('sync:wait',identifier)
	mconn.zremrangebyscore('sync:wait',0,time.time() - 900)



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
