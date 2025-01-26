import pygame
import math
import random
import numpy as np
from math import comb

# Initialize Pygame
pygame.init()

# Screen Configuration
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plinko Ball and Pegs")

# Colors
WHITE, BLACK, RED, BLUE, GREEN, GRAY = (255, 255, 255), (0, 0, 0), (255, 0, 0), (0, 0, 255), (0, 255, 0), (100, 100, 100)

# Game Variables
player_points = 1000
DEFAULT_ROWS = 10
DEFAULT_DIFFICULTY = 0.5
SPACING_X_MULTIPLIER = 1.5
FRAME_RATE = 60
SIZE_MULTI_PEG = 0.1
SIZE_MULTI_BALL = 0.15

peg_hit_sound = pygame.mixer.Sound("peg_hit.wav")
bucket_sound = pygame.mixer.Sound("bucket.wav")
# Adjust volumes
peg_hit_sound.set_volume(0.4)  # Lower volume for peg hit sound
bucket_sound.set_volume(0.8)

# Clock
clock = pygame.time.Clock()

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = GRAY

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        font = pygame.font.Font(None, 36)
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()


class Slider:
    def __init__(self, x, y, width, min_val, max_val, value, label):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min_val, self.max_val = min_val, max_val
        self.value = value
        self.label = label
        self.handle_x = x + (value - min_val) / (max_val - min_val) * width
        self.dragging = False

    def draw(self, surface):
        pygame.draw.line(surface, WHITE, (self.rect.left, self.rect.centery), (self.rect.right, self.rect.centery), 2)
        pygame.draw.circle(surface, GREEN, (int(self.handle_x), self.rect.centery), 10)
        font = pygame.font.Font(None, 24)
        label_text = font.render(f"{self.label}: {self.value:.2f}", True, WHITE)
        surface.blit(label_text, (self.rect.left, self.rect.top - 25))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(self.handle_x - 10, self.rect.centery - 10, 20, 20).collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_x = max(self.rect.left, min(self.rect.right, event.pos[0]))
            self.value = self.min_val + (self.handle_x - self.rect.left) / self.rect.width * (self.max_val - self.min_val)


class Peg:
    def __init__(self, x, y, radius):
        self.x, self.y = x, y
        self.radius = radius
        self.color = BLUE

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)


class Bucket:
    def __init__(self, position, width, multiplier=1):
        self.x, self.y = position
        self.width = width
        self.height = width
        self.multiplier = multiplier
        self.counter = 0
        self.color = GREEN
        self.num_balls = 0

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height), 2)
        self._draw_text(surface, f"{self.multiplier}x", self.y + self.height / 3)
        if self.num_balls > 0:
            self._draw_text(surface, f"{self.counter * 100 / self.num_balls: .2f}%", self.y + 2 * self.height / 3)

    def _draw_text(self, surface, text, y):
        font_size = int(self.width / 4)
        font = pygame.font.Font(None, font_size)
        text_surf = font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=(self.x + self.width / 2, y))
        surface.blit(text_surf, text_rect)

    def get_probability(self):
        if self.counter == 0:
            return 1 / (self.num_balls * 2)
        return self.counter / self.num_balls

    @staticmethod
    def calculate_multipliers(probabilities, house_edge=0.05):
        expected_return = 1 - house_edge
        multis = []
        for p in probabilities:
            multis.append(round(expected_return / (p * len(probabilities)), 2))
        
        return multis


class Ball:
    def __init__(self, x, y, peg_spacing_x):
        self.x = x + random.uniform(-peg_spacing_x / 2, peg_spacing_x / 2)
        self.y = y
        self.radius = peg_spacing_x * SIZE_MULTI_BALL
        self.color = RED
        self.vx, self.vy = 0, 0
        self.gravity = peg_spacing_x / 200
        self.dampening = 0.9

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def update(self, pegs):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        for peg in pegs:
            self._handle_peg_collision(peg)

    def _handle_peg_collision(self, peg):
        dx, dy = self.x - peg.x, self.y - peg.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance <= self.radius + peg.radius:
            angle = math.atan2(dy, dx)
            self.vx = math.cos(angle) * self.vy * self.dampening
            self.vy = math.sin(angle) * self.vy * self.dampening
            overlap = self.radius + peg.radius - distance
            self.x += math.cos(angle) * overlap * 2
            self.y += math.sin(angle) * overlap * 2
            if abs(self.vy) > 1:
                peg_hit_sound.play()  # Play peg hit sound


