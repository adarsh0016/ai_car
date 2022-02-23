import pygame
import neat
import time
import os
import math
import configparser
import sys
import pickle
import visualize

# geting the global variables from the config file
configParser = configparser.RawConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__), 'Setting.cfg')
configParser.read(configFilePath)

# window width and height
WIN_WIDTH = configParser.getint("window", "WIN_WIDTH")
WIN_HEIGHT = configParser.getint("window", "WIN_HEIGHT")

#fps settings
FPS = configParser.getint("window", "FPS")

# car width and height
CAR_SIZE_X = configParser.getint('car', 'CAR_SIZE_X')
CAR_SIZE_Y = configParser.getint('car', 'CAR_SIZE_Y')
CAR_VEL = configParser.getint('car', 'CAR_VEL')
CAR_VEL_MIN = configParser.getint('car', 'CAR_VEL_MIN')
CAR_ROT = configParser.getint('car', 'CAR_ROT')
CAR_POS_X = configParser.getint('car', 'CAR_POS_x')
CAR_POS_Y = configParser.getint('car', 'CAR_POS_y')

ROAD_COLOR = (0, 0, 0, 255) #black

GENERATION_FONT = ("Arial", 30)
ALIVE_FONT = ("Arial", 20)

# loading all the images nescessary for the game
CAR_IMAGE = pygame.image.load("Sprites\car.png")
CAR_IMAGE = pygame.transform.scale(CAR_IMAGE, (CAR_SIZE_X, CAR_SIZE_Y)) # scaling the image
CRASH_IMAGE = pygame.transform.scale(pygame.image.load("Sprites\crash.png"), (50, 50))

MAP = pygame.image.load("Sprites\mp2.png")
MAP = pygame.transform.scale(MAP, (WIN_WIDTH, WIN_HEIGHT)) # scaling the map

current_generation = 0 # Generation counter
trained_networks = [] #list of trained networks
best_ai_car = [] #best network of each generations

