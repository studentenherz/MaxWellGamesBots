from flask import Flask 
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS
import os
import telebot
from settings import bot_token

bot  = telebot.TeleBot(bot_token)

def decode(expr):
    return eval(bytes.fromhex(expr).decode("utf-8"))

app =  Flask('GamesAPI')
api =  Api(app)
CORS(app)

class GetScoreBoard(Resource):
	def get(self):
		parser = reqparse.RequestParser()

		parser.add_argument('data', required=True)
		data = decode(parser.parse_args()['data'])

		scores = []

		if data['inline_message_id']:
			print('getting scores from inline message')
			scores = bot.get_game_high_scores(data['user_id'], inline_message_id=data['inline_message_id'])
		else:
			print('getting scores from chat message')
			scores = bot.get_game_high_scores(data['user_id'], chat_id=data['chat_id'], message_id=data['message_id'])

		scores_json = []
		for score in scores:
			scores_json.append({
				'user_first_name': score.user.first_name,
				'position': score.position,
				'score': score.score,
				'current_player': score.user.id == data['user_id']
			})

		return scores_json, 200

class SetScore(Resource):
	def post(self):
		parser = reqparse.RequestParser()

		parser.add_argument('data', required=True, location='json')
		parser.add_argument('score', required=True, location='json')
		args = parser.parse_args()
		data = decode(args['data'])
		score = int(args['score'])
		
		print(data)

		if score == 0:
				return args, 200

		if data['inline_message_id']:
			print('updating inline message')
			# get scores 
			scores = bot.get_game_high_scores(data['user_id'], inline_message_id=data['inline_message_id'])
			for x in scores:
				if (x.user.id == data['user_id'] and score <= x.score):
					return args, 200
			bot.set_game_score(data['user_id'], score, False, inline_message_id=data['inline_message_id'])
		else:
			print('updating chat message')
			# get scores
			scores = bot.get_game_high_scores(data['user_id'], chat_id=data['chat_id'], message_id=data['message_id'])
			for x in scores:
				if (x.user.id == data['user_id'] and score <= x.score):
					return args, 200
			bot.set_game_score(data['user_id'], score, False, chat_id=data['chat_id'], message_id=data['message_id'])

		return args, 200

api.add_resource(SetScore, '/setScore')
api.add_resource(GetScoreBoard, '/getScoreBoard')

@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

if __name__ == '__main__':
	app.run(host = '0.0.0.0')