import redis
import time
import threading

conn = redis.Redis()

"""

simle redis code with subcrible and publish

"""
def publisher(n):
	time.sleep(1)
	for i in range(n):
		conn.publish('channel',i)
		time.sleep(1)

def run_pubsub():
	threading.Thread(target=publisher,args=(3,)).start()
	pubsub = conn.pubsub()
	pubsub.subscribe(['channel'])
	count = 0
	for item in pubsub.listen():
		print item
		count+=1
		if count == 4:
			pubsub.unsubscribe()
		if count == 5:
			break

"""

simple redis code without transactions

"""

def notransaction():
	print conn.incr('notransaction:')
	time.sleep(1)
	conn.incr('nostransaction',-1)

def run_notransaction():
	if 1:
		for i in xrange(3):
			threading.Thread(target=notransaction,args=()).start()
		time.sleep(1);


"""

simple redis code with transactions

"""

def transaction():
	pipeline = conn.pipeline()
	pipeline.incr('transaction:')
	time.sleep(1)
	pipeline.incr('transaction:',-1)
	print pipeline.execute()[0]

def run_transaction():
	if 1:
		for i in xrange(3):
			threading.Thread(target=transaction).start()
		time.sleep(1);
