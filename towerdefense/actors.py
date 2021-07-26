from cocos.sprite import Sprite
from cocos.euclid import Vector2
from cocos.collision_model import CircleShape, AARectShape
from cocos.actions import IntervalAction, Delay, CallFunc, MoveBy
from pyglet.image import ImageGrid, Animation, load
import math

# load the sprite sheet image
raw = load("assets/explosion.png")
# it has 1 row and 8 columns
seq = ImageGrid(raw, 1, 8)
# create an animation that cycles through the frames, playing
# each for 0.07 seconds and do NOT loop it
explosion_img = Animation.from_image_sequence(seq, 0.07, False)


class Actor(Sprite):
    def __init__(self, image, x, y):
        # like the Actor class in our other game, initialize
        # with image and starting coordinates
        super().__init__(image)
        pos = Vector2(x, y)
        self.position = pos

        # underscore to make this a private property
        self._cshape = CircleShape(pos, self.width * 0.5)

    @property
    def cshape(self):
        # now, every time the collider shape is accessed,
        # its position will be updated to match the Actor's
        self._cshape.center = Vector2(self.x, self.y)
        return self._cshape


# an action that tanks can perform to turn red when hit
class Hit(IntervalAction):
    # if no duration specified, will be half a second
    def init(self, duration=0.5):
        self.duration = duration

    # receives the percent of the action's duration that
    # has elapsed, from 0.0 - 1.0
    def update(self, pct_elapsed):
        self.target.color = (255, 255 * pct_elapsed, 255 * pct_elapsed)


class Explosion(Sprite):
    def __init__(self, pos):
        super().__init__(explosion_img, pos)
        # the do() method is how sprites perform actions
        # wait one second, then destroy yourself
        self.do(Delay(1) + CallFunc(self.kill))


class Enemy(Actor):
    def __init__(self, x, y, actions):
        super().__init__("tank.png", x, y)
        # starts with 100 health
        self.health = 100
        # worth 20 points when destroyed
        self.points = 20
        # points aren't awarded if the tank crashes into the bunker
        self.destroyed_by_player = False
        # do the action chain that came from the scenario
        self.do(actions)

    # called when a tank is destroyed
    def explode(self):
        # add an Explosion sprite to the game at tank's current position
        self.parent.add(Explosion(self.position))
        # remove itself from game
        self.kill()

    # called when the tank is hit by a turret
    def hit(self):
        # lose 25 health points
        self.health -= 25
        # perform the action to turn red
        self.do(Hit())

        # check if out of health and still in the game
        if self.health <= 0 and self.is_running:
            # health was reduced by a turret hit
            self.destroyed_by_player = True
            # destroy itself
            self.explode()


class Bunker(Actor):
    def __init__(self, x, y):
        super().__init__("bunker.png", x, y)
        # the bunker has 100 health to start
        self.health = 100

    def collide(self, other):
        # did bunker collide with an Enemy object?
        if isinstance(other, Enemy):
            # reduce health by 10
            self.health -= 10
            # explode the Enemy object
            other.explode()
            # check for bunker death
            if self.health <= 0 and self.is_running:
                self.kill()


# turret missiles aren't Actors because they don't collide
class Shoot(Sprite):
    def __init__(self, pos, travel_path, enemy):
        super().__init__("shoot.png", position=pos)
        # perform a chain of actions:
        # move toward enemy very quickly,
        # remove itself from game,
        # call the Enemy's hit() function
        self.do(MoveBy(travel_path, 0.1) +
                CallFunc(self.kill) +
                CallFunc(enemy.hit))


# turret slot images are part of the background image, so they
# are not sprites
class TurretSlot:
    def __init__(self, pos, side):
        # use the "splat" operator to unpack position vector into x and y
        self.cshape = AARectShape(Vector2(*pos), side * 0.5, side * 0.5)


class Turret(Actor):
    def __init__(self, x, y):
        super().__init__("turret.png", x, y)
        # contains a second sprite - the white range indicator circle
        self.add(Sprite("range.png", opacity=50, scale=5))
        # the collider is the same size as the range circle, which has
        # been scaled to 5 times its normal size
        self.cshape.r = self.width * 5 / 2
        # no tank targeted... yet
        self.target = None

        # turrets reload every 2 seconds
        self.period = 2.0
        # track time elapsed since last shot fired
        self.elapsed = 0.0
        # call the _shoot function every frame to see if eligible to fire
        self.schedule(self._shoot)

    def _shoot(self, delta_time):
        # not enough time elapsed since last shot fired
        if self.elapsed < self.period:
            # keep accumulating time
            self.elapsed += delta_time
        elif self.target is not None:
            # otherwise, if it has a target, fire!
            # reset the reload timer
            self.elapsed = 0.0

            # calculate difference between turret and tank positions
            target_path = Vector2(self.target.x - self.x, self.target.y - self.y)

            # normalize the vector so we can adjust it by the length of
            # the turret barrels
            pos = self.cshape.center + target_path.normalized() * 20

            # create a missile at the tip of the barrels
            self.parent.add(Shoot(pos, target_path, self.target))

    # called if a tank intersects the turret's firing range circle
    def collide(self, other):
        # uh oh, pal... you're a target now
        self.target = other
        # if it's a real target
        if self.target is not None:
            # find the angle of rotation for the turret to point at tank
            x, y = other.x - self.x, other.y - self.y
            # use arc tangent to find the angle
            angle = -math.atan2(y, x)
            # convert radians to degrees
            self.rotation = math.degrees(angle)
