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
		self.updateGameState()
		# print self.territories
		# print self.continents

	def parse_map(self, res):
		t = {}
		for territory in res['territories']:
			t_id = territory['territory']
			t[t_id] = territory

		c = {}
		for continent in res['continents']:
			c_id = continent['continent']
			c[c_id] = continent

		return (t, c)

	def target_continent(self, c_id):
		pass

	def target_territory(self, t_id):
		pass

	def updateGameState(self):
		self.own_territories = self.api.get_player_status()
		self.enemy_territories = self.api.get_enemy_status()
		self.to_be_captured = {}
		self.number_of_armies = {}
		self.enemy_armies = {}

		for c in self.continents:
			count = 0
			army_count = 0
			c_id = c['continent']
			for t in self.own_territories['territories']:
				if t['territory'] in c['territories']:
					count += 1
					army_count += t['num_armies']
			for t in self.enemy_territories['territories']:
				if t['territory'] in c['territories']:
					enemy_count += t['num_armies']
					self.to_be_captured[c_id].append(t['territory'])

			self.number_of_armies[c_id] = army_count
			self.enemy_armies[c_id] = enemy_count

		# print self.own_territories
		# print self.enemy_territories

	def attack(self):
		pass

	def defend(self):
		pass

	def play(self):
		self.updateGameState()

