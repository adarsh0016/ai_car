import neat
import pickle
import os
from car_training import *

def render(win, car):
    win.blit(sim.Map.image, (0, 0))
    sim.Map.draw_path(win)
    car.draw(win)
    pygame.display.flip()

def run_sim(genome, config):
    win = pygame.display.set_mode((sim.Map.width, sim.Map.height))
    
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    
    car = sim.Car()
    
    clock = pygame.time.Clock()
    
    while True:
        #exit on quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
                
        if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_presses = pygame.mouse.get_pressed()
                if mouse_presses[0]:
                    # Map.obstacle_pos.append(pygame.mouse.get_pos())
                    sim.Map.select_nearest_junction(pygame.mouse.get_pos())
                    
        if not sim.Map.dest_pos or car.if_reached():
            
            render(win, car)
            continue
                    
        output = net.activate(car.get_data())
        choice = output.index(max(output))
        car.update(choice)
        
        if not car.is_alive():
            print("crashed!")
            return
        
        render(win, car)
        clock.tick(FPS) #FPS

def main(config_path):
    #load configs
    config = neat.config.Config(neat.DefaultGenome,
                                    neat.DefaultReproduction,
                                    neat.DefaultSpeciesSet,
                                    neat.DefaultStagnation,
                                    config_path)

    with open('Trained_nets\\winner.pkl', "rb") as f:
        genome = pickle.load(f)

    # Call game with only the loaded genome
    run_sim(genome, config)
    
if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'Configs//NEAT_config.txt')
    main(config_path)