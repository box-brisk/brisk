#{"continent":1, "continent_name":"Continent 1", "continent_bonus":5, "territories":[1,2,3,5,6,7,8,10]}
#{"territory": 1, "territory_name": "Territory 1", "adjacent_territories":[2,3]}
#{"territory": 2,"num_armies": 3}, {"territory": 4, "num_armies": 3}

import Brisk
import time, random, sys, urllib2

class Game(object):

	EASY_CONTINENT_LIMIT = 3

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

	def prob_defend(self, your_army, their_army): 
		prob_table = [
		[0.42, 0.75, 0.92, 0.97, 0.99, 1, 1, 1, 1, 1], 
		[0.11, 0.36, 0.66, 0.79, 0.89, 0.93, 0.97, 0.98, 0.99, 0.99], 
		[0.03, 0.21, 0.47, 0.64, 0.77, 0.86, 0.91, 0.95, 0.97, 0.98], 
		[0.01, 0.09, 0.31, 0.48, 0.64, 0.74, 0.83, 0.89, 0.93, 0.95], 
		[0, 0.05, 0.21, 0.36, 0.51, 0.64, 0.74, 0.82, 0.87, 0.92], 
		[0, 0.02, 0.13, 0.25, 0.4, 0.52, 0.64, 0.73, 0.81, 0.86], 
		[0, 0.01, 0.08, 0.18, 0.3, 0.42, 0.54, 0.64, 0.73, 0.8], 
		[0, 0, 0.05, 0.12, 0.22, 0.33, 0.45, 0.55, 0.65, 0.72], 
		[0, 0, 0.03, 0.09, 0.16, 0.26, 0.36, 0.46, 0.56, 0.65],
		[0, 0, 0.02, 0.06, 0.12, 0.19, 0.29, 0.38, 0.48, 0.57]
		]
		if (your_army > 10 or their_army > 10):
			if (your_army >= their_army):
				scaled_their_army = int(round(their_army * 1.0 / your_army * 10))
				return prob_table[scaled_their_army][9]
			else:
				scaled_your_army = int(round(your_army * 1.0 / their_army * 10))
				return prob_table[9][scaled_your_army]
		else:
			return prob_table[their_army][your_army]

	def lost_cost(self, territory):
		# lost cost = 
		# a * (1 - prob_defend(your army, their army))
		# a = 1.0/3 + (if continent is occupied, plus the continent cost) + coefficient * (percentage of territories occupied in the current continent)
		pass

	def attack_continent(self, c_id):
		print 'Attacking continent\n\n'
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
		if (len(self.player_adj_territories[target]) == 0): 
			print 'target: ' + str(target)
			print 'adj-territories: ' + str(self.player_adj_territories)
			return
		while True:
			max_army = 0
			attacker = None
			for t_id in self.player_adj_territories[target]:
				if (self.own_territories[t_id]['num_armies'] > max_army):
					max_army = self.own_territories[t_id]['num_armies']
					attacker = t_id
			armies_to_attack_with = 0
			if self.own_territories[t_id]['num_armies'] > 3:
				armies_to_attack_with = 3
			elif self.own_territories[t_id]['num_armies'] > 1:
				armies_to_attack_with = self.own_territories[t_id]['num_armies'] - 1

			try:
				res = self.api.attack(attacker, target, armies_to_attack_with)
				print 'our territory attacking: ' + str(self.own_territories[attacker])
				print 'their territory defending: ' + str(self.enemy_territories[target])
				self.own_territories[attacker]['num_armies'] = res['attacker_territory_armies_left']
				self.enemy_territories[target]['num_armies'] = res['defender_territory_armies_left']
				print 'ATTACK ON ' + str(target) + ' SUCCESS: ' + str(res)
			except:
				print 'gameState: ' + str(self.api.get_game_state())
				print 'attacker:' + str(attacker)
				print 'target: ' + str(target)
				print 'armies attacking: ' + str(self.own_territories[attacker]['num_armies']-1)
				print 'target2' + str(self.enemy_territories[target])	
				sys.exit()

			if (res['defender_territory_captured'] or (res['attacker_territory_armies_left'] == 1)):
				print 'CANNOT ATTACK \n\n'
				return

	def place_armies(self, t_id, num_armies):
		if num_armies == 0:
			return

		player_adj_territories = self.player_adj_territories[t_id]
		largest_territory_id = 0
		largest_territory = 0

		if len(player_adj_territories) == 0:
			return

		for adj_t_id in player_adj_territories:
			if self.own_territories[adj_t_id]['num_armies'] > largest_territory:
				largest_territory = self.own_territories[adj_t_id]['num_armies']
				largest_territory_id = adj_t_id

		print self.player_state['num_reserves'], num_armies
		print 'Adding ' + str(num_armies)
		print 'Adding to: ' + str(self.own_territories[largest_territory_id])
		self.api.place_armies(largest_territory_id, num_armies)
		self.own_territories[largest_territory_id]['num_armies'] += num_armies

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
		if num_armies_to_transfer == 0:
			return

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
		print(self.player_state)

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
			print 'to_attack = ' + str(to_attack)
			print 'reserves: ' + str(self.player_state['num_reserves'])
			if self.player_state['num_reserves'] == 0:
				print self.api.get_player_status()
				sys.exit()
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
				return

	def play(self):
		print 'TURN START \n\n'
		print 'turn: ' + str(self.api.get_game_state()['num_turns_taken'])
		self.updateGameState()
		self.attack()
		self.defend()
		print 'END TURN\n\n'
		try:
			self.api.end_turn()
		except:
			pass

