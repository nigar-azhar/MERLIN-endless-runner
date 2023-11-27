import pygame
import random

from games.carracing2d.mutants.baseline.objects import Road, Nitro, Player, Coins, Obstacle, Tree, Fuel


import cv2

import torch

import numpy as np

# COLORS **********************************************************************

WHITE = (255, 255, 255)
BLUE = (30, 144,255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 20)

# FONTS ***********************************************************************

#font = pygame.font.SysFont('cursive', 32)

#select_car = font.render('Select Car', True, WHITE)

# IMAGES **********************************************************************

bg = pygame.image.load('games/carracing2d/actual/Assets/bg.png')

#home_img = pygame.image.load('Assets/home.png')
#play_img = pygame.image.load('Assets/buttons/play.png')
#end_img = pygame.image.load('Assets/end.jpg')
#end_img = pygame.transform.scale(end_img, (WIDTH, HEIGHT))
#game_over_img = pygame.image.load('Assets/game_over.png')
#game_over_img = pygame.transform.scale(game_over_img, (220, 220))
coin_img = pygame.image.load('games/carracing2d/actual/Assets/coins/1.png')
dodge_img = pygame.image.load('games/carracing2d/actual/Assets/car_dodge.png')

#left_arrow = pygame.image.load('Assets/buttons/arrow.png')
#right_arrow = pygame.transform.flip(left_arrow, True, False)