class Car:
    
    def __init__(self): # [550, 580]
        self.sprite = CAR_IMAGE
        self.updated_sprite = CAR_IMAGE 
        self.crash_sprite = CRASH_IMAGE
        self.position = (CAR_POS_X, CAR_POS_Y)
        self.angle = 0 # rotation of the car
        self.vel = CAR_VEL # velocity of the car
        
        self.center = [self.position[0] + CAR_SIZE_X/2, self.position[1] + CAR_SIZE_Y/2] # center of the car
        
        self.alive = True # if the car is alive or not
        
        self.distance = 0 # distance travelled
        self.time = 0 # time taken
        
        self.sensors = [] # list of the radars
        self.hitbox = [(self.position[0], self.position[1]), (self.position[0] + CAR_SIZE_X, self.position[1]), (self.position[0], self.position[1] + CAR_SIZE_Y), (self.position[0] + CAR_SIZE_X, self.position[1] + CAR_SIZE_Y)] # hitbox of the car
            
    def speed_up(self):
        self.vel = self.vel + 1
        
    def slow_down(self):
        if(self.vel == CAR_VEL_MIN):
            return
        self.vel = self.vel - 1
        
    def turn_left(self):
        self.angle = (self.angle + CAR_ROT) % 360 # rotating the car not more than 360 degrees
        
        self.updated_sprite = self.rotate_spritebycenter() # rotating the sprite
        
    def turn_right(self):
        self.angle = (self.angle - CAR_ROT) % 360
        
        self.updated_sprite = self.rotate_spritebycenter() # rotating the sprite
        
    # rotating the sprite by its center
    def rotate_spritebycenter(self):
        # https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
        # got this from stackoverflow how to rotate an image around its center
        rotated_image = pygame.transform.rotate(self.sprite, self.angle)
        new_rect = rotated_image.get_rect(center=self.updated_sprite.get_rect(topleft=self.position).center) #this function returns a rectangle with the same center as the rotated image
        self.position = new_rect.topleft
        self.center = new_rect.center

        # recalculating the hitbox
        # https://www.youtube.com/watch?v=paU8JumpTXc  rotating hitbox
        dx = CAR_SIZE_X/2 - 4 # -4 because the hitbox is 4 pixels smaller than the car for better collision detection and game feel
        dy = CAR_SIZE_Y/2 - 4
        
        self.hitbox[0] = ((-dx * math.cos(math.radians(self.angle)) - dy * math.sin(math.radians(self.angle)) + self.center[0]), 
                          (dx * math.sin(math.radians(self.angle)) - dy * math.cos(math.radians(self.angle)) + self.center[1]))
        self.hitbox[1] = ((dx * math.cos(math.radians(self.angle)) - dy * math.sin(math.radians(self.angle)) + self.center[0]), 
                          (-dx * math.sin(math.radians(self.angle)) - dy * math.cos(math.radians(self.angle)) + self.center[1]))
        self.hitbox[2] = ((dx * math.cos(math.radians(self.angle)) + dy * math.sin(math.radians(self.angle)) + self.center[0]), 
                          (-dx * math.sin(math.radians(self.angle)) + dy * math.cos(math.radians(self.angle)) + self.center[1]))
        self.hitbox[3] = ((-dx * math.cos(math.radians(self.angle)) + dy * math.sin(math.radians(self.angle)) + self.center[0]), 
                          (dx * math.sin(math.radians(self.angle)) + dy * math.cos(math.radians(self.angle)) + self.center[1]))
        
        return rotated_image
        
    def check_collision(self):
        # checking if the car has collided with the border
        for point in self.hitbox:
            # checking if the point is overlaps with the border
            if MAP.get_at((int(point[0]), int(point[1]))) != ROAD_COLOR:
                self.alive = False
                break
            
    # recalculating the sensor output
    def check_sensor(self, sensor_angle):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + sensor_angle))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + sensor_angle))) * length)

        # While We Don't Hit BORDER_COLOR AND length < 300 (just a max dist the sensor can calculate)
        while length < 300:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + sensor_angle))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + sensor_angle))) * length)
            if MAP.get_at((x, y)) != ROAD_COLOR:
                break

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.sensors.append([(x, y), dist])
        
        
    # moving the car, this function is called in the for every frame in the main loop
    def update(self):
        # end game when collision occurs
        if(self.alive == False):
            # restart new generation
            return
        
        # checking if the car has collided with the border every frame
        self.check_collision();
        
        # updating the distance travelled (-1 because the pygame calculates the distance from the top left corner)
        vel_x = math.cos(math.radians(self.angle)) * self.vel
        vel_y = math.sin(math.radians((-1) * self.angle)) * self.vel
        self.position = (self.position[0] + vel_x, self.position[1] + vel_y)
        
        self.center = (self.center[0] + vel_x, self.center[1] + vel_y)
        
        #updating the hitbox
        self.hitbox[0] = (self.hitbox[0][0] + vel_x, self.hitbox[0][1] + vel_y)
        self.hitbox[1] = (self.hitbox[1][0] + vel_x, self.hitbox[1][1] + vel_y)
        self.hitbox[2] = (self.hitbox[2][0] + vel_x, self.hitbox[2][1] + vel_y)
        self.hitbox[3] = (self.hitbox[3][0] + vel_x, self.hitbox[3][1] + vel_y)
        
        # updating the time and distance travelled
        self.time += 1
        self.distance += self.vel
        
        #removing the sensors for re-calculation
        self.sensors.clear()
        
        #all the sensors are calculated here
        for d in range(-90, 91, 45):
            self.check_sensor(d)  
    
    # drawing the map and car
    def draw(self, win):
        win.blit(self.updated_sprite, self.position)
        
        # drawing the sensors
        #self.draw_sensors(win)
        
        # drawing the hitbox and the center of the car
        #self.draw_hitbox(win)
        
    # drawing the hitbox and the center of the car
    def draw_hitbox(self, win):
        pygame.draw.circle(win, (255, 0, 0), self.center, 2)
        pygame.draw.circle(win, (255, 0, 0), self.hitbox[0], 1)
        pygame.draw.circle(win, (255, 0, 0), self.hitbox[1], 1)
        pygame.draw.circle(win, (255, 0, 0), self.hitbox[2], 1)
        pygame.draw.circle(win, (255, 0, 0), self.hitbox[3], 1)
        
    def draw_sensors(self, win):
    # Optionally Draw All Sensors
        for sensor in self.sensors:
            position = sensor[0]
            pygame.draw.line(win, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(win, (0, 255, 0), position, 5)
            
    # functions for the neat algorithm
    
    def get_data(self):
        # getting the distance to the border
        sensors = self.sensors
        return_values = [0, 0, 0, 0, 0] # five sensors
        for i, sensor in enumerate(sensors):
            return_values[i] = int(sensor[1] / 30) 
            
        return return_values
    
    def is_alive(self):
        return self.alive
    
    def get_reward(self):
        return self.distance/(self.time / 40) + self.vel * 10

#fitness funtion
def run_simulation(genomes, config):
    
    #collection for cars and networks
    nets = []
    cars = []
    
    # initializing the pygame display
    pygame.init()
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        
        cars.append(Car())
        
    #clock settings for fps
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont(GENERATION_FONT[0], GENERATION_FONT[1])
    alive_font = pygame.font.SysFont(ALIVE_FONT[0], ALIVE_FONT[1])
    
    global current_generation # generation counter
    current_generation += 1
    
    counter = 0 #time counter, needs to be rewritten using the time module for more accuracy
    
    last_alive_car_position = 0 #position of the last alive car in the cars list
    
    while True:
        #exit on quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_trained_networks(trained_networks)
                sys.exit(0)
                
        # for each car get the action it takes from the neural network
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.turn_left()
            elif choice == 1:
                car.turn_right()
            elif choice == 2:
                car.slow_down()
            else:
                car.speed_up()
                
        # count the number of alive cars
        #increase the fitness of the alive cars
        still_alive = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                still_alive += 1
                car.update()
                genomes[i][1].fitness += car.get_reward()
                last_alive_car_position = i
                
        # if there are no alive cars, remove the generation
        if still_alive == 0:
            
            #adding each trained generation to a list
            trained_networks.append((current_generation, nets))
            best_ai_car.append((current_generation, nets[last_alive_car_position]))
            #removing extinct generation
            break
        
        counter += 1
        if counter == FPS * 2: #stop after about 20 seconds
            
            #adding each trained generation to a list
            trained_networks.append((current_generation, nets))
            best_ai_car.append((current_generation, nets[last_alive_car_position]))
            break
        
        #Draw map and all cars that are alive
        win.blit(MAP, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(win)
                
        #Display Info
        text = generation_font.render("Generation: " + str(current_generation), True, (255,255,255))
        text_rect = text.get_rect()
        text_rect.center = (500, 350)
        win.blit(text, text_rect)

        text = alive_font.render("Still Alive: " + str(still_alive), True, (255,255,255))
        text_rect = text.get_rect()
        text_rect.center = (500, 390)
        win.blit(text, text_rect)

        #refreshing the display
        pygame.display.flip()
        clock.tick(FPS) #FPS
       
#saving the trained networks 
def save_trained_networks(trained_network_generations):
    #opening a new file
    local_dir = os.path.dirname(__file__)
    trained_networks_file_path = os.path.join(local_dir, 'Trained_nets\\trained_networks')
    best_ai_file_path = os.path.join(local_dir, 'Trained_nets\\best_ai_car')
    
    trained_network_file = open(trained_networks_file_path, "ab")
    best_ai_car_file = open(best_ai_file_path, "ab")
    
    #dumps the trained networks into the file using pickle
    pickle.dump(trained_network_generations, trained_network_file)
    pickle.dump(best_ai_car, best_ai_car_file)
    trained_network_file.close()
    best_ai_car_file.close()

def run(config_path):
    #load configs
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)
    
    # Create population and add reporters
    population = neat.Population(config)
    
    #load a checkpoint
    #population = neat.Checkpointer.restore_checkpoint('Trained_nets\\neat-checkpoint-120')
    
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    #checkpoints
    population.add_reporter(neat.Checkpointer(generation_interval = 10, filename_prefix='Trained_nets\\neat-checkpoint-'))
    
    #run simulation for a maximum of 1000 generations
    winner = population.run(run_simulation, 100)
    
    node_names = {-1: 'Sensor 1', -2: 'Sensor 2', -3: 'Sensor 3', -4: 'Sensor 4', -5: 'Sensor 5', 0: 'Left', 1: 'Right', 2: 'Slow', 3: 'Speed'}
    visualize.draw_net(population.config, winner, True, node_names=node_names)
    visualize.plot_stats(stats, ylog=True)
    visualize.plot_species(stats)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'NEAT_config.txt')
    run(config_path)