#http://rmgi.blog/pygame-2d-car-tutorial.html

import pickle
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
CAR_POS_X = configParser.getint('car', 'CAR_POS_x')
CAR_POS_Y = configParser.getint('car', 'CAR_POS_y')
CAR_VEL = configParser.getint('car', 'CAR_VEL')
CAR_VEL_MAX = configParser.getint('car', 'CAR_VEL_MAX')
CAR_VEL_MIN = configParser.getint('car', 'CAR_VEL_MIN')
CAR_ACC = configParser.getfloat('car', 'CAR_ACC')
CAR_ACC_BACK = configParser.getfloat('car', 'CAR_ACC_BACK')
CAR_FRICTION = configParser.getfloat('car', 'CAR_FRICTION')
CAR_ROT = configParser.getfloat('car', 'CAR_ROT')

ROAD_COLOR = (0, 0, 0, 255) #black

# loading all the images nescessary for the game
CAR_IMAGE = pygame.image.load("Sprites\car.png")
CAR_IMAGE = pygame.transform.scale(CAR_IMAGE, (CAR_SIZE_X, CAR_SIZE_Y)) # scaling the image

map = "mp2"

MAP = pygame.image.load("Sprites\\Maps\\" + map + ".png")
MAP = pygame.transform.scale(MAP, (WIN_WIDTH, WIN_HEIGHT)) # scaling the map


#--------------------------------------------------- Helper functions to calculate distances (vector formulas) -------------------------------------------------------------------


#distance between two points
def distance(point1, point2):
    return math.sqrt(abs(math.pow((point2[1] - point1[1]), 2)) + abs(math.pow((point2[0] - point1[0]), 2)))

# distance between a point and a finite line segment represented by two points
# https://stackoverflow.com/a/2233538 reference..
def distance_to_line(point, line_start_pos, line_end_pos): # x3,y3 is the point
    x1 = line_start_pos[0]
    y1 = line_start_pos[1]
    x2 = line_end_pos[0]
    y2 = line_end_pos[1]
    x3 = point[0]
    y3 = point[1]
    
    px = x2-x1
    py = y2-y1

    norm = px*px + py*py

    u =  ((x3 - x1) * px + (y3 - y1) * py) / float(norm)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    # Note: If the actual distance does not matter,
    # if you only want to compare what this function
    # returns to other results of this function, you
    # can just return the squared distance instead
    # (i.e. remove the sqrt) to gain a little performance

    dist = (dx*dx + dy*dy)**.5

    return dist


#----------------------------------------------------- Map class -----------------------------------------------------------------


