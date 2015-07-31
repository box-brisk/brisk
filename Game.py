#{"continent":1, "continent_name":"Continent 1", "continent_bonus":5, "territories":[1,2,3,5,6,7,8,10]}
#{"territory": 1, "territory_name": "Territory 1", "adjacent_territories":[2,3]}
#{"territory": 2,"num_armies": 3}, {"territory": 4, "num_armies": 3}

import Brisk
import time, random, sys, urllib2, math

class Game(object):

	EASY_CONTINENT_LIMIT = 2

	def __init__(self, game_id, game_type):
		self.api = Brisk.Brisk(game_id, game_type)
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
		for territory in t.itervalues():
			for continent in c.itervalues():
				if territory['territory'] in continent['territories']:
					territory['continent'] = continent['continent']
					t[territory['territory']] = territory

		for continent in c.itervalues():
			all_related = []
			for territory in continent['territories']:
				all_related.extend(t[territory]['adjacent_territories'])
			all_related = list(set(all_related))
			def not_within_continent(item):
				return item not in continent['territories']
			outside_borders = filter(not_within_continent, all_related)
			continent['border_size'] = len(outside_borders)
			continent['outside_border'] = outside_borders
			c[continent['continent']] = continent

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
		if (your_army >= 10 or their_army >= 10):
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

	def print_attack(self, res):
		print '---------------------------------'
		print '          ATTACK RESULTS         '
		print '---------------------------------'
		print 'Player territory ' + str(res['attacker_territory']) + ' attacks Enemy territory ' + str(res['defender_territory'])
		print 'Player attacks enemy with rolls of ' + str(res['attacker_dice'])
		print 'Enemey defends with rolls of ' + str(res['defender_dice'])
		print 'Captured target: ' + str(res['defender_territory_captured'])
		print 'Player lost ' + str(res['attacker_losses'])
		print 'Enemy lost ' + str(res['defender_losses'])
		print 'Player forces remaining: ' + str(res['attacker_territory_armies_left'])
		print 'Enemy forces remaining: ' + str(res['defender_territory_armies_left'])
		print '\n'
	

	# Return ordered list of targets based on out heuristics func
	def order_attack_targets(self, targets):
		def is_enemy(t_id): return t_id in self.enemy_territories
		targets = filter(is_enemy, targets)

		def calc(enemy_t):
			c_id = self.territories[enemy_t]['continent']
			a = 1-min(4, len(self.to_be_captured[c_id])-1)/((4*1.0)**2)
			b = 1 if (len(self.to_be_captured[c_id]) == len(self.continents[c_id]['territories'])) else 0
			territory_surrounding_enemies = 0
			for adj_t in self.territories[enemy_t]['adjacent_territories']:
				if adj_t in self.enemy_territories:
					territory_surrounding_enemies += self.enemy_territories[adj_t]['num_armies']
			
			threat = 0
			border_size = 0
			for border in self.continents[c_id]['outside_border']:
				if border in self.enemy_territories:
					threat += self.enemy_territories[border]['num_armies']
					border_size += 1
			if threat == 0: 
				threat = 1
			else:
				threat /= border_size

			return (a+b)*self.continents[c_id]['continent_bonus']/math.sqrt(threat)*3 - 0.5*self.enemy_territories[enemy_t]['num_armies'] - math.sqrt(territory_surrounding_enemies)

		def attack_heuristics(enemy_t):
			value = calc(enemy_t)
			for adj_t in self.territories[enemy_t]['adjacent_territories']:
				if adj_t in self.enemy_territories:
					value += calc(adj_t) / len(self.territories[enemy_t]['adjacent_territories']) * 0.7
			return value

		return sorted(targets, key=attack_heuristics, reverse=True)

	def order_defend_options(self, borders):
		def is_own(t_id): return t_id in self.own_territories
		borders = filter(is_own, borders)

		def calc(own_t):
			c_id = self.territories[own_t]['continent']
			a = 1 - min(Game.EASY_CONTINENT_LIMIT, (len(self.continents[c_id]['territories'])-(len(self.to_be_captured[c_id])-1))/((Game.EASY_CONTINENT_LIMIT*1.0)**2))
			b = 1 if (len(self.to_be_captured[c_id]) == 0) else 0
			return (a+b)*self.continents[c_id]['continent_bonus']-0.5*self.own_territories[own_t]['num_armies']

		def defend_heuristics(own_t):
			value = calc(own_t)
			for adj_t in self.territories[own_t]['adjacent_territories']:
				if adj_t in self.own_territories:
					value += calc(adj_t) / len(self.territories[own_t]['adjacent_territories']) * 0.7
			return value

		return sorted(borders, key=defend_heuristics, reverse=True)


	def attack_continent(self, c_id):
		print 'Attacking continent\n\n'
		armies_to_place = self.player_state['num_reserves']

		# Fortify the territories
		army_differences = []
		for t_id in self.to_be_captured[c_id]:
			army_differences.append((t_id, self.adj_player_armies[t_id] - self.enemy_territories[t_id]['num_armies']))
		
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

	def helper_get_border(self):
		self.updateGameState()
		borders = self.order_defend_options(self.borders)
		return borders[0]

	def attack_territory(self, target):
		while True:

			if (target is None): return
			max_army = 0
			attacker = None

			print 'target ' +str(target) + ' is enemy :' + str(target in self.enemy_territories)
			if (target not in self.enemy_territories):
				print self.api.get_enemy_status()
				return

			if len(self.adj_player_territories[target]) == 0:
				return

			for t_id in self.adj_player_territories[target]:
				if (self.own_territories[t_id]['num_armies'] > max_army):
					max_army = self.own_territories[t_id]['num_armies']
					attacker = t_id

			enemy_army = self.enemy_territories[target]['num_armies']
			if (self.prob_defend(max_army, enemy_army) < 0.7): return

			if max_army > 3:
				res = self.api.attack(attacker, target, 3)
				self.print_attack(res)
				self.updateGameState()
			elif (max_army == 3) and (self.enemy_territories[target]['num_armies'] == 1):
				res = self.api.attack(attacker, target, 2)
				self.print_attack(res)
				self.updateGameState()
			else:
				print 'CANNOT ATTACK \n\n'
				return

			if (res['defender_territory_captured']):
				print 'Looking for new target'

				targets = []
				for adj_t in self.territories[target]['adjacent_territories']:
					if (adj_t in self.enemy_territories) and (adj_t != target):
						targets.append(adj_t)

				if (self.own_territories[attacker]['num_armies'] > 2):
					try:
						if len(target != 0):
							self.api.transfer_armies(attacker, target, self.own_territories[attacker]['num_armies']-2)
							self.updateGameState()
					except:
						print('transfer ' + str(self.own_territories[attacker]['num_armies']-2) + ' armies from ' + str(attacker) + ' to ' + str(target))
						print self.api.get_game_state()


				if len(targets) == 0: 
					target = None
					# should move all but 1 armies from this territory to border
				else:
					targets = self.order_attack_targets(targets)
					target = targets[0]
				print target


	def place_armies_helper(self, t_id):
		adj_player_territories = self.adj_player_territories[t_id]
		if len(adj_player_territories) == 0: return None
		largest_territory_id = 0
		largest_territory = 0

		for adj_t_id in adj_player_territories:
			if self.own_territories[adj_t_id]['num_armies'] > largest_territory:
				largest_territory = self.own_territories[adj_t_id]['num_armies']
				largest_territory_id = adj_t_id

		return (largest_territory_id, largest_territory)

	def place_armies(self, t_id, num_armies):
		if num_armies == 0:
			return

		adj_player_territories = self.adj_player_territories[t_id]
		if len(adj_player_territories) == 0: return
		largest_territory_id = 0
		largest_territory = 0

		for adj_t_id in adj_player_territories:
			if self.own_territories[adj_t_id]['num_armies'] > largest_territory:
				largest_territory = self.own_territories[adj_t_id]['num_armies']
				largest_territory_id = adj_t_id

		print '================================='
		print 'Placing ' + str(num_armies) + ' on territory ' + str(largest_territory_id)
		print '================================='
		self.api.place_armies(largest_territory_id, num_armies)
		self.updateGameState()
		# self.own_territories[largest_territory_id]['num_armies'] += num_armies

	def updateAdjacentData(self):
		self.adj_player_armies = {}
		self.adj_player_territories = {}
		self.adj_enemy_territories = {}
		self.borders = []
		for t_id in self.enemy_territories:
			t = self.territories[t_id]
			self.adj_player_armies[t['territory']] = 0
			self.adj_player_territories[t['territory']] = []
			for adjacent_t in t['adjacent_territories']:
				if adjacent_t in self.own_territories:
					self.adj_player_armies[t['territory']] += self.own_territories[adjacent_t]['num_armies']
					self.adj_player_territories[t['territory']].append(adjacent_t)

		for t_id in self.own_territories:
			player_t = self.territories[t_id]
			self.adj_enemy_territories[player_t['territory']] = []
			for adjacent_t in player_t['adjacent_territories']:
				if adjacent_t in self.enemy_territories:
					self.adj_enemy_territories[player_t['territory']].append(adjacent_t)
			if t_id in self.adj_enemy_territories: self.borders.append(t_id)

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
		self.updateGameState()

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

		self.updateAdjacentData()

		# print self.player_state
		# print self.enemy_state

	def attack(self):
		to_attack = None
		enemy_armies = sys.maxint
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
			if self.player_state['num_reserves'] == 0:
				print self.api.get_player_status()
				sys.exit()

			# to_attack = random.choice(self.enemy_territories.keys())
			all_targets = []
			for c_id in self.adj_enemy_territories:
				all_targets.extend(self.adj_enemy_territories[c_id])
			all_targets = self.order_attack_targets(list(set(all_targets)))

			index = 0
			reserves = self.player_state['num_reserves']
			outnumber = min(reserves / 3 * 2 + 2, 4)
			attack_list = []
			while ((reserves > 0) and index < len(all_targets)):
				to_attack = all_targets[index]
				(territory_to_put, current_army) = self.place_armies_helper(to_attack)
				to_place = max(0, min(reserves, self.enemy_territories[to_attack]['num_armies'] + outnumber - current_army))
				reserves = reserves - to_place
				print reserves, to_place
				self.place_armies(to_attack, to_place)
				attack_list.append(to_attack)
				index += 1
			if (reserves > 0):
				self.place_armies(all_targets[0], reserves)
			map(self.attack_territory, attack_list)

	def defend(self):
		self.updateGameState()
		non_border_territory_with_most_army = None
		most_army = 0
		for t_id in self.own_territories:
			if t_id not in self.borders:
				if self.own_territories[t_id]['num_armies'] > most_army:
					most_army = self.own_territories[t_id]['num_armies']
					non_border_territory_with_most_army = t_id
		if non_border_territory_with_most_army is None:
			for t_id in self.own_territories:
				if t_id in self.borders:
					if self.own_territories[t_id]['num_armies'] > most_army:
						most_army = self.own_territories[t_id]['num_armies']
						non_border_territory_with_most_army = t_id


		all_targets = []
		for c_id in self.adj_enemy_territories:
			all_targets.extend(self.adj_enemy_territories[c_id])
		all_targets = self.order_attack_targets(list(set(all_targets)))

		to_trasfer = max(most_army - 2, 0)
		
		try:
			self.api.transfer_armies(non_border_territory_with_most_army, self.helper_get_border(), to_trasfer)
			self.updateGameState()
		except:
			pass

		# try:
		# 	self.api.transfer_armies(non_border_territory_with_most_army, all_targets[0], to_trasfer)
		# 	self.updateGameState()
		# except:
		# 	pass

	def play(self):
		print '---------------------------------'
		print '- - - - - - - - - - - - - - - - -'
		print '           TURN ' + str(self.api.get_game_state()['num_turns_taken'])
		print '- - - - - - - - - - - - - - - - -'
		print '---------------------------------'
		self.updateGameState()
		self.attack()
		self.defend()
		print 'ENDING TURN\n'
		try:
			self.api.end_turn()
		except:
			pass

