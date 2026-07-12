import unittest
import os
import sys

# Configure SDL to run in dummy/headless mode for tests
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Import game elements
from snake import Snake, Food, COLS, ROWS

class TestSnakeGameLogic(unittest.TestCase):
    def setUp(self):
        self.snake = Snake()
        # Reset snake direction queue and coordinates
        self.snake.body = [(15, 15), (15, 16), (15, 17)]
        self.snake.direction = (0, -1) # UP
        self.snake.direction_queue = []

    def test_snake_initial_state(self):
        self.assertEqual(self.snake.body[0], (15, 15))
        self.assertEqual(len(self.snake.body), 3)
        self.assertEqual(self.snake.direction, (0, -1))

    def test_direction_change_valid(self):
        # Moving UP (0, -1), turning RIGHT (1, 0) should succeed
        self.snake.change_direction((1, 0))
        self.snake.move(is_eating=False)
        self.assertEqual(self.snake.direction, (1, 0))
        self.assertEqual(self.snake.body[0], (16, 15))

    def test_direction_change_invalid_reverse(self):
        # Moving UP (0, -1), turning DOWN (0, 1) directly should be blocked
        self.snake.change_direction((0, 1))
        self.snake.move(is_eating=False)
        self.assertEqual(self.snake.direction, (0, -1)) # Direction stays UP
        self.assertEqual(self.snake.body[0], (15, 14))

    def test_input_buffering_queue(self):
        # Moving UP (0, -1)
        # Queueing RIGHT (1, 0) then DOWN (0, 1) should buffer both
        self.snake.change_direction((1, 0))
        self.snake.change_direction((0, 1))
        
        # First move tick: consumes RIGHT
        self.snake.move(is_eating=False)
        self.assertEqual(self.snake.direction, (1, 0))
        
        # Second move tick: consumes DOWN
        self.snake.move(is_eating=False)
        self.assertEqual(self.snake.direction, (0, 1))

    def test_boundary_collision(self):
        # Teleport snake close to left boundary
        self.snake.body = [(0, 15), (1, 15), (2, 15)]
        self.snake.direction = (-1, 0) # LEFT
        self.assertFalse(self.snake.check_collision(active_shield=False))
        
        # Move out of bounds
        self.snake.move(is_eating=False)
        self.assertTrue(self.snake.check_collision(active_shield=False))

    def test_self_collision(self):
        # Create a self-intersecting snake shape
        self.snake.body = [(15, 15), (16, 15), (16, 16), (15, 16), (15, 15)]
        self.assertTrue(self.snake.check_collision(active_shield=False))

    def test_shield_invulnerability(self):
        # Even with self-intersection, shield active should make it safe
        self.snake.body = [(15, 15), (16, 15), (16, 16), (15, 16), (15, 15)]
        self.assertFalse(self.snake.check_collision(active_shield=True))

    def test_eating_and_growth(self):
        old_length = len(self.snake.body)
        # Simulate eating food
        self.snake.move(is_eating=True)
        # Length should increase by 1
        self.assertEqual(len(self.snake.body), old_length + 1)
        # Tail should not be popped
        self.assertEqual(self.snake.body[-1], (15, 17))

if __name__ == "__main__":
    unittest.main()
