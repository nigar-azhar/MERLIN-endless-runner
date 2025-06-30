import argparse
# import os
# import sys
#
# # Redirect standard output to /dev/null
# sys.stdout = open(os.devnull, 'w')
# import warnings
#
# # Suppress all warnings
# warnings.filterwarnings("ignore")
from MERLIN import MERLINAgent
from randomagent import RandomAgent
import ModelReader

# import warnings
#
# # Suppress all warnings
# warnings.filterwarnings("ignore")


# ARGPARSER

parser = argparse.ArgumentParser(description="experiment options")

parser.add_argument("--agent",
                    type=str,
                    help="agent name merlin or random",
                    default="merlin",
                    choices=["merlin", "random"])

parser.add_argument("--mode",
                    type=str,
                    help="run the network for merlin in train or evaluation mode",
                    default="eval",
                    choices=["train", "eval"])

# DIRECTORY options
parser.add_argument("--exp_name",
                    type=str,
                    help="name of experiment, to be used as save_dir",
                    default="flappybird-v5")

parser.add_argument("--weights_dir",
                    type=str,
                    help="name of model to load",
                    default="")#flappybird-wieghts
# GameName
parser.add_argument("--game",
                    type=str,
                    help="name of game, to be trained and used to save logs",
                    default="flappybird",
                    choices=["flappybird", "angrywalls", "dodgywalls", "carracing2d"])

# MUTANT name
parser.add_argument("--mutant",
                    type=str,
                    help="name of mutant, to be evaluated and used to save logs",
                    default="baseline")


parser.add_argument("--tries",
                    type=int,
                    help="number of tries",
                    default=50)

parser.add_argument("--time_budget",
                    type=float,
                    help="number of hours to give random agent",
                    default=-1)

parser.add_argument("--score",
                    type=int,
                    help="terminal score",
                    default=50)

# TRAIN options
parser.add_argument("--n_train_iterations",
                    type=int,
                    help="number of iterations to train network",
                    default=5000000)
parser.add_argument("--learning_rate",
                    type=float,
                    help="learning rate",
                    default=1e-6) # DQN 1e-6,
parser.add_argument("--len_agent_history",
                    type=int,
                    help="number of stacked frames to send as input to networks",
                    default=4)
parser.add_argument("--discount_factor",
                    type=float,
                    help="discount factor used for discounting return",
                    default=0.99)

# DQN specific options
parser.add_argument("--batch_size",
                    type=int,
                    help="batch size",
                    default=32)
parser.add_argument("--initial_exploration",
                    type=float,
                    help="epsilon greedy action selection parameter",
                    default=1.0)
parser.add_argument("--final_exploration",
                    type=float,
                    help="epsilon greedy action selection parameter",
                    default=0.01)
parser.add_argument("--final_exploration_frame",
                    type=int,
                    help="epsilon greedy action selection parameter",
                    default=1000000)
parser.add_argument("--replay_memory_size",
                    type=int,
                    help="maximum number of transitions in replay memory",
                    default=25000)

# LOGGING options
parser.add_argument("--log_frequency",
                    type=int,
                    help="number of batches between each tensorboard log",
                    default=100)
parser.add_argument("--save_frequency",
                    type=int,
                    help="number of batches between each model save",
                    default=50000)

# GAME options
parser.add_argument("--n_actions",
                    type=int,
                    help="number of game output actions",
                    default=2)
parser.add_argument("--p_actions",
                    help="probability of game output actions",
                    default=[0.95,0.05])
parser.add_argument("--frame_size",
                    type=str,
                    help="size of game frame in pixels",
                    default=84)




if __name__ == '__main__': 
    options = parser.parse_args()

    #ModelReader = importlib.import_module('games.{}.actual.ModelReader'.format(options.game))
    options.n_actions, options.p_actions  = ModelReader.get_actions(options.game)#ModelReader.get_actions()

    if options.agent == "merlin":
        agent = MERLINAgent(options)
        # Train or evaluate agent
        if options.mode == 'train':
            agent.train(options.game)
        elif options.mode == 'eval':
            agent.play_game(options.game, options.mutant)

    elif options.agent == "random":
        agent = RandomAgent(options)
        # Train or evaluate agent
        if options.mode == 'train':
            raise ValueError("No need to train random agent.")
        elif options.mode == 'eval':
            agent.play_game(options.game, options.mutant)


