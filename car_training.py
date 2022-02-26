import pygame
import neat
import os
import configparser
import sys
import pickle

import visualize

import game

# geting the global variables from the config file
configParser = configparser.RawConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__), 'Configs//Setting.cfg')
configParser.read(configFilePath)

#fps settings
FPS = configParser.getint("window", "FPS")

# initializing the pygame display
pygame.init()

GENERATION_FONT = pygame.font.SysFont("Arial", 30)
ALIVE_FONT = pygame.font.SysFont("Arial", 20)

current_generation = 0 # Generation counter
trained_networks = [] #list of trained networks
best_ai_car = [] #best network of each generations

def render(win, cars, still_alive):
    #Draw map and all cars that are alive
        win.blit(game.Map.image, (0, 0))
        for car in cars:
            if car.is_alive():
                car.draw(win)
                
        #Display Info
        text = GENERATION_FONT.render("Generation: " + str(current_generation), True, (255,255,255))
        text_rect = text.get_rect()
        text_rect.center = (500, 350)
        win.blit(text, text_rect)

        text = ALIVE_FONT.render("Still Alive: " + str(still_alive), True, (255,255,255))
        text_rect = text.get_rect()
        text_rect.center = (500, 390)
        win.blit(text, text_rect)

        #refreshing the display
        pygame.display.flip()
        
#fitness funtion
def run_simulation(genomes, config):
    
    #collection for cars and networks
    nets = []
    cars = []

    win = pygame.display.set_mode((game.Map.width, game.Map.height))
    
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        
        cars.append(game.Car())
        
    #clock settings for fps
    clock = pygame.time.Clock()
    
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
            car.update(choice)
                
        # count the number of alive cars
        #increase the fitness of the alive cars
        still_alive = 0
        for i, car in enumerate(cars):
            if car.is_alive():
                still_alive += 1
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
        if counter == FPS * 10: #stop after about 20 seconds
            
            #adding each trained generation to a list
            trained_networks.append((current_generation, nets))
            best_ai_car.append((current_generation, nets[last_alive_car_position]))
            break

        #rendering the map and cars
        render(win, cars, still_alive)
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
    #population.add_reporter(neat.Checkpointer(generation_interval = 10, filename_prefix='Trained_nets\\neat-checkpoint-'))
    
    #run simulation for a maximum of 1000 generations
    winner = population.run(run_simulation, 100)
    
    node_names = {-1: 'Sensor 1', -2: 'Sensor 2', -3: 'Sensor 3', -4: 'Sensor 4', -5: 'Sensor 5', 0: 'Left', 1: 'Right', 2: 'Slow', 3: 'Speed'}
    visualize.draw_net(population.config, winner, True, node_names=node_names)
    visualize.plot_stats(stats, ylog=True)
    visualize.plot_species(stats)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'Configs//NEAT_config.txt')
    run(config_path)