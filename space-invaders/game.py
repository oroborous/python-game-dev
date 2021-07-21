from cocos.sprite import Sprite
from cocos.euclid import Vector2
from cocos.collision_model import CollisionManagerGrid, AARectShape
from cocos.layer import Layer
from cocos.director import director
from cocos.scene import Scene
from cocos.text import Label
from pyglet.window import key
from pyglet.image import load as iload, ImageGrid, Animation
from pyglet.media import load as mload
from random import random

shoot_sfx = mload("sfx/shoot.wav", streaming=False)
kill_sfx = mload("sfx/invaderkilled.wav", streaming=False)
die_sfx = mload("sfx/explosion.wav", streaming=False)


# utility function to create an animation from a sprite sheet
def load_animation(image):
    # load the grid of images with 2 rows, 1 column
    seq = ImageGrid(iload(image), 2, 1)
    # create an animation that cycles between images every half second
    return Animation.from_image_sequence(seq, 0.5)


TYPES = {
    "1": (load_animation("img/alien1.png"), 40),
    "2": (load_animation("img/alien2.png"), 20),
    "3": (load_animation("img/alien3.png"), 10)
}


# All game objects are sprites and can move, collide, etc.
class Actor(Sprite):
    def __init__(self, image, x, y):
        # call sprite constructor
        super().__init__(image)

        # initialize position vector
        pos = Vector2(x, y)
        self.position = pos

        # create a rectangular collider
        # "axis-aligned" because our sprites don't rotate
        self.cshape = AARectShape(pos, self.width * 0.5, self.height * 0.5)

    # utility function to move both sprite and collider together
    def move(self, offset):
        # update the sprite's position
        self.position += offset
        # also update the collider's position
        self.cshape.center += offset

    # subclasses of Actor (like Alien and Cannon) will define
    # how to update themselves
    def update(self, delta_time):
        pass  # do nothing

    # subclasses of Actor (like Alien and Cannon) will define
    # how to collide with other Actors
    def collide(self, other):
        pass  # do nothing


# all of the aliens are Actors
class Alien(Actor):
    def __init__(self, img, x, y, points, column=None):
        # call Actor constructor with image and coordinates
        super().__init__(img, x, y)
        # different aliens are worth different points
        self.points = points
        # aliens know which AlienColumn they belong to
        self.column = column

    def on_exit(self):
        # call the original on_exit method in CocosNode
        super().on_exit()

        # if an alien's column is set, remove it from the column
        if self.column:
            self.column.remove(self)

    @staticmethod
    def from_type(x, y, alien_type, column):
        # get the tuple from the dictionary and unpack it
        animation, points = TYPES[alien_type]
        # create and return the requested Alien
        return Alien(animation, x, y, points, column)


# a column creates and contains its Aliens
class AlienColumn:
    def __init__(self, x, y):
        # enumerate() provides an index number for each list item
        alien_types = enumerate(["3", "3", "2", "2", "1"])

        # # using a for loop works, but isn't "Pythonic"
        # self.aliens = []
        # # get the index and the alien type string
        # for i, alien_type in alien_types:
        #     self.aliens.append(
        #         # same x, increasing y
        #         # the string to use as dictionary index
        #         # and reference to the column itself
        #         Alien.from_type(x, y + i * 60, alien_type, self)
        #     )

        # a list comprehension is more Pythonic
        # translate one list into another list
        self.aliens = [
            Alien.from_type(x, y + i * 60, alien_type, self)
            for i, alien_type in alien_types
        ]

    # method to tell a column to remove an alien from itself
    def remove(self, alien):
        self.aliens.remove(alien)

    # method to ask the column if it's too close to the edge of
    # the screen and needs to change direction
    def should_turn(self, direction):
        # if all the aliens in the column have been destroyed,
        # its location doesn't matter
        if len(self.aliens) == 0:
            return False

        # get bottom-most alien
        alien = self.aliens[0]

        # get x coordinate and width of screen
        x, width = alien.x, alien.parent.width

        # direction of 1 means travelling right, -1 is left
        return x >= width - 50 and direction == 1 or \
               x <= 50 and direction == -1

    def shoot(self):
        # small random chance to fire if column has
        # at least one alien
        if random() < 0.001 and len(self.aliens) > 0:
            # unpack x, y from tuple of bottom alien in column
            x, y = self.aliens[0].position
            # create an AlienShoot 50 pixels below alien
            return AlienShoot(x, y - 50)
        else:
            # not firing this frame
            return None




