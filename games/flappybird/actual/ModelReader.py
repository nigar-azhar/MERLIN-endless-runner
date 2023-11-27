import xml.etree.ElementTree as ET
#import time
#from wrapper import Game
#from game.angrybird.sprites import PIPE_LOWER


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__






def get_actions():
    filename = "games/flappybird/actual/flappybird_model.xml"
    # filename= "angrywalls.xml"
    tree = ET.parse(filename)

    # Get the root element
    root = tree.getroot()

    #allstates = sm.findall('allmystates')

    allactions = root.findall('actions')


    action_probabilities = []
    for act in allactions:
        action_probabilities.append(float(act.find("frequency_of_use").text))


    #print("Number of actions in game",len(allactions), action_probabilities )
    return len(allactions), action_probabilities

def get_action_timeelapsed():
    filename = "games/flappybird/actual/flappybird_model.xml"
    # filename= "angrywalls.xml"
    tree = ET.parse(filename)

    # Get the root element
    root = tree.getroot()

    # allstates = sm.findall('allmystates')

    allactions = root.findall('actions')

    action_time = []
    for act in allactions:
        action_time.append(int(float(act.find("timeelapsed").text)))

    print("time of actions in game", len(allactions), action_time)
    return action_time