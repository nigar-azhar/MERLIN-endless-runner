# Dodgy Walls

# Author : Prajjwal Pathak (pyguru)
# Date : Tuesday, 13 July, 2021

import pygame
import random

from games.dodgywalls.actual.objects import Bar, Dot, Player, Message, Particle, ScoreCard, Button

import cv2

import torch

import numpy as np

# COLORS **********************************************************************

BLACK = (0, 0, 32)
WHITE = (255, 255, 255)

# SOUNDS **********************************************************************

# score_fx = pygame.mixer.Sound('Sounds/point.mp3')
# dead_fx = pygame.mixer.Sound('Sounds/dead.mp3')
# score_page_fx = pygame.mixer.Sound('Sounds/score_page.mp3')

# pygame.mixer.music.load('Sounds/Chill Gaming.mp3')
# pygame.mixer.music.play(loops=-1)
# pygame.mixer.music.set_volume(0.5)


# FONTS ***********************************************************************

score_font = "games/dodgywalls/actual/Fonts/EvilEmpire-4BBVK.ttf"
final_score_font = "games/dodgywalls/actual/Fonts/ghostclanital.ttf"
title_font = "games/dodgywalls/actual/Fonts/dpcomic.ttf"


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
        #print("self calling init")

        pygame.init()

        # Frame rate of the game
        # if drl_mode
        self.fps = 30#100

        # Game clock which ticks according to the game framerate
        self.clock = pygame.time.Clock()

        # Set up display
        self.width, self.height = width, height
        self.screen= self.width, self.height


        self.frame_size =frame_size
        #pygame.display.set_caption('Dodgy Walls')
        info = pygame.display.Info()
        width = info.current_w
        height = info.current_h

        if width >= height:
            self.win = pygame.display.set_mode(self.screen, pygame.NOFRAME)
        else:
            self.win = pygame.display.set_mode(self.screen, pygame.NOFRAME | pygame.SCALED | pygame.FULLSCREEN)

 

        if width >= height:
            self.win = pygame.display.set_mode(self.screen, pygame.NOFRAME)
        else:
            self.win = pygame.display.set_mode(self.screen, pygame.NOFRAME | pygame.SCALED | pygame.FULLSCREEN)



        self.bg = pygame.image.load(f'games/dodgywalls/actual/Assets/bg4.jpg')
        self.bg = pygame.transform.scale(self.bg, self.screen)

        self.frame_height = 150
        frame = pygame.image.load(f'games/dodgywalls/actual/Assets/bg3.jpg')
        self.frame = pygame.transform.scale(frame, (self.width - 10, self.frame_height))
        self.frameX, self.frameY = 5, self.height//2 - self.frame_height//2

        ##objects

        self.bar_group = pygame.sprite.Group()
        self.dot_group = pygame.sprite.Group()
        self.particle_group = pygame.sprite.Group()

        self.score_msg = ScoreCard(self.width//2, 100, 50, score_font, WHITE, self.win)

        self.p = Player(self.win)


        self.bar_frequency = 1800
        self.bar_heights = [height for height in range(60,100,10)]
        self.bar_speed = 3
        self.pos = -1
        self.pos_updater = 1
        self.start_time = pygame.time.get_ticks()

        self.clicked = False
        self.score = 0
        #highscore = 0
        self.player_alive = True
        self.bar_height = random.choice(self.bar_heights)
        self.pos = self.pos * -1

        if self.pos == -1:
            bar_y = self.frameY
            dot_y = self.frameY + self.bar_height + 20
        elif self.pos == 1:
            bar_y = self.frameY + self.frame_height - self.bar_height
            dot_y = self.frameY + self.frame_height - self.bar_height - 20

        self.bar = Bar(self.width, bar_y, self.bar_height, BLACK, self.win)
        self.bar.pos = self.pos
        self.dot = Dot(self.width + 10, dot_y, self.win)
        self.bar_group.add(self.bar)
        self.dot_group.add(self.dot)
        self.bar_score = False
        self.dot_score = False
        self.game_freeze = False
        self.initial_ticks = pygame.time.get_ticks()
        #self.start_time = current_time


    def get_game_state(self):
        ball = {'yCoordinate': self.p.rect.y, 'xCoordinate': self.p.rect.x, 'direction':self.p.get_direction()}
        bar = {'xCoordinate': self.bar.rect.x, 'yCoordinate': self.bar.get_bar_ycoord(), 'position': self.bar.pos
                   }
        collectatable = {'yCoordinate': self.dot.rect.y, 'xCoordinate': self.dot.rect.x}
        scoreupdate = {"dot": self.dot_score,
                       "bar": self.bar_score}
        state = {'ball': ball,
                 'collectable': collectatable,
                 'bar': bar,
                 'score': self.score,
                 'scoreupdate': scoreupdate}
        #print("\n\n\n",state,"\n\n")
        return state 

    def greyscale(self,surface: pygame.Surface):
        #start = time.time()  # delete me!
        arr = pygame.surfarray.array3d(surface)
        # calulates the avg of the "rgb" values, this reduces the dim by 1
        mean_arr = np.mean(arr, axis=2)
        # restores the dimension from 2 to 3
        #mean_arr3d = mean_arr[..., np.newaxis]
        # repeat the avg value obtained before over the axis 2
        #new_arr = np.repeat(mean_arr3d[:, :, :], 3, axis=2)
        #diff = time.time() - start  # delete me!
        # return the new surface
        return mean_arr#pygame.surfarray.make_surface(new_arr)



    def process_frame_drl(self):
        """
        Process and clean the frame so we can input into the DRL function.

        Returns:
            (tensor): 1x84x84 tensor
        """
        # Import game screen array
        state = self.greyscale(self.win)
        #state = np.array(array2d(self.win), dtype='uint8')
        #cv2.imwrite('win.png', np.array(state))

        # Crop out where the base would be
        #print(">>>>>>>>>> Size", state.shape)
        state = state[80:,170:340]
        #cv2.imwrite('win.png', np.array(state))

        # Resize to 84x 84
        state = cv2.resize(state, (self.frame_size, self.frame_size))
        cv2.imwrite('win2.png', np.array(state))
        #print(np.max(state), np.min(state))

        # Convert to black and white
        # state[state > 0] = 1
        #state = 255-state
        state = state/255.0
        #state = np.array(state)
        #print(state)
        #np.save("outfile.npy", state)#
        #cv2.imwrite('color_img.jpg', state)

        #np.savetxt('test1.txt', state, fmt='%f')#print(state)
        return torch.tensor(np.array([state])).float()


    def step(self, action):
        """
            Advances the game by one frame.

            The bird tries to accrue as many points as possible by passing through the pipe pairs. The agent can either flap its wings or do nothing. The game ends when the bird hits an obstacle (a pipe pair or
            the ground).

            Arguments:
                action (nothing, click):(0,1) #If True, the bird flaps its wings once. If False, the bird does nothing.

            Returns:
                tensor, float, bool: 84x84 processed frame, reward, done status
            """

        done = False

        self.bar_score = False
        self.dot_score = False
        reward = 0
        self.clicked = action == 1
        #self.win.blit(self.bg, (0,0))
        if action == 1:
            if not self.clicked:
                self.clicked = True

        else:
            self.clicked = False
        
        self.win.blit(self.frame, (self.frameX, self.frameY))
        

        current_time = pygame.time.get_ticks()

        if self.score > 25:
            self.game_freeze = True

        if not self.game_freeze:
            #new bar
            if self.bar.rect.x <= 136:# and not self.bird_dead:#if current_time - self.start_time >= self.bar_frequency:
                #print(">>>>>>bar",self.bar.x, self.bar.y, self.bar.pos)
                #print(">>>>>>ball", self.p.x, self.p.y)

                self.bar_height = random.choice(self.bar_heights)
                self.pos = self.pos * -1

                if self.pos == -1:
                    bar_y = self.frameY
                    dot_y = self.frameY + self.bar_height + 20
                elif self.pos == 1:
                    bar_y = self.frameY + self.frame_height - self.bar_height
                    dot_y = self.frameY + self.frame_height - self.bar_height - 20

                self.bar = Bar(self.width, bar_y, self.bar_height, BLACK, self.win)
                self.bar.pos = self.pos
                self.dot = Dot(self.width + 10, dot_y, self.win)
                self.bar_group.add(self.bar)
                self.dot_group.add(self.dot)

                self.start_time = current_time
                self.score += 1
                reward += 1

                self.bar_score = True

            for dot in self.dot_group:
                if dot.rect.colliderect(self.p):
                    dot.kill()
                    self.score += 5
                    self.dot_score = True
                    reward += 5
                    self.score_msg.animate = True

            if pygame.sprite.spritecollide(self.p, self.bar_group, False):
                x, y = self.p.rect.center
                for i in range(10):
                    particle = Particle(x, y, WHITE, self.win)
                    self.particle_group.add(particle)
                self.player_alive = False
                done = True
                # print("\n\n\nDones\n\n\n")
                #dead_fx.play()
                self.bar_speed = 0
            
        self.bar_group.update(self.bar_speed)
        self.dot_group.update(self.bar_speed)
        self.p.update(self.player_alive, self.clicked)

        self.score_msg.update(self.score)
        self.particle_group.update()

        pygame.draw.rect(self.win, WHITE, (0, 0, self.width, self.height), 5, border_radius=10)
        self.clock.tick(self.fps)
        pygame.display.update()



        frame = self.process_frame_drl()

        if done:
            #done = True
            self.close_game()
            self.__init__(self.frame_size)
            reward = - 10

        return frame, reward, done


    def close_game(self):
        pygame.display.quit()
        pygame.quit()


