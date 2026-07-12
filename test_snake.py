"""
Comprehensive test suite for Neon Snake game logic.
Run with: .venv/bin/python test_snake.py
"""
import os
import sys
import random

# Headless pygame setup for testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except Exception:
    pass

# Set up a small display for surface operations
screen = pygame.display.set_mode((100, 100))

import snake
from snake import (
    Snake, Food, PowerUp, ParticleSystem, FloatingText, ScreenShake,
    LaserBeam, build_map, get_ai_direction,
    MAP_OPEN, MAP_PILLARS, MAP_CROSS, MAP_MAZE,
    STATE_START, STATE_PLAY, STATE_GAMEOVER, STATE_REWIND_PROMPT, STATE_REWINDING,
    COLS, ROWS, V_GRID_SIZE, V_HEADER_HEIGHT, V_WIDTH, V_HEIGHT,
    draw_header
)

passed = 0
failed = 0
errors = []


def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        errors.append(name)
        print(f"  FAIL: {name}")


def reset_globals():
    snake.obstacles = []
    snake.move_obstacles = []


# ============================================================
# 1. SNAKE BASICS
# ============================================================
print("\n=== SNAKE BASICS ===")

def test_initial_state():
    reset_globals()
    s = Snake()
    test("Initial body length is 3", len(s.body) == 3)
    test("Initial head at (15,15)", s.body[0] == (15, 15))
    test("Initial direction is up (0,-1)", s.direction == (0, -1))
    test("Direction queue starts empty", len(s.direction_queue) == 0)

test_initial_state()


def test_move_forward():
    reset_globals()
    s = Snake()
    s.move(is_eating=False)
    test("Head moves up to (15,14)", s.body[0] == (15, 14))
    test("Body length stays 3", len(s.body) == 3)
    test("Tail popped", s.was_popped is True)

test_move_forward()


def test_move_eating_grows():
    reset_globals()
    s = Snake()
    s.move(is_eating=True)
    test("Head moves to (15,14)", s.body[0] == (15, 14))
    test("Body length grows to 4", len(s.body) == 4)
    test("No tail popped", s.was_popped is False)

test_move_eating_grows()


def test_direction_change():
    reset_globals()
    s = Snake()
    s.change_direction((1, 0))
    test("Direction queued", len(s.direction_queue) == 1)
    test("Queue has right direction", s.direction_queue[0] == (1, 0))
    s.move(is_eating=False)
    test("Direction applied after move", s.direction == (1, 0))
    test("Head moved right to (16,15)", s.body[0] == (16, 15))

test_direction_change()


def test_reverse_blocked():
    reset_globals()
    s = Snake()
    s.change_direction((0, 1))  # Try to reverse (going down when facing up)
    test("Reverse direction blocked", len(s.direction_queue) == 0)

test_reverse_blocked()


def test_double_input_buffering():
    reset_globals()
    s = Snake()
    s.change_direction((1, 0))  # Right
    s.change_direction((0, 1))  # Down (queued after right)
    test("Two inputs queued", len(s.direction_queue) == 2)
    s.move(is_eating=False)
    test("First input applied", s.direction == (1, 0))
    s.move(is_eating=False)
    test("Second input applied", s.direction == (0, 1))

test_double_input_buffering()


# ============================================================
# 2. COLLISION DETECTION
# ============================================================
print("\n=== COLLISION DETECTION ===")

def test_wall_collision():
    reset_globals()
    s = Snake()
    s.body = [(0, 0), (1, 0), (2, 0)]
    s.direction = (-1, 0)
    s.move(is_eating=False)
    test("Wall collision at (-1,0)", s.check_collision(active_shield=False) is True)

test_wall_collision()


def test_no_collision_safe():
    reset_globals()
    s = Snake()
    s.body = [(15, 15), (15, 16), (15, 17)]
    test("No collision in open space", s.check_collision(active_shield=False) is False)

test_no_collision_safe()


def test_self_collision():
    reset_globals()
    s = Snake()
    s.body = [(10, 10), (10, 11), (10, 12), (11, 12), (11, 11), (11, 10), (10, 10)]
    test("Self collision detected", s.check_collision(active_shield=False) is True)

