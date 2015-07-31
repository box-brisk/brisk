import Brisk, parser, Game, time

def main():
	# try:
	# 	game = Game.Game()
	# 	while (True):
	# 		res = game.api.get_player_status(True)
	# 		if (res['eliminated'] or res['winner']):
	# 			return
	# 		if (res['current_turn']):
	# 			game.play()
	# 		time.sleep(0.5)
	# except Exception, e:
	# 	raise e
	# 	pass

	game = Game.Game()
	while (True):
		res = game.api.get_player_status(True)
		if (res['eliminated'] or res['winner']):
			print res
			return
		if (res['current_turn']):
			game.play()
		time.sleep(0.3)

if __name__ == '__main__':
	main()