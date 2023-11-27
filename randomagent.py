"""
Implementation of Random Agent.
"""


import numpy as np 
import importlib




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
        Wrapper = importlib.import_module('..games.{}.mutants.{}.wrapper'.format(gamename, mutantname))
        ValidatorModule = importlib.import_module('..games.{}.actual.Validator'.format(gamename))
        ModelReaderModule = importlib.import_module('..games.{}.actual.ModelReader'.format(gamename))
        action_time = ModelReaderModule.get_action_timeelapsed()

        print(
            "\nEvaluating the mutant " + mutantname + " of game " + gamename + " using the Random Agent\n")
        tries = self.opt.tries# default 50 for random
        current_try = 0
        mutant_killed = False
        while not mutant_killed and current_try<tries:
            current_try +=1
            print("\n\n>>>>>>>>>>> Try", current_try)

            # The game instance
            self.game = Wrapper.Game(self.opt.frame_size)


            self.game.step(0)

            for _ in range(10):
                self.game.step(0)

            game_sate = self.game.get_game_state()

            validator = ValidatorModule.Validator( self.opt.exp_name, game_sate)
            validator.mutant_name = mutantname
            validator.algo = "random"

            # Start playing
            ep_len = 0
            mutant_killed = False

            while True:


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
                mutant_killed = validator.validate(game_sate,action, done)
                score = game_sate['score']

                if isinstance(score, dict):
                    score = game_sate['score']['score']

                ep_len +=1

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


            f = open("logs/mutation-testing-logs"+"/random/"+self.opt.game+"/mutant_log_" + gamename + ".csv", "a")
            f.write(mutantname + ", " + (
                "mutant killed" if mutant_killed else "alive") + ", \n")

            f.close()

