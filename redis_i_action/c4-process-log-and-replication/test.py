class TestCh04(unittest.TestCase):
	def setUp(self):
	import redis
	self.conn = redis.Redis(db=15)
	self.conn.flushdb()

	def tearDown(self):
		self.conn.flushdb()
		del self.conn
		print
		print

	def test_list_item(self):
		import pprint
		conn = self.conn
		print "We need to set up just enough state so that a user can list an item"
		seller = 'userX'
		item = 'itemX'
		conn.sadd('inventory:' + seller, item)
		i = conn.smembers('inventory:' + seller)
		print "The user's inventory has:", i
		self.assertTrue(i)
		print
		print "Listing the item..."
		l = list_item(conn, item, seller, 10)
		print "Listing the item succeeded?", l
		self.assertTrue(l)
		r = conn.zrange('market:', 0, -1, withscores=True)
		print "The market contains:"
		pprint.pprint(r)
		self.assertTrue(r)
		self.assertTrue(any(x[0] == 'itemX.userX' for x in r))

		def test_purchase_item(self):
			self.test_list_item()
			conn = self.conn
			print "We need to set up just enough state so a user can buy an item"
			buyer = 'userY'
			conn.hset('users:userY', 'funds', 125)
			r = conn.hgetall('users:userY')
			print "The user has some money:", r
			self.assertTrue(r)
			self.assertTrue(r.get('funds'))
			print
			print "Let's purchase an item"
			p = purchase_item(conn, 'userY', 'itemX', 'userX', 10)
			print "Purchasing an item succeeded?", p
			self.assertTrue(p)
			r = conn.hgetall('users:userY')
			print "Their money is now:", r
			self.assertTrue(r)
			i = conn.smembers('inventory:' + buyer)
			print "Their inventory is now:", i
			self.assertTrue(i)
			self.assertTrue('itemX' in i)
			self.assertEquals(conn.zscore('market:', 'itemX.userX'), None)

		def test_benchmark_update_token(self):
			benchmark_update_token(self.conn, 5)

if __name__ == '__main__':
unittest.main()
