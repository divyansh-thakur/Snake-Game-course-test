# Project Context & Documentation: Neon Snake

This file serves as the context and documentation register for the Neon Snake project, detailing the architecture, features, testing suite, and development log.

---

## 🏗️ Architecture: Native Desktop System Software

The project has been transitioned into a high-performance, native desktop system software utilizing Pygame. To overcome Pygame's basic rendering limitations and jagged edges, the game employs **Supersampling Anti-Aliasing (SSAA)**.

```
                  ┌──────────────────────────────┐
                  │      [High-Res Canvas]       │
                  │   Renders at 2x resolution   │
                  │        (1200 x 1320)         │
                  └──────────────┬───────────────┘
                                 │
                                 ▼ (Downsampled via bilinear smoothscale)
                  ┌──────────────────────────────┐
                  │     [Native Display Window]  │
                  │     Sharp, anti-aliased view │
                  │         (600 x 660)          │
                  └──────────────────────────────┘
```

- **Main File:** [snake.py](file:///Users/ellen/gemini%20Course/snake.py)
- **Technologies:** Pygame (GUI & Double Buffering), Audio Synthesizer, supersampling scale math.
- **Dependencies:** Listed in [requirements.txt](file:///Users/ellen/gemini%20Course/requirements.txt) (`pygame>=2.0.0`). Runs in `.venv`.

---

## ✨ Features (Desktop Mode)

### 🎨 Visual Polish (High-End Graphics)
- **Supersampling (SSAA):** The game renders all vector grids, glows, text, and entities to a `1200x1320` virtual canvas and uses Pygame's bilinear `smoothscale` downsampling filter to output a clean `600x660` window, completely removing pixelated, jagged lines.
- **Vaporwave Sunset Horizon:** Moving horizontal grid slices and horizontal slits inside a neon sun.
- **Perspective scrolling:** 3D diagonal grid scrolling simulation to provide depth and movement context.
- **Screen Shake Feedback:** Responsive board offsets when using the laser or crashing.
- **Animated Liquid Snake:** Sub-grid render interpolation, body size tapering, and custom-positioned animated eyes.

### ⚡ Creative Power-Ups & Mechanics
1. **⌛ Time Rewind Charge (Magenta Hourglass):** 
   - **How it works:** Spawns a glowing hourglass icon on the map. Collecting it awards 1 Time Charge.
   - **Temporal Mechanics:** If the snake crashes, a prompt appears allowing you to press `Backspace`. This plays a rewinding animation (running history buffers backward at high speed with VHS tracking distortions and audio sweep sweeps) and restores the state of the board from 3 seconds ago, letting you avoid death!
2. **🔋 Plasma Laser Blaster (Orange Battery):** 
   - **How it works:** Spawns on the board, giving you 3 Plasma Ammo. Pressing `Space` fires a thick, glowing orange laser beam.
   - **Vaporization Physics:** The laser vaporizes obstacles in your path or cuts off your own tail segments to prevent self-collisions, accompanied by high-quality particle bursts.
3. **🛡️ Shield (Cyan Circle):** 
   - **How it works:** Protects the snake from all collisions (walls, obstacles, and tail) and automatically wraps movement around screen edges.
4. **⚡ Speed Boost (Yellow Bolt):** 
   - **How it works:** Increases snake speed by 1.7x and doubles all score rewards.
5. **⏳ Slow-Mo (Purple Hourglass):** 
   - **How it works:** Slows down physics by 50% to navigate dense maze paths.
6. **✂️ Body Shrinker (Green Arrow):** 
   - **How it works:** Slices off 30% of the tail length instantly.

### 🧱 Selectable Arena Layouts
Selectable on the main menu using `1`, `2`, `3`, or `4`:
- **[1] Open Arena:** Clean grid workspace.
- **[2] Pillars:** 4 large glowing corner barrier towers.
- **[3] The Cross:** Central wall barricade divide.
- **[4] Maze:** Inner-outer wall matrix.

---

## 🧪 Testing Suite

Automated game logic test suite is located in **[test_snake.py](file:///Users/ellen/gemini%20Course/test_snake.py)**.

### How to run tests:
```bash
.venv/bin/python test_snake.py
```

### Covered Test Cases:
- `test_snake_initial_state`: Confirms default grid start coordinates and segment size.
- `test_direction_change_valid`: Validates basic turn updates.
- `test_direction_change_invalid_reverse`: Verifies that reversing directly into yourself is blocked.
- `test_input_buffering_queue`: Tests double-input queuing.
- `test_boundary_collision`: Verifies boundary crash detection.
- `test_self_collision`: Verifies self-tail crash detection.
- `test_shield_invulnerability`: Verifies that when the shield is active, self-collisions do not trigger crash states.
- `test_eating_and_growth`: Tests length growth and tail retention during eating.

---

## 📝 Change Log

### v6.0 (Current)
- Replaced the browser HTTP system launcher with a native desktop GUI system software launcher (`snake.py`).
- Implemented **Supersampling (SSAA)** to eradicate pixelation and jagged graphics.
- Added two highly addictive game systems: **Plasma Laser Cannon** (Space key to vaporize self-tail/obstacles) and **Temporal Rewind** (Backspace key to rewind the last 3 seconds of gameplay on crash).
- Created visual overlays for VHS rewinds (distortion lines, tracking text, audio sweeps) and laser beam paths.
- Updated `test_snake.py` and `CONTEXT.md` to document the new active shield mechanics and test coverage.

### v5.0
- Added project documentation (`CONTEXT.md`).
- Created unit test file (`test_snake.py`).
- Fixed browser overlay button focus lock.

### v4.0
- Added vaporwave horizon, 3D grids, screen shake, scanlines, and ripples.
- Added Pillars, Cross, Maze maps.
- Added Shield, Speed, Slow-mo, and Shrink power-ups.

### v3.0
- Built the HTTP server + Browser client.

### v2.0
- Added lime colors, game over menus, score popups, and persistent high scores.

### v1.0
- Initial basic grid implementation.