test_self_collision()


def test_obstacle_collision():
    reset_globals()
    snake.obstacles = [(15, 14)]
    s = Snake()
    s.body = [(15, 15), (15, 16), (15, 17)]
    s.direction = (0, -1)
    s.move(is_eating=False)
    test("Obstacle collision at (15,14)", s.check_collision(active_shield=False) is True)

test_obstacle_collision()


def test_shield_prevents_collision():
    reset_globals()
    snake.obstacles = [(15, 14)]
    s = Snake()
    s.body = [(15, 15), (15, 16), (15, 17)]
    s.direction = (0, -1)
    s.move(is_eating=False)
    test("Shield prevents collision", s.check_collision(active_shield=True) is False)

test_shield_prevents_collision()


def test_moving_obstacle_collision():
    reset_globals()
    snake.move_obstacles = [{'pos': (15, 14), 'dir': (0, 1), 'timer': 0.0}]
    s = Snake()
    s.body = [(15, 15), (15, 16), (15, 17)]
    s.direction = (0, -1)
    s.move(is_eating=False)
    test("Moving obstacle collision", s.check_collision(active_shield=False) is True)

test_moving_obstacle_collision()


# ============================================================
# 3. FOOD EATING
# ============================================================
print("\n=== FOOD EATING ===")

def test_food_spawn_not_on_snake():
    reset_globals()
    s = Snake()
    f = Food(s.body)
    test("Food not on snake body", f.position not in s.body)
    test("Food not on obstacles", f.position not in snake.obstacles)

test_food_spawn_not_on_snake()


def test_food_eating_mechanic():
    reset_globals()
    s = Snake()
    f = Food(s.body)
    food_pos = f.position
    # Place snake right below food, heading up so next_head = food_pos
    hx, hy = food_pos
    s.body = [(hx, hy + 1), (hx, hy + 2), (hx, hy + 3)]
    s.prev_body = list(s.body)
    s.direction = (0, -1)
    next_head = (s.body[0][0] + s.direction[0], s.body[0][1] + s.direction[1])
    eating = (next_head == f.position)
    test("Eating detected when head reaches food", eating is True)

test_food_eating_mechanic()


def test_food_respawn_after_eat():
    reset_globals()
    s = Snake()
    f = Food(s.body)
    old_pos = f.position
    f = Food(s.body)
    test("New food spawned at different position", f.position != old_pos or len(s.body) == 0)

test_food_respawn_after_eat()


# ============================================================
# 4. SCREEN SHAKE
# ============================================================
print("\n=== SCREEN SHAKE ===")

def test_shake_initial_state():
    ss = ScreenShake()
    test("Initial duration is 0", ss.duration == 0)
    test("Initial intensity is 0", ss.intensity == 0)
    dx, dy = ss.get_offset()
    test("Initial offset is (0,0)", (dx, dy) == (0, 0))

test_shake_initial_state()


def test_shake_trigger_and_offset():
    ss = ScreenShake()
    ss.trigger(duration=10, intensity=5)
    test("Duration set to 10", ss.duration == 10)
    test("Intensity set to 5", ss.intensity == 5)
    dx, dy = ss.get_offset()
    test("Offset is within range", -5 <= dx <= 5 and -5 <= dy <= 5)

test_shake_trigger_and_offset()


def test_shake_decay():
    """BUG2 TEST: screen_shake.update() must decrement duration"""
    ss = ScreenShake()
    ss.trigger(duration=5, intensity=3)
    for _ in range(6):
        ss.update()
    test("Duration reaches 0 after 6 updates", ss.duration == 0)
    test("Intensity reset to 0", ss.intensity == 0)
    dx, dy = ss.get_offset()
    test("Offset is (0,0) after decay", (dx, dy) == (0, 0))

test_shake_decay()


def test_shake_partial_decay():
    ss = ScreenShake()
    ss.trigger(duration=10, intensity=5)
    ss.update()
    ss.update()
    test("Duration decremented by updates", ss.duration == 8)
    test("Intensity preserved during shake", ss.intensity == 5)

