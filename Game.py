#{"continent":1, "continent_name":"Continent 1", "continent_bonus":5, "territories":[1,2,3,5,6,7,8,10]}
#{"territory": 1, "territory_name": "Territory 1", "adjacent_territories":[2,3]}
#{"territory": 2,"num_armies": 3}, {"territory": 4, "num_armies": 3}

import Brisk
import time, random, sys

class Game(object):

	EASY_CONTINENT_LIMIT = 2

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

	def attack_continent(self, c_id):
		armies_to_place = self.player_state['num_reserves']

		# Fortify the territories
		army_differences = []
		for t_id in self.to_be_captured[c_id]:
			army_differences.append((t_id, self.player_adj_armies[t_id] - self.enemy_territories[t_id]['num_armies']))
		
		print army_differences

		army_differences = sorted(army_differences, key=lambda tup: tup[1])
		# equalize so that the differences are positive
		for diff in army_differences:
			if diff[1] < 0:
				if abs(diff[1]) <= armies_to_place:
					self.place_armies(diff[0], abs(diff[1]))
					armies_to_place -= abs(diff[1])
				else:
					break

		# add the rest to the lowest
		if armies_to_place > 0:
			self.place_armies(army_differences[0][0], armies_to_place);

		# attack
		for t_id in self.to_be_captured[c_id]:
			self.attack_territory(t_id)

	def attack_territory(self, target):
		if (len(self.player_adj_territories[target]) == 0): return
		while True:
			max_army = 0
			attacker = None
			for t_id in self.player_adj_territories[target]:
				if (self.own_territories[t_id]['num_armies'] > max_army):
					max_army = self.own_territories[t_id]['num_armies']
					attacker = t_id

			res = self.api.attack(attacker, target, self.own_territories[attacker]['num_armies']-1)
			print res
			if (res['defender_territory_captured'] or (res['attacker_territory_armies_left'] == 1)):
				return

	def place_armies(self, t_id, num_armies):
		player_adj_territories = self.player_adj_territories[t_id]
		largest_territory_id = 0
		largest_territory = 0

		for adj_t_id in player_adj_territories:
			if self.own_territories[adj_t_id]['num_armies'] > largest_territory:
				largest_territory = self.own_territories[adj_t_id]['num_armies']
				largest_territory_id = adj_t_id

		print self.player_state['num_reserves'], num_armies
		self.api.place_armies(largest_territory_id, num_armies)

	def helper_calc_army_around_enemy_territories(self):
		self.player_adj_armies = {}
		self.player_adj_territories = {}
		for t_id in self.enemy_territories:
			t = self.territories[t_id]
			self.player_adj_armies[t['territory']] = 0
			self.player_adj_territories[t['territory']] = []
			for adjacent_t in t['adjacent_territories']:
				if adjacent_t in self.own_territories:
					self.player_adj_armies[t['territory']] += self.own_territories[adjacent_t]['num_armies']
					self.player_adj_territories[t['territory']].append(adjacent_t)

	def transfer_to_smallest_adjacent_territory(self, src_t_id, num_armies_to_transfer):
		smallest_territory = sys.maxint;
		smallest_territory_id = 0;

		for adj_t_id in self.territories[src_t_id]['adjacent_territories']:
			 if self.own_territories[adj_t_id]['num_armies'] < smallest_territory:
			 	smallest_territory = self.own_territories[adj_t_id]['num_armies']
			 	smallest_territory_id = adj_t_id

		self.api.transfer_armies(src_t_id, smallest_territory_id, num_armies_to_transfer)

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

		for c in self.continents.itervalues():
			c_id = c['continent']
			self.to_be_captured[c_id] = []
			count = 0
			army_count = 0
			enemy_count = 0
			for t in self.own_territories.itervalues():
				if t['territory'] in c['territories']:
					army_count += t['num_armies']
			for t in self.enemy_territories.itervalues():
				if t['territory'] in c['territories']:
					enemy_count += t['num_armies']
					self.to_be_captured[c_id].append(t['territory'])

			self.number_of_armies[c_id] = army_count
			self.enemy_armies[c_id] = enemy_count

		self.helper_calc_army_around_enemy_territories()

		# print self.player_state
		# print self.enemy_state

	def attack(self):
		to_attack = None
		enemy_armies = 99999
		for c in self.continents.itervalues():
			c_id = c['continent']
			if ((len(self.to_be_captured[c_id]) < Game.EASY_CONTINENT_LIMIT) 
						and (len(self.to_be_captured[c_id]) > 0)):
				count = 0
				for t_id in self.to_be_captured[c_id]:
					count += self.enemy_territories[t_id]['num_armies']
				if (count < enemy_armies):
					to_attack = c_id
					enemy_armies = count

		if (to_attack):
			self.attack_continent(to_attack)
		else:
			to_attack = random.choice(self.enemy_territories.keys())
			self.place_armies(to_attack, self.player_state['num_reserves'])
			self.attack_territory(to_attack)

	def defend(self):
		territories_that_can_transfer = []
		# Find our territories that can transfer
		for t_id in self.own_territories:
			t = self.territories[t_id]
			can_transfer = True
			for adj_t_id in t['adjacent_territories']:
				if adj_t_id in self.enemy_territories:
					can_transfer = False
			if can_transfer:
				# transfer all but 1 to the lowest
				num_armies_to_transfer = self.own_territories[t_id]['num_armies'] - 1
				self.transfer_to_smallest_adjacent_territory(t_id, num_armies_to_transfer)
				self.ended = True
				return

	def play(self):
		self.ended = False
		self.updateGameState()
		self.attack()
		self.defend()
		if (not self.ended):
			self.api.end_turn()
	

