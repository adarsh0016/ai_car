import pygame
import neat
import os
import configparser
import sys
import pickle
import random

import visualize

import sim_neat as sim

# geting the global variables from the config file
configParser = configparser.RawConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__), 'Configs//Setting.cfg')
configParser.read(configFilePath)

#fps settings
FPS = configParser.getint("window", "FPS")

RENDER_EVERY = 1

change_dest_every = 1

# initializing the pygame display
pygame.init()

GENERATION_FONT = pygame.font.SysFont("Arial", 30)
ALIVE_FONT = pygame.font.SysFont("Arial", 20)

current_generation = 566 # Generation counter

def render(win, cars, still_alive):
    #Draw map and all cars that are alive
        win.blit(sim.Map.image, (0, 0))
        sim.Map.draw_path(win)
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

    win = pygame.display.set_mode((sim.Map.width, sim.Map.height))
    
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        
        cars.append(sim.Car())
        #cars[-1].angle = random.choice([0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360])
        
    #clock settings for fps
    clock = pygame.time.Clock()
    
    global current_generation # generation counter
    
    counter = 0 #time counter, needs to be rewritten using the time module for more accuracy
    
    # select randomly
    if current_generation % change_dest_every == 0 and list(sim.Map.paths.keys()):
        sim.Map.dest_pos = list(sim.Map.paths.keys())[random.randrange(2, len(list(sim.Map.paths.keys())))]
        sim.Map.Shortest_path()
    
    while True:
        #exit on quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
                
        # select with mouse
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #         mouse_presses = pygame.mouse.get_pressed()
        #         if mouse_presses[0]:
        #             # Map.obstacle_pos.append(pygame.mouse.get_pos())
        #             sim.Map.select_nearest_junction(pygame.mouse.get_pos())
                
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
                
        # if there are no alive cars, remove the generation
        if still_alive == 0:
            #removing extinct generation
            break
        
        counter += 1
        if counter == FPS * 2: #stop after about 20 seconds
            break

        if current_generation % RENDER_EVERY == 0:
            #rendering the map and cars
            render(win, cars, still_alive)
            clock.tick(FPS) #FPS
            
    current_generation += 1
       

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
    if current_generation != 0:
        population = neat.Checkpointer.restore_checkpoint('Trained_nets\\neat-checkpoint-' + str(current_generation))
    
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    #checkpoints
    population.add_reporter(neat.Checkpointer(generation_interval = 10, filename_prefix='Trained_nets\\neat-checkpoint-'))
    
    #run simulation for a maximum of 1000 generations
    winner = population.run(run_simulation, 1)
    
    #saving the winner genome
    with open("Trained_nets\\winner.pkl", "wb") as f:
        pickle.dump(winner, f)
        f.close()
    
    #for the graph of the NN
    node_names = {-1: 'Sensor 1', -2: 'Sensor 2', -3: 'Sensor 3', -4: 'Sensor 4', -5: 'Sensor 5', -6: 'Sensor 6', -7: 'Sensor 7', -8: 'Sensor 8', 0: 'Left', 1: 'Right', 2: 'Speed', 3: 'Reverse', 4: 'Speed-left', 5: 'Speed-right', 6: 'Stall', 7: 'Reverse-left', 8: 'Reverse-right'}

    visualize.draw_net(population.config, winner, True, node_names=node_names)
    visualize.plot_stats(stats, ylog=True)
    visualize.plot_species(stats)

def main():
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'Configs//NEAT_config.txt')
    run(config_path)
    
if __name__ == "__main__":
    main()