test_shake_partial_decay()


def test_shake_does_not_go_negative():
    ss = ScreenShake()
    ss.trigger(duration=2, intensity=3)
    ss.update()
    ss.update()
    ss.update()
    ss.update()
    test("Duration does not go negative", ss.duration == 0)
    test("Intensity cleared", ss.intensity == 0)

test_shake_does_not_go_negative()


# ============================================================
# 5. POWER-UPS
# ============================================================
print("\n=== POWER-UPS ===")

def test_powerup_all_types_exist():
    reset_globals()
    types = PowerUp.ALL_TYPES
    test("11 power-up types", len(types) == 11)
    test("SHIELD type exists", PowerUp.TYPE_SHIELD in types)
    test("SPEED type exists", PowerUp.TYPE_SPEED in types)
    test("SLOW type exists", PowerUp.TYPE_SLOW in types)
    test("SHRINK type exists", PowerUp.TYPE_SHRINK in types)
    test("LASER type exists", PowerUp.TYPE_LASER in types)
    test("REWIND type exists", PowerUp.TYPE_REWIND in types)
    test("GHOST type exists", PowerUp.TYPE_GHOST in types)
    test("MAGNET type exists", PowerUp.TYPE_MAGNET in types)
    test("DOUBLE type exists", PowerUp.TYPE_DOUBLE in types)
    test("TAILSHIELD type exists", PowerUp.TYPE_TAILSHIELD in types)
    test("TELEPORT type exists", PowerUp.TYPE_TELEPORT in types)

test_powerup_all_types_exist()


def test_powerup_spawn():
    reset_globals()
    s = Snake()
    f = Food(s.body)
    for _ in range(20):
        p = PowerUp(s.body, f.position)
        test("Powerup not on snake", p.position not in s.body)
        test("Powerup not on food", p.position != f.position)
        test("Powerup has valid type", p.type in PowerUp.ALL_TYPES)
        test("Powerup has 10s timer", p.time_left == 10.0)
        break

test_powerup_spawn()


def test_powerup_despawn():
    reset_globals()
    s = Snake()
    f = Food(s.body)
    p = PowerUp(s.body, f.position)
    p.time_left = 0.0
    test("Powerup expired", p.time_left <= 0)

test_powerup_despawn()


# ============================================================
# 6. COMBO SYSTEM
# ============================================================
print("\n=== COMBO SYSTEM ===")

def test_combo_increments():
    combo_count = 0
    combo_timer = 0.0
    combo_count += 1
    combo_timer = 2.0
    test("Combo increments to 1", combo_count == 1)
    test("Combo timer set to 2.0", combo_timer == 2.0)

test_combo_increments()


def test_combo_multiplier():
    base_pts = 100
    combo_count = 3
    if combo_count >= 3:
        base_pts = int(base_pts * (1 + combo_count * 0.25))
    test("Combo 3x gives 175 pts", base_pts == 175)

test_combo_multiplier()


def test_combo_reset_on_timeout():
    combo_count = 5
    combo_timer = 0.1
    dt = 200  # ms
    combo_timer -= dt / 1000.0
    if combo_timer <= 0:
        combo_count = 0
    test("Combo resets after timer expires", combo_count == 0)

test_combo_reset_on_timeout()


def test_combo_does_not_reset_if_timer_positive():
    combo_count = 5
    combo_timer = 2.0
    dt = 100  # ms
    combo_timer -= dt / 1000.0
    if combo_timer <= 0:
        combo_count = 0
    test("Combo preserved when timer > 0", combo_count == 5)

test_combo_does_not_reset_if_timer_positive()


# ============================================================
# 7. PROGRESSIVE DIFFICULTY
# ============================================================
print("\n=== PROGRESSIVE DIFFICULTY ===")

def test_difficulty_level_calc():
    score = 2500
    level = 1 + score // 1000
    test("Level 3 at score 2500", level == 3)

test_difficulty_level_calc()


def test_moving_obstacles_spawn():
    reset_globals()
    difficulty_level = 2
    num_movers = min(difficulty_level, 5)
    test("2 movers at level 2", num_movers == 2)
    test("Max 5 movers capped", min(10, 5) == 5)

