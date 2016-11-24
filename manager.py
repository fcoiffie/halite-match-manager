#!/bin/python3
import os
import random
import sys
import math
import sqlite3
import argparse
import datetime
import shutil
from subprocess import Popen, PIPE

halite_command = "./halite"

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
        shutil.move(self.replay_file, "replays")

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
    def __init__(self, halite_binary, players=None, size_min=20, size_max=50, players_min=2, players_max=6, rounds=-1):
        self.halite_binary = halite_binary
        self.players = players
        self.size_min = size_min
        self.size_max = size_max
        self.players_min = players_min
        self.players_max = players_max
        self.rounds = rounds
        self.round_count = 0
        self.db = Database()

    def run_round(self, players, width, height, seed):
        player_paths = [self.players[i].path for i in players]
        m = Match(player_paths, width, height, seed, 2 * len(player_paths) * max_match_rounds(width, height))
        m.run_match(self.halite_binary)
        print(m)

    def pick_players(self, num):
        open_set = [i for i in range(0, len(self.players))]
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
            num_players = random.randint(2, len(self.players))
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

    def now(self):
        return datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S") #asctime()
    def recreate(self):
        cursor = self.db.cursor()
        try:
            cursor.execute("create table games(id integer, players text, map integer, datum date, turns integer default 0)")
            cursor.execute("create table players(id integer primary key autoincrement, name text unique, path text, lastseen date, rank integer default 1000, skill real default 0.0, mu real default 50.0, sigma real default 13.3,ngames integer default 0, active integer default 1)")
            self.db.commit()
        except:
            pass

    def update_deferred( self, sql, tup=() ):
        cursor = self.db.cursor()        
        cursor.execute(sql,tup)
        
    def update( self, sql, tup=() ):
        self.update_deferred(sql,tup)
        self.db.commit()
        
    def retrieve( self, sql, tup=() ):
        cursor = self.db.cursor()        
        cursor.execute(sql,tup)
        return cursor.fetchall()

    def add_match( self, match ):
        self.latest += 1
        players = ", ".join(match.paths)
        self.update("insert into games values(?,?,?,?,?,?)", (self.latest,players,match.map_seed,self.now(),turns)) 

    def add_player(self, name, path):
        self.update("insert into players values(?,?,?,?,?,?,?,?,?,?)", (None, name, path, self.now(), 1000, 0.0, 50.0, 50.0/3.0, 0, True))

    def delete_player(self, name):
        self.update("delete from players where name=?", [name])

    def get_player( self, names ):
        sql = "select * from players where name=?"
        for n in names[1:]:
            sql += " or name=?" 
        return self.retrieve(sql, names )
        

class Player:
    def __init__(self, name, path, last_seen = "", rank = 1000, skill = 0.0, mu = 50.0, sigma = (50.0 / 3.0), ngames = 0, active = 1):
        self.name = name
        self.path = path
        self.last_seen = last_seen
        self.rank = rank
        self.skill = skill
        self.mu = mu
        self.sigma = sigma
        self.ngames = ngames
        self.active = active

def parse_player_record (player):
    (player_id, name, path, last_seen, rank, skill, mu, sigma, ngames, active) = player
    return Player(name, path, last_seen, rank, skill, mu, sigma, ngames, active)
    

class Commandline:
    def __init__(self):
        self.manager = Manager(halite_command)
        self.cmds = None
        self.parser = argparse.ArgumentParser()
        self.no_args = False
        self.parser.add_argument("-a", "--addBot", dest="addBot",
                                 action = "store", default = "",
                                 help = "Add a new bot with a name")

        self.parser.add_argument("-d", "--deleteBot", dest="deleteBot",
                                 action = "store", default = "",
                                 help = "Delete the named bot")

#        self.parser.add_argument("-n", "--botName", dest="botName",
#                                 action = "store", default = "",
#                                 help = "Specify a name for a new bot")

        self.parser.add_argument("-p", "--botPath", dest="botPath",
                                 action = "store", default = "",
                                 help = "Specify the path for a new bot")

        self.parser.add_argument("-s", "--showBots", dest="showBots",
                                 action = "store_true", default = False,
                                 help = "Show a list of all bots")

    def parse(self, args):
        if len(args) == 0:
            self.no_args = True
        self.cmds = self.parser.parse_args(args)

    def add_bot(self, bot, path):
        self.manager.add_player(bot, path)

    def delete_bot(self, bot):
        self.manager.db.delete_player(bot)

    def valid_botfile(self, path):
        return True

    def act(self):
        if self.cmds.addBot != "":
            print("Adding new bot...")
            if self.cmds.botPath == "":
                print ("You must specify the path for the new bot")
            elif self.valid_botfile(self.cmds.botPath):
                self.add_bot(self.cmds.addBot, self.cmds.botPath)
        elif self.cmds.deleteBot != "":
            print("Deleting bot...")
            self.delete_bot(self.cmds.deleteBot)
        elif self.cmds.showBots:
            for p in self.manager.db.retrieve("select * from players order by skill desc"):
                print(p)
        elif self.no_args:
            print ("No arguments supplied, attempting to run some games...")
            player_records = self.manager.db.retrieve("select * from players where active > 0")
            players = [parse_player_record(player) for player in player_records]
            if len(players) < 2:
                print("Not enough players for a game. Need at least " + str(self.manager.players_min) + ", only have " + str(len(players)))
                print("use the -h flag to get help")
            else:
                self.manager.players = players
                self.manager.rounds = 1
                self.manager.run_rounds()

cmdline = Commandline()
cmdline.parse(sys.argv[1:])
cmdline.act()

#p1 = "./orchid"
#p2 = "./orchid"
#player_paths = [p1, p2]
#m = Manager("./halite", player_paths, 20, 50, 2, 6, 5)
#m.run_rounds()

#p1 = "./orchid"
#p2 = "./orchid"
#player_paths = [p1, p2]
#width, height = 30, 30
#seed = random.randint(100,1073741824)
#time_limit = None
#m = Match(player_paths, width, height, seed, time_limit)
#m.run_match("./halite")
#print(m)

