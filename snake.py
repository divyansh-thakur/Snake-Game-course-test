import pygame
import pygame.gfxdraw
import random
import sys
import math
import array
import os

# Configure SDL for high quality and native windows
os.environ["SDL_VIDEO_DOUBLEBUFFER"] = "1"

# Initialize Pygame & Mixer
pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except Exception:
    pass

# --- Window & Supersampling Configuration ---
# The game renders at 2x resolution (1200x1320) and is downscaled to 600x660 using smoothscale
# for ultra-sharp, anti-aliased, non-pixelated graphics.
GRID_SIZE = 20
COLS = 30
ROWS = 30
HEADER_HEIGHT = 60
WINDOW_WIDTH = COLS * GRID_SIZE
WINDOW_HEIGHT = ROWS * GRID_SIZE + HEADER_HEIGHT

V_SCALE = 2 # Supersampling factor
V_WIDTH = WINDOW_WIDTH * V_SCALE
V_HEIGHT = WINDOW_HEIGHT * V_SCALE
V_GRID_SIZE = GRID_SIZE * V_SCALE
V_HEADER_HEIGHT = HEADER_HEIGHT * V_SCALE

# Set up native desktop window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE)
pygame.display.set_caption("⚡ NEON SNAKE: CYBERPUNK EDITION ⚡")
clock = pygame.time.Clock()

# --- Synth Audio Generator ---
def play_synth_sound(frequency, duration_ms, wave_type='sine', volume=0.15):
    try:
        if not pygame.mixer.get_init():
            return
        
        sample_rate = 22050
        num_samples = int(sample_rate * (duration_ms / 1000.0))
        amplitude = 8000
        data = array.array('h')
        
        if wave_type == 'square':
            period = sample_rate / frequency
            for i in range(num_samples):
                val = amplitude if (i % period) < (period / 2) else -amplitude
                data.append(val)
        elif wave_type == 'sine':
            for i in range(num_samples):
                val = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
                data.append(val)
        elif wave_type == 'saw':
            period = sample_rate / frequency
            for i in range(num_samples):
                val = int(amplitude * (2.0 * (i % period) / period - 1.0))
                data.append(val)
        elif wave_type == 'noise':
            for i in range(num_samples):
                val = random.randint(-amplitude, amplitude)
                data.append(val)
                
        sound = pygame.mixer.Sound(buffer=data)
        sound.set_volume(volume)
        sound.play()
    except Exception:
        pass

# --- Color Scheme ---
BG_COLOR = (8, 5, 16)             # Deep space violet
GRID_LINE_COLOR = (0, 240, 255)   # Neon Cyan
SNAKE_COLOR = (0, 255, 136)       # Electric Green
SNAKE_HEAD_COLOR = (0, 255, 200)  # Bright Turquoise
FOOD_COLOR = (255, 0, 127)        # Hot Pink
TEXT_COLOR = (240, 240, 255)      # Ice White
OBSTACLE_COLOR = (255, 94, 0)     # Industrial Orange

# Power-up Colors
COLOR_SHIELD = (0, 240, 255)      # Cyan
COLOR_SPEED = (255, 230, 0)       # Gold
COLOR_SLOW = (189, 0, 255)        # Purple
COLOR_SHRINK = (0, 255, 136)      # Green
COLOR_LASER = (255, 94, 0)        # Orange
COLOR_REWIND = (255, 0, 127)      # Magenta

# --- Map Layouts ---
MAP_OPEN = 0
MAP_PILLARS = 1
MAP_CROSS = 2
MAP_MAZE = 3
selected_map = MAP_OPEN
obstacles = []

def build_map(layout_type):
    global obstacles
    obstacles = []
    if layout_type == MAP_PILLARS:
        # 4 corner columns
        def add_pillar(sx, sy):
            for x in range(sx, sx + 2):
                for y in range(sy, sy + 2):
                    obstacles.append((x, y))
        add_pillar(5, 5)
        add_pillar(23, 5)
        add_pillar(5, 23)
        add_pillar(23, 23)
    elif layout_type == MAP_CROSS:
        # Cross partition in middle
        for x in range(8, 22):
            obstacles.append((x, 15))
        for y in range(8, 22):
            if y != 15:
                obstacles.append((15, y))
    elif layout_type == MAP_MAZE:
        # Outer-inner labyrinth
        for x in range(5, 25):
            if x not in [14, 15, 16]:
                obstacles.append((x, 7))
                obstacles.append((x, 22))
        for y in range(10, 20):
            obstacles.append((7, y))
            obstacles.append((22, y))

# --- Game States ---
STATE_START = 0
STATE_PLAY = 1
STATE_GAMEOVER = 2
STATE_REWIND_PROMPT = 3
STATE_REWINDING = 4

# --- Visual Effects Utilities ---
def draw_glow_rect(surface, color, rect, glow_size, alpha=40, border_radius=4):
    for i in range(glow_size, 0, -3):
        ratio = i / glow_size
        a = int(alpha * (1.0 - ratio))
        g_rect = pygame.Rect(rect.x - i, rect.y - i, rect.width + i * 2, rect.height + i * 2)
        glow_surf = pygame.Surface((g_rect.width, g_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*color, a), (0, 0, g_rect.width, g_rect.height), border_radius=border_radius + i)
        surface.blit(glow_surf, (g_rect.x, g_rect.y))

def draw_glow_circle(surface, color, center, radius, glow_radius, alpha=50):
    for r in range(radius + glow_radius, radius, -3):
        ratio = (r - radius) / glow_radius
        a = int(alpha * (1.0 - ratio))
        glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, a), (r, r), r)
        surface.blit(glow_surf, (center[0] - r, center[1] - r))

def render_glowing_text(text, font, color, glow_color, glow_size=4):
    text_surf = font.render(text, True, color)
    w, h = text_surf.get_width(), text_surf.get_height()
    surf = pygame.Surface((w + glow_size * 2, h + glow_size * 2), pygame.SRCALPHA)
    
    glow_text = font.render(text, True, glow_color)
    for dx in range(-glow_size, glow_size + 1, 2):
        for dy in range(-glow_size, glow_size + 1, 2):
            if dx*dx + dy*dy <= glow_size*glow_size:
                dist = math.sqrt(dx*dx + dy*dy)
                alpha = int(120 * (1.0 - dist / (glow_size + 1)))
                glow_text.set_alpha(alpha)
                surf.blit(glow_text, (dx + glow_size, dy + glow_size))
                
    surf.blit(text_surf, (glow_size, glow_size))
    return surf

