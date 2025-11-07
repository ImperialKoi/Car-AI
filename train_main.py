import pygame
import sys

from simple_ai_trainer import SimpleAITrainer

def initialize_pygame():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Simple AI Racing Car Training")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    return screen, clock, font

def load_track_images():
    track_image = pygame.image.load("./track1.png").convert_alpha()
    track_image = pygame.transform.scale(track_image, (1280, 720))
    finish_image = pygame.image.load("./finish.png").convert_alpha()
    finish_image = pygame.transform.scale(finish_image, (160, 40))
    return track_image, finish_image

def setup_environment():
    import environment
    
    track_image = pygame.image.load("./track1.png").convert_alpha()
    track_image = pygame.transform.scale(track_image, (1280, 720))
    
    wall_mask_surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    wall_mask_surface.fill((0, 0, 0, 0))
    
    BLACK = (0, 0, 0, 255)
    WHITE = (255, 255, 255)
    
    for x in range(1280):
        for y in range(720):
            pixel_color = track_image.get_at((x, y))
            if (pixel_color[0] == BLACK[0] and 
                pixel_color[1] == BLACK[1] and 
                pixel_color[2] == BLACK[2]):
                wall_mask_surface.set_at((x, y), WHITE)
    
    wall_mask = pygame.mask.from_surface(wall_mask_surface)
    finish_rect = pygame.Rect(270, 200, 160, 40)
    
    environment.WALL_MASK = wall_mask
    environment.FINISH_LINE_RECT = finish_rect
    
    return True

def main():
    screen, clock, font = initialize_pygame()
    track_image, finish_image = load_track_images()
    setup_environment()
    
    trainer = SimpleAITrainer()
    trainer.start_training(screen, clock, font, track_image, finish_image)
    
    pygame.quit()

if __name__ == "__main__":
    main()