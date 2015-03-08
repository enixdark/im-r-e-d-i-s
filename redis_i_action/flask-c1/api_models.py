from flask.ext.restful import Resource, abort, reqparse
from models import Article,User,Vote
from flask import jsonify
from implement_func_redis import *
from run_redis import conn
from flask.ext.login import current_user
from flask import request

parser = reqparse.RequestParser()
parser.add_argument('votes', type=int)
parser.add_argument('id', type=str)
parser.add_argument('time', type=float)
parser.add_argument('score', type=float)
parser.add_argument('image', type=str)
parser.add_argument('link', type=str)

# args = parser.parse_args()

class ArticleResource(Resource):
	def get(self,id=0):
		# return [i.tran_serialize() for i in Article.query.all()]
		return get_articles(conn,int(id))

class ArticleUpdateResource(Resource):
	def get(self,id):
		return 'yes'

	def put(self,id):
		args = parser.parse_args()
		article = args['id']
		article_vote(conn,current_user.id,article)
		return 'success',200
		# list_data = get_articles(conn,id)
		# article = None
		# for i in list_data:
		# 	if i['article:'+id] == 'article:'+id:
		# 		article = i
		# 		break
		# article_vote(conn,current_user.id,article)

# class VoteResource(Resource):
# 	def put(id):
# 		pass
