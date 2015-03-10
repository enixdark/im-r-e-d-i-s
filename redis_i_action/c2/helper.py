import urlparse
import time

def extract_item_id(request):
	parsed = urlparse.urlparse(request)
	query = urlparse.parse_qs(parsed.query)
	return (query.get('item') or [None])[0]

def is_dynamic(request):
	parsed = urlparse.urlparse(request)
	query = urlparse.parse_qs(parsed.query)
	return '_' in query

def hash_request(request):
	return str(hash(request))

class Inventory(object):
	def __init__(self, id):
		self.id = id

	@classmethod
	def get(cls, id):
		return Inventory(id)

	def to_dict(self):
		return {'id':self.id, 'data':'data to cache...', 'cached':time.time()}
