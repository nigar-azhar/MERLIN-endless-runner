import re
import xml.etree.ElementTree as ET
import ModelReader
import json

# class dotdict(dict):
#     """dot.notation access to dictionary attributes"""
#     __getattr__ = dict.get
#     __setattr__ = dict.__setitem__
#     __delattr__ = dict.__delitem__



def get_current_values(state):
    return state


def get_previous_values(gstate):

    previous = {}
    for key, value in gstate.items():

        if key not in ['__builtins__']:
            key = str(key)
            if key.startswith('previous'):
                continue
            previous[f'previous{key}'] = value
    #print(previous)
    return previous
# def get_previous_values(state):
#     print(state)
#     return {'previousPlayer': state['player'], 'previousScore': state['score']}


class Validator:
    def __init__(self,exp_name, gamename= 'angrywalls'):
        self.gamename = gamename
        self.sm = None
        self.allstates = None
        self.allactions = None
        self.score_impacts = None
        self.booster_durations = None
        self.loadmodel(gamename)

        self.current_state = None
        self.previous_state = None
        self.current_score = 0#None
        self.previous_score = 0
        self.exp_name = exp_name
        self.mutant_name = ""
        self.history = []
        self.history_length = -1



    def __init__(self, exp_name, state, gamename= 'angrywalls'):
        self.gamename = gamename
        self.sm = None
        self.allstates = None
        self.allactions = None
        self.score_impacts = None
        self.booster_durations = None
        self.loadmodel(gamename)


        self.previous_score = state['score'] if (self.gamename != "carracing2d") else state['score']['score']#state['score']['score']
        state['action'] = 0


        self.previous_state = self.verify_state(state, None)
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


    def loadmodel(self, gamename='angrywalls'):
        self.gamename = gamename
        filename = "games/" + gamename + "/actual/" + gamename + ".xml"
        tree = ET.parse(filename)

        # Get the root element
        root = tree.getroot()

        self.sm = root.find('statemachine')

        self.allstates = self.sm.findall('allmystates')
        self.allactions = root.findall('actions')
        self.actions = ModelReader.get_action_names(gamename)
        print("=======HELLY======")
        print(self.actions)
        print("=============")
        self.score_impacts = ModelReader.get_score_impacts(gamename)
        self.booster_durations = ModelReader.get_boosterdurations(gamename)

    def validate(self, state, action, done):
        if "__builtins__" in state:
            print("Removing builtins from gstate")
            del state["__builtins__"]



        scoreupdate = state['scoreupdate']

        #scoreupdate = dotdict(scoreupdate)

        state[action] = 0

        self.current_score = state['score'] if (self.gamename != "carracing2d") else state['score']['score']#state['score']['score']
        #score = state['score']['score']
        self.current_state = self.verify_state(state, self.previous_state)

        action = self.actions[action]# "doNothing()

        state['action'] = action
        state['state'] = self.current_state.find('name').text

        #print(state)
        flag = False
        bugFound = False
        state_json_string = json.dumps({key: value for key, value in state.items() if key != '__builtins__'})

        #check if action effect has taken place
        action_verification = True
        booster_verification = True

        # check if action effect has taken place
        if not self.first:
            # print(";;;;;;;;;;;;;;;;;;;;")
            # print ("HERE")
            # print(";;;;;;;;;;;;;;;;;;;;")
            action_verification = self.verify_action_effect(state, self.history[-1])

        if not action_verification:
            self.updateLog(action, state, True, " Action did not perform as expected ")
            bugFound=True

        if self.booster_durations is not None:
            booster_verification = self.verify_booster_effect(state, self.history[-1])

        if not booster_verification:
            self.updateLog(action, state, True, " Booster Effect did not perform as expected ")
            bugFound=True


        ingoingTransition = ""
        for transition in self.previous_state.findall('outgoingTransitions'):
            if transition.find('name') is not None:
                tname = transition.find('name').text
                if transition.find('name').text != "":
                    tname = "any"
            else:
                tname = "any"

            if tname == action or tname == "any":

                if transition.find('guard') is not None:
                    guard_text = transition.find('guard').text
                    #print(guard_text)
                    if guard_text is not None:
                        #print(self.previous_state.find('name').text, guard_text)
                        guard_text = re.sub(r'(\b\w+)\.(\w+)', r'\1["\2"]', guard_text)

                        result = eval(guard_text, get_current_values(state))
                        if result:
                            #print(tname, guard_text)
                            #print(guard_text)
                            destinationStateName = transition.find("targetName").text
                            flag = True
                            ingoingTransition = "action { "+guard_text+" }"
                            if self.current_state.find("name").text == destinationStateName:
                                self.updateLog(action, state)
                                break
                            else:
                                self.updateLog(action, state, True, "  Actual State doesnot match expected state  "+ destinationStateName)
                                bugFound = True

                            #check if state has dead stereotype
                            destState = self.find_state_by_name(destinationStateName)
                            if destState.find("stereotype").text == "dead":
                                if not done:
                                    self.updateLog(action, state, True, "  Failed to close upon dead state   ")
                                    print("####################################################=====")

                                    bugFound = True
                    elif self.previous_state.find("stereotype").text == "dead":
                        self.updateLog(action, state, True, "  Failed to close upon dead state   ")
                        print("####################################################")

                        bugFound = True

            else:
                if transition.find('guard') is not None:
                    guard_text = transition.find('guard').text
                    #print(guard_text)
                    guard_text = re.sub(r'(\b\w+)\.(\w+)', r'\1["\2"]', guard_text)
                    #print(guard_text)
                    if guard_text is not None:
                        result = eval(guard_text, state)
                        #print(result)  #
                        if result:
                            #print(tname, guard_text)
                            destinationStateName = transition.find("targetName").text
                            flag = True
                            if self.current_state.find("name").text == destinationStateName:
                                #print ("validation satisfied"+", "+self.previous_state.find("name").text+", "+ tname+", "+guard_text+", "+destinationStateName+", "+self.current_state.find("name").text +", "+str( angryBird)+", "+str(leftBar)+", "+str(rightBar)+", "+str(score)+" \n")
                                self.updateLog(action, state, True, "  action is faulty doesnot perform as expected  ")


        if not flag:
            #print("No valid transition found <<ERROR>>")
            self.updateLog(action, state, True, "  No valid transition found ")
            bugFound = True


        delta = self.current_score - self.previous_score
        #bugFound = False

        # Sum expected deltas
        expected_total = 0
        triggered = []

        for key, expected_delta in self.score_impacts.items():
            if scoreupdate[key]:
                expected_total += expected_delta
                triggered.append(key)

        if expected_total != 0:
            if delta != expected_total:
                self.updateLog(
                    action, state, True,
                    f"Incorrect reward: expected addition of {expected_total}, got {delta} (triggers: {', '.join(triggered)})"
                )
                bugFound = True
        elif delta != 0:
            # Score changed, but no valid trigger
            self.updateLog(
                action, state, True,
                f"Unexpected score change: delta {delta} without valid trigger"
            )
            bugFound = True

        state['ingoingTransition'] = ingoingTransition
        self.history.append(state)
        self.history_length += 1

        gamefroze = self.checkGameFreeze()

        if gamefroze:
            self.updateLog(action, state, True, "  Game Froze ")

        self.previous_score = self.current_score
        self.previous_state = self.current_state

        bugFound = gamefroze or bugFound
        self.first = False
        # print(";;;;;;;;;;;;;;;;;;;;")
        # print("self.first", self.first)
        # print(";;;;;;;;;;;;;;;;;;;;")

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

    def updateLog(self, action, state, buggy = False, comment=" ... " ):
        if buggy:
            bugStr = "bug encountered"
        else:
            bugStr = "validation satisfied"

        state_json_string = json.dumps({key: value for key, value in state.items() if key != '__builtins__'})
        f = open(
            "logs/mutation-testing-logs" + "/" + self.algo + "/"+ self.gamename + "/bug_log_" + self.mutant_name + ".tsv",
            "a")
        f.write(bugStr + "\t" + self.previous_state.find(
            "name").text + "\t" + action + "\t \t \t " + self.current_state.find("name").text + " \t " + state_json_string
             + "\t" + str(self.previous_score) + "\t" + comment + " \n")
        print(bugStr + "\t" + self.previous_state.find(
            "name").text + "\t" + action + "\t \t \t " + self.current_state.find("name").text + " \t " + state_json_string
             + "\t" + str(self.previous_score) + "\t" + comment + " \n")
        f.close()

    def verify_state(self, gstate, previousState):

        for state in self.allstates:
            if state.find('constraint') is not None:
                constraint_test = state.find('constraint').text
                # Convert dot notation to dictionary-style access
                constraint_test = re.sub(r'(\b\w+)\.(\w+)', r'\1["\2"]', constraint_test)
                #print(constraint_test)
                result = eval(constraint_test, gstate)
                if result:
                    # print(state.find('name').text)
                    return state
                # print(state.find('constraint').text)
        print(">>>>>>>>>>>>> state not found", gstate)
        return previousState

    def find_state_by_name(self, statename):
        for state in self.allstates:
            # print(state.find('name').text)
            if state.find('name').text == statename:
                return state
                # print(state.find('constraint').text)

        return None  # None

    def verify_action_effect(self, gamestate, previous_game_State):
        # print("+++++++++++++++++++")
        # print("verify action")
        # print("+++++++++++++++++++")

        for action in self.allactions:

            if action.find('name').text == gamestate['action']:
                required_values = get_current_values(gamestate)
                required_values.update(get_previous_values(previous_game_State))
                if "__builtins__" in required_values:
                    #print("Removing builtins from gstate")
                    del required_values["__builtins__"]
                #print(required_values)
                action_effect = action.find('effect').text
                action_effect = re.sub(r'(\b\w+)\.(\w+)', r'\1["\2"]', action_effect)
                #print(previous_game_State)
                print(action_effect)


                result = eval(action_effect,
                              required_values)  # {'angryBird': angryBird, 'leftBar': leftBar, 'rightBar': rightBar}
                print(action_effect, result)
                return result

        # print("\n\naction not found\n\n")
        return None

    def verify_booster_effect(self, gamestate, previous_game_State):

        for booster in self.booster_durations.items():
            # print(booster[1])
            required_values = get_current_values(gamestate)
            required_values.update(get_previous_values(previous_game_State))
            if "__builtins__" in required_values:
                # print("Removing builtins from gstate")
                del required_values["__builtins__"]
            # print(required_values)
            booster_effect = booster[1]['effect']
            booster_effect = re.sub(r'(\b\w+)\.(\w+)', r'\1["\2"]', booster_effect)

            result = eval(booster_effect,
                          required_values)  # {'angryBird': angryBird, 'leftBar': leftBar, 'rightBar': rightBar}
            # print(action_effect, result)
            # if required_values[booster[0]]['isActive']:
            #     print("================")
            #     print("================")
            #     print(required_values)
            #     print("================")
            #     print("================")
            return (not required_values[booster[0]]['isActive']) or (result  and (required_values[booster[0]]['timeElapsed'] > 0) and (required_values[booster[0]]['timeElapsed'] <= booster[1]['boosterDuration']))

        # print("\n\naction not found\n\n")
        return None

