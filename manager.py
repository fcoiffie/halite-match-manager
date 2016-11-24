#!/bin/python3
import os
import random
import sys
import math
import sqlite3
import argparse
from subprocess import Popen, PIPE

def max_match_rounds(width, height):
    return math.sqrt(width * height)

class Match:
    def __init__(self, player_paths, width, height, seed, time_limit):
        self.map_seed = seed
        self.width = width
        self.height = height
        self.paths = player_paths
        self.finished = False
        self.result = [0 for _ in player_paths]
        self.return_code = None
        self.results_string = ""
        self.replay_file = ""
        self.total_time_limit = time_limit
        self.timeouts = []
        self.num_players = len(player_paths)

    def __repr__(self):
        title = "Match between " + ", ".join(self.paths) + "\n"
        dims = "dimensions = " + str(self.width) + ", " + str(self.height) + "\n"
        results = "\n".join([str(i) for i in self.result]) + "\n"
        replay = self.replay_file + "\n\n"
        return title + dims + results + replay

    def get_command(self, halite_binary):
        dims = "-d " + str(self.width) + " " + str(self.height)
        quiet = "-q"
        seed = "-s " + str(self.map_seed)
        result = [halite_binary, dims, quiet, seed]
        return result + self.paths
        
    def run_match(self, halite_binary):
        command = self.get_command(halite_binary)
        p = Popen(command, stdin=None, stdout=PIPE, stderr=None)
        results, _ = p.communicate(None, self.total_time_limit)
        self.results_string = results.decode('ascii')
        self.return_code = p.returncode
        self.parse_results_string()

    def parse_results_string(self):
        lines = self.results_string.split("\n")
        if len(lines) < (2 + (2 * self.num_players)):
            raise ValueError("Not enough lines in match output")
        else:
            count = 0
            for line in lines:
                if count == self.num_players: # replay file and seed
                    self.replay_file = line.split(" ")[0]
                elif count == (self.num_players * 2) + 1: # timeouts
                    self.timeouts = (line.split(" "))
                elif count < self.num_players: # names
                    pass
                elif count < (self.num_players * 2) + 1:
                    token = line.split(" ")
                    rank = int(token[0])
                    player = int(token[1]) - 1
                    self.result[player] = rank
                count += 1

class Manager:
    def __init__(self, halite_binary, player_binaries, size_min, size_max, players_min, players_max, rounds):
        self.halite_binary = halite_binary
        self.player_binaries = player_binaries
        self.size_min = size_min
        self.size_max = size_max
        self.players_min = players_min
        self.players_max = players_max
        self.rounds = rounds
        self.round_count = 0
        self.results = []
        self.db = Database()

    def run_round(self, players, width, height, seed):
        player_paths = [self.player_binaries[i] for i in players]
        m = Match(player_paths, width, height, seed, 2 * len(player_paths) * max_match_rounds(width, height))
        m.run_match(self.halite_binary)
        self.results.append(m)
        print(m)

    def pick_players(self, num):
        open_set = [i for i in range(0, len(self.player_binaries))]
        players = []
        count = 0
        while count < num:
            chosen = open_set[random.randint(0, len(open_set) - 1)]
            players.append(chosen)
            open_set.remove(chosen)
            count += 1
        return players

    def run_rounds(self):
        while self.round_count < self.rounds:
            num_players = random.randint(2, len(self.player_binaries))
            players = self.pick_players(num_players)
            size_w = random.randint((self.size_min / 5), (self.size_max / 5)) * 5
            size_h = size_w
            seed = random.randint(10000, 2073741824)
            print ("running match...\n")
            self.run_round(players, size_w, size_h, seed)
            self.round_count += 1

    def add_player(self, name, path):
        p = self.db.get_player((name,))
        if len(p) == 0:
            self.db.add_player(name, path)
            
class Database:
    def __init__(self, filename="game_db.sqlite3"):
        self.db = sqlite3.connect(filename)
        self.recreate()
        try:
            self.latest = int(self.db.retrieve("select id from games order by id desc limit 1;",())[0][0])
        except:
            self.latest = 1

    def __del__(self):
        try:
            self.db.close()
        except: pass

    def recreate(self):
        cursor = self.db.cursor()
        try:
            cursor.execute("create table games(id integer, players text, map integer, datum date, turns integer default 0)")
            cursor.execute("create table players(id integer primary key autoincrement, name text unique, path text, lastseen date, rank integer default 1000, skill real default 0.0, mu real default 50.0, sigma real default 13.3,ngames integer default 0)")
            self.db.commit()
        except:
            pass

    def update_deferred( self, sql, tup=() ):
        cur = self.con.cursor()        
        cur.execute(sql,tup)
        
    def update( self, sql, tup=() ):
        self.update_deferred(sql,tup)
        self.con.commit()
        
    def retrieve( self, sql, tup=() ):
        cur = self.con.cursor()        
        cur.execute(sql,tup)
        return cur.fetchall()

    def add_match( self, match ):
        self.latest += 1
        players = ", ".join(match.paths)
        self.update("insert into games values(?,?,?,?,?,?)", (self.latest,players,match.map_seed,self.now(),turns)) 

    def add_player(self, name, path):
        self.update("insert into players values(?,?,?,?,?,?,?,?,?)", (None, name, path, self.now(), 1000, 0.0, 50.0, 50.0/3.0, 0))

    def get_player( self, names ):
        sql = "select * from players where name=?"
        for n in names[1:]:
            sql += " or name=?" 
        return self.retrieve(sql, names )
        



class Player:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.mu = 50.0
        self.sigma = (50.0 / 3.0)

class Commandline:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-a", "addBot", dest="addBot",
                                 action = "store_true", default = False,
                                 help = "Add a new bot with name and path")

        self.parser.add_argument("-n", "", dest="--botName",
                                 action = "store", default = "",
                                 help = "Add a new bot with name and path")

p1 = "./orchid"
p2 = "./orchid"
player_paths = [p1, p2]
m = Manager("./halite", player_paths, 20, 50, 2, 6, 5)
m.run_rounds()

#p1 = "./orchid"
#p2 = "./orchid"
#player_paths = [p1, p2]
#width, height = 30, 30
#seed = random.randint(100,1073741824)
#time_limit = None
#m = Match(player_paths, width, height, seed, time_limit)
#m.run_match("./halite")
#print(m)

