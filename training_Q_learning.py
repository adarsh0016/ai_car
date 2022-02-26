import pygame
import os
import configparser
import sys
import pickle
import numpy as np
import matplotlib.pyplot as plt

import game

# https://www.youtube.com/watch?v=yMk_XtIEzH8&list=PLQVvvaa0QuDezJFIOU5wDdfy4e9vdnx-7


# q learning parameters
LEARNING_RATE = 0.9 #between 0 and 1, preffered to have it large and decay over time
DISCOUNT = 0.95 #future reward vs current reward or action
EPISODES = 3000 #number of episodes to run or simulations

SHOW_EVERY = 500 # how often to display the training progress

epsilon = 0.5 #probability of random action
START_EPSILON_DECAYING = 1
END_EPSILON_DECAYING = EPISODES // 1.25

epsilon_decay_value = epsilon/(END_EPSILON_DECAYING - START_EPSILON_DECAYING)

#q_table initiation
q_table = np.random.uniform(low = -2, high = 2, size = ([11, 11, 11, 11, 11] + [5])) #11x11x11x11x5 0-10 is the output of the sensors

# local_dir = os.path.dirname(__file__)
# Q_table_file_path = os.path.join(local_dir, 'Trained_nets\\Q_table_trained')
# q_table_file = open(Q_table_file_path, "rb")
# q_table = pickle.load(q_table_file)

ep_rewards = []
aggr_ep_rewards = {'ep': [], 'avg': [], 'min': [], 'max': []}

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

def render(win, car):
        win.blit(game.Map.image, (0, 0))
        #Draw map and all cars that are alive
        if car.is_alive():
            car.draw(win)

        #refreshing the display
        pygame.display.flip()
        
def get_discrete_state(state): # converting the state to a discrete state
    return tuple(state) # converting to tuple

def main():
    win = pygame.display.set_mode((game.Map.width, game.Map.height))
    
    #clock settings for fps
    clock = pygame.time.Clock()
    
    for episode in range(EPISODES):
        episode_reward = 0
        
        print("Episode: " + str(episode), end = "\r")
        
        car = game.Car()
        discrete_state = get_discrete_state(car.get_default_data())  # i have to improve this function in game.py because it always returns [0,0,0,0,0]
        
        counter = 0  #to remove the car after a certain amount of steps
        still_alive = True
        while still_alive:
            
            if counter > 1000:
               still_alive = False
               continue 
            
            #exit on quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    local_dir = os.path.dirname(__file__)
                    Q_table_file_path = os.path.join(local_dir, 'Trained_nets\\Q_table_trained')
                    
                    trained_network_file = open(Q_table_file_path, "ab")
                    pickle.dump(q_table, trained_network_file)
                    trained_network_file.close()
                    sys.exit(0)
                
            global epsilon
            if np.random.random() > epsilon:
                # Get action from Q table
                action = np.argmax(q_table[discrete_state])
            else:
                # Get random action
                action = np.random.randint(0, 2)  # 0 is left, 1 is right
                
            car.update(action)
            reward = car.get_reward()
            still_alive = car.is_alive()
            
            episode_reward += reward
            
            new_state = car.get_data()
            new_discrete_state = get_discrete_state(new_state)
            
            if episode % SHOW_EVERY == 0:
                #rendering the map and cars
                render(win, car)
                clock.tick(FPS) #FPS
            
            if not still_alive:
                reward = -5
                
            global LEARNING_RATE
            
            max_future_q = np.max(q_table[new_discrete_state])
            current_q = q_table[discrete_state + (action, )]
            new_q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT * max_future_q)
            q_table[discrete_state + (action, )] = new_q
                
            discrete_state = new_discrete_state
            
            counter += 1
            
        if END_EPSILON_DECAYING >= episode >= START_EPSILON_DECAYING:
            epsilon -= epsilon_decay_value
            
        LEARNING_RATE = LEARNING_RATE * 0.999
        
        ep_rewards.append(episode_reward)
        
        if not episode % SHOW_EVERY:
            average_reward = sum(ep_rewards[-SHOW_EVERY:])/len(ep_rewards[-SHOW_EVERY:])
            aggr_ep_rewards['ep'].append(episode)
            aggr_ep_rewards['avg'].append(average_reward)
            aggr_ep_rewards['min'].append(min(ep_rewards[-SHOW_EVERY:]))
            aggr_ep_rewards['max'].append(max(ep_rewards[-SHOW_EVERY:]))
            
            print(f"Episode: {episode} avg: {average_reward} min: {min(ep_rewards[-SHOW_EVERY:])} max: {max(ep_rewards[-SHOW_EVERY:])}")
            
          
    local_dir = os.path.dirname(__file__)
    Q_table_file_path = os.path.join(local_dir, 'Trained_nets\\Q_table_trained')
    
    trained_network_file = open(Q_table_file_path, "wb")
    pickle.dump(q_table, trained_network_file)
    trained_network_file.close()
    
    plt.plot(aggr_ep_rewards['ep'], aggr_ep_rewards['avg'], label = "avg")
    plt.plot(aggr_ep_rewards['ep'], aggr_ep_rewards['min'], label = "min")
    plt.plot(aggr_ep_rewards['ep'], aggr_ep_rewards['max'], label = "max")
    plt.legend(loc=4)
    plt.show()
       
if __name__ == "__main__":
    main()