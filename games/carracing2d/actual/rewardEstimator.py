import xml.etree.ElementTree as ET
#import time
#from wrapper import Game
#from game.angryBird.sprites import PIPE_LOWER

import torch

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__




filename= "games/carracing2d/actual/carracing2d.xml"
tree = ET.parse(filename)


# Get the root element
root = tree.getroot()

sm = root.find('statemachine')

allstates = sm.findall('allmystates')
allactions = root.findall('actions')
positive_reward_impacts = [float(act.find('positive_reward_impact').text) for act in allactions]

def verify_state(gamestate, previousState):
    # leftBar, rightBar, angryBird, redBall, score = gstate['leftBar'], gstate['rightBar'], gstate['angryBird'], gstate[
    #     'redBall'], gstate['score']
    # angryBird = dotdict(angryBird)
    # leftBar = dotdict(leftBar)
    # rightBar = dotdict(rightBar)
    # redBall = dotdict(redBall)

    for state in allstates:
        #print(state.find('name').text)
        if state.find('constraint') is not None:
            constraint_test = state.find('constraint').text
            #print(constraint_test)
            result = eval(constraint_test,gamestate)# {'angryBird': angryBird, 'leftBar': leftBar, 'rightBar': rightBar, 'redBall':redBall})
            if result:
                #print(constraint_test)
                return state
            #print(state.find('constraint').text)
    print(">>>>>>>>>>>>> state not found",gamestate)
    return previousState


class RewardEstimator:
    def __init__(self):
        self.current_state = None
        self.previous_state = None
        self.current_score = 0#None
        self.previous_score = 0


    def __init__(self, state):
        # leftBar, rightBar, angryBird,
        score = state['score']['score']
        #
        # angryBird = dotdict(angryBird)
        # leftBar = dotdict(leftBar)
        # rightBar = dotdict(rightBar)
        #print(angryBird)
        #print(leftBar)
        #print(rightBar)
        self.previous_score = score
        self.previous_state = verify_state(state, None)
        self.current_state = None
        #self.previous_state = None
        self.current_score = 0#None
        #self.previous_score = 0
        #self.startup= True


    def estimate(self, gstate, done, action=0):
        #print(positive_reward_impacts)
        # leftBar, rightBar, angryBird, redBall, score = state['leftBar'], state['rightBar'], state['angryBird'], state['redBall'], state['score']
        #
        # angryBird = dotdict(angryBird)
        # leftBar = dotdict(leftBar)
        # rightBar = dotdict(rightBar)
        # redBall = dotdict(redBall)
        # #print(angryBird)
        #print(leftBar)
        #print(rightBar)
        score = gstate['score']['score']
        self.current_score = score
        self.current_state = verify_state(gstate, self.previous_state)
        #print(self.current_state)
        if self.current_state is None:
            print(gstate)

            #print(leftBar)
            #print(rightBar)

        #print(self.current_state.find('name').text)
        #print(self.current_state.find('constraint').text)
        #print(self.current_state.find('stereotype').text)
        pstero = self.previous_state.find('stereotype').text
        cstero = self.current_state.find('stereotype').text
        pname = self.previous_state.find('name').text
        cname = self.current_state.find('name').text

        reward = 0
        if done:
            reward = -20
            #cstero = pstero
            #cname = pname
        elif cstero == "good" and pstero == "good":
            reward = 3 * positive_reward_impacts[action]
        elif cstero == "good" and pstero == "bad":
            reward = 2
        elif cstero == "bad" and pstero == "good":
            reward = -1
        elif cstero == "bad" and pstero == "bad":
            reward = -2
        elif cstero == "bad" and pstero == "dead":
            reward = -2
        elif cstero == "dead" and pstero == "bad":
            reward = -5
        elif cstero == "dead" and pstero == "dead":
            reward = -7
        elif cstero == None and pstero == "good":
            reward = -0.1
        elif cstero == None and pstero == "bad":
            reward = 0.5
        elif cstero == None and pstero == None:
            reward = 0.1
        #elif pstero == "dead":
        #    reward = -5
        if self.current_score > self.previous_score:
            reward += (10 + (self.current_score - self.previous_score))

        self.previous_state = self.current_state
        self.previous_score = self.current_score
        #print (gstate)
        #print("reward for state: (", pname,")", pstero, "->(", cname,")", cstero, "is", reward)
        # if pname !=cname:
        #     print("reward for state: (", pname, ")", pstero, "->(", cname, ")", cstero, "is", reward)
        #print()
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
# leftBar, rightBar, angryBird, score = game.get_game_state()
# rewarder = RewardEstimator(leftBar, rightBar, angryBird, score)
#
# #game.step(True)
# #angryBird = dotdict(angryBird)
# #leftBar = dotdict(leftBar)
# #rightBar = dotdict(rightBar)
# #print(angryBird)
# #print(leftBar)
# #print(rightBar)
# #prev_state = verify_state(angryBird, leftBar, rightBar)
# #prev_score = score
# for i in range(30):
#     print("\n\n Step "+str(i)+"\n\n")
#     frame, reward, done = game.step(False)
#     leftBar, rightBar, angryBird, score = game.get_game_state()
#     reward = rewarder.estimate(leftBar, rightBar, angryBird, score)
#
#     # Define variables
#     #twidth = pipes[0].pipe_width
#     #thgt = pipes[0].get_pipe_Hieght()#image.get_height()#.image.get_width()#,.get_pipe_Hieght()#PIPE_LOWER.get_height()
#
#     #bwidth = pipes[1].pipe_width
#     #bhgt = pipes[0].get_pipe_Hieght()#image.get_height()#.image.get_width()#,get_pipe_Hieght()# PIPE_LOWER.get_height()
#     #angryBird = {'yCoordinate': player.y, 'xCoordinate': player.x}
#     #leftBar = {'yCoordinate': pipes[0].y+thgt, 'xCoordinate': pipes[0].x}
#     #rightBar = {'yCoordinate': pipes[1].y+bhgt, 'xCoordinate': pipes[1].y}
#     # angryBird = dotdict(angryBird)
#     # leftBar = dotdict(leftBar)
#     # rightBar = dotdict(rightBar)
#     # print(angryBird)
#     # print(leftBar)
#     # print(rightBar)
#     # current_state = verify_state(angryBird, leftBar, rightBar)
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