class Explosion:
    def __init__(self, x, y):
        self.particles = [
            [x, y, random.uniform(-2, 2), random.uniform(-2, 2), random.randint(4, 10)]
            for _ in range(20)
        ]

    def update(self):
        for particle in self.particles:
            particle[0] += particle[2]  # Update x
            particle[1] += particle[3]  # Update y
            particle[4] -= 0.2  # Decrease size
        self.particles = [p for p in self.particles if p[4] > 0]

    def draw(self, surface):
        for particle in self.particles:
            pygame.draw.circle(
                surface, RED, (int(particle[0]), int(particle[1])), int(particle[4])
            )

class MultiplierText:
    def __init__(self, text, x, y, angle, font_size=80, duration=60):
        self.text = text
        self.x = x
        self.y = y
        self.angle = angle
        self.font_size = font_size
        self.duration = duration
        self.alpha = 255  # Text opacity
        self.font = pygame.font.Font(None, self.font_size)

    def update(self):
        self.duration -= 1
        self.alpha = max(0, self.alpha - 255 // 60)  # Fade out over 60 frames

    def draw(self, surface):
        if self.alpha > 0:
            text_surf = self.font.render(self.text, True, WHITE)
            text_surf.set_alpha(self.alpha)
            text_surf = pygame.transform.rotate(text_surf, self.angle)
            text_rect = text_surf.get_rect(center=(self.x, self.y))
            surface.blit(text_surf, text_rect)

    def is_expired(self):
        return self.duration <= 0

class Game:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.rows = DEFAULT_ROWS
        self.pegs, self.peg_spacing_x = self._generate_pegs()
        self.buckets = self._generate_buckets()
        self.balls = []
        self.explosions = []
        self.multiplier_texts = []
        self.bet_slider = Slider(50, 70, 200, 10, 100, 10, "Bet Size")
        self.rows_slider = Slider(300, 70, 200, 5, 20, self.rows, "Rows")
        self.drop_ball_button = Button(800, 70, 150, 50, "Drop Ball", self.drop_ball)
        self.simulate_button = Button(1000, 70, 200, 50, "Simulate Board", self.start_simulation)
        self.simulating = False
        self.simulation_count = 0
        self.simulation_limit = 1000
        self.simulation_timer = 0

    def start_simulation(self):
        self.simulating = True
        self.simulation_count = 0
        # self.bet_slider.value = 0
        self.simulation_timer = 0
        for bucket in self.buckets:
            bucket.num_balls = 0
            bucket.counter = 0

    def simulate_ball_drop(self):
        global player_points
        if self.simulation_count < self.simulation_limit and self.simulation_timer % 10 == 0:
            self.balls.append(Ball(SCREEN_WIDTH // 2, 130, self.peg_spacing_x))
            player_points -= self.bet_slider.value
            for bucket in self.buckets:
                bucket.num_balls += 1
            self.simulation_count += 1
        elif not self.balls:
            self.simulating = False  # Stop simulation after reaching the limi
        self.simulation_timer += 1

    def handle_events(self):
        if self.simulating:
            return True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if not self.balls:
                self.bet_slider.handle_event(event)
                self.rows_slider.handle_event(event)
            self.drop_ball_button.handle_event(event)
            self.simulate_button.handle_event(event)
        return True

    def update(self):
        if not self.balls:
            self.rows = int(self.rows_slider.value)
            if abs(self.rows - self.rows_slider.value) > .5:
                self.pegs, self.peg_spacing_x = self._generate_pegs()
                self.buckets = self._generate_buckets()

        if self.simulating:
            self.simulate_ball_drop()

        for ball in self.balls[:]:
            ball.update(self.pegs)
            if self._check_ball_in_buckets(ball) or ball.y > SCREEN_HEIGHT:
                self.balls.remove(ball)

        for explosion in self.explosions[:]:
            explosion.update()
            if not explosion.particles:
                self.explosions.remove(explosion)

        for text in self.multiplier_texts[:]:
            text.update()
            if text.is_expired():
                self.multiplier_texts.remove(text)

    def draw(self):
        screen.fill(BLACK)
        for peg in self.pegs:
            peg.draw(screen)
        for bucket in self.buckets:
            bucket.draw(screen)
        for ball in self.balls:
            ball.draw(screen)
        for explosion in self.explosions:
            explosion.draw(screen)
        for text in self.multiplier_texts:
            text.draw(screen)
        points_text = self.font.render(f"Points: {player_points: .2f}", True, WHITE)
        screen.blit(points_text, (10, 10))
        self.bet_slider.draw(screen)
        self.rows_slider.draw(screen)
        self.drop_ball_button.draw(screen)
        self.simulate_button.draw(screen)
        pygame.display.flip()

    def _generate_pegs(self):
        y_offset = 200
        peg_spacing_y = (SCREEN_HEIGHT - y_offset) // (self.rows + 1)
        peg_spacing_x = peg_spacing_y * SPACING_X_MULTIPLIER
        peg_radius = peg_spacing_x * SIZE_MULTI_PEG

        # Adjust the columns to match the number of rows for a square layout
        cols = self.rows
        pegs = [
            Peg(
                (col + 0.5 * (row % 2)) * peg_spacing_x + (SCREEN_WIDTH - cols * peg_spacing_x) // 2,
                peg_spacing_y * row + y_offset,
                peg_radius
            )
            for row in range(self.rows)
            for col in range(cols)
        ]
        return pegs, peg_spacing_x


    def _generate_buckets(self):
        last_row_y = max(peg.y for peg in self.pegs)
        bucket_width = (SCREEN_HEIGHT - 200) // (self.rows + 1) * SPACING_X_MULTIPLIER
        odd_offset = (self.rows % 2 == 0) * bucket_width / 2
        bucket_positions = [
            (SCREEN_WIDTH // 2 + (i - self.rows / 2) * bucket_width - odd_offset, last_row_y + bucket_width // 5)
            for i in range(self.rows + 1)
        ]
        return [Bucket(pos, bucket_width) for pos in bucket_positions]

    def drop_ball(self):
        global player_points
        bet_size = int(self.bet_slider.value)
        for bucket in self.buckets:
            bucket.num_balls += 1
        if player_points >= bet_size:
            self.balls.append(Ball(SCREEN_WIDTH // 2, 130, self.peg_spacing_x))
            player_points -= bet_size

    def _check_ball_in_buckets(self, ball):
        global player_points
        for bucket in self.buckets:
            if bucket.x <= ball.x <= bucket.x + bucket.width and bucket.y <= ball.y <= bucket.y + bucket.height:
                winnings = round(bucket.multiplier * int(self.bet_slider.value), 2)
                player_points += winnings
                bucket.counter += 1
                bucket_sound.play()  # Play bucket sound
                self.explosions.append(Explosion(ball.x, ball.y))  # Create explosion

                # Add a new multiplier text
                angle = random.randint(-45, 45)  # Random angle
                x = random.randint(100, SCREEN_WIDTH - 100)
                y = random.randint(100, SCREEN_HEIGHT - 100)
                self.multiplier_texts.append(MultiplierText(f"{bucket.multiplier}x", x, y, angle))

                multipliers = Bucket.calculate_multipliers([bucket.get_probability() for bucket in self.buckets])
                for multi, bucket in zip(multipliers, self.buckets):
                    bucket.multiplier = multi
                return True
        return False

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            clock.tick(FRAME_RATE)


if __name__ == "__main__":
    Game().run()
