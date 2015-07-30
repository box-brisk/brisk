#{"continent":1, "continent_name":"Continent 1", "continent_bonus":5, "territories":[1,2,3,5,6,7,8,10]}
#{"territory": 1, "territory_name": "Territory 1", "adjacent_territories":[2,3]}
#{"territory": 2,"num_armies": 3}, {"territory": 4, "num_armies": 3}

import Brisk
import time

class Game(object):

	def __init__(self):
		self.api = Brisk.Brisk()
		print("Joined game: " + str(self.api.game_id))
		map_res = self.api.get_map_layout()
		(self.territories, self.continents) = self.parse_map(map_res)
		# self.updateGameState()
		# print self.territories
		# print self.continents

	def list_to_dict(self, lst, id_key):
		d = {}
		for item in lst:
			id = item[id_key]
			d[id] = item
		return d

	def parse_map(self, res):
		t = self.list_to_dict(res['territories'], 'territory')
		c = self.list_to_dict(res['continents'], 'continent')
		return (t, c)

	def target_continent(self, c_id):
		pass

	def target_territory(self, t_id):
		pass

	def updateGameState(self):
		self.player_state = self.api.get_player_status()
		self.own_territories = self.list_to_dict(self.player_state['territories'], 'territory')
		# print(self.player_state)

		self.enemy_state = self.api.get_enemy_status()
		self.enemy_territories = self.list_to_dict(self.enemy_state['territories'], 'territory')
		# print(self.enemy_state)

		self.to_be_captured = {}
		self.number_of_armies = {}
		self.enemy_armies = {}

		for key in self.continents:
			c = self.continents[key]
			c_id = c['continent']
			self.to_be_captured[c_id] = []
			count = 0
			army_count = 0
			enemy_count = 0
			for key in self.own_territories:
				t = self.own_territories[key]
				if t['territory'] in c['territories']:
					army_count += t['num_armies']
			for key in self.enemy_territories:
				t = self.enemy_territories[key]
				if t['territory'] in c['territories']:
					enemy_count += t['num_armies']
					self.to_be_captured[c_id].append(t['territory'])

			self.number_of_armies[c_id] = army_count
			self.enemy_armies[c_id] = enemy_count

		# print self.player_state
		# print self.enemy_state

	def attack(self):
		pass

	def defend(self):
		pass

	def play(self):
		self.updateGameState()
		self.attack()
	

