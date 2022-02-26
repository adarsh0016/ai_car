import pygame
import os
import math
import configparser

# geting the global variables from the config file
configParser = configparser.RawConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__), 'Configs//Setting.cfg')
configParser.read(configFilePath)

# window width and height
WIN_WIDTH = configParser.getint("window", "WIN_WIDTH")
WIN_HEIGHT = configParser.getint("window", "WIN_HEIGHT")

# car width and height
CAR_SIZE_X = configParser.getint('car', 'CAR_SIZE_X')
CAR_SIZE_Y = configParser.getint('car', 'CAR_SIZE_Y')
CAR_VEL = configParser.getint('car', 'CAR_VEL')
CAR_VEL_MIN = configParser.getint('car', 'CAR_VEL_MIN')
CAR_ROT = configParser.getint('car', 'CAR_ROT')
CAR_POS_X = configParser.getint('car', 'CAR_POS_x')
CAR_POS_Y = configParser.getint('car', 'CAR_POS_y')

ROAD_COLOR = (0, 0, 0, 255) #black

# loading all the images nescessary for the game
CAR_IMAGE = pygame.image.load("Sprites\car.png")
CAR_IMAGE = pygame.transform.scale(CAR_IMAGE, (CAR_SIZE_X, CAR_SIZE_Y)) # scaling the image
CRASH_IMAGE = pygame.transform.scale(pygame.image.load("Sprites\crash.png"), (50, 50))

MAP = pygame.image.load("Sprites\map.png")
MAP = pygame.transform.scale(MAP, (WIN_WIDTH, WIN_HEIGHT)) # scaling the map

class Map:
    image = MAP
    width = WIN_WIDTH
    height = WIN_HEIGHT

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
        new_rect = rotated_image.get_rect(center=self.center) #this function returns a rectangle with the same center as the rotated image
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
            if Map.image.get_at((int(point[0]), int(point[1]))) != ROAD_COLOR:
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
            if Map.image.get_at((x, y)) != ROAD_COLOR:
                break

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.sensors.append([(x, y), dist])
        
        
    # moving the car, this function is called in the for every frame in the main loop
    def update(self, choice):
        if choice == 0:
            self.turn_left()
        elif choice == 1:
            self.turn_right()
        elif choice == 2:
            self.speed_up()
        elif choice == 3:
            self.slow_down()
        else:
            # do nothing just cruising
            pass
                
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
    
    def get_default_data(self):
        #return [3, 4, 4, 10, 2]
        return [0, 0, 0, 0, 0]
    
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
        return round(self.distance/(self.time * 20) + self.vel / 14)
    
def render(win, car):
    win.blit(Map.image, (0, 0))
    car.draw(win)   
    pygame.display.update()  

def main():
    car = Car()
    run = True
    win = pygame.display.set_mode((Map.width, Map.height))
    clock = pygame.time.Clock()
    
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            choice = 4
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    choice = 0
                elif event.key == pygame.K_RIGHT:
                    choice = 1
                elif event.key == pygame.K_UP:
                    choice = 2
                elif event.key == pygame.K_DOWN:
                    choice = 3
                            
        car.update(choice) 
        #drawing everything after updating the positions
        render(win, car)
                
    pygame.quit()
    quit()

if __name__ == "__main__":  # when used on its own i.e. just the game
    main()