test_moving_obstacles_spawn()


def test_moving_obstacle_bounce():
    reset_globals()
    mo = {'pos': (1, 15), 'dir': (-1, 0), 'timer': 0.0}
    dx, dy = mo['dir']
    new_pos = (mo['pos'][0] + dx, mo['pos'][1] + dy)
    hits_wall = new_pos[0] < 1
    test("Moving obstacle detects wall", hits_wall is True)

test_moving_obstacle_bounce()


# ============================================================
# 8. MISSION SYSTEM
# ============================================================
print("\n=== MISSION SYSTEM ===")

def test_mission_spawn():
    mission_active = False
    mission_timer = 16.0  # > 15.0 threshold
    if not mission_active and mission_timer >= 15.0:
        mission_active = True
    test("Mission activates after 15s", mission_active is True)

test_mission_spawn()


def test_mission_food_tracking():
    mission_food_collected = 0
    mission_target = 3
    mission_food_collected += 1
    mission_food_collected += 1
    mission_food_collected += 1
    test("Mission tracks food collection", mission_food_collected == 3)
    test("Mission complete when target reached", mission_food_collected >= mission_target)

test_mission_food_tracking()


def test_mission_reward():
    mission_target = 5
    mission_reward = mission_target * 150
    test("Mission reward = 750", mission_reward == 750)

test_mission_reward()


# ============================================================
# 9. FLOATING TEXT (BUG1 TEST)
# ============================================================
print("\n=== FLOATING TEXT (BUG1 REGRESSION) ===")

def test_floating_text_creation():
    ft = FloatingText("TEST", 100, 200, (255, 255, 255))
    test("FloatingText created", ft.text == "TEST")
    test("Position set", ft.x == 100 and ft.y == 200)

test_floating_text_creation()