# --- Particle Physics System ---
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2.5, 7.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.alpha = 255.0
        self.size = random.uniform(5.0, 10.0)
        self.decay = random.uniform(6.0, 12.0)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
        self.alpha = max(0.0, self.alpha - self.decay)
        self.size = max(0.5, self.size - 0.15)

    def draw(self, surface):
        if self.alpha > 0 and self.size > 0.5:
            s = int(self.size * 2) + 2
            p_surf = pygame.Surface((s, s), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*self.color, int(self.alpha)), (s // 2, s // 2), int(self.size))
            surface.blit(p_surf, (int(self.x - s // 2), int(self.y - s // 2)))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_explosion(self, x, y, color, count=25):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def spawn_trail(self, x, y, color):
        p = Particle(x, y, color)
        p.vx = random.uniform(-0.5, 0.5)
        p.vy = random.uniform(-0.5, 0.5)
        p.size = random.uniform(2.5, 6.0)
        p.decay = random.uniform(15.0, 25.0)
        self.particles.append(p)

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alpha > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

class FloatingText:
    def __init__(self, text, x, y, color):
        self.text = text
        self.x = x
        self.y = y
        self.vy = -2.4
        self.alpha = 255.0
        self.color = color

    def update(self):
        self.y += self.vy
        self.alpha = max(0.0, self.alpha - 8.0)

    def draw(self, surface, font):
        if self.alpha > 0:
            text_surf = font.render(self.text, True, self.color)
            alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((255, 255, 255, int(self.alpha)))
            text_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(text_surf, (int(self.x - text_surf.get_width() / 2), int(self.y)))

class ScreenShake:
    def __init__(self):
        self.duration = 0
        self.intensity = 0

    def trigger(self, duration, intensity):
        self.duration = duration
        self.intensity = intensity

    def update(self):
        if self.duration > 0:
            self.duration -= 1
        else:
            self.intensity = 0

    def get_offset(self):
        if self.duration > 0:
            dx = random.randint(-self.intensity, self.intensity)
            dy = random.randint(-self.intensity, self.intensity)
            return dx, dy
        return 0, 0

# --- Laser Beam visual effect ---
class LaserBeam:
    def __init__(self, start_px, end_px, direction_vec):
        self.start = start_px
        self.end = end_px
        self.dir = direction_vec
        self.duration = 15 # frames to show
        self.max_duration = 15

    def update(self):
        self.duration = max(0, self.duration - 1)

    def draw(self, surface):
        if self.duration > 0:
            # Laser fades out over time
            alpha = int(255 * (self.duration / self.max_duration))
            # Dynamic thickness pulse
            width = int(6 + 8 * math.sin(self.duration * 0.4))
            
            # Draw outer glow
            glow_surf = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(glow_surf, (255, 94, 0, int(alpha * 0.4)), self.start, self.end, width * 2)
            pygame.draw.line(glow_surf, (255, 230, 0, alpha), self.start, self.end, width)
            pygame.draw.line(glow_surf, (255, 255, 255, alpha), self.start, self.end, width // 2)
            surface.blit(glow_surf, (0, 0))

# --- Snake Entity ---
class Snake:
    def __init__(self):
        self.body = [(15, 15), (15, 16), (15, 17)]
        self.prev_body = list(self.body)
        self.direction = (0, -1)
        self.direction_queue = []
        self.was_popped = False
        self.popped_tail_pos = None

    def change_direction(self, new_dir):
        last_dir = self.direction_queue[-1] if self.direction_queue else self.direction
        if (new_dir[0] * -1, new_dir[1] * -1) != last_dir:
            self.direction_queue.append(new_dir)

    def move(self, is_eating):
        if self.direction_queue:
            self.direction = self.direction_queue.pop(0)

        head = self.body[0]
        dx, dy = self.direction
        new_head = (head[0] + dx, head[1] + dy)
        
        self.prev_body = list(self.body)
        self.body.insert(0, new_head)
        
        if not is_eating:
            self.was_popped = True
            self.popped_tail_pos = self.body[-1]
            self.body.pop()
        else:
            self.was_popped = False
            self.popped_tail_pos = None

    def check_collision(self, active_shield):
        head = self.body[0]
        if active_shield:
            return False # Shield protects against everything
        # Wall collision
        if head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS:
            return True
        # Obstacle collision
        if head in obstacles:
            return True
        # Self collision
        if head in self.body[1:]:
            return True
        return False

    def draw(self, surface, interpolation_factor, active_powers, time_ticks):
        t = interpolation_factor
        n_prev = len(self.prev_body)
        n_curr = len(self.body)

        # Determine skin color
        color_theme = SNAKE_COLOR
        glow_theme = (0, 255, 136)
        if active_powers.get('SHIELD', 0) > 0:
            color_theme = COLOR_SHIELD
            glow_theme = COLOR_SHIELD
        elif active_powers.get('SPEED', 0) > 0:
            color_theme = COLOR_SPEED
            glow_theme = COLOR_SPEED

        # 1. Draw shrinking popped tail segment
        if self.was_popped and self.popped_tail_pos:
            px = self.popped_tail_pos[0] * V_GRID_SIZE
            py = self.popped_tail_pos[1] * V_GRID_SIZE + V_HEADER_HEIGHT
            size = V_GRID_SIZE * (1.0 - t)
            offset = (V_GRID_SIZE - size) / 2
            rect = pygame.Rect(px + offset, py + offset, size, size)
            if size > 1:
                pygame.draw.rect(surface, color_theme, rect, border_radius=int(12 * (1.0 - t)))

        # 2. Draw active segments
        for i in range(n_curr):
            if i < n_prev:
                p_pos = self.prev_body[i]
                c_pos = self.body[i]
            else:
                p_pos = self.prev_body[-1]
                c_pos = self.body[i]

            ix = p_pos[0] + (c_pos[0] - p_pos[0]) * t
            iy = p_pos[1] + (c_pos[1] - p_pos[1]) * t

            px = ix * V_GRID_SIZE
            py = iy * V_GRID_SIZE + V_HEADER_HEIGHT

            # Tapering body size
            base_size_mult = 1.0
            if n_curr > 1 and i > 0:
                base_size_mult = 1.0 - 0.35 * (i / (n_curr - 1))
            
            size = V_GRID_SIZE * base_size_mult * 1.04
            offset = (V_GRID_SIZE - size) / 2
            rect = pygame.Rect(px + offset, py + offset, size, size)

            # Draw Glow
            if i == 0:
                draw_glow_rect(surface, glow_theme, rect, glow_size=18, alpha=70, border_radius=12)
            else:
                draw_glow_rect(surface, glow_theme, rect, glow_size=8, alpha=25, border_radius=8)

            # Draw body block
            pygame.draw.rect(surface, color_theme, rect, border_radius=int(12 * base_size_mult))

            # Draw Head Details (Eyes & Shield bubble)
            if i == 0:
                # Shield bubble glow surrounding head
                if active_powers.get('SHIELD', 0) > 0:
                    bubble_radius = int(V_GRID_SIZE * 0.95)
                    bubble_pulse = int(5 * math.sin(time_ticks * 0.02))
                    bubble_surf = pygame.Surface((bubble_radius * 2 + 10, bubble_radius * 2 + 10), pygame.SRCALPHA)
                    pygame.draw.circle(bubble_surf, (*COLOR_SHIELD, 60 + bubble_pulse * 4), (bubble_radius + 5, bubble_radius + 5), bubble_radius + bubble_pulse // 2, 4)
                    surface.blit(bubble_surf, (px + V_GRID_SIZE//2 - bubble_radius - 5, py + V_GRID_SIZE//2 - bubble_radius - 5))

                dx, dy = self.direction
                eye_size = max(3.0, size * 0.2)
                eye_offset = size * 0.22
                
                if dx == 1: # Right
                    eyes = [(px + size - eye_offset, py + eye_offset), (px + size - eye_offset, py + size - eye_offset)]
                elif dx == -1: # Left
                    eyes = [(px + eye_offset, py + eye_offset), (px + eye_offset, py + size - eye_offset)]
                elif dy == 1: # Down
                    eyes = [(px + eye_offset, py + size - eye_offset), (px + size - eye_offset, py + size - eye_offset)]
                else: # Up
                    eyes = [(px + eye_offset, py + eye_offset), (px + size - eye_offset, py + eye_offset)]

                for eye in eyes:
                    pygame.draw.circle(surface, (255, 255, 255), (int(eye[0]), int(eye[1])), int(eye_size))
                    pygame.draw.circle(surface, (8, 5, 16), (int(eye[0] + dx * 1.5), int(eye[1] + dy * 1.5)), int(eye_size * 0.5))

# --- Food Capsule Entity ---
class Food:
    def __init__(self, snake_body):
        self.position = self.randomize_position(snake_body)

    def randomize_position(self, snake_body):
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in snake_body and pos not in obstacles:
                return pos

    def draw(self, surface, time_ticks):
        # Pulsate size
        scale = 1.0 + 0.12 * math.sin(time_ticks * 0.008)
        size = V_GRID_SIZE * scale
        
        cx = self.position[0] * V_GRID_SIZE + V_GRID_SIZE // 2
        cy = self.position[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE // 2
        
        draw_glow_circle(surface, FOOD_COLOR, (cx, cy), int(size // 2), glow_radius=20, alpha=80)
        pygame.draw.circle(surface, FOOD_COLOR, (cx, cy), int(size // 2 - 2))
        pygame.draw.circle(surface, (255, 255, 255), (int(cx - size * 0.14), int(cy - size * 0.14)), int(size * 0.1))

# --- Power-Up Capsule Entity ---
class PowerUp:
    TYPE_SHIELD = 0
    TYPE_SPEED = 1
    TYPE_SLOW = 2
    TYPE_SHRINK = 3
    TYPE_LASER = 4
    TYPE_REWIND = 5

    def __init__(self, snake_body, food_pos):
        # Spawns dynamically
        self.type = random.choice([self.TYPE_SHIELD, self.TYPE_SPEED, self.TYPE_SLOW, self.TYPE_SHRINK, self.TYPE_LASER, self.TYPE_REWIND])
        self.position = self.randomize_position(snake_body, food_pos)
        self.time_left = 10.0 # disappearing countdown

    def randomize_position(self, snake_body, food_pos):
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in snake_body and pos not in obstacles and pos != food_pos:
                return pos

    def draw(self, surface, time_ticks):
        px = self.position[0] * V_GRID_SIZE + V_GRID_SIZE // 2
        py = self.position[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE // 2
        
        scale = 1.0 + 0.15 * math.sin(time_ticks * 0.015)
        size = V_GRID_SIZE * scale
        
        # Color mapping
        color = COLOR_SHIELD
        label = "SH"
        if self.type == self.TYPE_SPEED: color = COLOR_SPEED; label = "SP"
        elif self.type == self.TYPE_SLOW: color = COLOR_SLOW; label = "SL"
        elif self.type == self.TYPE_SHRINK: color = COLOR_SHRINK; label = "SC" # Scissors
        elif self.type == self.TYPE_LASER: color = COLOR_LASER; label = "LA"
        elif self.type == self.TYPE_REWIND: color = COLOR_REWIND; label = "RE"

        draw_glow_circle(surface, color, (px, py), int(size // 2), glow_radius=18, alpha=80)
        
        # Draw circular frame
        pygame.draw.circle(surface, color, (px, py), int(size // 2), 3)
        
        # Text symbol label
        font = pygame.font.SysFont("Helvetica", int(size * 0.45), bold=True)
        lbl_surf = font.render(label, True, TEXT_COLOR)
        surface.blit(lbl_surf, (px - lbl_surf.get_width() // 2, py - lbl_surf.get_height() // 2))

# --- AI Script for Start Screensaver ---
def get_ai_direction(snake, food, powerup):
    head = snake.body[0]
    target = powerup.position if powerup else food.position
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    
    def dist(d):
        np = (head[0] + d[0], head[1] + d[1])
        return abs(np[0] - target[0]) + abs(np[1] - target[1])
        
    directions.sort(key=dist)
    
    for d in directions:
        if (d[0] * -1, d[1] * -1) == snake.direction:
            continue
        
        np = (head[0] + d[0], head[1] + d[1])
        if np[0] < 0 or np[0] >= COLS or np[1] < 0 or np[1] >= ROWS:
            continue
        if np in obstacles:
            continue
        if np in snake.body:
            continue
        return d
        
    for d in directions:
        if (d[0] * -1, d[1] * -1) != snake.direction:
            return d
            
    return snake.direction

# --- Background Drawing Helpers ---
def draw_retro_sun(surface, time_ticks):
    cx = V_WIDTH // 2
    cy = V_HEIGHT // 2 - 80
    r = 180
    
    # Clip sun circle
    sun_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(sun_surf, (255, 0, 127), (r, r), r)
    # Sun gradient shade
    for y_offset in range(r * 2):
        factor = y_offset / (r * 2)
        color = (
            int(255 * (1.0 - factor)),
            int(150 * factor),
            int(127 + 128 * factor)
        )
        # Slices slits out of sun
        if (y_offset // 10) % 2 == 1:
            continue
        pygame.draw.line(sun_surf, color, (0, y_offset), (r * 2, y_offset))
        
    # Mask with circular sun
    mask = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255), (r, r), r)
    sun_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(sun_surf, (cx - r, cy - r))

def draw_perspective_grid(surface, time_ticks):
    grid_surf = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
    color = (0, 240, 255, 16)
    
    horizon_y = V_HEIGHT // 2 + 100
    cx = V_WIDTH // 2
    
    # Diagonal lines radiating from horizon
    num_lines = 16
    for i in range(num_lines + 1):
        t = i / num_lines
        sx = cx + (t - 0.5) * 200
        ex = cx + (t - 0.5) * 2200
        pygame.draw.line(grid_surf, color, (sx, horizon_y), (ex, V_HEIGHT), 2)
        
    # Horizontal receding lines scrolling
    num_horiz = 8
    scroll = (time_ticks * 0.001) % 1.0
    for i in range(num_horiz):
        t = (i + scroll) / num_horiz
        y = horizon_y + t * t * (V_HEIGHT - horizon_y)
        pygame.draw.line(grid_surf, color, (0, y), (V_WIDTH, y), 2)
        
    surface.blit(grid_surf, (0, 0))

def draw_static_grid(surface, time_ticks):
    grid_alpha = int(14 + 6 * math.sin(time_ticks * 0.002))
    for x in range(0, V_WIDTH + 1, V_GRID_SIZE):
        line_surf = pygame.Surface((2, ROWS * V_GRID_SIZE), pygame.SRCALPHA)
        line_surf.fill((*GRID_LINE_COLOR, grid_alpha))
        surface.blit(line_surf, (x, V_HEADER_HEIGHT))
    for y in range(0, ROWS * V_GRID_SIZE + 1, V_GRID_SIZE):
        line_surf = pygame.Surface((V_WIDTH, 2), pygame.SRCALPHA)
        line_surf.fill((*GRID_LINE_COLOR, grid_alpha))
        surface.blit(line_surf, (0, V_HEADER_HEIGHT + y))

# --- HUD Header Panel ---
def draw_header(surface, score, high_score, laser_ammo, rewind_charges, active_powers, time_ticks):
    header_surf = pygame.Surface((V_WIDTH, V_HEADER_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(header_surf, (16, 12, 32, 230), (0, 0, V_WIDTH, V_HEADER_HEIGHT))
    pygame.draw.line(header_surf, (0, 240, 255, 180), (0, V_HEADER_HEIGHT - 4), (V_WIDTH, V_HEADER_HEIGHT - 4), 4)
    surface.blit(header_surf, (0, 0))
    
    font_lbl = pygame.font.SysFont("Helvetica", 20, bold=True)
    font_val = pygame.font.SysFont("Helvetica", 36, bold=True)
    
    # Render Scores
    score_lbl = font_lbl.render("SCORE", True, (0, 240, 255))
    score_val = font_val.render(f"{score:04d}", True, TEXT_COLOR)
    surface.blit(score_lbl, (50, 20))
    surface.blit(score_val, (50, 48))
    
    high_lbl = font_lbl.render("HIGH SCORE", True, (255, 215, 0))
    high_val = font_val.render(f"{high_score:04d}", True, TEXT_COLOR)
    surface.blit(high_lbl, (V_WIDTH - high_lbl.get_width() - 50, 20))
    surface.blit(high_val, (V_WIDTH - high_val.get_width() - 50, 48))
    
    # Laser Ammo & Rewind Status Indicators
    ammo_lbl = font_lbl.render("PLASMA AMMO", True, COLOR_LASER)
    ammo_val = font_val.render(f"🔋 x{laser_ammo}", True, TEXT_COLOR)
    surface.blit(ammo_lbl, (350, 20))
    surface.blit(ammo_val, (350, 48))

    rewind_lbl = font_lbl.render("TIME CHARGE", True, COLOR_REWIND)
    rewind_val = font_val.render(f"⌛ x{rewind_charges}", True, TEXT_COLOR)
    surface.blit(rewind_lbl, (600, 20))
    surface.blit(rewind_val, (600, 48))

    # Glowing pulsing Logo
    font_logo = pygame.font.SysFont("Helvetica", 38, bold=True)
    logo_glow = render_glowing_text("NEON SNAKE", font_logo, SNAKE_COLOR, (0, 255, 136), glow_size=4)
    alpha = int(140 + 70 * math.sin(time_ticks * 0.005))
    logo_glow.set_alpha(alpha)
    surface.blit(logo_glow, (V_WIDTH // 2 - logo_glow.get_width() // 2 - 100, 32))

# --- Main Program ---
def main():
    global obstacles, selected_map
    high_score = 0
    try:
        if os.path.exists("highscore.txt"):
            with open("highscore.txt", "r") as f:
                high_score = int(f.read().strip())
    except Exception:
        pass

    state = STATE_START
    selected_map = MAP_OPEN
    build_map(selected_map)
    
    snake = Snake()
    food = Food(snake.body)
    spawned_powerup = None
    
    # Systems
    particles = ParticleSystem()
    floating_texts = []
    laser_beams = []
    screen_shake = ScreenShake()
    
    # Player inventories
    score = 0
    laser_ammo = 0
    rewind_charges = 1
    
    # Active powers timer counters (seconds)
    active_powers = {'SHIELD': 0.0, 'SPEED': 0.0, 'SLOW': 0.0}
    
    # Rewinding History Snapshot buffer
    history_buffer = []

    # Time tracking variables
    accumulated_time = 0.0
    last_ticks = pygame.time.get_ticks()
    
    # 2x Virtual Render surface
    virtual_surface = pygame.Surface((V_WIDTH, V_HEIGHT))
    
    # HUD fonts
    font_ui = pygame.font.SysFont("Helvetica", 22)
    font_title = pygame.font.SysFont("Helvetica", 82, bold=True)
    font_btn = pygame.font.SysFont("Helvetica", 36, bold=True)

    play_synth_sound(440, 150, 'sine')
    play_synth_sound(659, 300, 'sine')

    running = True
    while running:
        current_ticks = pygame.time.get_ticks()
        dt = current_ticks - last_ticks
        last_ticks = current_ticks
        dt = min(100, dt) # cap delta

        # Key listeners
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
                
            elif event.type == pygame.KEYDOWN:
                if state == STATE_START:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        # Start Game
                        play_synth_sound(523, 100, 'sine')
                        play_synth_sound(1046, 250, 'sine')
                        state = STATE_PLAY
                        snake = Snake()
                        food = Food(snake.body)
                        spawned_powerup = None
                        score = 0
                        laser_ammo = 0
                        rewind_charges = 1
                        active_powers = {'SHIELD': 0.0, 'SPEED': 0.0, 'SLOW': 0.0}
                        history_buffer = []
                        particles = ParticleSystem()
                        floating_texts = []
                        laser_beams = []
                        accumulated_time = 0
                    elif event.key == pygame.K_1:
                        selected_map = MAP_OPEN
                        build_map(selected_map)
                        resetDemo()
                        play_synth_sound(400, 50, 'sine')
                    elif event.key == pygame.K_2:
                        selected_map = MAP_PILLARS
                        build_map(selected_map)
                        resetDemo()
                        play_synth_sound(400, 50, 'sine')
                    elif event.key == pygame.K_3:
                        selected_map = MAP_CROSS
                        build_map(selected_map)
                        resetDemo()
                        play_synth_sound(400, 50, 'sine')
                    elif event.key == pygame.K_4:
                        selected_map = MAP_MAZE
                        build_map(selected_map)
                        resetDemo()
                        play_synth_sound(400, 50, 'sine')
                        
                elif state == STATE_PLAY:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        snake.change_direction((0, -1))
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        snake.change_direction((0, 1))
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        snake.change_direction((-1, 0))
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        snake.change_direction((1, 0))
                    elif event.key == pygame.K_SPACE:
                        # Fire Laser Blaster!
                        if laser_ammo > 0:
                            laser_ammo -= 1
                            screen_shake.trigger(duration=8, intensity=8)
                            
                            hx, hy = snake.body[0]
                            dx, dy = snake.direction
                            
                            # Calculate laser projection line
                            laser_length = 6
                            end_cell = (hx, hy)
                            for i in range(1, laser_length + 1):
                                target_cell = (hx + dx * i, hy + dy * i)
                                end_cell = target_cell
                                
                                # Vaporize obstacle block
                                if target_cell in obstacles:
                                    obstacles.remove(target_cell)
                                    px = target_cell[0] * V_GRID_SIZE + V_GRID_SIZE//2
                                    py = target_cell[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE//2
                                    particles.spawn_explosion(px, py, OBSTACLE_COLOR, 15)
                                    play_synth_sound(200, 200, 'noise', 0.25)
                                    break
                                    
                                # Vaporize snake's own tail (tail cutter!)
                                if target_cell in snake.body:
                                    idx = snake.body.index(target_cell)
                                    # Vaporize from index down to tail
                                    cut_count = len(snake.body) - idx
                                    for tail_idx in range(len(snake.body) - 1, idx - 1, -1):
                                        t_cell = snake.body[tail_idx]
                                        px = t_cell[0] * V_GRID_SIZE + V_GRID_SIZE//2
                                        py = t_cell[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE//2
                                        particles.spawn_explosion(px, py, SNAKE_COLOR, 8)
                                        snake.body.pop()
                                    
                                    play_synth_sound(300, 300, 'noise', 0.25)
                                    floating_texts.append(FloatingText(f"TAIL CUT -{cut_count}", hx*V_GRID_SIZE, hy*V_GRID_SIZE+V_HEADER_HEIGHT, SNAKE_HEAD_COLOR))
                                    break
                                    
                                # Map boundaries check
                                if target_cell[0] < 0 or target_cell[0] >= COLS or target_cell[1] < 0 or target_cell[1] >= ROWS:
                                    break
                                    
                            # Create visual beam
                            start_px = (hx * V_GRID_SIZE + V_GRID_SIZE//2, hy * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE//2)
                            end_px = (end_cell[0] * V_GRID_SIZE + V_GRID_SIZE//2, end_cell[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE//2)
                            laser_beams.append(LaserBeam(start_px, end_px, (dx, dy)))
                            play_synth_sound(600, 150, 'saw', 0.2)
                            
                elif state == STATE_GAMEOVER:
                    if event.key == pygame.K_r:
                        state = STATE_PLAY
                        snake = Snake()
                        food = Food(snake.body)
                        spawned_powerup = None
                        score = 0
                        laser_ammo = 0
                        rewind_charges = 1
                        active_powers = {'SHIELD': 0.0, 'SPEED': 0.0, 'SLOW': 0.0}
                        history_buffer = []
                        particles = ParticleSystem()
                        floating_texts = []
                        laser_beams = []
                        accumulated_time = 0
                        play_synth_sound(523, 100, 'sine')
                        play_synth_sound(1046, 250, 'sine')
                    elif event.key == pygame.K_q:
                        running = False
                        break
                        
                elif state == STATE_REWIND_PROMPT:
                    if event.key == pygame.K_BACKSPACE:
                        # Start rewinding time animation!
                        state = STATE_REWINDING
                        play_synth_sound(300, 600, 'saw', 0.25)
                    elif event.key == pygame.K_q:
                        # Skip rewind and trigger standard Game Over
                        state = STATE_GAMEOVER
                        play_synth_sound(120, 450, 'noise')

        if not running:
            break

        # Decrement active powers durations (in seconds)
        active_elapsed = dt / 1000.0
        if active_powers['SLOW'] > 0:
            active_elapsed *= 0.5 # slow-mo decays slower

        if active_powers['SHIELD'] > 0: active_powers['SHIELD'] = max(0.0, active_powers['SHIELD'] - active_elapsed)
        if active_powers['SPEED'] > 0: active_powers['SPEED'] = max(0.0, active_powers['SPEED'] - active_elapsed)
        if active_powers['SLOW'] > 0: active_powers['SLOW'] = max(0.0, active_powers['SLOW'] - active_elapsed)

        # Decay spawned powerup timer on board
        if spawned_powerup:
            spawned_powerup.time_left -= dt / 1000.0
            if spawned_powerup.time_left <= 0:
                spawned_powerup = None

        # --- Rewind History Recording ---
        if state == STATE_PLAY:
            # Take state snapshot
            snapshot = {
                'body': list(snake.body),
                'direction': snake.direction,
                'direction_queue': list(snake.direction_queue),
                'score': score,
                'food_position': food.position,
                'powerup_position': spawned_powerup.position if spawned_powerup else None,
                'powerup_type': spawned_powerup.type if spawned_powerup else None,
                'powerup_time': spawned_powerup.time_left if spawned_powerup else 0.0,
                'laser_ammo': laser_ammo,
                'rewind_charges': rewind_charges,
                'active_powers': dict(active_powers),
                'obstacles': list(obstacles)
            }
            history_buffer.append(snapshot)
            # Store up to 6 seconds of history (about 180 snapshots at standard speed)
            if len(history_buffer) > 180:
                history_buffer.pop(0)

        # --- Rewinding Time State Machine Execution ---
        if state == STATE_REWINDING:
            # Pop 4 history snapshots per frame to simulate reverse rewind
            for _ in range(4):
                if history_buffer:
                    snap = history_buffer.pop()
                    # Apply popped state
                    snake.body = snap['body']
                    snake.prev_body = list(snake.body)
                    snake.direction = snap['direction']
                    snake.direction_queue = snap['direction_queue']
                    score = snap['score']
                    food.position = snap['food_position']
                    laser_ammo = snap['laser_ammo']
                    rewind_charges = snap['rewind_charges']
                    active_powers = snap['active_powers']
                    obstacles = snap['obstacles']
                    if snap['powerup_position']:
                        spawned_powerup = PowerUp(snake.body, food.position)
                        spawned_powerup.position = snap['powerup_position']
                        spawned_powerup.type = snap['powerup_type']
                        spawned_powerup.time_left = snap['powerup_time']
                    else:
                        spawned_powerup = None
                else:
                    break
            
            # Play a dynamic rewinding synth sweep sound
            play_synth_sound(150 + len(history_buffer) * 4, 35, 'saw', 0.15)
            
            # Finished rewinding
            if not history_buffer or len(history_buffer) <= 1:
                state = STATE_PLAY
                accumulated_time = 0.0
                play_synth_sound(523, 150, 'sine')

        # --- Logical Tick Updates ---
        # Logical Tick Speed factors
        speed_factor = 1.0
        if active_powers['SPEED'] > 0: speed_factor = 1.7
        if active_powers['SLOW'] > 0: speed_factor = 0.55

        logical_tick_cooldown = max(65.0, 140.0 - score * 0.03) / speed_factor if state == STATE_PLAY else 100.0

        if state == STATE_PLAY or state == STATE_START:
            accumulated_time += dt
            if accumulated_time >= logical_tick_cooldown:
                accumulated_time -= logical_tick_cooldown
                
                # Screensaver/Start screen updates
                if state == STATE_START:
                    ai_dir = get_ai_direction(snake, food, spawned_powerup)
                    snake.change_direction(ai_dir)
                    next_head = (snake.body[0][0] + snake.direction[0], snake.body[0][1] + snake.direction[1])
                    
                    eating = (next_head == food.position)
                    collecting = spawned_powerup and (next_head == spawned_powerup.position)
                    
                    snake.move(eating or collecting)
                    
                    if eating:
                        px = food.position[0] * V_GRID_SIZE + V_GRID_SIZE // 2
                        py = food.position[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE // 2
                        particles.spawn_explosion(px, py, FOOD_COLOR, 15)
                        food = Food(snake.body)
                        if random.random() < 0.25:
                            spawned_powerup = PowerUp(snake.body, food.position)
                            
                    elif collecting:
                        px = spawned_powerup.position[0] * V_GRID_SIZE + V_GRID_SIZE // 2
                        py = spawned_powerup.position[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE // 2
                        particles.spawn_explosion(px, py, COLOR_SHIELD, 15)
                        spawned_powerup = None
                        
                    if snake.check_collision(active_shield=False):
                        resetDemo()
                        
                # Active Gameplay updates
                elif state == STATE_PLAY:
                    next_head = (snake.body[0][0] + snake.direction[0], snake.body[0][1] + snake.direction[1])
                    
                    # Wrap around boundaries if Shield active
                    if active_powers['SHIELD'] > 0:
                        nx, ny = next_head
                        if nx < 0: nx = COLS - 1
                        elif nx >= COLS: nx = 0
                        if ny < 0: ny = ROWS - 1
                        elif ny >= ROWS: ny = 0
                        next_head = (nx, ny)

                    eating = (next_head == food.position)
                    collecting = spawned_powerup and (next_head == spawned_powerup.position)
                    
                    snake.move(eating or collecting)
                    
                    if eating:
                        add_pts = 100 if active_powers['SPEED'] <= 0 else 200
                        score += add_pts
                        
                        px = food.position[0] * V_GRID_SIZE + V_GRID_SIZE // 2
                        py = food.position[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE // 2
                        particles.spawn_explosion(px, py, FOOD_COLOR, 20)
                        screen_shake.trigger(duration=6, intensity=4)
                        floating_texts.append(FloatingText(f"+{add_pts}", px, py - 20, COLOR_SPEED if active_powers['SPEED'] > 0 else COLOR_SHIELD))
                        
                        play_synth_sound(659, 60, 'sine')
                        play_synth_sound(880, 100, 'sine')
                        
                        food = Food(snake.body)
                        
                        # Probabilistically spawn a powerup item
                        if random.random() < 0.28:
                            spawned_powerup = PowerUp(snake.body, food.position)
                            
                    elif collecting:
                        power_type = spawned_powerup.type
                        spawned_powerup = None
                        screen_shake.trigger(duration=10, intensity=6)
                        px = next_head[0] * V_GRID_SIZE + V_GRID_SIZE // 2
                        py = next_head[1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE // 2
                        
                        if power_type == PowerUp.TYPE_SHRINK:
                            # Scissors Tail Cut powerup
                            sounds['shrinkPop']()
                            particles.spawn_explosion(px, py, COLOR_SHRINK, 25)
                            cut_len = max(3, int(len(snake.body) * 0.7))
                            cut_diff = len(snake.body) - cut_len
                            while len(snake.body) > cut_len:
                                snake.body.pop()
                            floating_texts.append(FloatingText(f"SHRINK TAIL -{cut_diff}", px, py - 25, COLOR_SHRINK))
                        elif power_type == PowerUp.TYPE_LASER:
                            # Ammo battery powerup
                            play_synth_sound(600, 200, 'saw')
                            particles.spawn_explosion(px, py, COLOR_LASER, 20)
                            laser_ammo += 3
                            floating_texts.append(FloatingText("+3 LASER AMMO 🔋", px, py - 25, COLOR_LASER))
                        elif power_type == PowerUp.TYPE_REWIND:
                            # Chronos Hourglass rewind powerup
                            play_synth_sound(500, 250, 'sine')
                            particles.spawn_explosion(px, py, COLOR_REWIND, 20)
                            rewind_charges += 1
                            floating_texts.append(FloatingText("+1 TIME CHARGE ⌛", px, py - 25, COLOR_REWIND))
                        else:
                            # Shield, Speed, Slow-mo timers
                            play_synth_sound(587, 200, 'sine')
                            label = "SHIELD" if power_type == PowerUp.TYPE_SHIELD else ("SPEED" if power_type == PowerUp.TYPE_SPEED else "SLOW-MO")
                            color = COLOR_SHIELD if power_type == PowerUp.TYPE_SHIELD else (COLOR_SPEED if power_type == PowerUp.TYPE_SPEED else COLOR_SLOW)
                            active_powers[label] = 8.0 # active for 8 seconds
                            particles.spawn_explosion(px, py, color, 25)
                            floating_texts.append(FloatingText(f"{label} ACTIVE", px, py - 25, color))

                    # Crash checking
                    if snake.check_collision(active_shield=(active_powers['SHIELD'] > 0)):
                        if rewind_charges > 0:
                            # Play trigger chime, enter Rewind Prompt screen instead of immediate death
                            state = STATE_REWIND_PROMPT
                            play_synth_sound(300, 300, 'saw')
                            play_synth_sound(200, 300, 'saw')
                            screen_shake.trigger(duration=15, intensity=10)
                        else:
                            # Save Highscore & Game over
                            if score > high_score:
                                high_score = score
                                try:
                                    with open("highscore.txt", "w") as f:
                                        f.write(str(high_score))
                                except Exception:
                                    pass
                            
                            state = STATE_GAMEOVER
                            screen_shake.trigger(duration=25, intensity=12)
                            hx = snake.body[0][0] * V_GRID_SIZE + V_GRID_SIZE // 2
                            hy = snake.body[0][1] * V_GRID_SIZE + V_HEADER_HEIGHT + V_GRID_SIZE // 2
                            particles.spawn_explosion(hx, hy, (255, 50, 50), 30)
                            play_synth_sound(120, 450, 'noise')

        # --- Frames update (60 FPS) ---
        particles.update()
        for ft in floating_texts: ft.update()
        floating_texts = [ft for ft in floating_texts if ft.alpha > 0]
        
        for lb in laser_beams: lb.update()
        laser_beams = [lb for lb in laser_beams if lb.duration > 0]

        # --- Draw scene to 2x High-Res Virtual Surface ---
        virtual_surface.fill(BG_COLOR)
        draw_retro_sun(virtual_surface, current_ticks)
        draw_perspective_grid(virtual_surface, current_ticks)
        draw_static_grid(virtual_surface, current_ticks)
        
        # Draw obstacles
        for obs in obstacles:
            px = obs[0] * V_GRID_SIZE
            py = obs[1] * V_GRID_SIZE + V_HEADER_HEIGHT
            rect = pygame.Rect(px + 2, py + 2, V_GRID_SIZE - 4, V_GRID_SIZE - 4)
            # Glowing wall border
            draw_glow_rect(virtual_surface, OBSTACLE_COLOR, rect, glow_size=12, alpha=60, border_radius=8)
            # Inner core block
            pygame.draw.rect(virtual_surface, OBSTACLE_COLOR, rect, border_radius=8)
            pygame.draw.rect(virtual_surface, (255, 230, 0), rect, width=2, border_radius=8)

        # Draw Food & Powerup
        food.draw(virtual_surface, current_ticks)
        if spawned_powerup:
            spawned_powerup.draw(virtual_surface, current_ticks)

        # Draw Snake
        interpolation = min(1.0, accumulated_time / logical_tick_cooldown)
        snake.draw(virtual_surface, interpolation, active_powers, current_ticks)
        
        # Draw Laser Beams & Particles & Float text
        for lb in laser_beams:
            lb.draw(virtual_surface)
        particles.draw(virtual_surface)
        
        for ft in floating_texts:
            ft.draw(virtual_surface, font_ui)

        # Draw HUD Header
        draw_header(virtual_surface, score, high_score, laser_ammo, rewind_charges, active_powers, current_ticks)

        # Draw Overlays on virtual surface
        if state == STATE_START:
            overlay = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 5, 16, 180))
            virtual_surface.blit(overlay, (0, 0))
            
            # Giga Title Logo
            title_glow = render_glowing_text("NEON SNAKE", font_title, (0, 255, 180), SNAKE_COLOR, glow_size=8)
            y_bounce = int(10 * math.sin(current_ticks * 0.004))
            virtual_surface.blit(title_glow, (V_WIDTH // 2 - title_glow.get_width() // 2, 280 + y_bounce))
            
            # Map Selection UI Indicators
            map_lbl = font_btn.render("SELECT ARENA :  [1] OPEN  [2] PILLARS  [3] CROSS  [4] MAZE", True, COLOR_SHIELD)
            active_map_name = "OPEN"
            if selected_map == MAP_PILLARS: active_map_name = "PILLARS"
            elif selected_map == MAP_CROSS: active_map_name = "THE CROSS"
            elif selected_map == MAP_MAZE: active_map_name = "MAZE"
            
            map_act = font_ui.render(f"ACTIVE MAP : {active_map_name}", True, COLOR_SPEED)
            virtual_surface.blit(map_lbl, (V_WIDTH // 2 - map_lbl.get_width() // 2, 540))
            virtual_surface.blit(map_act, (V_WIDTH // 2 - map_act.get_width() // 2, 600))

            # Start prompt
            blink_alpha = int(140 + 115 * math.sin(current_ticks * 0.007))
            btn_surf = font_btn.render("PRESS [ ENTER ] OR [ SPACE ] TO PLAY", True, FOOD_COLOR)
            btn_alpha_surf = pygame.Surface(btn_surf.get_size(), pygame.SRCALPHA)
            btn_alpha_surf.fill((255, 255, 255, blink_alpha))
            btn_surf.blit(btn_alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            virtual_surface.blit(btn_surf, (V_WIDTH // 2 - btn_surf.get_width() // 2, 700))
            
            # Manual controls
            ctrl_1 = font_ui.render("STEER :  W A S D  or  ARROW KEYS", True, TEXT_COLOR)
            ctrl_2 = font_ui.render("LASER CANNON :  SPACE BAR (clears obstacles and cuts tail)", True, COLOR_LASER)
            ctrl_3 = font_ui.render("TIME REWIND :  BACKSPACE (rewinds clock on crash)", True, COLOR_REWIND)
            virtual_surface.blit(ctrl_1, (V_WIDTH // 2 - ctrl_1.get_width() // 2, 850))
            virtual_surface.blit(ctrl_2, (V_WIDTH // 2 - ctrl_2.get_width() // 2, 910))
            virtual_surface.blit(ctrl_3, (V_WIDTH // 2 - ctrl_3.get_width() // 2, 970))

        elif state == STATE_REWIND_PROMPT:
            overlay = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            overlay.fill((20, 8, 20, 200))
            virtual_surface.blit(overlay, (0, 0))
            
            title_glow = render_glowing_text("CRASH DETECTED", font_title, COLOR_REWIND, (255, 0, 127), glow_size=8)
            virtual_surface.blit(title_glow, (V_WIDTH // 2 - title_glow.get_width() // 2, 300))
            
            opt_r = font_btn.render("Press  [ BACKSPACE ]  to Rewind Time", True, COLOR_SPEED)
            opt_q = font_ui.render(f"Press  [ Q ]  to skip and Game Over  (Time Charges Remaining: {rewind_charges})", True, TEXT_COLOR)
            virtual_surface.blit(opt_r, (V_WIDTH // 2 - opt_r.get_width() // 2, 540))
            virtual_surface.blit(opt_q, (V_WIDTH // 2 - opt_q.get_width() // 2, 620))

        elif state == STATE_REWINDING:
            # Purple matrix rewind tint
            overlay = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            overlay.fill((100, 0, 150, 40))
            virtual_surface.blit(overlay, (0, 0))
            
            # VHS distortion lines
            for _ in range(3):
                y_pos = random.randint(0, V_HEIGHT)
                pygame.draw.line(virtual_surface, (255, 255, 255, 80), (0, y_pos), (V_WIDTH, y_pos), 3)
                
            # Rewinding indicator text
            blink = current_ticks // 150 % 2 == 0
            if blink:
                lbl = font_btn.render("◀◀  REWINDING TIME", True, COLOR_REWIND)
                virtual_surface.blit(lbl, (50, V_HEIGHT - 80))

        elif state == STATE_GAMEOVER:
            overlay = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            overlay.fill((20, 5, 10, 210))
            virtual_surface.blit(overlay, (0, 0))
            
            go_glow = render_glowing_text("GAME OVER", font_title, FOOD_COLOR, COLOR_REWIND, glow_size=8)
            virtual_surface.blit(go_glow, (V_WIDTH // 2 - go_glow.get_width() // 2, 280))
            
            score_summary = font_btn.render(f"FINAL SCORE : {score}", True, TEXT_COLOR)
            best_summary = font_btn.render(f"HIGH SCORE : {high_score}", True, (255, 215, 0))
            virtual_surface.blit(score_summary, (V_WIDTH // 2 - score_summary.get_width() // 2, 450))
            virtual_surface.blit(best_summary, (V_WIDTH // 2 - best_summary.get_width() // 2, 510))
            
            act_r = font_btn.render("Press  [ R ]  to Play Again", True, SNAKE_COLOR)
            act_q = font_ui.render("Press  [ Q ]  to Quit Game", True, (160, 160, 180))
            virtual_surface.blit(act_r, (V_WIDTH // 2 - act_r.get_width() // 2, 660))
            virtual_surface.blit(act_q, (V_WIDTH // 2 - act_q.get_width() // 2, 730))

        # --- Supersampling Downscale (Anti-aliased rendering) ---
        # Scale the 1200x1320 high-res surface down to 600x660 using Pygame's bilinear/trilinear smoothscale filter.
        scaled_surface = pygame.transform.smoothscale(virtual_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))

        # Render scaled surface to screen with camera Screen Shake offset
        screen.fill(BG_COLOR)
        dx, dy = screen_shake.get_offset()
        screen.blit(scaled_surface, (dx, dy))
        pygame.display.flip()

        # Framerate lock (60 FPS)
        clock.tick(60)

    pygame.quit()
    sys.exit()

def resetDemo():
    pass # Hook for screensaver resets in event handlers

if __name__ == "__main__":
    main()
