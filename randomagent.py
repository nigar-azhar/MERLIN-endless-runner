"""
Implementation of Random Agent.
"""


import numpy as np 
import importlib
import ModelReader

from Validator import Validator
from datetime import datetime, timedelta



class RandomAgent:

    def __init__(self, options):
        """
        Initialize an agent instance.
        """
        self.opt = options

        # The game instance#
        self.game = None

        # Log to tensorBoard
        if self.opt.mode == 'train':
            raise ValueError("No need to train random agent.")



    def select_action(self):
        """
        Selects a random action from list of available actions provided


        Returns:
            int: 0 to (total number of distint action -1)
        """


        return np.random.choice(self.opt.n_actions, p=self.opt.p_actions)#[0.95, 0.05])



    def train(self, gamename="flappybird"):
        """
        Main training loop.
        """
        raise ValueError("No need to train random agent.")



    def play_game(self, gamename="flappybird", mutantname="baseline"):
        """
        Play Game using the trained network.
        """
        Wrapper = importlib.import_module('games.{}.mutants.{}.wrapper'.format(gamename, mutantname))
        #ValidatorModule = importlib.import_module('..games.{}.actual.Validator'.format(gamename))
        #ModelReaderModule = importlib.import_module('..games.{}.actual.ModelReader'.format(gamename))
        action_time = ModelReader.get_action_timeelapsed(gamename)

        print(
            "\nEvaluating the mutant " + mutantname + " of game " + gamename + " using the Random Agent\n")
        tries = self.opt.tries# default 50 for random
        budgettime = self.opt.time_budget

        budget = timedelta(hours=budgettime)
        start_time = datetime.now()
        now = datetime.now()

        elapsed = now - start_time
        remaining = budget - elapsed

        current_try = 0
        mutant_killed = False
        while not mutant_killed and ((current_try<tries and budgettime== -1) or (remaining > timedelta(0))):
            current_try +=1
            print("\n\n>>>>>>>>>>> Try", current_try)

            # The game instance
            self.game = Wrapper.Game(self.opt.frame_size)


            self.game.step(0)

            for _ in range(10):
                self.game.step(0)

            game_sate = self.game.get_game_state()

            validator = Validator( self.opt.exp_name, game_sate, gamename)
            validator.mutant_name = mutantname
            validator.algo = "random"

            # Start playing
            ep_len = 0
            mutant_killed = False

            close_condition = 50000

            while True:

                close_condition-=1
                action = self.select_action()

                frame, reward, done = self.game.step(action)
                if done:
                    self.game.close_game()

                    break

                elif action == 1:

                    for _ in range(action_time[1]-1):

                        frame, reward, done = self.game.step(0)
                        if done:
                            self.game.close_game()
                            break
                    if done:
                        break
                elif action == 2:
                    for _ in range(action_time[2] - 1):
                        frame, reward, done = self.game.step(0)
                        if done:
                            self.game.close_game()
                            break
                    if done:
                        break

                game_sate = self.game.get_game_state()
                mutant_killed, bugs = validator.validate(game_sate,action, done)
                score = game_sate['score']

                if isinstance(score, dict):
                    score = game_sate['score']['score']

                ep_len +=1

                #print(mutant_killed)
                mutant_killed =  is_bug_relevant(mutantname, bugs,mutant_killed, gamename )

                if done:
                    self.game.close_game()
                    break
                elif score >= self.opt.score:
                    self.game.close_game()
                    break
                elif self.opt.mutant != "" and score>self.opt.score:
                    self.game.close_game()
                    break
                elif mutant_killed:
                   self.game.close_game()
                   print("\n\n######### mutant killed\n\n")
                   break
                elif close_condition <= 0:
                    self.game.close_game()
                    break

            now = datetime.now()

            elapsed = now - start_time
            remaining = budget - elapsed
            print("remaining time: ", remaining)
            if self.opt.time_budget == -1:
                f = open("logs/mutation-testing-logs"+"/random/"+self.opt.game+"/mutant_log_" + gamename + ".csv", "a")
                f.write(mutantname + ", " + (
                    "mutant killed" if mutant_killed else "alive") + ", \n")

                f.close()
            else:
                f = open("logs/mutation-testing-logs" + "/random/" + self.opt.game + "/mutant_log_" + gamename +"_"+mutantname+ ".csv",
                         "a")
                f.write(mutantname + ", " + (
                    "mutant killed" if mutant_killed else "alive") + ", \n")

                f.close()



def is_bug_relevant(mutant_name, bugs, mutantkilled, gamename="dodgywalls"):
    # Extract mutant type and ID
    parts = mutant_name.split("_")
    if len(parts) != 2:
        return False  # Invalid format or baseline

    prefix, _ = parts

    if mutant_name in ["DCD_05", "DCD_06"] and gamename == "flappybird":
        return 1 in bugs
    elif mutant_name in ["GFA_01"] and gamename == "flappybird":
        return 3 in bugs
    elif mutant_name == "DCD_04" and gamename=="carracing2d":
        return 3 in bugs
    elif parts[0] in ["DCD"] and gamename != "flappybird":
        return mutantkilled

    # Mapping of mutant type to bug ID
    bug_map = {

        "RUSD": 1,  # reward based
        "RUOR": 1,  # reward based
        "RUAR": 1,  # reward based
        "DCD": 2,  # collision bug
        "DAL": 3,   # action
        "ARR": 3,   # action
        "ADD": 3,   # action
        "AVD": 3,   # action
        "AVI": 3,   # action
        "GFR": 4,  # freeze mutant
        "GFT": 4,  # freeze mutant
        "GFA": 4,  # freeze mutant
    }

    expected_bug_id = bug_map.get(prefix)
    # print(expected_bug_id in bugs, expected_bug_id, bugs)
    if expected_bug_id is None:
        return False  # Unknown mutant type

    # print (expected_bug_id in bugs,expected_bug_id, bugs )
    return expected_bug_id in bugs