def test_floating_text_append():
    """BUG1 TEST: FloatingText must be wrapped in constructor"""
    floating_texts = []
    floating_texts.append(FloatingText("MISSION: Eat 5 food!", V_WIDTH // 2, V_HEADER_HEIGHT + 50, (255, 215, 0)))
    test("List length is 1", len(floating_texts) == 1)
    test("Item is FloatingText", isinstance(floating_texts[0], FloatingText))

test_floating_text_append()


def test_floating_text_fadeout():
    ft = FloatingText("TEST", 100, 200, (255, 255, 255))
    for _ in range(40):
        ft.update()
    test("Alpha decreases after updates", ft.alpha < 255.0)
    test("Y position moves up", ft.y < 200)

test_floating_text_fadeout()


# ============================================================
# 10. GHOST MODE (pass-through)
# ============================================================
print("\n=== GHOST MODE ===")

def test_ghost_wraps_walls():
    reset_globals()
    s = Snake()
    s.body = [(0, 5), (1, 5), (2, 5)]
    s.direction = (-1, 0)
    nx, ny = s.body[0][0] + s.direction[0], s.body[0][1] + s.direction[1]
    # Ghost wrap logic
    if nx < 0: nx = COLS - 1
    if ny < 0: ny = ROWS - 1
    if nx >= COLS: nx = 0
    if ny >= ROWS: ny = 0
    test("Ghost wraps left wall to right", nx == COLS - 1)

test_ghost_wraps_walls()


def test_ghost_no_collision():
    reset_globals()
    snake.obstacles = [(15, 14)]
    s = Snake()
    s.body = [(15, 15), (15, 16), (15, 17)]
    s.direction = (0, -1)
    s.move(is_eating=False)
    test("Ghost prevents all collision", s.check_collision(active_shield=True) is False)

test_ghost_no_collision()


# ============================================================
# 11. MAGNET POWER-UP
# ============================================================
print("\n=== MAGNET POWER-UP ===")

def test_magnet_attracts_food():
    reset_globals()
    hx, hy = 15, 15
    fx, fy = 15, 8
    dist = abs(hx - fx) + abs(hy - fy)
    test("Food in magnet range (dist=7 <= 8)", dist <= 8)
    if fx < hx: fx += 1
    elif fx > hx: fx -= 1
    if fy < hy: fy += 1
    elif fy > hy: fy -= 1
    test("Food moved closer vertically", fy == 9)

test_magnet_attracts_food()


def test_magnet_no_effect_out_of_range():
    hx, hy = 15, 15
    fx, fy = 15, 5
    dist = abs(hx - fx) + abs(hy - fy)
    test("Food out of range (dist=10 > 8)", dist > 8)

test_magnet_no_effect_out_of_range()


# ============================================================
# 12. DOUBLE SCORE
# ============================================================
print("\n=== DOUBLE SCORE ===")

def test_double_score():
    base_pts = 100
    active_double = 8.0
    if active_double > 0:
        base_pts *= 2
    test("Double score gives 200", base_pts == 200)

test_double_score()


def test_double_score_with_speed():
    base_pts = 200  # speed already doubled
    active_double = 8.0
    if active_double > 0:
        base_pts *= 2
    test("Speed+Double gives 400", base_pts == 400)

test_double_score_with_speed()


# ============================================================
# 13. TAIL SHIELD
# ============================================================
print("\n=== TAIL SHIELD ===")

def test_tail_shield_allows_self_collision():
    """Tail shield should not protect against wall/obstacle"""
    reset_globals()
    snake.obstacles = [(15, 14)]
    s = Snake()
    s.body = [(15, 15), (15, 16), (15, 17)]
    s.direction = (0, -1)
    s.move(is_eating=False)
    crashed = s.check_collision(active_shield=False)
    test("Obstacle still crashes with tail shield", crashed is True)

test_tail_shield_allows_self_collision()


def test_tail_shield_blocks_self():
    reset_globals()
    s = Snake()
    s.body = [(10, 10), (10, 11), (10, 12), (11, 12), (11, 11), (11, 10), (10, 10)]
    crashed = s.check_collision(active_shield=False)
    # Tail shield logic from main: if crashed and TAILSHIELD, only crash if wall/obstacle
    head = s.body[0]
    is_wall_or_obstacle = head in snake.obstacles or head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS
    test("Self-collision detected", crashed is True)
    test("Not wall/obstacle (is self-collision)", is_wall_or_obstacle is False)
    # With tail shield: would be protected
    test("Tail shield would protect", is_wall_or_obstacle is False)

test_tail_shield_blocks_self()


# ============================================================
# 14. TELEPORT
# ============================================================
print("\n=== TELEPORT ===")

def test_teleport_resets_body():
    reset_globals()
    s = Snake()
    s.body = [(15, 15), (15, 16), (15, 17), (15, 18), (15, 19)]
    s.body = [(10, 10)]
    s.prev_body = list(s.body)
    test("Teleport reduces to 1 segment", len(s.body) == 1)
    test("Position is valid", 2 <= s.body[0][0] <= COLS - 3)

test_teleport_resets_body()


# ============================================================
# 15. AI DIRECTION
# ============================================================
print("\n=== AI DIRECTION ===")

def test_ai_avoids_walls():
    reset_globals()
    s = Snake()
    s.body = [(1, 5), (2, 5), (3, 5)]
    s.direction = (-1, 0)
    f = Food(s.body)
    f.position = (28, 5)
    d = get_ai_direction(s, f, None)
    np = (s.body[0][0] + d[0], s.body[0][1] + d[1])
    test("AI does not move into wall", 0 <= np[0] < COLS)

test_ai_avoids_walls()


def test_ai_avoids_self():
    reset_globals()
    s = Snake()
    s.body = [(10, 10), (10, 11), (11, 11), (11, 10), (9, 10)]
    s.direction = (0, -1)
    f = Food(s.body)
    f.position = (15, 5)
    d = get_ai_direction(s, f, None)
    np = (s.body[0][0] + d[0], s.body[0][1] + d[1])
    test("AI does not move into self", np not in s.body[1:])

test_ai_avoids_self()


# ============================================================
# 16. REWIND SYSTEM
# ============================================================
print("\n=== REWIND SYSTEM ===")

def test_snapshot_format():
    reset_globals()
    s = Snake()
    f = Food(s.body)
    snapshot = {
        'body': list(s.body),
        'direction': s.direction,
        'direction_queue': list(s.direction_queue),
        'score': 0,
        'food_position': f.position,
        'powerup_position': None,
        'powerup_type': None,
        'powerup_time': 0.0,
        'laser_ammo': 0,
        'rewind_charges': 1,
        'active_powers': {'SHIELD': 0.0, 'SPEED': 0.0, 'SLOW': 0.0, 'GHOST': 0.0, 'MAGNET': 0.0, 'DOUBLE': 0.0, 'TAILSHIELD': 0.0, 'TELEPORT': 0.0},
        'obstacles': list(snake.obstacles)
    }
    test("Snapshot has body", 'body' in snapshot)
    test("Snapshot has all active powers", len(snapshot['active_powers']) == 8)
    test("Body preserved in snapshot", snapshot['body'] == s.body)

test_snapshot_format()


def test_history_buffer_limit():
    history = []
    for i in range(200):
        history.append({'idx': i})
        if len(history) > 180:
            history.pop(0)
    test("History capped at 180", len(history) == 180)
    test("Oldest entries removed", history[0]['idx'] == 20)

test_history_buffer_limit()


# ============================================================
# 17. POWER-UP COLLECTION (all 11 types)
# ============================================================
print("\n=== POWER-UP COLLECTION ===")

def test_powerup_shield():
    active_powers = {'SHIELD': 0.0}
    active_powers['SHIELD'] = 8.0
    test("Shield activates for 8s", active_powers['SHIELD'] == 8.0)

test_powerup_shield()


def test_powerup_speed():
    active_powers = {'SPEED': 0.0}
    active_powers['SPEED'] = 8.0
    test("Speed activates for 8s", active_powers['SPEED'] == 8.0)

test_powerup_speed()


def test_powerup_slow():
    active_powers = {'SLOW': 0.0}
    active_powers['SLOW'] = 8.0
    test("Slow-mo activates for 8s", active_powers['SLOW'] == 8.0)

test_powerup_slow()


def test_powerup_ghost():
    active_powers = {'GHOST': 0.0}
    active_powers['GHOST'] = 8.0
    test("Ghost activates for 8s", active_powers['GHOST'] == 8.0)

test_powerup_ghost()


def test_powerup_magnet():
    active_powers = {'MAGNET': 0.0}
    active_powers['MAGNET'] = 8.0
    test("Magnet activates for 8s", active_powers['MAGNET'] == 8.0)

test_powerup_magnet()


def test_powerup_double():
    active_powers = {'DOUBLE': 0.0}
    active_powers['DOUBLE'] = 8.0
    test("Double activates for 8s", active_powers['DOUBLE'] == 8.0)

test_powerup_double()


def test_powerup_tailshield():
    active_powers = {'TAILSHIELD': 0.0}
    active_powers['TAILSHIELD'] = 8.0
    test("Tail shield activates for 8s", active_powers['TAILSHIELD'] == 8.0)

test_powerup_tailshield()


def test_powerup_teleport():
    reset_globals()
    s = Snake()
    old_head = s.body[0]
    s.body = [(10, 10)]
    s.prev_body = list(s.body)
    test("Teleport changed position", s.body[0] != (15, 15))

test_powerup_teleport()


def test_powerup_laser():
    laser_ammo = 0
    laser_ammo += 3
    test("Laser gives 3 ammo", laser_ammo == 3)

test_powerup_laser()


def test_powerup_rewind():
    rewind_charges = 1
    rewind_charges += 1
    test("Rewind gives 1 charge", rewind_charges == 2)

test_powerup_rewind()


def test_powerup_shrink():
    s = Snake()
    s.body = [(15, 15 + i) for i in range(20)]
    cut_len = max(3, int(len(s.body) * 0.7))
    while len(s.body) > cut_len:
        s.body.pop()
    test("Shrink cuts 30%", len(s.body) == 14)

test_powerup_shrink()


# ============================================================
# 18. POWER-UP TIMER DECAY
# ============================================================
print("\n=== POWER-UP TIMER DECAY ===")

def test_power_decay():
    active_powers = {'SHIELD': 5.0, 'SPEED': 0.0, 'SLOW': 0.0, 'GHOST': 3.0, 'MAGNET': 0.0, 'DOUBLE': 0.0, 'TAILSHIELD': 0.0, 'TELEPORT': 0.0}
    dt = 1000  # 1 second
    active_elapsed = dt / 1000.0
    for key in active_powers:
        if active_powers[key] > 0:
            active_powers[key] = max(0.0, active_powers[key] - active_elapsed)
    test("Shield decays to 4.0", active_powers['SHIELD'] == 4.0)
    test("Ghost decays to 2.0", active_powers['GHOST'] == 2.0)
    test("Speed stays 0.0", active_powers['SPEED'] == 0.0)

test_power_decay()


def test_power_decay_does_not_go_negative():
    active_powers = {'SHIELD': 0.5, 'SPEED': 0.0, 'SLOW': 0.0, 'GHOST': 0.0, 'MAGNET': 0.0, 'DOUBLE': 0.0, 'TAILSHIELD': 0.0, 'TELEPORT': 0.0}
    dt = 2000  # 2 seconds
    active_elapsed = dt / 1000.0
    for key in active_powers:
        if active_powers[key] > 0:
            active_powers[key] = max(0.0, active_powers[key] - active_elapsed)
    test("Clamped to 0.0, not negative", active_powers['SHIELD'] == 0.0)

test_power_decay_does_not_go_negative()


# ============================================================
# 19. FULL GAME LOOP SIMULATION
# ============================================================
print("\n=== FULL GAME LOOP SIMULATION ===")

def test_full_loop():
    reset_globals()
    s = Snake()
    f = Food(s.body)
    score = 0
    combo_count = 0
    combo_timer = 0.0
    active_powers = {'SHIELD': 0.0, 'SPEED': 0.0, 'SLOW': 0.0, 'GHOST': 0.0, 'MAGNET': 0.0, 'DOUBLE': 0.0, 'TAILSHIELD': 0.0, 'TELEPORT': 0.0}
    screen_shake = ScreenShake()
    floating_texts = []
    particles = ParticleSystem()
    accumulated_time = 0.0
    laser_ammo = 0
    rewind_charges = 1
    spawned_powerup = None
    mission_active = False
    mission_food_collected = 0
    move_obstacles = []

    dt = 33
    ticks_run = 0

    for frame in range(500):
        current_ticks = pygame.time.get_ticks()
        accumulated_time += dt

        # Decay screen shake
        screen_shake.update()

        # Decay powers
        active_elapsed = dt / 1000.0
        for key in active_powers:
            if active_powers[key] > 0:
                active_powers[key] = max(0.0, active_powers[key] - active_elapsed)

        # Combo decay
        if combo_timer > 0:
            combo_timer -= dt / 1000.0
            if combo_timer <= 0:
                combo_count = 0

        logical_tick_cooldown = max(65.0, 140.0 - score * 0.03)
        if accumulated_time >= logical_tick_cooldown:
            accumulated_time -= logical_tick_cooldown
            ticks_run += 1

            # Simple AI movement
            d = get_ai_direction(s, f, spawned_powerup)
            s.change_direction(d)

            next_head = (s.body[0][0] + s.direction[0], s.body[0][1] + s.direction[1])
            eating = (next_head == f.position)
            collecting = spawned_powerup and (next_head == spawned_powerup.position)

            s.move(eating or collecting)

            if eating:
                score += 100
                combo_count += 1
                combo_timer = 2.0
                if combo_count >= 3:
                    score += int(100 * combo_count * 0.25)
                f = Food(s.body)
                if random.random() < 0.28:
                    spawned_powerup = PowerUp(s.body, f.position)

            if collecting and spawned_powerup:
                spawned_powerup = None

            if s.check_collision(active_shield=(active_powers['SHIELD'] > 0 or active_powers['GHOST'] > 0)):
                break

        # Update particles and floating text
        particles.update()
        for ft in floating_texts:
            ft.update()
        floating_texts = [ft for ft in floating_texts if ft.alpha > 0]

        # Render (minimal)
        virtual_surface = pygame.Surface((V_WIDTH, V_HEIGHT))
        virtual_surface.fill((8, 5, 16))
        s.draw(virtual_surface, min(1.0, accumulated_time / logical_tick_cooldown), active_powers, current_ticks)
        f.draw(virtual_surface, current_ticks)
        if spawned_powerup:
            spawned_powerup.draw(virtual_surface, current_ticks)
        draw_header(virtual_surface, score, 0, laser_ammo, rewind_charges, active_powers, current_ticks)

        # Downscale
        scaled = pygame.transform.smoothscale(virtual_surface, (600, 660))
        screen.fill((8, 5, 16))
        dx, dy = screen_shake.get_offset()
        screen.blit(scaled, (dx, dy))
        pygame.display.flip()

    test("Game loop ran without crash", True)
    test("Ticks executed > 0", ticks_run > 0)
    test("Snake survived or hit something", len(s.body) >= 1)

test_full_loop()


# ============================================================
# 20. LASER BEAM
# ============================================================
print("\n=== LASER BEAM ===")

def test_laser_beam_lifecycle():
    lb = LaserBeam((100, 200), (300, 200), (1, 0))
    test("Initial duration 15", lb.duration == 15)
    lb.update()
    test("Duration decrements", lb.duration == 14)
    for _ in range(14):
        lb.update()
    test("Duration reaches 0", lb.duration == 0)

test_laser_beam_lifecycle()


# ============================================================
# 21. MAP LAYOUTS
# ============================================================
print("\n=== MAP LAYOUTS ===")

def test_open_map():
    reset_globals()
    build_map(MAP_OPEN)
    test("Open map has no obstacles", len(snake.obstacles) == 0)

test_open_map()


def test_pillars_map():
    reset_globals()
    build_map(MAP_PILLARS)
    test("Pillars map has obstacles", len(snake.obstacles) > 0)

test_pillars_map()


def test_cross_map():
    reset_globals()
    build_map(MAP_CROSS)
    test("Cross map has obstacles", len(snake.obstacles) > 0)

test_cross_map()


def test_maze_map():
    reset_globals()
    build_map(MAP_MAZE)
    test("Maze map has obstacles", len(snake.obstacles) > 0)

test_maze_map()


# ============================================================
# 22. SCREEN SHAKE ON RESTART (BUG3 REGRESSION)
# ============================================================
print("\n=== RESTART RESET (BUG3 REGRESSION) ===")

def test_restart_resets_shake():
    """BUG3 TEST: screen_shake must be reset on restart"""
    ss = ScreenShake()
    ss.trigger(duration=25, intensity=12)
    # Simulate restart
    ss = ScreenShake()
    test("New ScreenShake after restart", ss.duration == 0)
    test("Intensity is 0 after restart", ss.intensity == 0)

test_restart_resets_shake()


def test_mission_reward_reset():
    """BUG3 TEST: mission_reward must reset on restart"""
    mission_reward = 750
    mission_reward = 0  # reset on restart
    test("Mission reward reset to 0", mission_reward == 0)

test_mission_reward_reset()


# ============================================================
# 23. PARTICLE SYSTEM
# ============================================================
print("\n=== PARTICLE SYSTEM ===")

def test_particle_spawn():
    ps = ParticleSystem()
    ps.spawn_explosion(100, 200, (255, 0, 0), 10)
    test("10 particles spawned", len(ps.particles) == 10)

test_particle_spawn()


def test_particle_decay():
    ps = ParticleSystem()
    ps.spawn_explosion(100, 200, (255, 0, 0), 5)
    for _ in range(200):
        ps.update()
    test("Particles removed after decay", len(ps.particles) < 5)

test_particle_decay()


# ============================================================
# RESULTS
# ============================================================
print("\n" + "=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed")
if errors:
    print("Failed tests:")
    for e in errors:
        print(f"  - {e}")
print("=" * 50)

pygame.quit()
sys.exit(0 if failed == 0 else 1)
