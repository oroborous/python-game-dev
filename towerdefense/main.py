import pyglet.resource
from cocos.director import director
from towerdefense.mainmenu import new_menu

if __name__ == "__main__":
    # make the assets directory known to Pyglet
    pyglet.resource.path.append("assets")
    pyglet.resource.reindex()

    # give Pyglet access to our custom font
    pyglet.font.add_file("assets/Oswald-Regular.ttf")

    director.init(caption="Tower Defense")
    director.run(new_menu())