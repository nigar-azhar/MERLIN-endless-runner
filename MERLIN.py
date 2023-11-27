"""
Implementation of MERLIN based on Deep Q-Networks by the Google Brain team using State machine for reward calculation function.
"""

import os
import random
import numpy as np 
from collections import namedtuple
import torch
from tensorboardX import SummaryWriter
import importlib

# Global parameter which tells us if we have detected a CUDA capable device
CUDA_DEVICE = torch.cuda.is_available()
print(">>>>>>>>>>CUDA_DEVICE", CUDA_DEVICE)

class DQN(torch.nn.Module):

    def __init__(self, options):
        """
        Initialize a Deep Q-Network instance.
        Uses the same parameters as specified in the paper.
        """
        super(DQN, self).__init__()

        self.opt = options
        
        self.conv1 = torch.nn.Conv2d(self.opt.len_agent_history, 32, 8, 4)
        self.relu1 = torch.nn.ReLU(inplace=True)
        self.conv2 = torch.nn.Conv2d(32, 64, 4, 2)
        self.relu2 = torch.nn.ReLU(inplace=True)
        self.conv3 = torch.nn.Conv2d(64, 64, 3, 1)
        self.relu3 = torch.nn.ReLU(inplace=True)
        self.fc4 = torch.nn.Linear(3136, 512) 
        self.relu4 = torch.nn.ReLU(inplace=True)
        self.fc5 = torch.nn.Linear(512, self.opt.n_actions)


    def init_weights(self, m):
        """
        Initialize the weights of the network.

        Arguments:
            m (tensor): layer instance 
        """
        if type(m) == torch.nn.Conv2d or type(m) == torch.nn.Linear:
            torch.nn.init.uniform_(m.weight, -0.01, 0.01)
            m.bias.data.fill_(0.0)


    def forward(self, x):
        """
        Forward pass to compute Q-values for given input states.

        Arguments:
            x (tensor): minibatch of input states

        Returns:
            tensor: state-action values of size (batch_size, n_actions)
        """
        out = self.conv1(x)
        out = self.relu1(out)
        out = self.conv2(out)
        out = self.relu2(out)
        out = self.conv3(out)
        out = self.relu3(out)
        out = out.view(out.size()[0], -1)
        out = self.fc4(out)
        out = self.relu4(out)
        out = self.fc5(out)
        return out


Experience = namedtuple('Experience', ('state', 'action', 'reward', 'next_state', 'done'))

class ReplayMemory():

    def __init__(self, options):
        """
        Initialize a replay memory instance.
        Used by agent to create minibatches of experiences. Resuts in greater 
        data efficiency, reduced update variance, and smoother learning.
        """
        self.memory = []
        self.capacity = options.replay_memory_size


    def add(self, experience):
        """
        Add an experience to replay memory.

        Arguments:
            experience (Experience): add experience to replay memory 
        """
        self.memory.append(experience)

        # Remove oldest experience if replay memory full
        if len(self.memory) > self.capacity:
            self.memory.pop(0)


    def sample(self, batch_size):
        """
        Sample some transitions from replay memory.

        Arguments:
            batch_size (int): # of experiences to sample from replay memory

        Returns:
            dict: dictionary of random experiences if there are enough available, else None
        """
        if batch_size > len(self.memory):
            return None

        # Sample a batch
        sample = random.sample(self.memory, batch_size)

        # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for
        # detailed explanation). This converts batch-array of Transitions
        # to Transition of batch-arrays.
        sample = Experience(*zip(*sample))

        sample_batch = {
            'state': torch.stack(sample.state),
            'action': torch.tensor(sample.action).unsqueeze(1),
            'reward': torch.tensor(sample.reward),
            'next_state': torch.stack(sample.next_state),
            'done': torch.tensor(sample.done)
        }

        if CUDA_DEVICE:
            sample_batch['state'] = sample_batch['state'].cuda()
            sample_batch['action'] = sample_batch['action'].cuda()
            sample_batch['reward'] = sample_batch['reward'].cuda()
            sample_batch['next_state'] = sample_batch['next_state'].cuda()
            sample_batch['done'] = sample_batch['done'].cuda()

        return sample_batch



