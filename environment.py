import pygame
import math

# Constants (these should match main.py)
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WHITE = (255, 255, 255)
BLACK = (0, 0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# These will be set by main.py
WALL_MASK = None
FINISH_LINE_RECT = None

# --- Car Class ---
class Car(pygame.sprite.Sprite):
    def __init__(self, car_id, x, y, angle=0.0, color=BLUE): # Added car_id and color param
        super().__init__()
        self.id = car_id # Identify the car
        self.width = 40
        self.height = 20
        self.color = color
        self.original_image = pygame.Surface([self.width, self.height], pygame.SRCALPHA)
        self.original_image.fill(self.color)
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image) # Mask for car itself (wall collisions)

        self.start_pos = pygame.math.Vector2(x, y) # Store start position for reset
        self.start_angle = angle

        self.position = pygame.math.Vector2(x, y)
        self.angle = angle
        self.speed = 0
        self.rotation_speed = 3
        self.acceleration = 0.5
        self.max_speed = 30
        self.friction = 0.05

        self.crashed = False # Indicates if currently touching a wall
        self.laps_completed = 0
        self.was_on_finish_line = False # To detect crossing edge
        
        # Checkpoint tracking
        self.current_checkpoint = 0  # Next checkpoint to reach
        self.checkpoints_reached = 0  # Total checkpoints reached
        self.checkpoint_times = []  # Time when each checkpoint was reached
        self.last_checkpoint_time = 0
        self.checkpoints_this_lap = 0  # Checkpoints reached in current lap
        self.completed_checkpoints_this_lap = set()  # Track which checkpoints completed this lap

        self.num_sensors = 9
        self.sensor_range = 600
        self.sensor_angles = [-60, -45, -30, -15, 0, 15, 30, 45, 60]
        self.sensor_readings = [self.sensor_range] * self.num_sensors
        self.sensor_end_points = [(0,0)] * self.num_sensors

        self.update_sensors() # Initial sensor update

    # Takes AI action instead of keys
    def update(self, action):
        accelerate, brake, steer = action # Unpack the action tuple

        # 1. Process Speed Input (Acceleration/Deceleration/Friction)
        if accelerate:
            self.speed = min(self.speed + self.acceleration, self.max_speed)
        if brake:
             if self.speed > 0 :
                 self.speed = max(self.speed - self.acceleration * 2, 0)
             else:
                  self.speed = max(self.speed - self.acceleration * 0.5, -self.max_speed / 2)

        if not accelerate and not brake:
            if self.speed > self.friction:
                self.speed -= self.friction
            elif self.speed < -self.friction:
                self.speed += self.friction
            else:
                self.speed = 0

        # 2. Process Rotation Input
        if steer == -1:
            self.angle += self.rotation_speed
        elif steer == 1:
            self.angle -= self.rotation_speed
        self.angle %= 360

        # 3. Calculate Potential Movement
        velocity_x = math.cos(math.radians(self.angle)) * self.speed
        velocity_y = -math.sin(math.radians(self.angle)) * self.speed
        potential_new_position = self.position + pygame.math.Vector2(velocity_x, velocity_y)

        # 4. Prepare for Collision Check
        rotated_image = pygame.transform.rotate(self.original_image, self.angle)
        potential_rect = rotated_image.get_rect(center=potential_new_position)
        potential_mask = pygame.mask.from_surface(rotated_image)

        # 5. Perform Wall Collision Detection
        is_colliding_at_potential_pos = False
        offset_x = potential_rect.left
        offset_y = potential_rect.top

        if not (0 <= potential_rect.left and potential_rect.right < SCREEN_WIDTH and \
                0 <= potential_rect.top and potential_rect.bottom < SCREEN_HEIGHT):
            is_colliding_at_potential_pos = True
        else:
            if WALL_MASK.overlap(potential_mask, (offset_x, offset_y)):
                is_colliding_at_potential_pos = True

        # 6. Collision Response and Finalizing State
        if is_colliding_at_potential_pos:
            self.crashed = True
            self.speed = 0
            self.image = rotated_image
            self.rect = self.image.get_rect(center=self.position)
            self.mask = pygame.mask.from_surface(self.image)
        else:
            self.crashed = False
            self.position = potential_new_position
            self.image = rotated_image
            self.rect = potential_rect
            self.mask = potential_mask

        self.update_sensors()
        self.check_finish_line()
        self.check_checkpoints()


    def update_sensors(self):
        self.sensor_readings = []
        self.sensor_end_points = []
        sensor_start_offset = self.width * 0.4
        base_x = self.rect.centerx + math.cos(math.radians(self.angle)) * sensor_start_offset
        base_y = self.rect.centery - math.sin(math.radians(self.angle)) * sensor_start_offset

        for i in range(self.num_sensors):
            sensor_angle_rad = math.radians(self.angle + self.sensor_angles[i])
            current_sensor_distance = self.sensor_range
            hit_point = None
            for d_step in range(1, int(self.sensor_range) + 1):
                check_x = int(base_x + math.cos(sensor_angle_rad) * d_step)
                check_y = int(base_y - math.sin(sensor_angle_rad) * d_step)
                if not (0 <= check_x < SCREEN_WIDTH and 0 <= check_y < SCREEN_HEIGHT):
                    current_sensor_distance = d_step
                    hit_point = (check_x, check_y)
                    break
                try:
                     if WALL_MASK.get_at((check_x, check_y)):
                        current_sensor_distance = d_step
                        hit_point = (check_x, check_y)
                        break
                except IndexError:
                     current_sensor_distance = d_step
                     hit_point = (check_x, check_y)
                     break
            self.sensor_readings.append(current_sensor_distance)
            if hit_point:
                end_x, end_y = hit_point
            else:
                end_x = base_x + math.cos(sensor_angle_rad) * self.sensor_range
                end_y = base_y - math.sin(sensor_angle_rad) * self.sensor_range
            self.sensor_end_points.append(((base_x, base_y), (end_x, end_y)))

    def check_finish_line(self):
        # Check for collision with the defined FINISH_LINE_RECT
        is_currently_on_finish = self.rect.colliderect(FINISH_LINE_RECT)

        if is_currently_on_finish and not self.was_on_finish_line:
            # Only allow lap completion if all checkpoints have been reached
            if hasattr(self, 'checkpoints') and self.current_checkpoint == 0 and self.checkpoints_this_lap >= len(self.checkpoints):
                self.laps_completed += 1
                self.checkpoints_this_lap = 0  # Reset for next lap
                self.completed_checkpoints_this_lap.clear()  # Clear completed checkpoints for new lap
                print(f"Car {self.id} completed lap {self.laps_completed}! (All checkpoints reached)")
            elif not hasattr(self, 'checkpoints'):
                # Fallback for cars without checkpoints
                self.laps_completed += 1
                print(f"Car {self.id} completed lap {self.laps_completed}!")
            else:
                # Car reached finish line but hasn't completed all checkpoints
                checkpoints_needed = len(self.checkpoints) if hasattr(self, 'checkpoints') else 0
                print(f"Car {self.id} reached finish line but needs to complete all {checkpoints_needed} checkpoints first! (Completed this lap: {self.checkpoints_this_lap})")

        self.was_on_finish_line = is_currently_on_finish
    
    def check_checkpoints(self):
        """Check if car has reached the next checkpoint"""
        if not hasattr(self, 'checkpoints') or not self.checkpoints:
            return
        
        # Check all checkpoints to see if car is within any of them
        for checkpoint_index, (checkpoint_x, checkpoint_y, checkpoint_radius) in enumerate(self.checkpoints):
            # Calculate distance to this checkpoint
            distance = math.sqrt(
                (self.position.x - checkpoint_x) ** 2 + 
                (self.position.y - checkpoint_y) ** 2
            )
            
            # Check if car is within checkpoint radius
            if distance <= checkpoint_radius:
                # Only reward if this is the next expected checkpoint and hasn't been completed this lap
                if (checkpoint_index == self.current_checkpoint and 
                    checkpoint_index not in self.completed_checkpoints_this_lap):
                    
                    current_time = pygame.time.get_ticks() / 1000.0
                    self.checkpoint_times.append(current_time)
                    self.checkpoints_reached += 1
                    self.checkpoints_this_lap += 1
                    self.completed_checkpoints_this_lap.add(checkpoint_index)
                    
                    print(f"Car {self.id} reached checkpoint {checkpoint_index + 1} ({self.checkpoints_this_lap}/{len(self.checkpoints)} this lap)")
                    
                    # Move to next checkpoint
                    self.current_checkpoint += 1
                    
                    # If all checkpoints reached, reset for next lap
                    if self.current_checkpoint >= len(self.checkpoints):
                        self.current_checkpoint = 0
                        print(f"Car {self.id} completed all checkpoints! Can now finish lap.")
                    
                    break  # Only process one checkpoint per update
                
                elif checkpoint_index in self.completed_checkpoints_this_lap:
                    # Car is revisiting a checkpoint - no reward
                    pass
    
    def set_checkpoints(self, checkpoints):
        """Set the checkpoints for this car"""
        self.checkpoints = checkpoints
    
    def update_color(self, new_color):
        """Update the car's color and regenerate the image"""
        self.color = new_color
        self.original_image.fill(self.color)
        # Update the current rotated image
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.position)
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def draw_debug(self, surface, font):
         lap_text = f"Car {self.id} Laps: {self.laps_completed}"
         text_surface = font.render(lap_text, True, self.color)
         text_rect = text_surface.get_rect(topleft=(10, 10 + (self.id -1) * 20))
         surface.blit(text_surface, text_rect)
         if self.crashed :
             for i, line_points in enumerate(self.sensor_end_points):
                 start_pos, end_pos = line_points
                 color = RED if self.sensor_readings[i] < self.sensor_range else GREEN
                 pygame.draw.line(surface, color, start_pos, end_pos, 1)
                 if self.sensor_readings[i] < self.sensor_range:
                     pygame.draw.circle(surface, RED, (int(end_pos[0]), int(end_pos[1])), 3)

    def reset(self):
        self.position = pygame.math.Vector2(self.start_pos.x, self.start_pos.y)
        self.angle = self.start_angle
        self.speed = 0
        self.crashed = False
        self.laps_completed = 0
        self.was_on_finish_line = False
        
        # Reset checkpoint tracking
        self.current_checkpoint = 0
        self.checkpoints_reached = 0
        self.checkpoint_times = []
        self.last_checkpoint_time = 0
        self.checkpoints_this_lap = 0
        self.completed_checkpoints_this_lap = set()
        
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.position)
        self.mask = pygame.mask.from_surface(self.image)
        self.update_sensors()
