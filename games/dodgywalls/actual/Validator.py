import json
import xml.etree.ElementTree as ET
#import time
#from wrapper import Game
#from game.angrybird.sprites import PIPE_LOWER

import torch

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__




filename= "games/dodgywalls/actual/dodgywalls_model.xml"
#filename= "dodgywalls.xml"
tree = ET.parse(filename)


# Get the root element
root = tree.getroot()

sm = root.find('statemachine')

allstates = sm.findall('allmystates')

allactions = root.findall('actions')

def get_current_values(state):
    return {'ball': state.ball, 'bar': state.bar, 'collectable': state.collectable, 'score':state.score}


def get_previous_values(state):
    return {'previousball': state.ball, 'previousbar': state.bar, 'previouscollectable': state.collectable, 'previousscore':state.score}

def verify_action_effect(gamestate, previous_game_State):

    for action in allactions:

        if action.find('name').text == gamestate['action']:
            required_values = get_current_values(gamestate)
            required_values.update(get_previous_values(previous_game_State))
            #print(required_values)
            action_effect = action.find('effect').text
            #print (action_effect, required_values)

            result = eval(action_effect, required_values)  # {'angryBird': angryBird, 'leftBar': leftBar, 'rightBar': rightBar}
            #print(action_effect, result)
            return result

    #print("\n\naction not found\n\n")
    return None


def verify_state(game_state, previousState):
    for state in allstates:
        #print(state.find('name').text)
        if state.find('constraint') is not None:
            constraint_test = state.find('constraint').text
            result = eval(constraint_test, get_current_values(game_state))#{'angryBird': angryBird, 'leftBar': leftBar, 'rightBar': rightBar}
            if result:
                return state
            #print(state.find('constraint').text)

    return previousState#None

def find_state_by_name(statename):
    for state in allstates:
        #print(state.find('name').text)
        if state.find('name').text == statename:
            return state
            #print(state.find('constraint').text)

    return None#None


actions = ['doNothing()', 'click()'] #0,1