# the Swarm contains all AlienColumns
class Swarm:
    # initialized with x and y of bottom alien in first column
    def __init__(self, x, y):
        # make 10 columns, 60 pixels apart, using list comprehension
        self.columns = [
            AlienColumn(x + i * 60, y)
            for i in range(10)
        ]
        # swarm initially moves to the right (direction 1)
        self.direction = 1
        # only has horizontal speed
        self.speed = Vector2(10, 0)

        # swarm moves once per second, so accumulate the
        # delta_times until it reaches 1
        self.elapsed = 0.0
        self.period = 1.0

    # return True/False whether any column is too close to edge of screen
    def side_reached(self):
        # execute the lambda (anonymous inline function), passing it each
        # AlienColumn, then test if any of the columns report True
        return any(map(lambda col: col.should_turn(self.direction), self.columns))

    # define an iterator that returns all the aliens in the swarm, one at a time
    # (much easier than writing nested loops over and over!)
    def __iter__(self):
        for column in self.columns:
            for alien in column.aliens:
                yield alien

    # called once per frame so the swarm can move all the aliens in its columns
    def update(self, delta_time):
        # accumulate the elapsed time
        self.elapsed += delta_time

        # if the elapsed time exceeds the movement period (1 second)
        while self.elapsed >= self.period:
            # deduct the period from the elapsed time
            self.elapsed -= self.period

            # multiply speed by direction to get +10 or -10 vector
            movement = self.direction * self.speed

            # test if it's time to change direction
            if self.side_reached():
                # reverse the sign of the direction (+/-1)
                self.direction *= -1
                # don't move left/right, move down instead
                movement = Vector2(0, -10)

            # use iterator to move each Alien (the Swarm itself is an iterator)
            for alien in self:
                alien.move(movement)


# the cannon controlled by the player that fires at aliens
class PlayerCannon(Actor):
    def __init__(self, x, y):
        # call Actor constructor
        super().__init__("img/cannon.png", x, y)

        # use a vector for speed to support the move() method
        self.speed = Vector2(200, 0)

    # if anything collides with the cannon, both are destroyed
    def collide(self, other):
        # .kill() is a Cocos function that removes an object from the game
        other.kill()
        self.kill()

    def update(self, delta_time):
        # boolean math trick that results in -1, 0, or 1
        horizontal_movement = keyboard[key.RIGHT] - keyboard[key.LEFT]

        # keep cannon on screen by restricting the x coordinate range
        left_edge = self.width * 0.5
        right_edge = self.parent.width - left_edge

        # uncomment to find the movement bug
        # print(left_edge, self.x, right_edge)

        if left_edge <= self.x <= right_edge:
            self.move(self.speed * horizontal_movement * delta_time)

        # is the space key down?
        is_firing = keyboard[key.SPACE]
        # only one missile at a time!
        if PlayerShoot.ACTIVE_SHOOT is None and is_firing:
            # originate a new missile 50 pixels above the
            # cannon's current position
            self.parent.add(PlayerShoot(self.x, self.y + 50))

            # play sound effect
            shoot_sfx.play()


# the missile fired by the PlayerCannon
class PlayerShoot(Actor):
    # this variable is static
    ACTIVE_SHOOT = None

    def __init__(self, x, y):
        super().__init__("img/missile.png", x, y)
        # only moves vertically, quite fast
        self.speed = Vector2(0, 400)
        # when a shoot is constructed, it is the active shoot
        PlayerShoot.ACTIVE_SHOOT = self

    # called when PlayerShoot collides with other Actors
    def collide(self, other):
        # if other Actor is an Alien, tell GameLayer to update score
        if isinstance(other, Alien):
            # add however many points the Alien was worth to the score
            self.parent.update_score(other.points)
            # remove both Alien and PlayerShoot from game
            other.kill()
            self.kill()

    # called when PlayerShoot is destroyed with .kill() in collide()
    def on_exit(self):
        # call original on_exit
        super().on_exit()
        # set the active shoot to None so the player can fire again
        PlayerShoot.ACTIVE_SHOOT = None

    def update(self, delta_time):
        # pretty simple implementation to move the shoot every frame
        self.move(self.speed * delta_time)


class AlienShoot(Actor):
    def __init__(self, x, y):
        super().__init__("img/shoot.png", x, y)
        # only moves down (negative y)
        self.speed = Vector2(0, -400)

    def update(self, delta_time):
        self.move(self.speed * delta_time)


# holds the text labels that display the score, lives, game over
class HUD(Layer):
    def __init__(self):
        super().__init__()

        # get the screen size and unpack the tuple into two variables
        w, h = director.get_window_size()

        # create a label to hold the score
        self.score_text = Label("", font_size=18)
        # set the position as an (x, y) tuple
        self.score_text.position = (20, h - 40)

        # create a label to hold the lives remaining
        self.lives_text = Label("", font_size=18)
        # set the position as an (x, y) tuple
        self.lives_text.position = (w - 100, h - 40)

        # add both labels to the layer, making them visible
        self.add(self.score_text)
        self.add(self.lives_text)

    # method to update the score label
    def update_score(self, score):
        self.score_text.element.text = "Score: {}".format(score)

    # method to update the lives label
    def update_lives(self, lives):
        self.lives_text.element.text = "Lives: {}".format(lives)

    # method to create a "Game Over" label and add it to the layer
    def show_game_over(self, message):
        # get the screen size and unpack the tuple into two variables
        w, h = director.get_window_size()
        game_over_text = Label(message, font_size=50, anchor_x="center", anchor_y="center")

        # position in center of screen
        game_over_text.position = (w * 0.5, h * 0.5)

        # add to layer
        self.add(game_over_text)


