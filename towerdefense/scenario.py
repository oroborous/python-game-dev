import cocos.actions as action
from cocos.tiles import load

# convenience constants for turning right and left
RIGHT = action.RotateBy(90, 1)
LEFT = action.RotateBy(-90, 1)


# convenience function to calculate 100 pixel/second movement
def move(x, y):
    # calculate the total pixels moved, then divide by desired
    # speed of 100 pixels/second
    duration = abs(x + y) / 100.0
    # create a Cocos action for correct duration
    return action.MoveBy((x, y), duration=duration)


class Scenario:
    def __init__(self, tmx_file, map_layer, turrets, bunker, enemy_start):
        self.tmx_file_name = tmx_file
        self.map_layer_name = map_layer
        self.turret_slots = turrets
        self.bunker_position = bunker
        self.enemy_start = enemy_start
        self._enemy_actions = None

    @property
    def enemy_actions(self):
        # returns the "private" field
        return self._enemy_actions

    @enemy_actions.setter
    def enemy_actions(self, action_list):
        # anchor the chain of actions with a 0-second delay
        self._enemy_actions = action.Delay(0)
        # chain the desired actions after the delay
        for step in action_list:
            # You can use the + operator with Actions
            self._enemy_actions += step

    def get_background(self):
        # load the TMX file with map info
        tmx_map_layers = load("assets/{}.tmx".format(self.tmx_file_name))
        # select the desired map layer
        bg = tmx_map_layers[self.map_layer_name]
        # use 100% of the layer as the viewable area
        bg.set_view(0, 0, bg.px_width, bg.px_height)

        return bg


# will be called by GameLayer at game start
def get_scenario_1():
    # gather all the information for this scenario into one object
    turret_slots = [(96, 320), (288, 288), (448, 320), (96, 96), (320, 96), (512, 96)]
    bunker_position = (48, 400)
    enemy_start = (-80, 176)
    sc = Scenario("level1", "map1", turret_slots, bunker_position, enemy_start)
    sc.enemy_actions = [RIGHT, move(640, 0), LEFT, move(0, 224), LEFT, move(-512, 0)]
    return sc
