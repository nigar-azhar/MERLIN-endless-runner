import xml.etree.ElementTree as ET
#import time
from games.flappybird.actual.wrapper import Game
#from game.flappybird.sprites import PIPE_LOWER

import torch

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__




filename= "games/flappybird/actual/flappybird_model.xml"
tree = ET.parse(filename)


# Get the root element
root = tree.getroot()

sm = root.find('statemachine')

allstates = sm.findall('allmystates')

def verify_state(flappyBird, topPipe, bottomPipe, previousState):
    for state in allstates:
        #print(state.find('name').text)
        if state.find('constraint') is not None:
            constraint_test = state.find('constraint').text
            result = eval(constraint_test, {'flappyBird': flappyBird, 'topPipe': topPipe, 'bottomPipe': bottomPipe})
            if result:
                return state
            #print(state.find('constraint').text)

    return previousState


class RewardEstimator:
    def __init__(self):
        self.current_state = None
        self.previous_state = None
        self.current_score = 0#None
        self.previous_score = 0


    def __init__(self, game_state):
        topPipe, bottomPipe, flappyBird, score = game_state["topPipe"], game_state["bottomPipe"], game_state["flappyBird"], game_state["score"]
        flappyBird = dotdict(flappyBird)
        topPipe = dotdict(topPipe)
        bottomPipe = dotdict(bottomPipe)
        #print(flappyBird)
        #print(topPipe)
        #print(bottomPipe)
        self.previous_score = score
        self.previous_state = verify_state(flappyBird, topPipe, bottomPipe, None)
        self.current_state = None
        #self.previous_state = None
        self.current_score = 0#None
        #self.previous_score = 0
        #self.startup= True


    def estimate(self, game_state, done, action=0):
        topPipe, bottomPipe, flappyBird, score = game_state["topPipe"], game_state["bottomPipe"], game_state["flappyBird"], game_state["score"]
        flappyBird = dotdict(flappyBird)
        topPipe = dotdict(topPipe)
        bottomPipe = dotdict(bottomPipe)
        #print(flappyBird)
        #print(topPipe)
        #print(bottomPipe)
        self.current_score = score
        self.current_state = verify_state(flappyBird, topPipe, bottomPipe, self.previous_state)
        if self.current_state is None:
            print(flappyBird)
            print(topPipe)
            print(bottomPipe)

        #print(self.current_state.find('name').text)
        #print(self.current_state.find('constraint').text)
        #print(self.current_state.find('stereotype').text)
        pstero = self.previous_state.find('stereotype').text
        cstero = self.current_state.find('stereotype').text
        pname = self.previous_state.find('name').text
        cname = self.current_state.find('name').text

        reward = 0
        if done:
            reward = -10
            cstero = pstero
            cname = pname
        elif cstero == "good" and pstero == "good":
            reward = 2
        elif cstero == "good" and pstero == "bad":
            reward = 1
        elif cstero == "bad" and pstero == "good":
            reward = -1
        elif cstero == "bad" and pstero == "bad":
            reward = -2
        elif cstero == "bad" and pstero == "dead":
            reward = -1
        elif cstero == "dead" and pstero == "bad":
            reward = -5
        elif cstero == "dead" and pstero == "dead":
            reward = -5
        #elif pstero == "dead":
        #    reward = -5
        if self.current_score > self.previous_score:
            reward += 10

        self.previous_state = self.current_state
        self.previous_score = self.current_score
        #print("reward for state: (", pname,")", pstero, "->(", cname,")", cstero, "is", reward)
        #self.startup = False
        return reward, self.current_state.find('name').text

#
# CUDA_DEVICE = torch.cuda.is_available()
# print("CUDA", CUDA_DEVICE)
#
# game = Game(84)
# for i in range(10):
#     game.step(False)
#
#
# topPipe, bottomPipe, flappyBird, score = game.get_game_state()
# rewarder = RewardEstimator(topPipe, bottomPipe, flappyBird, score)
#
# #game.step(True)
# #flappyBird = dotdict(flappyBird)
# #topPipe = dotdict(topPipe)
# #bottomPipe = dotdict(bottomPipe)
# #print(flappyBird)
# #print(topPipe)
# #print(bottomPipe)
# #prev_state = verify_state(flappyBird, topPipe, bottomPipe)
# #prev_score = score
# for i in range(30):
#     print("\n\n Step "+str(i)+"\n\n")
#     frame, reward, done = game.step(False)
#     topPipe, bottomPipe, flappyBird, score = game.get_game_state()
#     reward = rewarder.estimate(topPipe, bottomPipe, flappyBird, score)
#
#     # Define variables
#     #twidth = pipes[0].pipe_width
#     #thgt = pipes[0].get_pipe_Hieght()#image.get_height()#.image.get_width()#,.get_pipe_Hieght()#PIPE_LOWER.get_height()
#
#     #bwidth = pipes[1].pipe_width
#     #bhgt = pipes[0].get_pipe_Hieght()#image.get_height()#.image.get_width()#,get_pipe_Hieght()# PIPE_LOWER.get_height()
#     #flappyBird = {'yCoordinate': player.y, 'xCoordinate': player.x}
#     #topPipe = {'yCoordinate': pipes[0].y+thgt, 'xCoordinate': pipes[0].x}
#     #bottomPipe = {'yCoordinate': pipes[1].y+bhgt, 'xCoordinate': pipes[1].y}
#     # flappyBird = dotdict(flappyBird)
#     # topPipe = dotdict(topPipe)
#     # bottomPipe = dotdict(bottomPipe)
#     # print(flappyBird)
#     # print(topPipe)
#     # print(bottomPipe)
#     # current_state = verify_state(flappyBird, topPipe, bottomPipe)
#     #
#     # print(current_state.find('name').text)
#     # print(current_state.find('constraint').text)
#     # print(current_state.find('stereotype').text)
#     # pstero = prev_state.find('stereotype').text
#     # cstero = current_state.find('stereotype').text
#     # reward = 0
#     # if cstero == "good" and pstero == "good":
#     #     reward = 2
#     # elif cstero == "good" and pstero == "bad":
#     #     reward = 1
#     # elif cstero == "bad" and pstero == "good":
#     #     reward = -1
#     # elif cstero == "bad" and pstero == "bad":
#     #     reward = -2
#     # elif cstero == "bad" and pstero == "dead":
#     #     reward = -1
#     # elif cstero == "dead" and pstero == "bad":
#     #     reward = -5
#     # if score > prev_score:
#     #     reward+=5
#     #
#     # prev_state = current_state
#     # prev_score = score
#     # print("reward for state:",pstero,"->",cstero,"is",reward)
#
#     time.sleep(1)
#