class Validator:
    def __init__(self,exp_name):
        self.current_state = None
        self.previous_state = None
        self.current_score = 0#None
        self.previous_score = 0
        self.exp_name = exp_name
        self.mutant_name = ""
        self.history = []
        self.history_length = -1
        self.first = True



    def __init__(self, exp_name, state ):
        ball, bar, collectable, score, scoreupdate = state['ball'], state['bar'], state['collectable'], state['score'], state['scoreupdate']

        ball = dotdict(ball)
        bar = dotdict(bar)
        collectable = dotdict(collectable)
        scoreupdate = dotdict(scoreupdate)
        #print(angryBird)
        #print(leftBar)
        #print(rightBar)
        self.previous_score = score
        state = {
            'ball': ball,
            'bar': bar,
            'collectable': collectable,
            'scoreupdate': scoreupdate,
            'score': 0,
            'action': 0
        }
        state = dotdict(state)

        self.previous_state = verify_state(state, None)
        self.current_state = None
        #self.previous_state = None
        self.current_score = 0#None
        #self.previous_score = 0
        self.exp_name = exp_name
        self.mutant_name = ""
        state['state'] = self.previous_state.find('name').text
        state['ingoingTransition'] =  "init"
        #state = dotdict(state)
        self.history = []
        self.history.append(state)
        self.history_length = 0
        self.algo= "random"
        self.first = True


    def validate(self, state, action, done):
        ball, bar, collectable, score, scoreupdate = state['ball'], state['bar'], state['collectable'], state['score'], \
                                                     state['scoreupdate']

        ball = dotdict(ball)
        bar = dotdict(bar)
        collectable = dotdict(collectable)
        scoreupdate = dotdict(scoreupdate)

        #self.previous_score = score
        state = {
            'ball': ball,
            'bar': bar,
            'collectable': collectable,
            'scoreupdate': scoreupdate,
            'score': score,
            'action': 0
        }
        state = dotdict(state)

        statevalues = state
        self.current_score = score
        self.current_state = verify_state(state, self.previous_state)
        # if self.current_state is None:
        #     print(angryBird)
        #     print(leftBar)
        #     print(rightBar)

        action = actions[action]# "doNothing()

        state['action'] = action
        state['state'] = self.current_state.find('name').text

        #print(state)
        flag = False
        bugFound = False
        action_verification = True

        #check if action effect has taken place
        if not self.first:
            action_verification = verify_action_effect(state, self.history[-1])
        #print("\n\n\n\n\n",action_verification)
        if not action_verification:
            # f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls" + "/bug_log_" + self.mutant_name + ".tsv", "a")
            # f.write("bug encountered" + "\t" + self.previous_state.find(
            #     "name").text + "\t" + action + "\t \t \t " + self.current_state.find("name").text + " \t " + str(
            #     statevalues) + "\t" + str(
            #     score) + "\t" + str(self.previous_score) + "\t" + " Action did not perform as expected " + " \n")
            # f.close()
            self.updateLog(action, state, True, "  Action did not perform as expected ")
            bugFound=True

        #print(self.previous_state.find("name").text)
        ingoingTransition = ""
        for transition in self.previous_state.findall('outgoingTransitions'):
            if transition.find('name') is not None:
                tname = transition.find('name').text
                if transition.find('name').text != "":
                    tname = "any"
            else:
                tname = "any"
                #print("any")
            #print(tname)
            if tname == action or tname == "any":

                if transition.find('guard') is not None:
                    guard_text = transition.find('guard').text
                    #print(guard_text)
                    if guard_text is not None:
                        result = eval(guard_text, get_current_values(state))
                        #print(result)  #
                        if result:
                            #print(tname, guard_text)
                            #print(guard_text)
                            destinationStateName = transition.find("targetName").text
                            flag = True
                            ingoingTransition = "action { "+guard_text+" }"
                            if self.current_state.find("name").text == destinationStateName:
                                #print("validation satisfied")
                                #print ("validation satisfied"+", "+self.previous_state.find("name").text+", "+ tname+", "+guard_text+", "+destinationStateName+", "+self.current_state.find("name").text +", "+str( angryBird)+", "+str(leftBar)+", "+str(rightBar)+", "+str(score)+" \n")

                                # f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls"+"/bug_log_"+self.mutant_name+".tsv", "a")
                                # f.write("validation satisfied"+"\t"+self.previous_state.find("name").text+"\t"+ tname+"\t"+guard_text+"\t"+destinationStateName+"\t"+self.current_state.find("name").text +"\t"+str( statevalues)+"\t"+str(score) +"\t"+ str(self.previous_score)+" \n")
                                # f.close()
                                self.updateLog(action, state)
                            else:
                                #print("bug encountered")
                                #print("bug encountered"+", "+self.previous_state.find("name").text+", "+ tname+", "+guard_text+", "+destinationStateName+", "+self.current_state.find("name").text +", "+str( angryBird)+", "+str(leftBar)+", "+str(rightBar)+", "+str(score) +"\t"+ str(self.previous_score)+" \n")

                                # f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls"+"/bug_log_"+self.mutant_name+".tsv", "a")
                                # f.write("bug encountered"+"\t"+self.previous_state.find("name").text+"\t"+ tname+"\t"+
                                #         guard_text+"\t"+destinationStateName+"\t"+self.current_state.find("name").text
                                #         +"\t"+str( statevalues)+"\t"+str(score) +"\t"+ str(self.previous_score)
                                #         + "\t"+" Actual State doesnot match expected state "+ " \n")
                                # f.close()
                                self.updateLog(action, state, True, "  Failed to close upon dead state ")
                                bugFound = True

                            #check if state has dead stereotype
                            # destState = find_state_by_name(destinationStateName)
                            # if destState.find("stereotype").text == "dead":
                            #     if not done:
                            #         f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls"+"/bug_log_"+self.mutant_name+".tsv", "a")
                            #         f.write("bug encountered" + "\t" + self.previous_state.find(
                            #             "name").text + "\t" + tname + "\t" + guard_text + "\t" + destinationStateName + "\t" + self.current_state.find(
                            #             "name").text + "\t" + str(statevalues) + "\t" + str(score) +"\t"+ str(self.previous_score) + "\t"+" Failed to close upon dead state "+ " \n")
                            #         f.close()
                            #         bugFound = True
                    elif self.previous_state.find("stereotype").text == "dead" and self.current_state.find("stereotype").text == "dead" and not done:
                        # f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls" + "/bug_log_" + self.mutant_name + ".tsv", "a")
                        # f.write("bug encountered" + "\t" + self.previous_state.find(
                        #     "name").text + "\t" + "empty" + "\t" + ""+ "\t" + "final" + "\t"
                        #         + "\t" + str(statevalues) + "\t" + str(score) +"\t"+ str(self.previous_score) + "\t" + " Failed to close upon dead state " + " \n")
                        # f.close()
                        self.updateLog(action, state, True, "  Failed to close upon dead state ")
                        bugFound = True
            else:
                if transition.find('guard') is not None:
                    guard_text = transition.find('guard').text
                    #print(guard_text)
                    if guard_text is not None:
                        result = eval(guard_text, get_current_values(statevalues))#{'angryBird': angryBird, 'leftBar': leftBar, 'rightBar': rightBar})
                        #print(result)  #
                        if result:
                            #print(tname, guard_text)
                            #print(guard_text)
                            destinationStateName = transition.find("targetName").text
                            flag = True
                            if self.current_state.find("name").text == destinationStateName:
                                #print("validation satisfied")
                                #print ("validation satisfied"+", "+self.previous_state.find("name").text+", "+ tname+", "+guard_text+", "+destinationStateName+", "+self.current_state.find("name").text +", "+str( angryBird)+", "+str(leftBar)+", "+str(rightBar)+", "+str(score)+" \n")

                                # f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls"+"/bug_log_"+self.mutant_name+".tsv", "a")
                                # f.write("bug encountered"+"\t"+self.previous_state.find("name").text+"\t"+ tname+"\t"+guard_text+"\t"+destinationStateName+"\t"+self.current_state.find("name").text +"\t"+str( angryBird)+"\t"+str(leftBar)+"\t"+str(rightBar)+"\t"+str(score) +"\t"+ str(self.previous_score)+"\t action is faulty doesnot perform as expected \n")
                                # f.close()
                                self.updateLog(action, state, True, "  action is faulty doesnot perform as expected ")


        if not flag:
            #print("No valid transition found <<ERROR>>")
            # f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls"+"/bug_log_"+self.mutant_name+".tsv", "a")
            # f.write("bug encountered" + "\t" + self.previous_state.find(
            #     "name").text + "\t" + action + "\t \t \t "+self.current_state.find("name").text+" \t " + str(statevalues) + "\t" + str(
            #     score) +"\t"+ str(self.previous_score) + "\t" + " No valid transition found " + " \n")
            # f.close()
            self.updateLog(action, state, True, "  No valid transition found ")
            bugFound = True

        # if self.previous_score != self.current_score:
        #
        #     if (self.current_score != self.previous_score + 1 and scoreupdate.bar) or (self.current_score != self.previous_score + 5 and scoreupdate.ball):
        #         #print("Incorrect reward")
        #
        #         f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls"+"/bug_log_"+self.mutant_name+".tsv", "a")
        #         f.write("bug encountered" + "\t" + self.previous_state.find(
        #             "name").text + "\t" + action + "\t \t \t "+
        #                 self.current_state.find("name").text+" \t " + str(statevalues) + "\t" + str(
        #             score) +"\t"+ str(self.previous_score) + "\t" + " incorrect reward " + " \n")
        #         f.close()
        #         bugFound = True

        if scoreupdate.bar and not scoreupdate.dot and (self.current_score != self.previous_score + 1 or self.current_score != self.previous_score + 6):
            #f = open("mutation-testing-logs" + "/"+self.algo+"/dodgywalls" + "/bug_log_" + self.mutant_name + ".tsv", "a")
            # f.write("bug encountered" + "\t" + self.previous_state.find(
            #     "name").text + "\t" + action + "\t \t \t " +
            #         self.current_state.find("name").text + " \t " + str(statevalues) + "\t" + str(
            #     score) + "\t" + str(self.previous_score) + "\t" + " Incorrect Reward " + " \n")
            # f.close()
            self.updateLog(action, state, True, "  Incorrect Reward for bar and dot ")
            bugFound = True

        if scoreupdate.dot and not scoreupdate.bar and self.current_score != self.previous_score + 5:
            f = open("mutation-testing-logs" + "/"+self.algo+"/dodgywalls" + "/bug_log_" + self.mutant_name + ".tsv", "a")
            # f.write("bug encountered" + "\t" + self.previous_state.find(
            #     "name").text + "\t" + action + "\t \t \t " +
            #         self.current_state.find("name").text + " \t " + str(statevalues) + "\t" + str(
            #     score) + "\t" + str(self.previous_score) + "\t" + " Incorrect Reward " + " \n")
            # f.close()
            self.updateLog(action, state, True, "  Incorrect Reward for dot")
            bugFound = True

        if scoreupdate.dot and scoreupdate.bar and self.current_score != self.previous_score + 6:
            # f = open("mutation-testing-logs" + "/"+self.algo+"/dodgywalls" + "/bug_log_" + self.mutant_name + ".tsv", "a")
            # f.write("bug encountered" + "\t" + self.previous_state.find(
            #     "name").text + "\t" + action + "\t \t \t " +
            #         self.current_state.find("name").text + " \t " + str(statevalues) + "\t" + str(
            #     score) + "\t" + str(self.previous_score) + "\t" + " Incorrect Reward " + " \n")
            # f.close()
            self.updateLog(action, state, True, "  Incorrect Reward for bar")
            bugFound = True
        #if action == "doNothing()":

        state['ingoingTransition'] = ingoingTransition
        self.history.append(state)
        self.history_length += 1

        gamefroze = self.checkGameFreeze()

        if gamefroze:
            #print("Game froze")
            # f = open("mutation-testing-logs"+"/"+self.algo+"/dodgywalls" + "/bug_log_" + self.mutant_name + ".tsv", "a")
            # f.write("bug encountered" + "\t" + self.previous_state.find(
            #     "name").text + "\t" + action + "\t \t \t " + self.current_state.find("name").text + " \t " + str(
            #     statevalues) + "\t" + str(
            #     score) + "\t" + str(self.previous_score) + "\t" + " Game Froze " + " \n")
            # f.close()
            self.updateLog(action, state, True, "  Game Froze ")

        self.previous_score = self.current_score
        self.previous_state = self.current_state

        bounds = not self.isPlayerinBounds(statevalues)
        bugFound = gamefroze or bugFound or bounds

        self.first = False
        return bugFound

    def checkStateEquality(self, state1, state2):
        state1['ingoingTransition'] = ''
        state2['ingoingTransition'] = ''
        state1['action'] = 0
        state2['action'] = 0
        return  state1 == state2

    def checkGameFreeze(self):
        if self.history_length > 100:
            for i in range (0,99):
                if not self.checkStateEquality(self.history[self.history_length-i],self.history[self.history_length-(i+1)]):
                    return False

            return True
        return False

    def isPlayerinBounds(self, statevalues):
        if statevalues.ball.xCoordinate <0 or statevalues.ball.xCoordinate > 228 or statevalues.ball.yCoordinate < 181 or statevalues.ball.yCoordinate >325:
            return False
        return True

    def updateLog(self, action, state, buggy = False, comment=" ... " ):
        if buggy:
            bugStr = "bug encountered"
        else:
            bugStr = "validation satisfied"

        state_json_string = json.dumps({key: value for key, value in state.items() if key != '__builtins__'})

        f = open(
            "logs/mutation-testing-logs" + "/" + self.algo + "/dodgywalls" + "/bug_log_" + self.mutant_name + ".tsv",
            "a")
        f.write(bugStr + "\t" + self.previous_state.find(
            "name").text + "\t" + action + "\t \t \t " + self.current_state.find("name").text + " \t " + state_json_string
             + "\t" + str(self.previous_score) + "\t" + comment + " \n")
        f.close()


