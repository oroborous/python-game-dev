from cocos.scene import Scene
from cocos.layer import Layer
from cocos.director import director
from cocos.collision_model import CollisionManagerGrid
from cocos.scenes import FadeTransition, SplitColsTransition
from cocos.text import Label
from cocos.actions import Delay, CallFunc
from towerdefense.scenario import get_scenario_1
import towerdefense.actors as actors
import towerdefense.mainmenu as mainmenu
import random


def new_game():
    scenario = get_scenario_1()
    background = scenario.get_background()
    hud = HUD()
    game_layer = GameLayer(hud, scenario)
    return Scene(background, game_layer, hud)


class GameLayer(Layer):
    is_event_handler = True

    def __init__(self, hud, scenario):
        super().__init__()
        self.hud = hud
        self.scenario = scenario

        # create and add the Bunker
        self.bunker = actors.Bunker(*scenario.bunker_position)
        self.add(self.bunker)

        # find the window dimensions for collision grids
        w, h = director.get_window_size()
        cell_size = 32

        # collision manager for tanks/bunker
        self.collman_enemies = CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)
        # and one for turret slots, which don't change
        self.collman_slots = CollisionManagerGrid(0, w, 0, h, cell_size, cell_size)

        # create clickable turret slots as specified in scenario
        for slot in scenario.turret_slots:
            self.collman_slots.add(actors.TurretSlot(slot, cell_size))

        # create properties for score and scrap
        self.score = 0
        self.scrap = 40
        self.turrets = []

        # schedule game loop to run every frame
        self.schedule(self.game_loop)

    @property
    def scrap(self):
        return self._scrap

    @scrap.setter
    def scrap(self, val):
        self._scrap = val
        self.hud.update_scrap(val)

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, val):
        self._score = val
        self.hud.update_score(val)

    def create_enemy(self):
        # get tank spawn coordinates from scenario
        spawn_x, spawn_y = self.scenario.enemy_start
        # add a little variation to starting coords
        x = spawn_x + random.uniform(-10, 10)
        y = spawn_y + random.uniform(-10, 10)
        # create an Enemy and give it its actions from the scenario
        self.add(actors.Enemy(x, y, self.scenario.enemy_actions))

    # don't need delta_time, so use _ to ignore it
    def game_loop(self, _):
        # clear enemies from collision manager
        self.collman_enemies.clear()

        # for every child object of the layer
        for obj in self.get_children():
            # if it's an Enemy tank
            if isinstance(obj, actors.Enemy):
                # add it to the collision manager
                self.collman_enemies.add(obj)

        # for every child object colliding with the bunker
        for obj in self.collman_enemies.iter_colliding(self.bunker):
            # crash it!
            self.bunker.collide(obj)

        # check each turret to see if it has a tank in range
        for turret in self.turrets:
            # if nothing is colliding, next() will return None
            obj = next(self.collman_enemies.iter_colliding(turret), None)
            # pass tank (or None) to turret to become its new target
            turret.collide(obj)

        # small probability of spawning a tank
        if random.random() < 0.005:
            self.create_enemy()

    def on_mouse_press(self, x, y, buttons, mod):
        # anything in this collision grid where the mouse
        # click happened?
        slots = self.collman_slots.objs_touching_point(x, y)

        # is there a slot here, and do we have at least 20 scrap?
        if len(slots) > 0 and self.scrap >= 20:
            # spend 20 scrap
            self.scrap -= 20
            # get the first slot by iterating the set
            slot = next(iter(slots))
            # unpack the slot collider's coords
            turret = actors.Turret(*slot.cshape.center)
            # add turret to list of turrets and to game layer
            self.turrets.append(turret)
            self.add(turret)

    def remove(self, obj):
        if obj is self.bunker:
            director.replace(SplitColsTransition(game_over()))
        elif isinstance(obj, actors.Enemy) and obj.destroyed_by_player:
            self.score += obj.points
            self.scrap += 5
        super().remove(obj)



class HUD(Layer):
    def __init__(self):
        super().__init__()
        # get dimensions of window
        w, h = director.get_window_size()
        # create labels for score and scrap
        self.score_text = self._create_text(60, h - 40)
        self.scrap_text = self._create_text(w - 60, h - 40)

    def _create_text(self, x, y):
        text = Label(font_size=18, font_name="Oswald",
                     anchor_x="center", anchor_y="center")
        text.position = (x, y)
        self.add(text)
        return text

    def update_score(self, score):
        self.score_text.element.text = "Score: {}".format(score)

    def update_scrap(self, scrap):
        self.scrap_text.element.text = "Scrap: {}".format(scrap)


def game_over():
    # get window dimensions
    w, h = director.get_window_size()
    # create a layer
    layer = Layer()
    # create a text label
    text = Label("Game Over",
                 position=(w * 0.5, h * 0.5),
                 font_name="Oswald",
                 font_size=72,
                 anchor_x="center",
                 anchor_y="center")
    # add label to layer
    layer.add(text)
    # add layer to scene
    scene = Scene(layer)
    # create a transition to the main menu scene
    menu_scene = FadeTransition(mainmenu.new_menu())
    # a function that tells the director to replace the
    # current scene with the menu scene
    show_menu = lambda: director.replace(menu_scene)
    # wait three seconds (showing "Game Over"), then show the menu
    scene.do(Delay(3) + CallFunc(show_menu))
    return scene
