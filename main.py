import flask
from flask import Flask 
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS
import time
import telebot
from telebot import types
from settings import bot_token
bot  = telebot.TeleBot(bot_token)


WEBHOOK_URL_BASE = 'https://magiclobster.ml'
WEBHOOK_URL_PATH = f'/{bot_token}'

MSG_START = 'Hi there! If you want to have fun share a game with your friends and start playing!'
MSG_ABOUT = "This all started as almost everything else starts for me: I saw someone doing it and I wondered if I could do it too.\n\n<i>DumbGame</i> was my way of testing tha I was doing ok with Telegram's API for games.\n\n<i>Vector</i> is the first trial of a playable game, inspired in a game I played years ago of which I can't remeber the name. It is made using SVG instead of canvas, as I tought it would be better to generate the geometry on the fly and draw it. Code can be seen <a href='https://github.com/studentenherz/MaxwellGamesTelegramBot-games/blob/master/Vector/js/game.js'>here</a> (as well as in your own browser when game is loaded), please help me improve it."

games = {
	'dumbgame': 'Dumb Game',
	'vector': 'Vector'
}

def encode(expr):
    return str(expr).encode("utf-8").hex()

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

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
	if flask.request.headers.get('content-type') == 'application/json':
		json_string = flask.request.get_data().decode('utf-8')
		update = telebot.types.Update.de_json(json_string)
		bot.process_new_updates([update])
		return ''
	else:
		flask.abort(403)


@app.route(WEBHOOK_URL_PATH + '/setWebhook', methods=['GET'])
def set_webhook():
	# Remove old
	bot.remove_webhook()
	time.sleep(0.1)
	# Set webhook
	bot.set_webhook(url=WEBHOOK_URL_BASE + f'/{bot_token}')
	return '', 200

#####################################################################
# Bot commands and handlers

@bot.callback_query_handler(func=lambda call: call.game_short_name)
def callback_handler(call):
	data = {
		'user_id' : call.from_user.id,
		'chat_id': call.message.chat.id if call.message else None,
		'message_id': call.message.id if call.message else None,
		'inline_message_id': call.inline_message_id 
	}

	enc_data = encode(data)
	print(enc_data)
	
	bot.answer_callback_query(call.id, url=f'https://sharp-wright-258540.netlify.app/{call.game_short_name}/#data={enc_data}')
	# bot.answer_callback_query(call.id, url=f'http://127.0.0.1:5500/DumbGame/#data={enc_data}')

@bot.inline_handler(lambda query: True)
def inline_query_handler(inline_query):
	try:
		res = []
		i = 1;
		for game in games:
			# make inline keyboard
			m = types.InlineKeyboardMarkup()
			m.row(types.InlineKeyboardButton(f'Play {games[game]}!', callback_game=game), types.InlineKeyboardButton('Share',\
				 switch_inline_query=f'{game}'))

			r = types.InlineQueryResultGame(f'{i}', f'{game}', reply_markup=m)
			res.append(r)
			i+=1

		bot.answer_inline_query(inline_query.id, res)
	except Exception as e:
		print(e)

@bot.message_handler(commands=["start"])
def send_welcome(message):
	if(message.chat.type == 'private'):
		m = types.InlineKeyboardMarkup()
		m.row(types.InlineKeyboardButton('Start playing!',\
				 switch_inline_query=''))
		bot.send_message(message.chat.id, MSG_START , reply_markup=m)


@bot.message_handler(commands=["about"])
def about_message(message):
	if(message.chat.type == 'private'):
		bot.send_message(message.chat.id, MSG_ABOUT, parse_mode='HTML', disable_web_page_preview=True)


if __name__ == '__main__':
	# app.run(host = '0.0.0.0')

	#just for testing purposes
	bot.polling()