from towerdefense.gamelayer import new_game
from cocos.menu import Menu, MenuItem, ToggleMenuItem
from cocos.scene import Scene
from cocos.layer import ColorLayer
from cocos.actions import ScaleTo
from cocos.director import director
from cocos.scenes.transitions import FadeTRTransition
import pyglet.app


class MainMenu(Menu):
    def __init__(self):
        super().__init__("Tower Defense")
        # set the font for the main menu title
        self.font_title["font_name"] = "Oswald"
        # set the font for the menu items (regular and selected)
        self.font_item["font_name"] = "Oswald"
        self.font_item_selected["font_name"] = "Oswald"

        # menu will be centered in the screen
        self.menu_anchor_y = "center"
        self.menu_anchor_x = "center"

        # create a list of menu items
        items = list()
        # add menu item to start new game by calling function on_new_game
        items.append(MenuItem("New Game", self.on_new_game))
        # add menu item to show/hide framerate, initialized to current
        # setting of the director, which will call function show_fps
        # passing it the True/False state of the toggle
        items.append(ToggleMenuItem("Show FPS: ", self.show_fps, director.show_FPS))
        # add menu item to exit the game
        items.append(MenuItem("Quit", pyglet.app.exit))

        # run some actions to grow/shrink the menu items when they are
        # activated/deactivated (enlarge on hover effect)
        self.create_menu(items, ScaleTo(1.25, duration=0.25), ScaleTo(1.0, duration=0.25))

    def on_new_game(self):
        # director.push will suspend the running scene and load a new one
        # with a 2-second wipe effect transition
        director.push(FadeTRTransition(new_game(), duration=2))

    def show_fps(self, value):
        director.show_FPS = value

def new_menu():
    # create a scene for the menu
    scene = Scene()
    # create a sandy-colored layer
    color_layer = ColorLayer(205, 133, 63, 255)
    
    # add MainMenu to scene
    scene.add(MainMenu(), z=1)
    # add color layer behind it
    scene.add(color_layer, z=0)

    return scene
