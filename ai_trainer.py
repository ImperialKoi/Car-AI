import neat
import pygame
import math
import pickle
import os
import sys

sys.path.append('..')
from environment import Car

class SimpleAITrainer:
    def __init__(self):
        self.generation = 0
        self.best_fitness_ever = 0
        self.population_size = 20
        self.screen_width = 1280
        self.screen_height = 720
        self.time_limits = {'early': 15, 'mid': 30, 'late': 60}
        self.config_file = "train/neat_config.txt"
        self.setup_checkpoints()
    
    def setup_checkpoints(self):
        self.checkpoints = [
            (407, 353, 50), (618, 326, 50), (782, 125, 50),
            (944, 390, 50), (1177, 529, 50), (923, 642, 50),
            (608, 560, 50), (362, 636, 50), (125, 520, 50),
            (145, 281, 50), (170, 75, 50), (348, 136, 50)
        ]

    def create_cars(self, genomes, config):
        self.cars = []
        self.genomes = []
        self.networks = []
        colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), 
                  (255, 255, 100), (255, 100, 255), (100, 255, 255)]
        start_x, start_y, start_angle = 400, 360, 0
        
        for i, (genome_id, genome) in enumerate(genomes):
            network = neat.nn.FeedForwardNetwork.create(genome, config)
            color = colors[i % len(colors)]
            car = Car(i + 1, start_x, start_y, start_angle, color)
            car.set_checkpoints(self.checkpoints)
            self.cars.append(car)
            self.genomes.append(genome)
            self.networks.append(network)
            genome.fitness = 0
    
    def get_ai_decision(self, car_index):
        if car_index >= len(self.cars):
            return (False, False, 0)
        
        car = self.cars[car_index]
        network = self.networks[car_index]
        inputs = []
        
        for sensor_reading in car.sensor_readings:
            inputs.append(sensor_reading / car.sensor_range)
        inputs.append(car.speed / car.max_speed)
        inputs.append(car.angle / 360.0)
        
        outputs = network.activate(inputs)
        accelerate = outputs[0] > 0.5
        brake = outputs[1] > 0.5
        steering_output = outputs[2]
        
        if steering_output < -0.33:
            steer = -1
        elif steering_output > 0.33:
            steer = 1
        else:
            steer = 0
        
        return (accelerate, brake, steer)
    
    def calculate_fitness(self, car, time_alive):
        fitness = time_alive * 3
        fitness += car.checkpoints_reached * 50
        fitness += car.laps_completed * 1000
        fitness += car.speed * 0.5
        
        if car.crashed:
            fitness -= 25
        
        if hasattr(car, 'checkpoints') and car.current_checkpoint < len(car.checkpoints):
            checkpoint_x, checkpoint_y, checkpoint_radius = car.checkpoints[car.current_checkpoint]
            distance = math.sqrt((car.position.x - checkpoint_x) ** 2 + (car.position.y - checkpoint_y) ** 2)
            progress_bonus = max(0, (checkpoint_radius - distance) * 0.1)
            fitness += progress_bonus
        
        return max(0, fitness)
    
    def get_time_limit(self):
        if self.generation <= 5:
            return self.time_limits['early']
        elif self.generation <= 15:
            return self.time_limits['mid']
        else:
            return self.time_limits['late']
    
    def run_generation(self, genomes, config, screen, clock, font, track_image, finish_image):
        self.generation += 1
        time_limit = self.get_time_limit()
        self.create_cars(genomes, config)
        start_time = pygame.time.get_ticks()
        
        while True:
            current_time = pygame.time.get_ticks()
            time_alive = (current_time - start_time) / 1000.0
            
            if time_alive >= time_limit:
                break
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
            
            active_cars = 0
            for i, car in enumerate(self.cars):
                if car.laps_completed < 2:
                    ai_decision = self.get_ai_decision(i)
                    car.update(ai_decision)
                    if not car.crashed:
                        active_cars += 1
            
            for i, (car, genome) in enumerate(zip(self.cars, self.genomes)):
                fitness = self.calculate_fitness(car, time_alive)
                genome.fitness = fitness
                if fitness > self.best_fitness_ever:
                    self.best_fitness_ever = fitness
            
            self.draw_training_screen(screen, font, track_image, finish_image, time_alive, time_limit, active_cars)
            pygame.display.flip()
            clock.tick(60)
        
        return True

    def draw_training_screen(self, screen, font, track_image, finish_image, time_alive, time_limit, active_cars):
        screen.fill((0, 0, 0))
        screen.blit(track_image, (0, 0))
        screen.blit(finish_image, (270, 200))
        
        for i, (x, y, radius) in enumerate(self.checkpoints):
            color = (0, 255, 0) if i == 0 else (255, 255, 0)
            pygame.draw.circle(screen, color, (int(x), int(y)), radius, 3)
            text = font.render(str(i + 1), True, (255, 255, 255))
            text_rect = text.get_rect(center=(int(x), int(y)))
            screen.blit(text, text_rect)
        
        for car in self.cars:
            car.draw(screen)
        
        info_color = (100, 200, 255)
        info_texts = [
            f"Generation: {self.generation}",
            f"Time: {time_alive:.1f}s / {time_limit}s",
            f"Active Cars: {active_cars}",
            f"Best Fitness: {self.best_fitness_ever:.1f}",
            f"Population: {len(self.cars)}"
        ]
        
        for i, text in enumerate(info_texts):
            rendered_text = font.render(text, True, info_color)
            screen.blit(rendered_text, (10, 10 + i * 25))
        
        self.draw_simple_fitness_bars(screen, font)
    
    def draw_simple_fitness_bars(self, screen, font):
        if not self.genomes:
            return
        
        car_fitness_pairs = [(car, genome.fitness) for car, genome in zip(self.cars, self.genomes)]
        car_fitness_pairs.sort(key=lambda x: x[1], reverse=True)
        top_3 = car_fitness_pairs[:3]
        
        if not top_3:
            return
        
        start_x = self.screen_width - 300
        start_y = 10
        title = font.render("Top 3:", True, (255, 255, 255))
        screen.blit(title, (start_x, start_y))
        
        max_fitness = max(fitness for car, fitness in top_3) if top_3 else 1
        
        for i, (car, fitness) in enumerate(top_3):
            y_pos = start_y + 30 + (i * 30)
            bar_width = 200
            bar_height = 20
            fitness_ratio = fitness / max_fitness if max_fitness > 0 else 0
            filled_width = int(bar_width * fitness_ratio)
            
            pygame.draw.rect(screen, (50, 50, 50), (start_x, y_pos, bar_width, bar_height))
            if filled_width > 0:
                pygame.draw.rect(screen, car.color, (start_x, y_pos, filled_width, bar_height))
            
            text = font.render(f"Car {car.id}: {fitness:.1f}", True, (255, 255, 255))
            screen.blit(text, (start_x + bar_width + 10, y_pos))
    
    def start_training(self, screen, clock, font, track_image, finish_image):
        config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                           neat.DefaultSpeciesSet, neat.DefaultStagnation, self.config_file)
        population = neat.Population(config)
        population.add_reporter(neat.StdOutReporter(True))
        
        def evaluate_generation(genomes, config):
            return self.run_generation(genomes, config, screen, clock, font, track_image, finish_image)
        
        try:
            winner = population.run(evaluate_generation, 50)
            if winner:
                with open('train/best_simple_ai.pkl', 'wb') as f:
                    pickle.dump(winner, f)
            return winner
        except KeyboardInterrupt:
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None