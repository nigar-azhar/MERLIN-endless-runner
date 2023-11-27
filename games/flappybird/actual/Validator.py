import xml.etree.ElementTree as ET
import json


class dotdict(dict):
    """a utility function for dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__




filename= "games/flappybird/actual/flappybird_model.xml"
tree = ET.parse(filename)


# Get the root element
root = tree.getroot()

sm = root.find('statemachine')

allstates = sm.findall('allmystates')

allactions = root.findall('actions')

def get_current_values(state):
    return {'flappyBird': state.flappyBird, 'topPipe': state.topPipe, 'bottomPipe': state.bottomPipe}


def get_previous_values(state):
    return {'previousflappyBird': state.flappyBird, 'previoustopPipe': state.topPipe, 'previousbottomPipe': state.bottomPipe}

def verify_action_effect(gamestate, previous_game_State):

    for action in allactions:

        if action.find('name').text == gamestate['action']:
            required_values = get_current_values(gamestate)
            required_values.update(get_previous_values(previous_game_State))
            #print(required_values)
            action_effect = action.find('effect').text

            result = eval(action_effect, required_values)  # {'flappyBird': flappyBird, 'topPipe': topPipe, 'bottomPipe': bottomPipe}
            #print(action_effect, result)
            return result

    #print("\n\naction not found\n\n")
    return None


def verify_state(game_state, previousState):
    for state in allstates:
        #print(state.find('name').text)
        if state.find('constraint') is not None:
            constraint_test = state.find('constraint').text
            result = eval(constraint_test, get_current_values(game_state))#{'flappyBird': flappyBird, 'topPipe': topPipe, 'bottomPipe': bottomPipe}
            if result:
                return state

    return previousState


def find_state_by_name(statename):
    for state in allstates:
        if state.find('name').text == statename:
            return state

    return None


actions = ['doNothing()', 'flap()'] #0,1

class Validator:
    def __init__(self,exp_name):
        self.current_state = None
        self.previous_state = None
        self.current_score = 0
        self.previous_score = 0
        self.exp_name = exp_name
        self.mutant_name = ""
        self.history = []
        self.history_length = -1



    def __init__(self, exp_name,  game_state):
        topPipe, bottomPipe, flappyBird, score = game_state["topPipe"], game_state["bottomPipe"], game_state["flappyBird"], game_state["score"]

        flappyBird = dotdict(flappyBird)
        topPipe = dotdict(topPipe)
        bottomPipe = dotdict(bottomPipe)
        self.previous_score = score
        state = {
            'flappyBird': flappyBird,
            'topPipe': topPipe,
            'bottomPipe': bottomPipe,
            'score': 0,
            'action': 0
        }
        state = dotdict(state)

        self.previous_state = verify_state(state, None)
        self.current_state = None
        self.current_score = 0#None
        self.exp_name = exp_name
        self.mutant_name = ""
        state['state'] = self.previous_state.find('name').text
        state['ingoingTransition'] =  "init"
        self.history = []
        self.history.append(state)
        self.history_length = 0


    def validate(self,  game_state,action, done):
        topPipe, bottomPipe, flappyBird, score = game_state["topPipe"], game_state["bottomPipe"], game_state["flappyBird"], game_state["score"]
        flappyBird = dotdict(flappyBird)
        topPipe = dotdict(topPipe)
        bottomPipe = dotdict(bottomPipe)

        state = {
            'flappyBird': flappyBird,
            'topPipe': topPipe,
            'bottomPipe': bottomPipe,
            'score': score
        }
        state = dotdict(state)


        self.current_score = score
        self.current_state = verify_state(state, self.previous_state)
        action = actions[action]# "doNothing()

        state['action'] = action
        state['state'] = self.current_state.find('name').text

        flag = False
        bugFound = False

        #check if action effect has taken place
        action_verification = verify_action_effect(state, self.history[-1])

        if not action_verification:
            self.updateLog(action, state, True, "  Action did not perform as expected ")
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
                        result = eval(guard_text, {'flappyBird': flappyBird, 'topPipe': topPipe, 'bottomPipe': bottomPipe})

                        if result:

                            destinationStateName = transition.find("targetName").text
                            flag = True
                            ingoingTransition = "action { "+guard_text+" }"
                            if self.current_state.find("name").text == destinationStateName:
                                #print("validation satisfied")
                                self.updateLog(action, state)

                            else:
                                #print("bug encountered")
                                self.updateLog(action, state, True, "  Actual State doesnot match expected state ")
                                bugFound = True

                            #check if state has dead stereotype
                            destState = find_state_by_name(destinationStateName)
                            if destState.find("stereotype").text == "dead":
                                if not done:
                                    self.updateLog(action, state, True, "  Failed to close upon dead state ")
                                    bugFound = True

                    elif self.previous_state.find("stereotype").text == "dead":
                        self.updateLog(action, state, True, "  Failed to close upon dead state ")
                        bugFound = True
                        flag = True

            else:
                if transition.find('guard') is not None:
                    guard_text = transition.find('guard').text
                    #print(guard_text)
                    if guard_text is not None:
                        result = eval(guard_text, {'flappyBird': flappyBird, 'topPipe': topPipe, 'bottomPipe': bottomPipe})
                        #print(result)  #
                        if result:

                            destinationStateName = transition.find("targetName").text
                            flag = True
                            if self.current_state.find("name").text == destinationStateName:
                                self.updateLog(action, state, True, "  action is faulty doesnot perform as expected ")


        if not flag:
            self.updateLog(action, state, True, "  Incorrect Reward ")
            bugFound = True

        if bugFound:
            if (flappyBird.xCoordinate >= (topPipe.xCoordinate - 0) and flappyBird.xCoordinate <= (topPipe.xCoordinate + 52) ) and (flappyBird.yCoordinate <= topPipe.yCoordinate + 0):
                if (flappyBird.xCoordinate >= (topPipe.xCoordinate - 0) and flappyBird.xCoordinate <= (
                        topPipe.xCoordinate + 5)) and (flappyBird.yCoordinate <= topPipe.yCoordinate + 0 and flappyBird.yCoordinate >= topPipe.yCoordinate -5):
                    bugFound = False
                    #print("corner issue")

            elif (flappyBird.xCoordinate >= (bottomPipe.xCoordinate - 0) and flappyBird.xCoordinate <= (bottomPipe.xCoordinate + 52) ) and (flappyBird.yCoordinate >= bottomPipe.yCoordinate + 0):
                if (flappyBird.xCoordinate >= (bottomPipe.xCoordinate - 0) and flappyBird.xCoordinate <= (
                        bottomPipe.xCoordinate + 5)) and (flappyBird.yCoordinate >= bottomPipe.yCoordinate + 0 and flappyBird.yCoordinate <= bottomPipe.yCoordinate +5):
                    bugFound = False
                    #print("corner issue")

        if self.previous_score != self.current_score:
            #print(topPipe.xCoordinate, flappyBird.xCoordinate )
            #print("Score Updated")

            if self.current_score != self.previous_score + 1:
                self.updateLog(action, state, True, "  Incorrect Reward ")
                bugFound = True

        elif topPipe.xCoordinate <= 56:# and topPipe.xCoordinate >= 53: #+ 52 < flappyBird.xCoordinate and topPipe.xCoordinate + 52 > flappyBird.xCoordinate - 25 :
            #print(topPipe.xCoordinate, flappyBird.xCoordinate, self.history[-1]["topPipe"].xCoordinate)
            if (self.history[-1]["topPipe"].xCoordinate > topPipe.xCoordinate + 4 and topPipe.xCoordinate >= 36) or (self.history[-1]["topPipe"].xCoordinate == topPipe.xCoordinate + 4 and topPipe.xCoordinate >= 53) :
                self.updateLog(action, state, True, "  Incorrect Reward ")
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
            "logs/mutation-testing-logs" + "/" + self.algo + "/flappybird" + "/bug_log_" + self.mutant_name + ".tsv",
            "a")
        f.write(bugStr + "\t" + self.previous_state.find(
            "name").text + "\t" + action + "\t \t \t " + self.current_state.find("name").text + " \t " + state_json_string
             + "\t" + str(self.previous_score) + "\t" + comment + " \n")
        f.close()
