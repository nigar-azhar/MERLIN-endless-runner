import xml.etree.ElementTree as ET

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__






def get_actions(gamename = "carracing2d"):
    filename = "games/"+gamename+"/actual/"+gamename+".xml"
    # filename= "angrywalls.xml"
    tree = ET.parse(filename)

    # Get the root element
    root = tree.getroot()

    #allstates = sm.findall('allmystates')

    allactions = root.findall('actions')


    action_probabilities = []
    for act in allactions:
        action_probabilities.append(float(act.find("frequency_of_use").text))


    print("Number of actions in game",len(allactions), action_probabilities )
    return len(allactions), action_probabilities

def get_action_names(gamename = "carracing2d"):
    filename = "games/"+gamename+"/actual/"+gamename+".xml"
    # filename= "angrywalls.xml"
    tree = ET.parse(filename)

    # Get the root element
    root = tree.getroot()

    #allstates = sm.findall('allmystates')

    allactions = root.findall('actions')


    actions = []
    for act in allactions:
        actions.append(act.find("name").text)


    print("Number of actions in game",len(allactions), actions)
    return actions

def get_action_timeelapsed(gamename = "carracing2d"):
    filename = "games/"+gamename+"/actual/"+gamename+".xml"
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

def get_boosterdurations(gamename = "carracing2d"):
    filename = "games/"+gamename+"/actual/"+gamename+".xml"
    # filename= "angrywalls.xml"
    tree = ET.parse(filename)

    # Get the root element
    root = tree.getroot()

    durations = {}

    allassets = root.findall('assets')

    for asset in allassets:
        stereotype = asset.findtext('stereotype')
        # print(stereotype)
        if stereotype in ["Booster"]:
            name = asset.findtext('name')
            # print(name)
            duration = {}
            dtime = None
            effect = None
            for attr in asset.findall('stereotype_attributes'):
                if attr.findtext('name') == 'boosterDuration':
                    dtime = float(attr.findtext('float_value', default='0'))
                    #durations[name] = dtime
                elif attr.findtext('name') == 'effect':
                    effect = str(attr.findtext('string_value', default=''))
                    #durations[name] = effect
                    # print("hello")
                    break

            duration['boosterDuration'] = dtime
            duration['effect'] = effect
            if dtime is not None:
                durations[name] = duration


    print(durations)
    return durations


def get_score_impacts(gamename = "carracing2d"):
    filename = "games/"+gamename+"/actual/"+gamename+".xml"
    # filename= "angrywalls.xml"
    tree = ET.parse(filename)

    # Get the root element
    root = tree.getroot()

    score_impacts = {}

    assets = root.findall('assets')

    for asset in assets:
        stereotype = asset.findtext('stereotype')
        #print(stereotype)
        if stereotype in ["Collectable", "Booster"]:
            name = asset.findtext('name')
            #print(name)
            impact = None
            for attr in asset.findall('stereotype_attributes'):
                if attr.findtext('name') == 'scoreImpact':
                    impact = float(attr.findtext('float_value', default='0'))
                    score_impacts[name] = impact
                    #print("hello")
                    break

    rewards = root.findall('rewards')

    for asset in rewards:

        name = asset.findtext('name')
        #print(name)
        impact = None
        for attr in asset.findall('stereotype_attributes'):
            if attr.findtext('name') == 'scoreImpact':
                impact = float(attr.findtext('float_value', default='0'))
                score_impacts[name] = impact
                #print("hello")
                break

    print(score_impacts )
    return score_impacts

if __name__ == '__main__':
    print(get_score_impacts("angrywalls"))