class GameLayer(Layer):
    def __init__(self, hud):
        super().__init__()
        # store reference to the hud so text labels can be updated
        self.hud = hud

        # create variables for the screen width and height
        w, h = director.get_window_size()
        self.width = w
        self.height = h

        # player's lives remaining and game score
        self.lives = 3
        self.score = 0

        # create a collision manager assuming the average sprite
        # size is 50 pixels
        cell = 1.25 * 50
        self.collman = CollisionManagerGrid(0, w, 0, h, cell, cell)

        # create the player and set the initial score
        self.update_score()
        self.create_player()

        # create the alien swarm
        self.create_swarm(100, 300)

        # schedule the game loop to run every frame
        self.schedule(self.game_loop)

    # the game layer creates the player cannon at game start or if
    # it is destroyed by aliens
    def create_player(self):
        # starting position for cannon is bottom center of screen
        self.player = PlayerCannon(self.width * 0.5, 50)

        # add cannon to layer
        self.add(self.player)

        # update the lives remaining label using the GameLayer's variable
        self.hud.update_lives(self.lives)

    # default value for points allows us to call this method without a value
    def update_score(self, points=0):
        self.score += points

        # update the game score label using the GameLayer's variable
        self.hud.update_score(self.score)

    # called once per frame
    def game_loop(self, delta_time):
        # do collision checking first
        # remove all previous Actors from collision manager
        self.collman.clear()
        # add back any actors that are still in the game
        # (children of the layer)
        for _, actor in self.children:
            self.collman.add(actor)

            # any Actors not on the collision grid should
            # be removed from the game (specifically, the
            # PlayerShoot if it flies offscreen)
            if not self.collman.knows(actor):
                self.remove(actor)

        # check for missile impact
        if self.collide(PlayerShoot.ACTIVE_SHOOT):
            # play sound effect
            kill_sfx.play()

        # if the cannon hit anything, respawn it
        if self.collide(self.player):
            # play sound effect
            die_sfx.play()
            # create a new PlayerCannon
            self.respawn_player()

        # tell each AlienColumn in the swarm to shoot
        for column in self.swarm.columns:
            # this may be None if the column did not fire
            shoot = column.shoot()
            # if not, add it to the GameLayer
            if shoot is not None:
                self.add(shoot)

        # update all Actors
        for _, actor in self.children:
            actor.update(delta_time)
        # also update the Swarm, which is not a child of the layer
        self.swarm.update(delta_time)

    # create the swarm of aliens
    def create_swarm(self, x, y):
        # create Swarm with x, y of left bottom alien
        self.swarm = Swarm(x, y)
        # the Swarm is an iterator that returns all its aliens
        for alien in self.swarm:
            # add each Alien to the layer to make it visible
            self.add(alien)

    # method to create a new PlayerCannon
    def respawn_player(self):
        # subtract one life
        self.lives -= 1
        # check for game over
        if self.lives < 0:
            # stop the game loop from running
            self.unschedule(self.game_loop)
            # show the Game Over layer with the losing message
            self.hud.show_game_over("Game Over")
        else:
            # still alive! create a new PlayerCannon
            self.create_player()

    # have the GameLayer find all collisions with the given actor
    def collide(self, actor):
        # check for None because of PlayerShoot.ACTIVE_SHOOT
        if actor is not None:
            # for everything the given actor is colliding with
            for other in self.collman.iter_colliding(actor):
                # call its collide method and pass the other thing
                actor.collide(other)
                return True
        return False


if __name__ == "__main__":
    # load sound media files
    song = mload("sfx/level1.ogg")
    player = song.play()
    player.loop = True

    # init the Cocos director
    director.init(caption="WCTC Invaders", width=800, height=650)

    # respond to keyboard input
    keyboard = key.KeyStateHandler()
    director.window.push_handlers(keyboard)

    # create the scene to hold the layers
    main_scene = Scene()

    # create the HUD layer as the top layer (higher z axis)
    hud_layer = HUD()
    main_scene.add(hud_layer, z=1)

    # create the game layer as the bottom layer (lower z axis)
    game_layer = GameLayer(hud_layer)
    main_scene.add(game_layer, z=0)

    # run it!
    director.run(main_scene)
