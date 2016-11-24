#!/bin/python3
import os
import random
import sys
from subprocess import Popen, PIPE

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


p1 = "./orchid"
p2 = "./orchid"
player_paths = [p1, p2]
width, height = 30, 30
seed = random.randint(100,sys.maxsize >> 32)
time_limit = None
m = Match(player_paths, width, height, seed, time_limit)
m.run_match("./halite")
print(m)
#        from subprocess import call
#        import os
#        import sys
#
#        # cd to the script directory
#        os.chdir(os.path.dirname(os.path.realpath(__file__)))
#
#        # the gradle `application` plugin generates a script to run your in `bin`
##        call(['./bin/MyBot'], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

