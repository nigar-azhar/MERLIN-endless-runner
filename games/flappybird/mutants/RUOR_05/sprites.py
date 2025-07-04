import math
import random

import pygame
from pygame.locals import *
from pygame.sprite import Sprite

import os
import sys

WHITE = (255, 255, 255)

# Redirect standard output to /dev/null
sys.stdout = open(os.devnull, 'w')
# Load in all the sprites
# global PIPE_LOWER, PIPE_UPPER, IM_UPFLAP, IM_MIDFLAP, IM_DOWNFLAP, MSG_START, MSG_END, DIGITS, BASE
PIPE_LOWER = pygame.image.load('games/flappybird/actual/assets/pipe.png').convert_alpha()
PIPE_UPPER = pygame.transform.rotate(PIPE_LOWER, 180)

IM_UPFLAP = pygame.image.load('games/flappybird/actual/assets/bird_upflap.png').convert_alpha()
IM_MIDFLAP = pygame.image.load('games/flappybird/actual/assets/bird_midflap.png').convert_alpha()
IM_DOWNFLAP = pygame.image.load('games/flappybird/actual/assets/bird_downflap.png').convert_alpha()

MSG_START = pygame.image.load('games/flappybird/actual/assets/start_msg.png').convert_alpha()
MSG_END = pygame.image.load('games/flappybird/actual/assets/end_msg.png').convert_alpha()
DIGITS = []
for i in range(10):
    DIGITS.append(pygame.image.load('games/flappybird/actual/assets/%i.png' % i).convert_alpha())

BASE = pygame.image.load('games/flappybird/actual/assets/base.png').convert_alpha()

sys.stdout = sys.__stdout__


class Pipe(Sprite):

    def __init__(self, x_init):
        """
        Initialize a new pipe pair sprite instance.
        The pipe placement on the y-axis is randomly generated.

        Arguments:
            x_init (int): x-coordinate of starting position
        """
        # Game surface
        self.surface = pygame.display.get_surface()
        screen_height = self.surface.get_height()

        # Pipe position
        self.x = x_init

        # Size of gap between pipes (in pixels)
        self.gap = 160  # 120

        # Sprite images
        pipe_width = PIPE_LOWER.get_width()
        pipe_height = PIPE_LOWER.get_height()

        # Randomly generate coordinates for upper and lwer pipe
        midpoint = random.randrange(int(0.55 * screen_height),
                                    int(0.65 * screen_height))
        y_upper = midpoint - pipe_height - self.gap / 2
        y_lower = midpoint + self.gap / 2
        self.y = y_upper

        self.y_upper_end = y_upper + 210

        # Create surface and mask
        self.image = pygame.Surface((pipe_width, screen_height)).convert_alpha()
        self.image.fill((0, 0, 0, 0))
        self.image.blit(PIPE_LOWER, (0, y_lower))
        self.image.blit(PIPE_UPPER, (0, y_upper))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        """
        Update the pipe pair's x-position by continually shifting 4 pixels to
        the left.
        """
        self.x -= 4

    def draw(self, booster_flag):
        """
        Draw the sprite to the game display.
        """
        if booster_flag:
            self.image.set_alpha(100)
        else:
            self.image.set_alpha(255)
        self.surface.blit(self.image, (self.x, self.y))
        # print("draw pipes", self.rect.topleft)

    @property
    def rect(self):
        """
        This property is needed for pygame.sprite.collide_mask
        """
        # print(self.x, self.y, self.image.get_width(), self.image.get_height())
        return Rect(self.x, self.y, self.image.get_width(), self.image.get_height())

    def get_pipe_Hieght(self):
        return PIPE_LOWER.get_height()