class Map:
    image = MAP
    width = WIN_WIDTH
    height = WIN_HEIGHT
    # obstacle_pos = []
    
    #----------------------------------------------------- path graph -----------------------------------------------------------------
    
    with open('Sprites\\Maps\\' + map + '.pkl', "rb") as f:
        paths = pickle.load(f)
    
    #initialization of start and end position of the path
    if list(paths.keys()):
        start_pos = list(paths.keys())[1]
    dest_pos = ()
    
    #selects the nearnest junction when cliked on the juction under 20 pixel range
    def select_nearest_junction(mouse_click_pos):
        min_dist = 10000
        for junc in Map.paths:
            if distance(junc, mouse_click_pos) < min_dist and distance(junc, mouse_click_pos) < 20:
                min_dist = distance(junc, mouse_click_pos)
                Map.dest_pos = junc
                
        Map.Shortest_path()
    
    #the shortest path from start to destination
    shortest_path = []
    shortest_path_comb = []
    
    
    #----------------------------------------------------- Shortest path algorithm -----------------------------------------------------------------
    
    
    #bfs algorithm
    def Shortest_path():
        Map.shortest_path = []
        Map.shortest_path_comb = []
    
        queue = []
        
        visited = []
        
        #if not destination then add the start position to the queue
        if Map.start_pos != Map.dest_pos:
            queue.append([Map.start_pos])
            visited.append(Map.start_pos)
            
        else:
            Map.shortest_path = [Map.start_pos]
            return
        
        while(queue):
            path = queue.pop(0)
            current = path[-1]
            
            if current == Map.dest_pos:
                Map.shortest_path = path
                
                # make pairs of sart and end points(junctions) of paths and saving it in shortest_path_comb for ease of use 
                line_start_pos = ()
                for junc in Map.shortest_path:
                    line_end_pos = junc
                    if line_start_pos:
                        Map.shortest_path_comb.append((line_start_pos, line_end_pos))  
                        
                    line_start_pos = line_end_pos
                        
                return
            
            for neighbour in Map.paths[current]:
                if neighbour[0] not in visited:
                    visited.append(neighbour[0])
                    new_path = path.copy()
                    new_path.append(neighbour[0])
                    queue.append(new_path)
        
        Map.shortest_path = []    
                    
        return
    
    # checks if the pixel is not on road i.e. offroad or on an obstacle
    # return true if the pixel is offroad
    def check_pixel_offroad(point):
        #checks if the pixel is offroas i.e. black
        if Map.image.get_at((int(point[0]), int(point[1]))) != ROAD_COLOR:
            return True
        
        # for obs in Map.obstacle_pos:
        #     if math.sqrt(abs(math.pow((obs[1] - point[1]), 2)) + abs(math.pow((obs[0] - point[0]), 2))) <= 20:
        #         return True
        
        dist = 1000
        for (start_pos, end_pos) in Map.shortest_path_comb:
            dist = min(dist, distance_to_line(point, start_pos, end_pos))
        if dist != 1000 and dist > 30:
            return True
        
        return False
    
    #draws the shortest path
    def draw_path(win):
        for (line_start_pos, line_end_pos) in Map.shortest_path_comb:
            
            pygame.draw.line(win, (255, 255, 255), line_start_pos, line_end_pos, 1)
            
            
            
#----------------------------------------------------- Car class -----------------------------------------------------------------
            
            

