import pickle
import pygame
import os
import configparser

import game

# geting the global variables from the config file
configParser = configparser.RawConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__), 'Configs//Setting.cfg')
configParser.read(configFilePath)

#fps settings
FPS = configParser.getint("window", "FPS")

def render(win, car):
    win.blit(game.Map.image, (0, 0))
    car.draw(win) 
    pygame.display.update()

def main():
    car = game.Car()
    run = True
    win = pygame.display.set_mode((game.Map.width, game.Map.height))
    clock = pygame.time.Clock()
    
    trained_ai_file = open('Trained_nets\\best_ai_car', 'rb')
    
    trained_ai_list = pickle.load(trained_ai_file)
    trained_ai = trained_ai_list[len(trained_ai_list) - 1][1]
    
    trained_ai_file.close()
    
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        if car.is_alive():
            output = trained_ai.activate(car.get_data())
            choice = output.index(max(output))
            
            car.update(choice) 
            
            #drawing everything after updating the positions
            render(win, car)
            
    pygame.quit()
    quit() 

if __name__ == "__main__":
    main()