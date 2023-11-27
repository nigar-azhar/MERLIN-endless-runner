import pygame
import random
import numpy as np
from pygame.surfarray import array2d
import cv2

import torch

from games.angrywalls.mutants.baseline.objects import Player, Bar, Ball, Block, ScoreCard, Message, Particle, generate_particles


# COLORS

RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (54, 69, 79)


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
        self.fps = 45#100

        # Game clock which ticks according to the game framerate
        self.clock = pygame.time.Clock()

        # Set up display
        self.width, self.height = width, height

        self.frame_size =frame_size
        pygame.display.set_caption('Angry Walls')


        SCREEN = WIDTH, HEIGHT = width, height#288, 512

        info = pygame.display.Info()
        width = info.current_w
        height = info.current_h

        if width >= height:
            self.win = pygame.display.set_mode(SCREEN, pygame.NOFRAME)
        else:
            self.win = pygame.display.set_mode(SCREEN, pygame.NOFRAME | pygame.SCALED | pygame.FULLSCREEN)

        #clock = pygame.time.Clock()
        #FPS = 45


        self.c_list = [RED, BLACK, WHITE]

        # Fonts

        pygame.font.init()
        #score_font = pygame.font.Font('Fonts/BubblegumSans-Regular.ttf', 50)

        # Sounds

        #coin_fx = pygame.mixer.Sound('Sounds/coin.mp3')
        #death_fx = pygame.mixer.Sound('Sounds/death.mp3')
        #move_fx = pygame.mixer.Sound('Sounds/move.mp3')

        # backgrounds

        bg_list = []
        for i in range(1, 2):
            if i == 2:
                ext = "jpeg"
            else:
                ext = "jpg"
            img = pygame.image.load(f"games/angrywalls/actual/Assets/Backgrounds/bg{i}.{ext}")
            img = pygame.transform.scale(img, (WIDTH, HEIGHT))
            bg_list.append(img)

        #home_bg = pygame.image.load(f"Assets/Backgrounds/home.jpeg")

        #bg = home_bg

        # objects
        self.bar_group = pygame.sprite.Group()
        self.ball_group = pygame.sprite.Group()
        self.block_group = pygame.sprite.Group()
        self.destruct_group = pygame.sprite.Group()
        self.win_particle_group = pygame.sprite.Group()
        self.bar_gap = 120

        #particles = []

        self.p = Player(self.win)
        self.score_card = ScoreCard(140, 470, self.win)

        # Variables

        self.bar_width_list = [i for i in range(40, 150, 10)]
        self.bar_frequency = 1200
        self.bar_speed = 4
        self.touched = False
        self.pos = None
        self.home_page = True
        self.score_page = False
        self.bird_dead = False
        self.score = 0
        high_score = 0
        self.move_left = False
        self.move_right = True
        self.prev_x = 0
        self.p_count = 0

        home_page = False
        score_page = False
        self.win_particle_group.empty()

        self.bg = random.choice(bg_list)

        particles = []
        self.last_bar = 0#pygame.time.get_ticks() - self.bar_frequency
        self.next_bar = 0
        #self.bar_speed = 4
        #bar_frequency = 1200
        #bird_dead = False
        #score = 0
        #p_count = 0
        self.score_list = []

        # for _ in range(15):
        #     x = random.randint(30, WIDTH - 30)
        #     y = random.randint(60, HEIGHT - 60)
        #     max = random.randint(8, 16)
        #     b = Block(x, y, max, self.win)
        #     self.block_group.add(b)
        self.clockticks = 0
        bwidth = random.choice(self.bar_width_list)

        b1prime = Bar(0, 20, bwidth + 3, GRAY, self.win)
        b1 = Bar(0, 17, bwidth, WHITE, self.win)

        b2prime = Bar(bwidth + self.bar_gap + 3, 20, self.width - bwidth - self.bar_gap, GRAY, self.win)
        b2 = Bar(bwidth + self.bar_gap, 17, self.width - bwidth - self.bar_gap, WHITE, self.win)

        self.bar_group.add(b1prime)
        self.bar_group.add(b1)
        self.bar_group.add(b2prime)
        self.bar_group.add(b2)

        color = random.choice(["black", "white"])
        pos = random.choice([0, 1])
        if pos == 0:
            x = bwidth + 12
        elif pos == 1:
            x = bwidth + self.bar_gap - 12
        ball = Ball(x, 30, 1, color, self.win)

        self.ball_group.add(ball)

        self.left_bar = b1prime
        self.right_bar = b2prime
        self.ball = ball

        if color == "black":
            if pos == 0:
                self.redBallPresent_left = True
                self.redBallPresent_right = False
            elif pos == 1:
                self.redBallPresent_right = True
                self.redBallPresent_left = False

            self.whiteBallPresent_left = False
            self.whiteBallPresent_right = False

        elif color == "white":
            if pos == 0:
                self.whiteBallPresent_left = True
                self.whiteBallPresent_right = False
            elif pos == 1:
                self.whiteBallPresent_right = True
                self.whiteBallPresent_left = False
            self.redBallPresent_left = False
            self.redBallPresent_right = False

        else:

            self.redBallPresent_left = False
            self.redBallPresent_right = False
            self.whiteBallPresent_left = False
            self.whiteBallPresent_right = False

        self.ball_score = False
        self.bar_score = False


    def destroy_bird(self):
        x, y = self.p.rect.center
        for i in range(50):
            c = random.choice(self.c_list)
            particle = Particle(x, y, 1, c, self.win)
            self.destruct_group.add(particle)

    def win_particles(self):
        for x, y in [(40, 120), (self.width - 20, 240), (15, self.height - 30)]:
            for i in range(10):
                particle = Particle(x, y, 2, WHITE, self.win)
                self.win_particle_group.add(particle)

    def update_display(self):
        """
        Update the game display with the game background and sprites.

        Args:
            mode (str): One of ['drl' or 'game']. If 'dqn', then we would like
                to render a simplistic version. If 'game', then we would like to
                render the full version.
        """
        self.ball_score = False
        self.bar_score = False
        self.clockticks += 1
        self.win.blit(self.bg, (0, 0))
        next_bar = self.clockticks#pygame.time.get_ticks()

        #print(self.last_bar, next_bar, self.clockticks)
        #print(self.p.x, self.p.y)

        if self.left_bar.rect.y >= 270 and not self.bird_dead:
            #print("creating new bar")

        #if next_bar - self.last_bar >= self.bar_frequency and not self.bird_dead:
         #   print("creating new bar")

            #print(self.bar_group[0])
            bwidth = random.choice(self.bar_width_list)

            b1prime = Bar(0, 20, bwidth + 3, GRAY, self.win)
            b1 = Bar(0, 17, bwidth, WHITE, self.win)

            b2prime = Bar(bwidth + self.bar_gap + 3, 20, self.width - bwidth - self.bar_gap, GRAY, self.win)
            b2 = Bar(bwidth + self.bar_gap, 17, self.width - bwidth - self.bar_gap, WHITE, self.win)

            self.bar_group.add(b1prime)
            self.bar_group.add(b1)
            self.bar_group.add(b2prime)
            self.bar_group.add(b2)

            self.left_bar_next = b1prime
            self.right_bar_next = b2prime

            color = random.choice(["black", "white"])
            pos = random.choice([0, 1])
            if pos == 0:
                x = bwidth + 12
            elif pos == 1:
                x = bwidth + self.bar_gap - 12
            ball = Ball(x, 25, 1, color, self.win)

            self.ball_group.add(ball)
            self.last_bar = next_bar
            if color == "black":
                if pos == 0:
                    self.redBallPresent_left_next = True
                    self.redBallPresent_right_next = False
                elif pos == 1:
                    self.redBallPresent_right_next = True
                    self.redBallPresent_left_next = False

                self.whiteBallPresent_left_next = False
                self.whiteBallPresent_right_next = False

            elif color == "white":
                if pos == 0:
                    self.whiteBallPresent_left_next = True
                    self.whiteBallPresent_right_next = False
                elif pos == 1:
                    self.whiteBallPresent_right_next = True
                    self.whiteBallPresent_left_next = False
                self.redBallPresent_left_next = False
                self.redBallPresent_right_next = False

            else:

                self.redBallPresent_left_next = False
                self.redBallPresent_right_next = False
                self.whiteBallPresent_left_next = False
                self.whiteBallPresent_right_next = False

            self.ball_next = ball

        if self.left_bar.rect.y >= 270:
            self.left_bar = self.left_bar_next
            self.right_bar = self.right_bar_next
            self.redBallPresent_left = self.redBallPresent_left_next
            self.redBallPresent_right = self.redBallPresent_right_next
            self.whiteBallPresent_left = self.whiteBallPresent_left_next
            self.whiteBallPresent_right = self.whiteBallPresent_right_next
            self.ball = self.ball_next
            self.score += 1
            self.bar_score = True

        for ball in self.ball_group:
            if ball.rect.colliderect(self.p):
                if ball.color == "white":
                    ball.kill()
                    #coin_fx.play()
                    self.score += 5
                    self.ball_score = True
                    #if self.score > shigh_score:
                    #    high_score += 1
                    self.score_card.animate = True
                elif ball.color == "black":
                    if not self.bird_dead:
                        #death_fx.play()
                        self.destroy_bird()

                    self.bird_dead = True
                    self.bar_speed = 0

        if pygame.sprite.spritecollide(self.p, self.bar_group, False):
            if not self.bird_dead:
                #death_fx.play()
                self.destroy_bird()

            self.bird_dead = True
            self.bar_speed = 0

        self.block_group.update()
        self.bar_group.update(self.bar_speed)
        self.ball_group.update(self.bar_speed)

        if self.bird_dead:
            self.destruct_group.update()

        self.score_card.update(self.score)

        if not self.bird_dead:
            # particles = generate_particles(p, particles, WHITE, win)
            self.p.update()

        if self.score and self.score % 10 == 0:
            rem = self.score // 10
            if rem not in self.score_list:
                self.score_list.append(rem)
                self.bar_speed += 1
                self.bar_frequency -= 200

        #if self.bird_dead and len(self.destruct_group) == 0:
        #    self.__init__()
            #print("init called")
            # score_page = True
            # font = "Fonts/BubblegumSans-Regular.ttf"
            # #if score < high_score:
            # score_msg = Message(144, 60, 55, "Score", font, WHITE, self.win)
            # #else:
            # #    score_msg = Message(144, 60, 55, "New High", font, WHITE, win)
            #
            # score_point = Message(144, 110, 45, f"{self.score}", font, WHITE, self.win)

        # if score_page:
        #     block_group.empty()
        #     bar_group.empty()
        #     ball_group.empty()
        #
        #     p.reset()

        if self.p.x <= 1 or self.p.x>=287:
            self.bird_dead = True


        pygame.display.update()

    def get_game_state(self):
        angryBird = {'yCoordinate': self.p.y, 'xCoordinate': self.p.x}
        leftbar = {'yCoordinate': self.left_bar.y, 'xCoordinate': self.left_bar.get_leftbar_xcoord()
                   }
        rightbar = {'yCoordinate': self.right_bar.y, 'xCoordinate': self.right_bar.x}
        redBall = {'yCoordinate': self.ball.rect.y, 'xCoordinate': self.ball.rect.x, 'present_left':self.redBallPresent_left, 'present_right':self.redBallPresent_right}
        whiteBall = {'yCoordinate': self.ball.rect.y, 'xCoordinate': self.ball.rect.x,
                   'present_left': self.whiteBallPresent_left, 'present_right': self.whiteBallPresent_right}
        scoreupdate = {"ball": self.ball_score,
                       "bar": self.bar_score}
        state = {'angryBird': angryBird,
                 'rightBar': rightbar,
                 'leftBar': leftbar,
                 'redBall': redBall,
                 'whiteBall': whiteBall,
                 'score': self.score,
                 'scoreupdate': scoreupdate}
        #print("\n\n\n",state,"\n\n")
        return state  # topPipe, bottomPipe, flappyBird, self.game_text.score

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
        state = state[:,:300]
        #cv2.imwrite('win.png', np.array(state))

        # Resize to 84x 84
        state = cv2.resize(state, (self.frame_size, self.frame_size))
        #cv2.imwrite('win2.png', np.array(state))
        #print(np.max(state), np.min(state))

        # Convert to black and white
        # state[state > 0] = 1
        #state = 255-state
        state = state/255.0
        #state = np.array(state)
        #print(state)
        #np.save("outfile.npy", state)#cv2.imwrite('color_img.jpg', state)

        #np.savetxt('test1.txt', state, fmt='%f')#print(state)
        return torch.tensor(np.array([state])).float()




    def step(self, action):
        """
        Advances the game by one frame.

        The bird tries to accrue as many points as possible by passing through the pipe pairs. The agent can either flap its wings or do nothing. The game ends when the bird hits an obstacle (a pipe pair or
        the ground).

        Arguments:
            action (nothing, left, right):(0,1,2) #If True, the bird flaps its wings once. If False, the bird does nothing.

        Returns:
            tensor, float, bool: 84x84 processed frame, reward, done status
        """

        reward = 0.1
        #done = False
        x, y = (self.p.x, self.p.y)
        offset_x = self.p.rect.x - x

        #print(self.p.x, self.p.rect.x, self.p.y,self.p.rect.y)

        if action == 0:
            self.touched = False
        elif action == 1:
            self.move_right = False
            self.move_left = True
            self.p.x = self.p.x - 5
        elif action == 2:
            # self.move_right = True
            # self.move_left = False
            # self.p.x = self.p.x + 5
            self.move_right = False
            self.move_left = True
            self.p.x = self.p.x - 5


        self.p.rect.x = self.p.x
        self.p.rect.y = self.p.y

        if action == 1 or action == 2:
            if self.p.rect.collidepoint((self.p.x,self.p.y)):
                self.touched = True
                x, y = (self.p.x,self.p.y)
                offset_x = self.p.rect.x - x

        self.prev_x = x
        self.p.rect.x = x + offset_x

        self.update_display()

        frame = self.process_frame_drl()

        #self.clock.tick(self.fps)
        done = self.bird_dead

        if self.p.x <=5 or self.p.x+40 >=283:
            done = True

        if done:
            self.close_game()
            self.__init__(self.frame_size)

        return frame, reward, done


    def close_game(self):
        pygame.display.quit()
        pygame.quit()