class Bird(Sprite):

    def __init__(self, x_init, y_init):
        """
        Initialize a new bird sprite instance.
        Arguments:
            x_init (int): x-coordinate of starting position
            y_init (int): y-coordinate of starting position
        """
        # Game surface
        self.surface = pygame.display.get_surface()

        # Game frame counter
        self.count = 0

        # Whether we are in game play
        self.game_play = False

        # Bird position
        self.x = x_init
        self.y = y_init
        self.y_init = y_init
        self.y_max = self.surface.get_height() - BASE.get_height()
        # print("Y max", self.y_max)

        # Bird dynamics - angle of rotation
        self.angle = 0
        self.angle_threshold = 0
        self.angle_flap = 30
        self.rate_of_rotation = 3

        # Bird dynamics - velocity along the y axis
        self.velocity_y = -9
        self.velocity_flap = -9
        self.velocity_terminal = 10

        # Sprite masks
        mask_upflap = pygame.mask.from_surface(IM_UPFLAP)
        mask_midflap = pygame.mask.from_surface(IM_MIDFLAP)
        mask_downflap = pygame.mask.from_surface(IM_DOWNFLAP)

        # Oscillation state parameters
        self.osc_cycle = [0, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1, 0,
                          -1, -2, -3, -4, -5, -6, -7, -8, -7, -6, -5, -4, -3, -2, -1]

        # Flap state parameters
        self.im_cycle = [IM_UPFLAP, IM_MIDFLAP, IM_DOWNFLAP, IM_MIDFLAP]
        self.mask_cycle = [mask_upflap, mask_midflap, mask_downflap, mask_midflap]
        self.image = self.im_cycle[self.count]
        self.mask = self.mask_cycle[self.count]

    def update(self, key_press=False):
        """
        Update the bird sprite.

        The default behavior in the game welcome screen is for the bird sprite
        to oscillate up and down and flap its wings.

        During game play, the bird sprite will respond to user keyboard input.
        If the space bar is pressed, the bird  will tilt and climb up the
        screen. If there is no key press, then the bird will fall due to the
        influence of gravity.

        Arguments:
            key_press (bool): whether or not the space bar has been pressed
        """
        # If we are in game play, then respond to user key presses
        if self.game_play:

            # Update the bird's angle of rotation, velocity, and y position
            # according to whether there was a key press (wing flap)
            self.update_angle(key_press)
            self.update_velocity(key_press)
            self.y += self.velocity_y

            # Correct y position so the bird cannot go "out of bounds"
            if self.y > self.y_max:
                self.y = self.y_max
            if self.y < 0:
                self.y = 0

        # Every 5 frames, update the player bird by changing the wing flap
        if self.count % 5 == 0:
            self.change_flap_state()

        self.count += 1

    def update_angle(self, is_flap):
        """
        Adjust the angle of the bird sprite.
        If the bird has flapped its wings, tilt upward. Else, slowly rotate
        back to a neutral position.

        Arguments:
            is_flap (bool): whether or not the bird has flapped its wings
        """
        if is_flap:
            self.angle = self.angle_flap
        else:
            self.angle -= self.rate_of_rotation
            if self.angle < self.angle_threshold:
                self.angle = self.angle_threshold

    def update_velocity(self, is_flap):
        """
        Adjust the bird sprite's velocity.
        If the bird has flapped its wings, then climb upward. Else, slowly
        decrease the bird's velocity until it reaches terminal velocity.

        Arguments:
            is_flap (bool): whether or not the bird has flapped its wings
        """
        if is_flap:
            self.velocity_y = self.velocity_flap
        else:
            self.velocity_y += 1
            if self.velocity_y > self.velocity_terminal:
                self.velocity_y = self.velocity_terminal

    def change_flap_state(self):
        """
        Change the flap state.
        """
        flap_state = self.count % len(self.im_cycle)
        self.image = self.im_cycle[flap_state]
        self.mask = self.mask_cycle[flap_state]


    def check_collide(self, sprite):
        """
        Check if the player sprite has collided with another sprite.
        The bird can collide with the pipes or the ground.

        Arguments:
            sprite (pygame.sprite or list): A sprite instance or a list of
                sprite instances. All must have the rect property.

        Returns:
            bool: True if collision with sprite instance, False otherwise
        """
        if self.y <= 5:
            return True
        if isinstance(sprite, list):
            for s in sprite:
                if pygame.sprite.collide_mask(self, s):
                    return True
            return False
        else:
            return pygame.sprite.collide_mask(self, sprite)

    def draw(self):
        """Draw the sprite onto the game display."""
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        self.surface.blit(rotated_image, (self.x, self.y))

    def set_game_play_mode(self, is_playing):
        """
        Set the game play attribute.

        Arguments:
            is_playing (bool): whether or not we are in game play mode
        """
        self.game_play = is_playing

    @property
    def rect(self):
        """
        This property is needed for pygame.sprite.collide_mask
        """
        return Rect(self.x, self.y, self.image.get_width(), self.image.get_height())


