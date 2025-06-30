import cv2
import sys
import torch
import random
import numpy as np

import pygame
from pygame.locals import *
from pygame.surfarray import array2d


import os


# To tell pygame we don't need audio
# https://raspberrypi.stackexchange.com/questions/83254/pygame-and-alsa-lib-error
os.environ['SDL_AUDIODRIVER'] = 'dsp'


class Game():

    def __init__(self, frame_size=84, width=288, height=512):
        """
        Initialize the game.
        A minimal version for use training deep reinforcement learning methods.

        Argument:
            frame_size (int): width, height of extracted frame for DRL in pixels
            width (int): width of game screen in pixels
            height (int): height of game screen in pixels
        """
        pygame.init()

        # Frame rate of the game
        self.fps = 100

        # Game clock which ticks according to the game framerate
        self.clock = pygame.time.Clock()

        # Set up display
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Flappy Bird')

        # Set up game objects
        from .sprites import Pipe, Bird, GameText, Base, HeartBoosterGuage, Heart, Coin
        # from sprites import Pipe, Bird, GameText, Base
        self.bg = pygame.image.load('games/flappybird/actual/assets/background.png').convert_alpha()
        self.game_text = GameText()
        self.player = Bird(91,250)#(0.2 * width, 0.45 * height)
        self.base = Base()
        # changed initialization of pipe
        self.pipes = [Pipe(self.width), Pipe(self.width * 2)]
        self.pipe = Pipe

        # List of flags indicating whether or not the pass through of the pipe
        # pairs has been counted yet
        self.pipe_counted = [False, False]

        # Tell bird sprite the game has started.
        self.player.set_game_play_mode(True)

        # Size of extracted frames for use in DRL training
        self.frame_size = frame_size
        self.pipe_pass = False
        self.coin_collect = False
        self.heart_collect = False
        self.heartboosterguage = HeartBoosterGuage(width - 50, height - 50)
        self.heart = Heart((self.width, self.height))
        self.coin = Coin((self.width, self.height))

        self.last_heart_spawn_time = 0
        self.last_coin_spawn_time = 0  # ms

    # get game state information information
    def get_game_state(self):
        flappyBird = {'yCoordinate': self.player.y, 'xCoordinate': self.player.x + self.player.image.get_width(), 'width':self.player.image.get_width(), 'hieght':self.player.image.get_height()}
        topPipe = {'yCoordinate': self.pipes[0].y_upper_end, 'xCoordinate': self.pipes[0].x, 'isActive':not self.heartboosterguage.active}
        bottomPipe = {'yCoordinate': self.pipes[0].y_upper_end + 158, 'xCoordinate': self.pipes[0].x, 'isActive':not self.heartboosterguage.active}
        scoreupdate = {'pipe_pass': self.pipe_pass, 'coin':self.coin_collect, 'heart':self.heart_collect}
        coin = {'yCoordinate': self.coin.y, 'xCoordinate': self.coin.x}
        heart = {'yCoordinate': self.heart.y, 'xCoordinate': self.heart.x, 'timeElapsed': max(self.last_heart_spawn_time,0), 'isActive':self.heartboosterguage.active}

        game_state = {"flappyBird": flappyBird,
                      "topPipe": topPipe,
                      "bottomPipe": bottomPipe,
                      "coin":coin,
                      'heart':heart,
                      "score": self.game_text.score,
                      'scoreupdate': scoreupdate
                      }
        # print("+++++++++++++++++++++")
        # print("i here", self.pipe_pass)
        # print("+++++++++++++++++++++")
        self.pipe_pass = False
        self.coin_collect = False
        self.heart_collect = False

        return game_state

    def take_screenshot(self, name):
        pygame.image.save(self.screen, name)

    def update_display(self):
        """
        Update the game display with the game background and sprites.

        Args:
            mode (str): One of ['drl' or 'game']. If 'dqn', then we would like
                to render a simplistic version. If 'game', then we would like to
                render the full version.
        """
        # Draw the background
        self.screen.fill(((0, 0, 0)))

        # Draw the sprites
        for pipe in self.pipes:
            pipe.draw(self.heartboosterguage.active)
        self.player.draw()
        self.base.draw()

        # Draw any messages
        self.game_text.draw('main')

        self.heartboosterguage.draw()
        self.heart.draw()
        self.coin.draw()

        # Update the entire game display
        pygame.display.flip()

    def process_frame_drl(self):
        """
        Process and clean the frame so we can input into the DRL function.

        Returns:
            (tensor): 1x84x84 tensor
        """
        # Import game screen array
        state = np.array(array2d(self.screen), dtype='uint8')

        # Crop out where the base would be
        state = state[:, :400]

        # Resize to 84x 84
        state = cv2.resize(state, (self.frame_size, self.frame_size))

        # Convert to black and white
        # state[state > 0] = 1
        state = state / 255.
        state = np.array([state])
        # print(state)
        return torch.tensor(state).float()

    def step(self, action):
        """
        Advances the game by one frame.

        The bird tries to accrue as many points as possible by passing through the pipe pairs. The agent can either flap its wings or do nothing. The game ends when the bird hits an obstacle (a pipe pair or
        the ground).

        Arguments:
            action (bool): If True, the bird flaps its wings once. If False, the bird does nothing.

        Returns:
            tensor, float, bool: 84x84 processed frame, reward, done status
        """
        reward = 0.1
        done = False
        # self.pipe_pass = False

        # Update base sprite
        self.base.update()

        # Update player sprite
        self.player.update(action)

        # Update pipes
        for pipe in self.pipes:
            pipe.update()

        # Add a new pipe when one of the pipes has shifted off screen
        if self.pipes[0].x < 0 and len(self.pipes) < 3:
            self.pipes.append(self.pipe(2 * self.width))
            self.pipe_counted.append(False)

        # Remove pipe that has shifted left off screen
        if self.pipes[0].x < -self.pipes[0].image.get_width():
            self.pipes.pop(0)
            self.pipe_counted.pop(0)

        # Update the game display
        self.update_display()
        frame = self.process_frame_drl()

        #print(self.heart.x, self.heart.y)
        self.last_heart_spawn_time -= 1
        if self.game_text.score > 5 and self.heart.x < 0 and self.last_heart_spawn_time <0:  # and random.randint(0, 10) == 1:
            #print("I am spawning heart")
            self.heart.spawn(self.pipes)
            self.last_heart_spawn_time = self.heart.spawn_delay

        #print(self.coin.x, self.coin.y)
        self.last_coin_spawn_time -= 1
        if self.game_text.score > 5 and self.coin.x < 0 and self.last_coin_spawn_time < 0:  # and random.randint(0, 10) == 1:
            #print("I am spawning heart")
            self.coin.spawn(self.pipes)
            self.last_coin_spawn_time = self.coin.spawn_delay
            # self.heartboosterguage.collect()

        if self.player.check_collide(self.heart):
            reward += 2
            self.heartboosterguage.collect()
            self.game_text.update_score(2)
            self.heart.remove_()
            self.heart_collect = True

        # mutant
        if self.player.check_collide(self.coin):
            reward += 2
            #self.game_text.update_score(1)
            self.coin.remove_()
            self.coin_collect = True

        self.heartboosterguage.update()
        self.heartboosterguage.draw()
        # if self.heartboosterguage.active:

        self.heart.update()
        self.heart.draw()
        self.coin.update()
        self.coin.draw()

        # Check to see if the player bird has collided with any of the pipe
        # pairs or the base. If so, exit the game loop.
        obstacles = self.pipes
        if self.player.check_collide(obstacles) and not self.heartboosterguage.active:
            reward = -5
            done = True

        if self.player.check_collide([self.base]):
            reward = -5
            done = True

        # If the player passes through a pipe, add +1 to score
        for i in range(len(self.pipes)):
            if not self.pipe_counted[i]:
                if self.pipes[i].x < self.player.x:
                    self.game_text.update_score(1)
                    self.pipe_pass = True
                    self.pipe_counted[i] = True
                    reward = 1
                    # print("+++++++++++++++++++++")
                    # print("+++++++++++++++++++++")
                    # print("why am i here", self.pipe_pass)
                    # print("+++++++++++++++++++++")
                    # print("+++++++++++++++++++++")

        # Increment
        self.clock.tick(self.fps)

        # If the game ended, restart
        if done:
            #print("================\nI am done\n==============")
            self.close_game()
            self.__init__(self.frame_size)


        return frame, reward, done

    def close_game(self):
        pygame.display.quit()
        pygame.quit()


def listen():
    """
    Listen and log key presses from user (spacebar, arrow keys).
    Will automatically exit game if it gets a quit signal.

    Returns:
        list (str): a list of the names of the keys pressed
    """
    keypress = []

    for event in pygame.event.get():
        # If spacebar is pressed
        if event.type == KEYDOWN and event.key == K_SPACE:
            doNothing()

            keypress.append('spacebar')

        # If arrows pressed
        if event.type == KEYDOWN and event.key == K_RIGHT:
            keypress.append('right_arrow')

        if event.type == KEYDOWN and event.key == K_LEFT:
            keypress.append('left_arrow')

        # If quit triggered
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        # do nothing on mouse click
        if event.type == MOUSEBUTTONUP:
            None

    return keypress
