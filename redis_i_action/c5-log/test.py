import unittest
from log import *
import random
import requests
import csv
import threading
class TestCh05(unittest.TestCase):
    def setUp(self):
        global config_connection
        import redis
        #set host and password if you use redis-server with extract host and requirepass
        HOST = '192.168.0.106'
        PASSWORD = 123456
        self.conn = config_connection = redis.Redis(HOST,db=15)
        # self.conn.execute_command("AUTH",PASSWORD)
        # import ipdb; ipdb.set_trace()
        # config_connection.execute_command("AUTH",PASSWORD)
        self.conn.flushdb()

    def tearDown(self):
        self.conn.flushdb()
        del self.conn
        global config_connection, QUIT, SAMPLE_COUNT
        config_connection = None
        QUIT = False
        SAMPLE_COUNT = 100
        print
        print

    def test_log_recent(self):
        import pprint
        conn = self.conn

        print "Let's write a few logs to the recent log"
        for msg in xrange(5):
            log_recent(conn, 'test', 'this is message %s'%msg)
        recent = conn.lrange('recent:test:info', 0, -1)
        print "The current recent message log has this many messages:", len(recent)
        print "Those messages include:"
        pprint.pprint(recent[:10])
        self.assertTrue(len(recent) >= 5)

    def test_log_common(self):
        import pprint
        conn = self.conn

        print "Let's write some items to the common log"
        for count in xrange(1, 6):
            for i in xrange(count):
                log_common(conn, 'test', "message-%s"%count)
        common = conn.zrevrange('common:test:info', 0, -1, withscores=True)
        print "The current number of common messages is:", len(common)
        print "Those common messages are:"
        pprint.pprint(common)
        self.assertTrue(len(common) >= 5)

    def test_counters(self):
        import pprint
        global QUIT, SAMPLE_COUNT
        conn = self.conn

        print "Let's update some counters for now and a little in the future"
        now = time.time()
        for delta in xrange(10):
            update_counter(conn, 'test', count=random.randrange(1,5), now=now+delta)
        counter = get_counter(conn, 'test', 1)
        print "We have some per-second counters:", len(counter)
        self.assertTrue(len(counter) >= 10)
        counter = get_counter(conn, 'test', 5)
        print "We have some per-5-second counters:", len(counter)
        print "These counters include:"
        pprint.pprint(counter[:10])
        self.assertTrue(len(counter) >= 2)
        print

        tt = time.time
        def new_tt():
            return tt() + 2*86400
        time.time = new_tt

        print "Let's clean out some counters by setting our sample count to 0"
        SAMPLE_COUNT = 0
        t = threading.Thread(target=clean_counters, args=(conn,))
        t.setDaemon(1) # to make sure it dies if we ctrl+C quit
        t.start()
        time.sleep(1)
        QUIT = True
        time.time = tt
        counter = get_counter(conn, 'test', 86400)
        print "Did we clean out all of the counters?", not counter
        self.assertFalse(counter)

    def test_stats(self):
        import pprint
        conn = self.conn

        print "Let's add some data for our statistics!"
        for i in xrange(5):
            r = update_stats(conn, 'temp', 'example', random.randrange(5, 15))
        print "We have some aggregate statistics:", r
        rr = get_stats(conn, 'temp', 'example')
        print "Which we can also fetch manually:"
        pprint.pprint(rr)
        self.assertTrue(rr['count'] >= 5)

    # def test_access_time(self):
    #     import pprint
    #     conn = self.conn

    #     print "Let's calculate some access times..."
    #     for i in xrange(10):
    #         with access_time(conn, "req-%s"%i):
    #             time.sleep(.5 + random.random())
    #     print "The slowest access times are:"
    #     atimes = conn.zrevrange('slowest:AccessTime', 0, -1, withscores=True)
    #     pprint.pprint(atimes[:10])
    #     self.assertTrue(len(atimes) >= 10)
    #     print

    #     def cb():
    #         time.sleep(1 + random.random())

    #     print "Let's use the callback version..."
    #     for i in xrange(5):
    #         request.path = 'cbreq-%s'%i
    #         process_view(conn, cb)
    #     print "The slowest access times are:"
    #     atimes = conn.zrevrange('slowest:AccessTime', 0, -1, withscores=True)
    #     pprint.pprint(atimes[:10])
    #     self.assertTrue(len(atimes) >= 10)

    # def test_ip_lookup(self):
    #     conn = self.conn

    #     try:
    #         open('GeoLiteCity-Blocks.csv', 'rb')
    #         open('GeoLiteCity-Location.csv', 'rb')
    #     except:
    #         print "********"
    #         print "You do not have the GeoLiteCity database available, aborting test"
    #         print "Please have the following two files in the current path:"
    #         print "GeoLiteCity-Blocks.csv"
    #         print "GeoLiteCity-Location.csv"
    #         print "********"
    #         return

    #     print "Importing IP addresses to Redis... (this may take a while)"
    #     import_ips_to_redis(conn, 'GeoLiteCity-Blocks.csv')
    #     ranges = conn.zcard('ip2cityid:')
    #     print "Loaded ranges into Redis:", ranges
    #     self.assertTrue(ranges > 1000)
    #     print

    #     print "Importing Location lookups to Redis... (this may take a while)"
    #     import_cities_to_redis(conn, 'GeoLiteCity-Location.csv')
    #     cities = conn.hlen('cityid2city:')
    #     print "Loaded city lookups into Redis:", cities
    #     self.assertTrue(cities > 1000)
    #     print

    #     print "Let's lookup some locations!"
    #     rr = random.randrange
    #     for i in xrange(5):
    #         print find_city_by_ip(conn, '%s.%s.%s.%s'%(rr(1,255), rr(256), rr(256), rr(256)))

    def test_is_under_maintenance(self):
        print "Are we under maintenance (we shouldn't be)?", is_under_maintenance(self.conn)
        self.conn.set('is-under-maintenance', 'yes')
        print "We cached this, so it should be the same:", is_under_maintenance(self.conn)
        time.sleep(1)
        print "But after a sleep, it should change:", is_under_maintenance(self.conn)
        print "Cleaning up..."
        self.conn.delete('is-under-maintenance')
        time.sleep(1)
        print "Should be False again:", is_under_maintenance(self.conn)

    # def test_config(self):
    #     print "Let's set a config and then get a connection from that config..."
    #     set_config(self.conn, 'redis', 'test', {'db':15})
    #     @redis_connection('test')
    #     def test(conn2):
    #         return bool(conn2.info())
    #     print "We can run commands from the configured connection:", test()

if __name__ == '__main__':
    unittest.main()