class GameText():

    def __init__(self):
        """
        Initialize a new text instance.
        This handles any global game text, game scores, as well as menu text.
        """
        # Game surface
        self.surface = pygame.display.get_surface()

        # Location of game_over message
        self.x_msg_end = (self.surface.get_width() - MSG_END.get_width()) / 2
        self.y_msg_end = 0.3 * self.surface.get_height()

        # Location of level selection digits. Want event spacing.
        digit_gap = 50
        x_level_1 = (self.surface.get_width() - DIGITS[0].get_width()) / 2
        x_level_0 = x_level_1 - digit_gap - DIGITS[1].get_width()
        x_level_2 = x_level_1 + digit_gap + DIGITS[1].get_width()
        self.x_level = [x_level_0, x_level_1, x_level_2]
        self.y_level = 0.7 * self.surface.get_height()

        # The location of the score
        self.y_score = self.surface.get_height() * 0.85

        # The currently selected level
        self.level = 1
        self.level_box_height = DIGITS[0].get_height() + 10
        self.level_box_width = DIGITS[0].get_width() + 10

        # Score value
        self.score = 0

    def draw(self, mode):
        """
        Draw any required text to the screen.
        In 'welcome' mode, we'll need to display the starting instructions as
        well as the level selection menu. In 'game_over' mode, we'll need to
        display the game over text.

        Arguments:
            mode (str): One of 'welcome', 'main', or 'game_over'
        """

        # In main mode, display the score
        if mode == 'main':
            self.draw_score()


    def draw_score(self):
        """
        Draw the score to the game display.
        """
        # Extract a list of the individual digits in the score
        score_digits = [int(i) for i in list(str(self.score))]

        # Find the total width (in pixels) of the score
        score_width = sum([DIGITS[i].get_width() for i in score_digits])

        # Blit the score digits onto the screen
        x = (self.surface.get_width() - score_width) / 2
        for i in score_digits:
            self.surface.blit(DIGITS[i], (x, self.y_score))
            x += DIGITS[i].get_width()

    def update_level(self, keys_pressed):
        """
        Update the selected level.

        Arguments:
            keys_pressed

        Returns:
            int: the selected level, where [0,1,2] corresponds to
            ['easy', 'medium', 'hard'], respectively.
        """
        if 'right_arrow' in keys_pressed:
            if self.level == 2:
                return self.level
            self.level += 1

        if 'left_arrow' in keys_pressed:
            if self.level == 0:
                return self.level
            self.level -= 1

        return self.level

    def update_score(self, amount):
        """
        Update the game score.
        We call this function every time the bird makes it through a pair of
        pipes, so we increment the score by 1.
        """
        self.score **= amount