class Car:
    
    def __init__(self):
        self.center = (CAR_POS_X + CAR_SIZE_X/2, CAR_POS_Y+ CAR_SIZE_Y/2) # center of the car
        
        self.sprite = CAR_IMAGE
        self.updated_sprite = CAR_IMAGE 
        self.rect = self.sprite.get_rect(center = self.center)
        self.offset = CAR_SIZE_X/2.2
        self.offset_vector = pygame.math.Vector2(self.offset, 0)
        self.back_wheel_position = (self.center[0] - self.offset, self.center[1])
        self.angle = 0 # rotation of the car
        self.vel = CAR_VEL # velocity of the car
        self.vel_max = CAR_VEL_MAX
        self.vel_min = CAR_VEL_MIN
        self.acc = CAR_ACC
        self.acc_back = CAR_ACC_BACK
        self.friction = CAR_FRICTION

        self.alive = True # if the car is alive or not
        
        self.distance = 0 # distance travelled
        self.time = 0 # time taken
        
        self.sensors = [] # list of the radars
        self.hitbox = [(self.center[0] - CAR_SIZE_X/2, self.center[1] - CAR_SIZE_Y/2), 
                       (self.center[0] + CAR_SIZE_X/2, self.center[1] - CAR_SIZE_Y/2), 
                       (self.center[0] + CAR_SIZE_X/2, self.center[1] + CAR_SIZE_Y/2), 
                       (self.center[0] - CAR_SIZE_X/2, self.center[1] + CAR_SIZE_Y/2)] # hitbox of the car
            
            
    #---------------------------------- vechicle control methods ----------------------------------
            
            
    def speed_up(self):
        if self.vel < self.vel_max:
            self.vel += self.acc
        
    def brake(self):
        if(self.vel <= 0):
            if(self.vel > self.vel_min):
                self.vel -= self.acc_back #reverse
        else:
            self.vel = 0 #brake
        
    def turn_left(self):
        self.angle = (self.angle - CAR_ROT * self.vel / 2) % 360
        self.updated_sprite = self.rotate_sprite()
        
    def turn_right(self):
        self.angle = (self.angle + CAR_ROT * self.vel / 2) % 360
        self.updated_sprite = self.rotate_sprite()
        
        
    #---------------------------------- vechicle rotate methods ----------------------------------
        
        
    # rotating the sprite
    def rotate_sprite(self):
        #https://stackoverflow.com/questions/15098900/how-to-set-the-pivot-point-center-of-rotation-for-pygame-transform-rotate
        rotated_image = pygame.transform.rotozoom(self.sprite, -self.angle, 1)
        rotated_offset = self.offset_vector.rotate(self.angle)
        self.center = self.back_wheel_position + rotated_offset
        self.rect = rotated_image.get_rect(center = self.center)
        
        if self.angle == 0: # had to do this because of weird streching in this case
            rotated_image = self.sprite
            
        # recalculating the hitbox
        # https://www.youtube.com/watch?v=paU8JumpTXc  rotating hitbox
        dx1 = CAR_SIZE_X/2 - self.offset -1 # -1 because the hitbox is 4 pixels smaller than the car for better collision detection and game feel
        dx2 = CAR_SIZE_X/2 + self.offset -1
        dy = CAR_SIZE_Y/2 -1
        
        self.hitbox[0] = ((-dx1 * math.cos(math.radians(self.angle)) + dy * math.sin(math.radians(self.angle)) + self.back_wheel_position[0]), 
                          (-dx1 * math.sin(math.radians(self.angle)) - dy * math.cos(math.radians(self.angle)) + self.back_wheel_position[1]))
        self.hitbox[1] = ((dx2 * math.cos(math.radians(self.angle)) + dy * math.sin(math.radians(self.angle)) + self.back_wheel_position[0]), 
                          (dx2 * math.sin(math.radians(self.angle)) - dy * math.cos(math.radians(self.angle)) + self.back_wheel_position[1]))
        self.hitbox[2] = ((dx2 * math.cos(math.radians(self.angle)) - dy * math.sin(math.radians(self.angle)) + self.back_wheel_position[0]), 
                          (dx2 * math.sin(math.radians(self.angle)) + dy * math.cos(math.radians(self.angle)) + self.back_wheel_position[1]))
        self.hitbox[3] = ((-dx1 * math.cos(math.radians(self.angle)) - dy * math.sin(math.radians(self.angle)) + self.back_wheel_position[0]), 
                          (-dx1 * math.sin(math.radians(self.angle)) + dy * math.cos(math.radians(self.angle)) + self.back_wheel_position[1]))
        
        return rotated_image
    
    
    #---------- boundary check, collision detection and destination check (checks if the car has reached its destination) methods ----------------------
    
    #cheks if hitbox of the car is offroad
    def check_collision(self):
        # checking if the car has collided with the border
        for point in self.hitbox:
            # checking if the point is overlaps with the border
            if Map.check_pixel_offroad(point):
                self.alive = False
                break
    
    #calculates the length of the sensors, or the output of the sensors
    def check_sensor(self, sensor_angle):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (-self.angle + sensor_angle))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (-self.angle + sensor_angle))) * length)

        # While We Don't Hit BORDER_COLOR AND length < 300 (just a max dist the sensor can calculate)
        while length < 300:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (-self.angle + sensor_angle))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (-self.angle + sensor_angle))) * length)
            if Map.check_pixel_offroad((x,y)):
                break

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.sensors.append([(x, y), dist])
        
        
    #checks if the car has reached its destination
    def if_reached(self):
        #first we check if we have a destination to avoid error
        if Map.dest_pos and distance(self.center, Map.dest_pos) < 15:
            #once reachead we reset the start and destination
            Map.start_pos = Map.dest_pos
            Map.dest_pos = ()
            return True
        
        
    #---------------------------------- update method runs every frame ----------------------------------
        
        
    # moving the car, this function is called in the for every frame in the main loop
    def update(self, choice):
        if choice == 1:
            self.speed_up()
        elif choice == 2:
            self.turn_left()
        elif choice == 3:
            self.turn_right()
        elif choice == 4:
            self.brake()
        elif choice == 5:
            self.turn_left()
            self.speed_up()
        elif choice == 6:
            self.turn_right()
            self.speed_up()
        elif choice == 7:
            self.turn_left()
            self.brake()
        elif choice == 8:
            self.turn_right()
            self.brake()
        elif choice == 0:
            pass
        
        # end game when collision occurs
        if(self.alive == False):
            # restart new generation
            return
        
        # end game when car reaches the destination
        if(self.if_reached()):
            # restart new generation
            print("reached")
            self.vel = 0
            return
        
        # checking if the car has collided with the border every frame
        self.check_collision();
            
        # moving the car every frame
        vel_x = self.vel*math.cos(math.radians(self.angle))
        vel_y = self.vel*math.sin(math.radians(self.angle))
        self.center = (self.center[0] + vel_x, self.center[1] + vel_y)
        self.back_wheel_position = (self.back_wheel_position[0] + vel_x, self.back_wheel_position[1] + vel_y)
        self.hitbox[0] = (self.hitbox[0][0] + vel_x, self.hitbox[0][1] + vel_y)
        self.hitbox[1] = (self.hitbox[1][0] + vel_x, self.hitbox[1][1] + vel_y)
        self.hitbox[2] = (self.hitbox[2][0] + vel_x, self.hitbox[2][1] + vel_y)
        self.hitbox[3] = (self.hitbox[3][0] + vel_x, self.hitbox[3][1] + vel_y)

        self.rect = self.updated_sprite.get_rect(center = self.center)
        
        # friction implementation
        if self.vel >= 0:
            self.vel -= min(self.vel, self.friction)
        else:
            self.vel -= max(self.vel, -1 * self.friction)
            
        # updating the time and distance travelled
        self.time += 1
        self.distance += self.vel
        
        #removing the sensors for re-calculation
        self.sensors.clear()
        
        #all the sensors are calculated here
        for d in range(-90, 91, 45):
            self.check_sensor(d)  
    
    
    #---------------------------------- render/drawing methods ----------------------------------
    
    
    # drawing the map and car
    def draw(self, win):
        win.blit(self.updated_sprite, self.rect)
        
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
            pygame.draw.circle(win, (0, 255, 0), position, 3)
            
    
    #---------------------------------- methods for the NEAT algorithm ----------------------------------
    
    
    def get_default_data(self):
        #return [3, 4, 4, 10, 2]
        self.check_sensor(self.angle)
        sensors = self.sensors
        return_values = [0, 0, 0, 0, 0] # eight sensors
        for i, sensor in enumerate(sensors):
            return_values[i] = int(sensor[1] / 30) 
          
        return return_values
    
    def get_data(self):
        # getting the distance to the border
        sensors = self.sensors
        return_values = [0, 0, 0, 0, 0] # eight sensors
        for i, sensor in enumerate(sensors):
            return_values[i] = int(sensor[1] / 30) 
          
        return return_values
    
    def is_alive(self):
        return self.alive
    
    def get_reward(self):
        if self.if_reached():
            return 5 # if it reaches the destination then it will give 5 reward points
        
        return round(self.distance/(self.time * 20) + self.vel / 14)
    
    
    
