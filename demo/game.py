from cocos.sprite import Sprite
from cocos.euclid import Vector2
from cocos.collision_model import CollisionManagerGrid, CircleShape
from cocos.layer import Layer
from cocos.director import director
from cocos.scene import Scene
from pyglet.window import key


class Actor(Sprite):
    def __init__(self, x, y, color):
        # call the Sprite constructor with initial params
        super(Actor, self).__init__("img/ball.png", color=color)

        # create a vector that defines the sprite's position
        # relative to the screen's origin (bottom left)
        pos = Vector2(x, y)
        self.position = pos

        # create a circle shaped collider centered on the sprite
        self.cshape = CircleShape(pos, self.width / 2)

        # the actor should move 100 pixels per second
        self.speed = 100


class MainLayer(Layer):
    def __init__(self):
        super(MainLayer, self).__init__()

        # create an Actor to represent the player
        # positioned at (x=320, y=240) with a blue overlay
        self.player = Actor(320, 240, (0, 0, 255))

        # add the Actor to the layer (makes it visible)
        self.add(self.player)

        # loop through a list of coordinates (as tuples)
        for pos in [(100, 100), (540, 380), (540, 100), (100, 300)]:
            # add an Actor with a red overlay as a pickup
            self.add(Actor(pos[0], pos[1], (255, 0, 0)))

        # create the collision manager grid
        cell = self.player.width * 1.25
        self.collman = CollisionManagerGrid(0, 640, 0, 480, cell, cell)

        # tell Cocos to run the update() function each frame
        self.schedule(self.update)

    def update(self, delta_time):
        print(delta_time)

        # calculate the -1/0/1 modifier for horizontal movement
        horizontal_movement = keyboard[key.RIGHT] - keyboard[key.LEFT]

        # calculate the -1/0/1 modifier for vertical movement
        vertical_movement = keyboard[key.UP] - keyboard[key.DOWN]

        # get the sprite's current position
        pos = self.player.position

        # calculate new x coordinate
        new_x = pos[0] + self.player.speed * horizontal_movement * delta_time

        # calculate new y coordinate
        new_y = pos[1] + self.player.speed * vertical_movement * delta_time

        # update the sprite's position
        self.player.position = (new_x, new_y)

        # also update the collider's position so they stay together
        self.player.cshape.center = self.player.position

        # perform collision checking
        # first, clear the collision manager of all known actors
        self.collman.clear()

        # loop over actors that are still in the game
        for _, actor in self.children:
            # add them back to the collision manager
            self.collman.add(actor)

        # get an iterator of all objects colliding with the player sprite
        # then loop over them, one at a time
        for pickup in self.collman.iter_colliding(self.player):
            # remove the pickup sprite from the layer
            # which destroys it (no longer in the game)
            self.remove(pickup)


# code to start the game
if __name__ == "__main__":
    # the director controls the active scene
    director.init(caption="Cocos Demo")

    # listen for keyboard input
    keyboard = key.KeyStateHandler()
    director.window.push_handlers(keyboard)

    # create the layer and scene
    layer = MainLayer()
    scene = Scene(layer)
    # director, run this scene
    director.run(scene)
