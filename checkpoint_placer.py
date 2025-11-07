import pygame
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Checkpoint Placer - Click 12 points around the track")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Track setup
TRACK_IMAGE_FILENAME = "track1.png"
FINISH_IMAGE_FILENAME = "finish.png"

# Finish line setup
FINISH_LINE_X = 270
FINISH_LINE_Y = 200
FINISH_IMAGE_WIDTH_SCALED = 160
FINISH_IMAGE_HEIGHT_SCALED = 40

class CheckpointPlacer:
    def __init__(self):
        self.checkpoints = []
        self.max_checkpoints = 12
        self.checkpoint_radius = 50
        
        # Load track images
        try:
            self.track_image = pygame.image.load(TRACK_IMAGE_FILENAME).convert_alpha()
            self.track_image = pygame.transform.scale(self.track_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
            self.finish_image = pygame.image.load(FINISH_IMAGE_FILENAME).convert_alpha()
            self.finish_image = pygame.transform.scale(self.finish_image, (FINISH_IMAGE_WIDTH_SCALED, FINISH_IMAGE_HEIGHT_SCALED))
            
        except pygame.error as e:
            print(f"Error loading images: {e}")
            print(f"Please ensure '{TRACK_IMAGE_FILENAME}' and '{FINISH_IMAGE_FILENAME}' are in the same directory.")
            pygame.quit()
            sys.exit()
    
    def add_checkpoint(self, x, y):
        """Add a checkpoint at the given coordinates"""
        if len(self.checkpoints) < self.max_checkpoints:
            self.checkpoints.append((x, y, self.checkpoint_radius))
            print(f"Added checkpoint {len(self.checkpoints)}: ({x}, {y})")
            
            if len(self.checkpoints) == self.max_checkpoints:
                self.save_checkpoints()
                return True
        return False
    
    def remove_last_checkpoint(self):
        """Remove the last placed checkpoint"""
        if self.checkpoints:
            removed = self.checkpoints.pop()
            print(f"Removed checkpoint: {removed}")
    
    def save_checkpoints(self):
        """Save checkpoints to a Python file"""
        checkpoint_code = "# Generated checkpoints\ncheckpoints = [\n"
        for i, (x, y, radius) in enumerate(self.checkpoints):
            checkpoint_code += f"    ({x}, {y}, {radius}),   # Checkpoint {i + 1}\n"
        checkpoint_code += "]\n"
        
        with open('generated_checkpoints.py', 'w') as f:
            f.write(checkpoint_code)
        
        print("\nCheckpoints saved to 'generated_checkpoints.py'")
        print("Copy the checkpoints list to your ai_trainer.py file")
        print("\nGenerated checkpoints:")
        for i, (x, y, radius) in enumerate(self.checkpoints):
            print(f"    ({x}, {y}, {radius}),   # Checkpoint {i + 1}")
    
    def draw(self, screen):
        """Draw the track and checkpoints"""
        # Draw track
        screen.blit(self.track_image, (0, 0))
        screen.blit(self.finish_image, (FINISH_LINE_X, FINISH_LINE_Y))
        
        # Draw placed checkpoints
        for i, (x, y, radius) in enumerate(self.checkpoints):
            color = GREEN if i == 0 else YELLOW
            pygame.draw.circle(screen, color, (x, y), radius, 3)
            
            # Draw checkpoint number
            font = pygame.font.SysFont(None, 24)
            text = font.render(str(i + 1), True, WHITE)
            text_rect = text.get_rect(center=(x, y))
            screen.blit(text, text_rect)
        
        # Draw instructions
        font = pygame.font.SysFont(None, 36)
        instruction_text = f"Click to place checkpoints ({len(self.checkpoints)}/{self.max_checkpoints})"
        text_surface = font.render(instruction_text, True, WHITE)
        screen.blit(text_surface, (10, 10))
        
        if len(self.checkpoints) > 0:
            undo_text = font.render("Press U to undo last checkpoint", True, WHITE)
            screen.blit(undo_text, (10, 50))
        
        if len(self.checkpoints) == self.max_checkpoints:
            complete_text = font.render("All checkpoints placed! Check console for output.", True, GREEN)
            screen.blit(complete_text, (10, 90))
    
    def run(self):
        """Main loop for checkpoint placement"""
        clock = pygame.time.Clock()
        running = True
        
        print("Checkpoint Placer")
        print("================")
        print("Instructions:")
        print("- Click 12 points around the track in racing order")
        print("- First checkpoint should be at the start/finish line")
        print("- Press U to undo the last checkpoint")
        print("- Press ESC to exit")
        print("- Checkpoints will be saved automatically when all 12 are placed")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_u:
                        self.remove_last_checkpoint()
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        x, y = event.pos
                        completed = self.add_checkpoint(x, y)
                        if completed:
                            print("\nAll checkpoints placed! You can now close this window.")
            
            # Draw everything
            screen.fill(BLACK)
            self.draw(screen)
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    placer = CheckpointPlacer()
    placer.run()