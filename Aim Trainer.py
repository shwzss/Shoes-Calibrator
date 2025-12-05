# Aim Calibrator Full Application
# Features: FPS/TPP modes, controller mapping, multi‑game settings, short/long range, infinite trainer, explanations
# NOTE: This is a standalone training tool. It does NOT modify games, read memory, or automate aim.

import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 1280, 720
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Aim Calibration & Trainer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22)

# --------------------------- CONTROLLER SETUP ---------------------------
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

# Sensitivity Profiles per game
GAME_SETTINGS = {
    "Valorant": {"base_sens": 1.0, "notes": "Low sens favored. 0.25–0.5 typical."},
    "Fortnite": {"base_sens": 5.0, "notes": "Medium sens. Edit/build sensitivities separate."},
    "Warzone": {"base_sens": 7.0, "notes": "Higher sens for movement + aim assist tuning."},
    "CS2": {"base_sens": 1.5, "notes": "Classic low-sens tracking. eDPI matters most."},
    "Apex Legends": {"base_sens": 2.0, "notes": "Steady tracking + recoil control focus."}
}

current_game = "Valorant"
fps_mode = True  # True = first person, False = third person

# Calibration state
training_mode = False
trainer_infinite = False
short_range = True

# Crosshair
crosshair_size = 16
mouse_sens = 1.0
controller_sens = 1.0

# Target data
class Target:
    def __init__(self, x, y, size=32, speed=4):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.dx = speed
        self.dy = speed

    def move(self):
        self.x += self.dx
        self.y += self.dy

        if self.x < 0 or self.x > WIDTH - self.size:
            self.dx *= -1
        if self.y < 0 or self.y > HEIGHT - self.size:
            self.dy *= -1

    def draw(self, surf):
        pygame.draw.rect(surf, (255, 80, 80), (self.x, self.y, self.size, self.size))

# spawn initial target
current_target = Target(600, 300)

# --------------------------- DRAW HELPERS ---------------------------
def draw_text(text, x, y, color=(255,255,255)):
    surf = font.render(text, True, color)
    win.blit(surf, (x, y))


def draw_crosshair(x, y):
    # FPS mode: small precise crosshair
    if fps_mode:
        pygame.draw.line(win, (0,255,0), (x - crosshair_size, y), (x + crosshair_size, y), 2)
        pygame.draw.line(win, (0,255,0), (x, y - crosshair_size), (x, y + crosshair_size), 2)
    # TPP mode: bigger reticle circle
    else:
        pygame.draw.circle(win, (0,255,0), (x, y), crosshair_size, 2)

# --------------------------- MAIN LOOP ---------------------------
def main():
    global fps_mode, current_game, training_mode, trainer_infinite
    global mouse_sens, controller_sens, short_range, current_target

    running = True
    cx, cy = WIDTH // 2, HEIGHT // 2

    while running:
        dt = clock.tick(60) / 1000
        win.fill((20, 20, 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                # Toggle FPS/TPP
                if event.key == pygame.K_p:
                    fps_mode = not fps_mode
                # Cycle games
                if event.key == pygame.K_g:
                    games = list(GAME_SETTINGS.keys())
                    idx = games.index(current_game)
                    current_game = games[(idx + 1) % len(games)]
                # Toggle ranges
                if event.key == pygame.K_r:
                    short_range = not short_range
                # Start / stop trainer
                if event.key == pygame.K_t:
                    training_mode = not training_mode
                # Infinite mode
                if event.key == pygame.K_i:
                    trainer_infinite = not trainer_infinite
                # Adjust sensitivity
                if event.key == pygame.K_UP:
                    mouse_sens += 0.1
                if event.key == pygame.K_DOWN:
                    mouse_sens = max(0.1, mouse_sens - 0.1)
                if event.key == pygame.K_RIGHT:
                    controller_sens += 0.1
                if event.key == pygame.K_LEFT:
                    controller_sens = max(0.1, controller_sens - 0.1)

        # ------------------------------- CONTROLLER INPUT -------------------------------
        if joystick:
            axis_x = joystick.get_axis(2)   # Right stick horizontal
            axis_y = joystick.get_axis(3)   # Right stick vertical
            cx += axis_x * 40 * controller_sens
            cy += axis_y * 40 * controller_sens

        # Clamp aim reticle
        cx = max(0, min(WIDTH, cx))
        cy = max(0, min(HEIGHT, cy))

        # Move target in trainer
        if training_mode or trainer_infinite:
            current_target.move()
            current_target.draw(win)

        # Detect hit
        if training_mode or trainer_infinite:
            mx, my = cx, cy
            if (current_target.x < mx < current_target.x + current_target.size and
                current_target.y < my < current_target.y + current_target.size):
                # Respawn if not infinite
                if not trainer_infinite:
                    current_target = Target(
                        200 if short_range else 600,
                        200 if short_range else 400,
                        size=28 if short_range else 40,
                        speed=4 if short_range else 7
                    )

        # Crosshair
        draw_crosshair(cx, cy)

        # UI / Settings
        draw_text(f"Mode: {'FPS' if fps_mode else 'TPP'} (P to toggle)", 20, 20)
        draw_text(f"Game Profile: {current_game} (G to cycle)", 20, 50)
        draw_text(f"Range: {'Short' if short_range else 'Long'} (R to toggle)", 20, 80)
        draw_text(f"Trainer: {'Active' if training_mode else 'Off'} (T to toggle)", 20, 110)
        draw_text(f"Infinite Trainer: {'ON' if trainer_infinite else 'OFF'} (I to toggle)", 20, 140)
        draw_text(f"Mouse Sens: {mouse_sens:.2f} (UP/DOWN)", 20, 170)
        draw_text(f"Controller Sens: {controller_sens:.2f} (LEFT/RIGHT)", 20, 200)

        game_info = GAME_SETTINGS[current_game]
        draw_text(f"Recommended Sens: {game_info['base_sens']}", 20, 240)
        draw_text(f"Tip: {game_info['notes']}", 20, 270)

        draw_text("Hit targets precisely to measure ideal sensitivity.", 20, HEIGHT - 60)
        draw_text("Lower sens = precision, Higher sens = speed.", 20, HEIGHT - 30)

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