#home_btn_img = pygame.image.load('Assets/buttons/home.png')
#replay_img = pygame.image.load('Assets/buttons/replay.png')




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
        # print("self calling init")


        pygame.init()
        self.SCREEN = self.WIDTH, self.HEIGHT = width, height

        info = pygame.display.Info()
        width = info.current_w
        height = info.current_h

        if width >= height:
            self.win = pygame.display.set_mode(self.SCREEN, pygame.NOFRAME)
        else:
            self.win = pygame.display.set_mode(self.SCREEN, pygame.NOFRAME | pygame.SCALED | pygame.FULLSCREEN)

        #self.win = pygame.display.set_mode(self.SCREEN, pygame.NOFRAME | pygame.SCALED | pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.FPS = 30
        self.frame_size = frame_size
        self.lane_pos = [50, 95, 142, 190]

        self.cars = []
        self.car_type = 1
        for i in range(1, 2):
            img = pygame.image.load(f'games/carracing2d/actual/Assets/cars/{i}.png')
            img = pygame.transform.scale(img, (59, 101))
            self.cars.append(img)

        self.nitro_frames = []
        self.nitro_counter = 0
        for i in range(6):
            img = pygame.image.load(f'games/carracing2d/actual/Assets/nitro/{i}.gif')
            img = pygame.transform.flip(img, False, True)
            img = pygame.transform.scale(img, (18, 36))
            self.nitro_frames.append(img)

        # OBJECTS *********************************************************************
        self.road = Road()
        self.nitro = Nitro(self.WIDTH - 80, self.HEIGHT - 80)
        self.p = Player(100, self.HEIGHT - 120, self.car_type)

        self.tree_group = pygame.sprite.Group()
        self.coin_group = pygame.sprite.Group()
        self.fuel_group = pygame.sprite.Group()
        self.obstacle_group = pygame.sprite.Group()

        # VARIABLES *******************************************************************
        # home_page = True
        # car_page = False
        # game_page = False
        # over_page = False

        self.move_left = False
        self.move_right = False
        self.nitro_on = False
        # sound_on = True

        self.counter = 0
        self.counter_inc = 1
        self.speed = 10
        self.dodged = 0
        self.coins = 0
        self.cfuel = 100

        self.endx, self.enddx = 0, 0.5
        self.gameovery = -50

        self.win.fill(BLACK)
        self.distance = 0
        self.score = 0
        self.game_freeze = False

    # FUNCTIONS *******************************************************************
    def center(self,image):
        return (self.WIDTH // 2) - image.get_width() // 2

    def step(self, action):
        """
                    Advances the game by one frame.

                    The bird tries to accrue as many points as possible by passing through the pipe pairs. The agent can either flap its wings or do nothing. The game ends when the bird hits an obstacle (a pipe pair or
                    the ground).

                    Arguments:
                        action (nothing, left, right, nitro, nitro-left, nitro-right):(0,1,2,3,4,5) #If True, the bird flaps its wings once. If False, the bird does nothing.

                    Returns:
                        tensor, float, bool: 84x84 processed frame, reward, done status
                    """


        #
        self.coin_score_flag =False
        self.feul_score_flag = False
        self.car_dodge_flag = False

        # motion reset
        self.move_left = False
        self.move_right = False
        self.nitro_on = False
        # sound_on = True

        #self.counter = 0
        #self.counter_inc = 1
        self.speed = 10

        done = False
        reward = 0


        if self.dodged >= 7:
            self.game_freeze = True

        if not self.game_freeze:

            if action == 1:
                self.move_left = True
            elif action == 2:
                self.move_right = True
            elif action == 3:
                self.nitro_on = True
            elif action == 4:
                self.nitro_on = True
                self.move_left = True
            elif action == 5:
                self.nitro_on = True
                self.move_right = True

            self.win.blit(bg, (0, 0))
            self.road.update(self.speed)
            self.road.draw(self.win)

            self.counter += self.counter_inc

            #adding roadside trees
            if self.counter % 60 == 0:
                tree = Tree(random.choice([-5, self.WIDTH - 35]), -20)
                self.tree_group.add(tree)


            #adding boosters and collectables
            if self.counter % 270 == 0:
                type = random.choices([1, 2], weights=[6, 4], k=1)[0]
                x = random.choice(self.lane_pos) + 10
                if type == 1:
                    count = random.randint(1, 3)
                    for i in range(count):
                        coin = Coins(x, -100 - (25 * i))
                        self.coin_group.add(coin)
                elif type == 2:
                    fuel = Fuel(x, -100)
                    self.fuel_group.add(fuel)
            elif self.counter % 90 == 0:
                obs = random.choices([1, 2, 3], weights=[6, 2, 2], k=1)[0]
                obstacle = Obstacle(obs)
                self.obstacle_group.add(obstacle)

            if self.nitro_on and self.nitro.gas > 0:
                x, y = self.p.rect.centerx - 8, self.p.rect.bottom - 10
                self.win.blit(self.nitro_frames[self.nitro_counter], (x, y))
                self.nitro_counter = (self.nitro_counter + 1) % len(self.nitro_frames)

                self.speed = 30
                if self.counter_inc == 1:
                    self.counter = self.counter - (self.counter%10)
                    self.counter_inc = 5

            if self.nitro.gas <= 0:
                self.speed = 10
                self.counter_inc = 1
                self.nitro_on = False
                self.nitro.gas = 0

            self.nitro.update(self.nitro_on)
            self.nitro.draw(self.win)
            self.obstacle_group.update(self.speed)
            self.obstacle_group.draw(self.win)
            self.tree_group.update(self.speed)
            self.tree_group.draw(self.win)
            self.coin_group.update(self.speed)
            self.coin_group.draw(self.win)
            self.fuel_group.update(self.speed)
            self.fuel_group.draw(self.win)

            self.p.update(self.move_left, self.move_right)
            self.p.draw(self.win)

            if self.cfuel > 0:
                pygame.draw.rect(self.win, GREEN, (20, 20, self.cfuel, 15), border_radius=5)
            pygame.draw.rect(self.win, WHITE, (20, 20, 100, 15), 2, border_radius=2)
            self.cfuel -= 0.05

            # COLLISION DETECTION & KILLS
            for obstacle in self.obstacle_group:


                if pygame.sprite.spritecollide(self.p, self.obstacle_group, True):#.sprite.collide_mask(self.p, obstacle):
                    pygame.draw.rect(self.win, RED, self.p.rect, 1)
                    self.speed = 0

                    #game_page = False
                    #over_page = True
                    done = True
                    #print("hit obs", obstacle.rect.x, obstacle.rect.y, obstacle.rect.height, obstacle.type,obstacle.rect.height+obstacle.rect.y, obstacle.collide_height )
                    reward = -10
                    self.tree_group.empty()
                    self.coin_group.empty()
                    self.fuel_group.empty()
                    self.obstacle_group.empty()

                if obstacle.rect.y >= obstacle.collide_height:#self.HEIGHT:
                    if obstacle.type == 1:
                        self.dodged += 1
                        self.car_dodge_flag = True
                        self.score+=1
                        reward+=10
                    obstacle.kill()

            if pygame.sprite.spritecollide(self.p, self.coin_group, True):
                self.coins += 1
                self.coin_score_flag = True
                reward+=5
                self.score+=2
            # coin_fx.play()

            if pygame.sprite.spritecollide(self.p, self.fuel_group, True):
                self.cfuel += 25
                reward+=10
                self.feul_score_flag = True
                self.score+=5

                # fuel_fx.play()
                if self.cfuel >= 100:
                    self.cfuel = 100

            if self.cfuel < 0:
                #game_page = False
                #over_page = True
                done = True
                reward = -10
            # add cfeull < 0 game over

            pygame.draw.rect(self.win, BLUE, (0, 0, self.WIDTH, self.HEIGHT), 3)
            self.clock.tick(self.FPS)
            pygame.display.update()

            self.distance += self.speed

        frame = self.process_frame_drl()
        if done:
            #done = True
            #print("\n\n\nDones\n\n\n")
            self.close_game()
            self.__init__(self.frame_size)
            reward = - 10
        return frame, reward, done


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
        state = state[35:253,:]
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

    def close_game(self):
        pygame.display.quit()
        pygame.quit()

    def get_game_state(self):
        # print(self.p.rect.width, self.p.rect.height)
        player = {'yCoordinate': self.p.rect.y, 'xCoordinate': self.p.rect.x, 'nitro_on':self.nitro_on, 'width':self.p.rect.width, 'height':self.p.rect.height, 'nitro':self.nitro.gas}
        allcoins = []

        for c in self.coin_group:
            allcoins.append({'yCoordinate': c.rect.y, 'xCoordinate': c.rect.x, 'type':c.type, 'width':c.rect.width, 'height':c.rect.height})
            # print("\nCoin", c.rect.width,c.rect.height)

        allobs = []

        for o in self.obstacle_group:
            allobs.append({'yCoordinate': o.rect.y, 'xCoordinate': o.rect.x, 'type':o.type, 'width':o.rect.width, 'height':o.rect.height, 'collide_height':o.collide_height})
            # print("\nobs", o.rect.width,o.rect.height,o.type)

        feul = []
        for f in self.fuel_group:
            feul.append({'yCoordinate': f.rect.y, 'xCoordinate': f.rect.x, 'type':f.type, 'width':f.rect.width, 'height':f.rect.height})
            # print("\nfeul", f.rect.width, f.rect.height)

        #allcoins = {'allcoins': self.left_bar.y, 'xCoordinate': self.left_bar.get_leftbar_xcoord()
                #   }
        allassets = []
        allassets.extend(allcoins)
        allassets.extend(allobs)
        allassets.extend(feul)

        if allobs:

            closestobs = max(allobs, key=lambda x: x['yCoordinate'])
        else:
            closestobs = None

        scoreupdate = {"coin": self.coin_score_flag,
                       "feul": self.feul_score_flag,
                       "car_dodge": self.car_dodge_flag}
        reward = {"distance":self.distance,
                 "coincount":self.coins,
                 "fuel":self.cfuel,
                 "nitro": self.nitro.gas,
                  "score": self.score,
                  "car_dodge":self.dodged}
        state = {'player': player,
                 'obstacles': allobs,
                 'closestobs': closestobs,
                 'coins':allcoins,
                 'fuel':feul,
                 'allassets': allassets,
                 'score': reward,
                 'scoreupdate': scoreupdate}
        #print(self.score)
        return state#{'score':self.coins}