class MERLINAgent:

    def __init__(self, options):
        """
        Initialize an agent instance.
        """
        self.opt = options

        # Replay memory buffer
        self.replay_memory = ReplayMemory(self.opt)

        # Epsilon used for selecting actions
        self.epsilon = np.linspace(
            self.opt.initial_exploration, 
            self.opt.final_exploration, 
            self.opt.final_exploration_frame
        )

        # Create network
        self.net = DQN(self.opt)
        if self.opt.mode == 'train':
            self.net.apply(self.net.init_weights)
            if self.opt.weights_dir:
                print("loading weights from ","trained-weights/"+self.opt.game+"/"+self.opt.weights_dir)
                self.net.load_state_dict(torch.load("trained-weights/"+self.opt.game+"/"+self.opt.weights_dir))
        if self.opt.mode == 'eval':
            self.net.load_state_dict(torch.load("trained-weights/"+self.opt.game+"/"+self.opt.weights_dir, map_location=torch.device('cpu')))
            # self.net.eval()

        if CUDA_DEVICE:
            self.net = self.net.cuda()

        # The optimizer
        self.optimizer = torch.optim.Adam(
            self.net.parameters(),
            lr=self.opt.learning_rate
        )

        # The game instance
        self.game = None#Game(self.opt.frame_size)

        # Log to tensorBoard
        if self.opt.mode == 'train':
            self.writer = SummaryWriter("tensorboard-logs/"+self.opt.game+"/"+self.opt.exp_name)

        # Loss
        self.loss = torch.nn.MSELoss()


    def select_action(self, state, step):
        """
        Use epsilon-greedy exploration to select the next action. 
        Controls exploration vs. exploitation in the network.

        Arguments:
            state (tensor): stack of four frames
            step (int): the current training step
            
        Returns:
            int: [0, number of actions - 1]
        """
        # Make state have a batch size of 1
        state = state.unsqueeze(0)
        if CUDA_DEVICE:
            state = state.cuda()

        # Select epsilon
        step = min(step, self.opt.final_exploration_frame - 1)
        epsilon = self.epsilon[step]

        # Perform random action with probability self.epsilon. Otherwise, select
        # the action which yields the maximum reward.
        if random.random() <= epsilon:
            return np.random.choice(self.opt.n_actions, p=self.opt.p_actions)#[0.95, 0.05])
        else:
            return torch.argmax(self.net(state)[0])


    def optimize_model(self):
        """
        Performs a single step of optimization.
        Samples a minibatch from replay memory and uses that to update the net.

        Returns:
            loss (float)
        """
        # Sample a batch [state, action, reward, next_state]
        batch = self.replay_memory.sample(self.opt.batch_size)
        if batch is None:
            return

        # Compute Q(s_t, a) 
        q_batch = torch.gather(self.net(batch['state']), 1, batch['action'])
        q_batch = q_batch.squeeze()

        # Compute V(s_{t+1}) for all next states
        q_batch_1, _ = torch.max(self.net(batch['next_state']), dim=1)
        y_batch = torch.tensor(
            [batch['reward'][i] if batch['done'][i] else 
            batch['reward'][i] + self.opt.discount_factor * q_batch_1[i] 
            for i in range(self.opt.batch_size)]
        )
        if CUDA_DEVICE:
            y_batch = y_batch.cuda()
        y_batch = y_batch.detach()

        # Compute loss
        loss = self.loss(q_batch, y_batch)

        # Optimize model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss


    def train(self, gamename="flappybird"):
        """
        Main training loop.
        """

        Wrapper = importlib.import_module('games.{}.actual.wrapper'.format(gamename))
        RewardEstimatorModule = importlib.import_module('games.{}.actual.rewardEstimator'.format(gamename))
        ModelReaderModule = importlib.import_module('games.{}.actual.ModelReader'.format(gamename))
        action_time = ModelReaderModule.get_action_timeelapsed()

        folder_path = "trained-weights/"+self.opt.game+"/"+self.opt.exp_name

        # Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print("creating log and weights folder")


        # The game instance
        self.game = Wrapper.Game(self.opt.frame_size)


        # Episode lengths
        eplen = 0

        # Initialize the environment and state (do nothing)
        for _ in range(11):
            frame, reward, done = self.game.step(0)

        state = torch.cat([frame for i in range(self.opt.len_agent_history)])
        game_sate = self.game.get_game_state()
        score = game_sate['score']#['score']
        if isinstance(score, dict):
            # print("score is of type 'dict'")
            score = game_sate['score']['score']
        rewarder = RewardEstimatorModule.RewardEstimator(game_sate)

        # Start a training episode
        eplen_sum = 0
        for i in range(1, self.opt.n_train_iterations):

            # Perform an action
            action = self.select_action(state, i)
            frame, reward, done = self.game.step(action)
            #print ("***************** action is ", action)
            if action == 1:
                #print ("######## action is ", action)
                for _ in range(action_time[1]-1):
                    frame, reward, done = self.game.step(0)
                    if done:
                        break

            elif action == 2:
                # print ("######## action is ", action)
                for _ in range(action_time[2] - 1):
                    frame, reward, done = self.game.step(0)
                    if done:
                        break
                #eplen += 10
            #else:
            eplen += 1
            game_sate = self.game.get_game_state()
            reward, state_name = rewarder.estimate(game_sate, done, action)

            next_state = torch.cat([state[1:], frame])
            #self.game.take_screenshot(str(i)+"-"+state_name+".jpeg")

            # Save experience to replay memory
            self.replay_memory.add(
                Experience(state, action, reward, next_state, done)
            )

            # Perform optimization
            loss = self.optimize_model()

            # Move on to the next state
            state = next_state

            # Save network
            if i % self.opt.save_frequency == 0:
                if not os.path.exists(f'trained-weights/{self.opt.game}/{self.opt.exp_name}'):
                    os.mkdir(f'trained-weights/{self.opt.game}/{self.opt.exp_name}')
                torch.save(self.net.state_dict(), f'trained-weights/{self.opt.game}/{self.opt.exp_name}/{str(i).zfill(7)}.pt')

            # Write results to log
            if i % self.opt.log_frequency == 0:
                self.writer.add_scalar('loss', loss, i)


            #time.sleep(1)

            if done:
                f = open("trained-weights/"+self.opt.game+"/"+self.opt.exp_name+"/log.txt", "a")
                f.write('episode_length '+ str(eplen)+", "+str(i)+"\n")
                f.close()
                self.writer.add_scalar('episode_length', eplen, i)
                print('episode_length', eplen, i)
                eplen = 0
                for _ in range(11):
                    frame, reward, done = self.game.step(0)
                state = torch.cat([frame for i in range(self.opt.len_agent_history)])
                game_sate = self.game.get_game_state()
                rewarder = RewardEstimatorModule.RewardEstimator(game_sate)

            if score >= 200 or eplen >=10000:
                f = open("trained-weights/"+self.opt.game+"/"+self.opt.exp_name + "/log.txt", "a")
                f.write('episode_length ' + str(eplen) + ", " + str(i) + "\n")
                f.close()
                self.writer.add_scalar('episode_length', eplen, i)
                print('episode_length', eplen, i)

                self.game.close_game()

                eplen = 0
                self.game = Wrapper.Game(self.opt.frame_size)
                for _ in range(11):
                    frame, reward, done = self.game.step(0)
                state = torch.cat([frame for i in range(self.opt.len_agent_history)])
                game_sate = self.game.get_game_state()
                rewarder = RewardEstimatorModule.RewardEstimator(game_sate)

        torch.save(self.net.state_dict(), f'trained-weights/{self.opt.game}/{self.opt.exp_name}/{str(i).zfill(7)}.pt')
        f = open("trained-weights/"+self.opt.game+"/"+self.opt.exp_name+"/log.txt", "a")
        f.write('episode_length ' + str(eplen) + ", " + str(i) + "\n")
        f.close()
        self.writer.add_scalar('episode_length', eplen, i)
        print('episode_length', eplen, i)


    def play_game(self, gamename="flappybird", mutantname="baseline"):
        """
        Play Flappy Bird using the trained network.
        """
        Wrapper = importlib.import_module('games.{}.mutants.{}.wrapper'.format(gamename, mutantname))
        ValidatorModule = importlib.import_module('games.{}.actual.Validator'.format(gamename))
        ModelReaderModule = importlib.import_module('games.{}.actual.ModelReader'.format(gamename))
        action_time = ModelReaderModule.get_action_timeelapsed()
        #print("\n\n>>>>>>>",action_time,"\n\n")
        print(
            "\nEvaluating the mutant " + mutantname + " of game " + gamename + " using the weights in " + self.opt.weights_dir + "\n")
        tries = self.opt.tries
        if (mutantname == "ADD_02" or mutantname == "AVI_04" or mutantname == "AVD_03") and gamename == "flappybird":
            tries = 10
        current_try = 0
        mutant_killed = False
        while not mutant_killed and current_try<tries:
            current_try +=1
            print("\n\n>>>>>>>>>>> Try", current_try)
            # The flappy bird game instance
            self.game = Wrapper.Game(self.opt.frame_size)


            with torch.no_grad():
                # Initialize the environment and state (do nothing)
                frame, reward, done = self.game.step(0)

                for _ in range(10):
                    frame, reward, done = self.game.step(0)
                state = torch.cat([frame for i in range(self.opt.len_agent_history)])
                game_sate = self.game.get_game_state()
                #print("\n\n\n>>>>>>>>>> Validator reinitialized")
                validator = ValidatorModule.Validator( self.opt.exp_name, game_sate)
                validator.mutant_name = mutantname#'IRP_DSU_01'#self.opt.mutant
                validator.algo = "merlin"
                # Start playing
                ep_len = 0
                mutant_killed = False

                while True:

                    # Perform an action
                    state = state.unsqueeze(0)
                    if CUDA_DEVICE:
                        state = state.cuda()
                    action = torch.argmax(self.net(state)[0])
                    action = action.item()
                    #print(action)
                    frame, reward, done = self.game.step(action)
                    if done:
                        self.game.close_game()
                        break
                    elif action == 1:
                        #print ("######## action is ", action)
                        for _ in range(action_time[1]-1):
                            #print("repeat")
                            frame, reward, done = self.game.step(0)
                            if done:
                                self.game.close_game()
                                break
                        if done:
                            #print("\n\nEnd play-game loop\n\n")
                            break
                    elif action == 2:
                        # print ("######## action is ", action)
                        for _ in range(action_time[2] - 1):
                            frame, reward, done = self.game.step(0)
                            if done:
                                self.game.close_game()
                                break
                        if done:
                            # print("\n\nEnd play-game loop\n\n")
                            break

                    game_sate = self.game.get_game_state()
                    mutant_killed = validator.validate(game_sate,action, done)
                    score = game_sate['score']
                    if isinstance(score, dict):
                        # print("score is of type 'dict'")
                        score = game_sate['score']['score']

                    if CUDA_DEVICE:
                        frame = frame.cuda()
                    next_state = torch.cat([state[0][1:], frame])

                    # Move on to the next state
                    state = next_state

                    ep_len +=1

                    # If we lost, exit
                    if done:
                        self.game.close_game()
                        break
                    elif score >= 250:
                        self.game.close_game()
                        break
                    elif self.opt.mutant != "" and score>self.opt.score:
                        self.game.close_game()
                        break
                    elif mutant_killed:
                       self.game.close_game()
                       print("\n\n######### mutant killed\n\n")
                       break



                #print(ep_len)

                f = open("logs/mutation-testing-logs"+"/merlin/"+self.opt.game+"/mutant_log_" + gamename + ".csv", "a")
                f.write(mutantname + ", " + (
                    "mutant killed" if mutant_killed else "alive") + ", \n")
                f.close()