#-------------------------------------------------------- main method ----------------------------------------------------------------
    
    
def render(win, car):
    win.blit(Map.image, (0, 0))  
    # for obs in Map.obstacle_pos:
    #     pygame.draw.circle(win, (255,255,255), obs, 20)
    
    Map.draw_path(win)
        
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
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_presses = pygame.mouse.get_pressed()
                if mouse_presses[0]:
                    # Map.obstacle_pos.append(pygame.mouse.get_pos())
                    Map.select_nearest_junction(pygame.mouse.get_pos())

           
        if car.is_alive():         
            choice = 0
            key = pygame.key.get_pressed()
            if key[pygame.K_UP] and key[pygame.K_LEFT]:
                choice = 5
            elif key[pygame.K_UP] and key[pygame.K_RIGHT]:
                choice = 6
            elif key[pygame.K_DOWN] and key[pygame.K_LEFT]:
                choice = 7
            elif key[pygame.K_DOWN] and key[pygame.K_RIGHT]:
                choice = 8
            elif key[pygame.K_UP]:
                choice = 1
            elif key[pygame.K_LEFT]:
                choice = 2
            elif key[pygame.K_RIGHT]:
                choice = 3
            elif key[pygame.K_DOWN]:
                choice = 4
                                
            car.update(choice) 
            #drawing everything after updating the positions
            render(win, car)
        else:
            print("crashed!", end ="\r")
                
    pygame.quit()
    quit()

if __name__ == "__main__":  # when used on its own i.e. just the game
    main()