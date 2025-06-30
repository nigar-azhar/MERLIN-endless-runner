import json
import re
import xml.etree.ElementTree as ET


class RewardEstimator:
    def __init__(self, gamename='angrywalls'):
        self.current_state = None
        self.previous_state = None
        self.current_score = 0#None
        self.previous_score = 0

        self.sm = None
        self.allstates = None
        self.allactions = None
        self.positive_reward_impacts = None
        self.reward_config = None
        self.loadmodel(gamename)


    def __init__(self, state, gamename='angrywalls'):
        self.gamename = gamename
        self.sm = None
        self.allstates = None
        self.allactions = None
        self.positive_reward_impacts = None
        self.reward_config = None
        self.loadmodel(gamename)
        score = state['score'] if (self.gamename != "carracing2d") else state['score']['score']

        self.previous_score = score
        print(gamename,state)
        self.previous_state = self.verify_state(state, None)
        self.current_state = None
        self.current_score = 0



    def loadmodel(self, gamename='angrywalls'):
        self.gamename = gamename
        filename = "games/" + gamename + "/actual/" + gamename + ".xml"
        tree = ET.parse(filename)

        # Get the root element
        root = tree.getroot()

        self.sm = root.find('statemachine')

        self.allstates = self.sm.findall('allmystates')
        self.allactions = root.findall('actions')
        self.positive_reward_impacts = [float(act.find('positive_reward_impact').text) for act in self.allactions]

        reward_config_file = "games/" + gamename + "/actual/" + "reward_config.json"
        with open(reward_config_file) as f:
            self.reward_config = json.load(f)


    def estimate(self, gstate, done, action=0):
        if "__builtins__" in gstate:
            print("Removing builtins from gstate")
            del gstate["__builtins__"]

        print(self.gamename)

        score = gstate['score'] if (self.gamename != "carracing2d") else gstate['score']['score']

        self.current_score = score
        self.current_state = self.verify_state(gstate, self.previous_state)
        if self.current_state is None:
            print(gstate)


        pstero = self.previous_state.find('stereotype').text
        cstero = self.current_state.find('stereotype').text
        pname = self.previous_state.find('name').text
        cname = self.current_state.find('name').text

        reward = 0
        if done:
            reward = self.reward_config.get("terminal_reward", -20)

        elif cstero == "good" and pstero == "good":
            reward = self.reward_config.get("persistence_reward", 3) * self.positive_reward_impacts[action]
        elif (cstero == "good" and pstero == "bad") or (pstero == None and cstero == "good") :
            reward = self.reward_config.get("change_reward", 1)
        elif cstero == "bad" and pstero == "good":
            reward = -1 * self.reward_config.get("change_reward", 1)#-1
        elif cstero == "bad" and pstero == "bad":
            reward = -1 * self.reward_config.get("persistence_reward", 3)#-2
        elif cstero == "bad" and pstero == "dead":
            reward = -1 * self.reward_config.get("persistence_reward", 3)
        elif cstero == "dead" and pstero == "bad":
            reward = -1 * self.reward_config.get("persistence_reward", 3)
        elif cstero == "dead" and pstero == "dead":
            reward = self.reward_config.get("terminal_reward", -20)
        elif cstero == None:
            reward = 0.1

        print(self.current_score, self.previous_score)
        if self.current_score > self.previous_score:
            reward += (10 + (self.current_score - self.previous_score))

        self.previous_state = self.current_state
        self.previous_score = self.current_score

        #print (gstate)
        if "__builtins__" in gstate:
            print("Removing builtins from gstate")
            del gstate["__builtins__"]        #print(positive_reward_impacts)
            print(gstate)
        print("reward for state: (", pname,")", pstero, "->(", cname,")", cstero, "is", reward)

        return reward, self.current_state.find('name').text

    def verify_state(self, gstate, previousState):

        for state in self.allstates:
            if state.find('constraint') is not None:
                constraint_test = state.find('constraint').text
                # Convert dot notation to dictionary-style access
                constraint_test = re.sub(r'(\b\w+)\.(\w+)', r'\1["\2"]', constraint_test)
                print(constraint_test)
                result = eval(constraint_test, gstate)
                if result:
                    # print(state.find('name').text)
                    return state
                # print(state.find('constraint').text)
        print(">>>>>>>>>>>>> state not found", gstate)
        return previousState