class Base(Sprite):

    def __init__(self):
        """
        Initialize the ground sprite.
        """
        # Game surface
        self.surface = pygame.display.get_surface()

        # Sprite and mask
        self.mask = pygame.mask.from_surface(BASE)

        # Position
        self.x = 0
        self.y = self.surface.get_height() - BASE.get_height()
        self.max_shift = BASE.get_width() - self.surface.get_width()

    def update(self):
        """
        Update the position of the base sprite.
        The base should continually shift by 4 pixels and loop.
        """
        self.x = -((-self.x + 4) % self.max_shift)

    def draw(self):
        """
        Draw the sprite to the game display.
        """
        self.surface.blit(BASE, (self.x, self.y))

    @property
    def rect(self):
        """
        This property is needed for pygame.sprite.collide_mask
        """
        return Rect(self.x, self.y, BASE.get_width(), BASE.get_height())


class HeartBoosterGuage(Sprite):
    def __init__(self, x, y):
        self.image = pygame.image.load('games/flappybird/actual/Assets/heart.png')
        self.image = pygame.transform.scale(self.image, (42, 42))

        # Game surface
        self.surface = pygame.display.get_surface()

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.radius = 25
        self.center = self.rect.centerx, self.rect.centery
        self.active = False
        self.max_timer = 300  # 5 seconds at 30 FPS
        self.timer = 0

    def collect(self):
        self.active = True
        self.timer = self.max_timer

    def update(self):
        if self.active:
            self.timer -= 1
            if self.timer <= 0:
                self.timer = 0
                self.active = False

    def draw(self):
        if self.active:

            self.surface.blit(self.image, self.rect)
            gas = int((self.timer / self.max_timer) * 360)

            if gas > 0:
                for i in range(gas):
                    x = round(self.center[0] + self.radius * math.cos(i * math.pi / 180))
                    y = round(self.center[1] + self.radius * math.sin(i * math.pi / 180))
                    pygame.draw.circle(self.surface, WHITE, (x, y), 3)


class Heart(Sprite):
    def __init__(self, screen_size):
        super().__init__()
        self.image = pygame.image.load('games/flappybird/actual/Assets/heart.png')

        self.image = pygame.transform.scale(self.image, (40, 40))

        self.rect = self.image.get_rect()

        self.screen_width, self.screen_height = screen_size
        # Game surface
        self.surface = pygame.display.get_surface()

        self.x = -1
        self.y = -1
        self.spawn_delay = 300
        self.rect.topleft = (-50, -50)

    def spawn(self, pipes):
        """Place heart randomly where it doesn't overlap pipes."""
        x = random.randint(100, self.screen_width - 50)
        y = random.randint(50, self.screen_height - 200)
        self.rect.topleft = (x, y)
        print(x, y)
        self.x = x
        self.y = y


    def draw(self):
        # print("draw heart", self.rect.topleft)
        self.surface.blit(self.image, self.rect)

    def update(self):
        """Move heart left. Respawn if it moves off-screen."""
        self.rect.x -= 4  # self.speed

        self.x -= 4

    def remove_(self):
        self.rect.topleft = (-50, -50)


class Coin(Sprite):
    def __init__(self, screen_size):
        super().__init__()
        self.image = pygame.image.load('games/flappybird/actual/Assets/coin.png')

        self.image = pygame.transform.scale(self.image, (30, 30))

        self.rect = self.image.get_rect()

        self.screen_width, self.screen_height = screen_size
        # Game surface
        self.surface = pygame.display.get_surface()

        self.x = -1
        self.y = -1
        self.spawn_delay = 150
        self.rect.topleft = (-50, -50)


    def spawn(self, pipes):
        """Place heart randomly where it doesn't overlap pipes."""
        # while True:
        x = random.randint(100, self.screen_width - 50)
        y = random.randint(50, self.screen_height - 200)
        self.rect.topleft = (x, y)
        print(x, y)
        self.x = x
        self.y = y



    def draw(self):
        self.surface.blit(self.image, self.rect)

    def update(self):
        """Move heart left. Respawn if it moves off-screen."""
        self.rect.x -= 4  # self.speed

        self.x -= 4

    def remove_(self):
        self.rect.topleft = (-50, -50)

