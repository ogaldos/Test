import math
import pygame
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple


# === CONFIGURACIÓN GLOBAL ===
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
PADDLE_WIDTH = 110
PADDLE_HEIGHT = 20
PADDLE_SPEED = 7
PADDLE_SPEED_INCREMENT = 0.6
PADDLE_WIDTH_DECREMENT = 8
PADDLE_MIN_WIDTH = 70
BALL_SIZE = 16
BALL_SPEED = 5.0
BALL_SPEED_INCREMENT_LEVEL = 0.35
BALL_SPEED_INCREMENT_BRICK = 0.15
BRICKS_PER_SPEEDUP = 12
BRICK_ROWS = 6
BRICK_COLUMNS = 10
BRICK_WIDTH = 70
BRICK_HEIGHT = 25
BRICK_PADDING = 6
BRICK_TOP_OFFSET = 80
INITIAL_LIVES = 3


Color = Tuple[int, int, int]
WHITE: Color = (255, 255, 255)
BLACK: Color = (0, 0, 0)
GREY: Color = (40, 40, 40)
RED: Color = (200, 50, 50)
GREEN: Color = (60, 180, 75)
BLUE: Color = (66, 135, 245)
YELLOW: Color = (240, 230, 90)
ORANGE: Color = (255, 140, 0)
PURPLE: Color = (180, 120, 255)

BRICK_PALETTE: List[Color] = [
    (255, 99, 71),
    (255, 165, 0),
    (255, 215, 0),
    (144, 238, 144),
    (65, 105, 225),
    (186, 85, 211),
    (255, 182, 193),
    (135, 206, 235),
    (173, 216, 230),
    (152, 251, 152),
]

POWERUP_TYPES = [
    "slow",
    "widen",
    "multiball",
    "sticky",
    "laser",
    "1up",
]

POWERUP_COLORS: Dict[str, Color] = {
    "slow": (120, 200, 255),
    "widen": (255, 200, 80),
    "multiball": (200, 255, 200),
    "sticky": (255, 120, 200),
    "laser": (255, 80, 80),
    "1up": (120, 255, 120),
}

POWERUP_DURATION_MS: Dict[str, int] = {
    "slow": 8000,
    "widen": 10000,
    "sticky": 8000,
    "laser": 8000,
}


def adjust_color(color: Color, factor: float) -> Color:
    return tuple(int(clamp(channel * factor, 0, 255)) for channel in color)  # type: ignore


def get_row_color(row: int) -> Color:
    base_color = BRICK_PALETTE[row % len(BRICK_PALETTE)]
    cycle = row // len(BRICK_PALETTE)
    if cycle == 0:
        return base_color
    factor = 0.9 + 0.08 * (cycle % 4)
    return adjust_color(base_color, factor)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


@dataclass
class Paddle:
    rect: pygame.Rect
    speed: int = PADDLE_SPEED

    def move(self, direction: int) -> None:
        self.rect.x += direction * self.speed
        self.rect.x = int(clamp(self.rect.x, 0, WINDOW_WIDTH - self.rect.width))

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=6)


@dataclass
class Ball:
    rect: pygame.Rect
    velocity: pygame.Vector2
    attached: bool = False
    attachment_offset: int = 0

    def update(self) -> None:
        self.rect.x += int(self.velocity.x)
        self.rect.y += int(self.velocity.y)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.ellipse(surface, WHITE, self.rect)

    def reset(self, position: Tuple[int, int]) -> None:
        self.rect.center = position
        self.velocity = pygame.Vector2(BALL_SPEED, -BALL_SPEED)
        self.attached = False
        self.attachment_offset = 0

    def set_speed(self, speed: float) -> None:
        if self.velocity.length() == 0:
            return
        self.velocity = self.velocity.normalize() * speed

    def attach_to_paddle(self, paddle: Paddle) -> None:
        self.attached = True
        self.attachment_offset = self.rect.centerx - paddle.rect.centerx
        self.velocity.update(0, 0)

    def follow_paddle(self, paddle: Paddle) -> None:
        self.rect.centerx = paddle.rect.centerx + self.attachment_offset
        self.rect.bottom = paddle.rect.top - 1

    def release_from_paddle(self, speed: float) -> None:
        self.attached = False
        self.velocity = pygame.Vector2(0, -speed)


@dataclass
class Brick:
    rect: pygame.Rect
    color: Color
    hit_points: int = 1
    destructible: bool = True
    explosive: bool = False

    def draw(self, surface: pygame.Surface) -> None:
        color = self.color
        if not self.destructible:
            color = (90, 90, 120)
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, BLACK, self.rect, width=2, border_radius=4)
        if self.explosive:
            center = self.rect.center
            pygame.draw.circle(surface, (255, 255, 255), center, self.rect.width // 6)


@dataclass
class PowerUp:
    rect: pygame.Rect
    kind: str
    speed: int = 3

    def update(self) -> None:
        self.rect.y += self.speed

    def draw(self, surface: pygame.Surface) -> None:
        color = POWERUP_COLORS.get(self.kind, WHITE)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        text = str.upper(self.kind[0])
        font = pygame.font.SysFont("arial", 18, bold=True)
        label = font.render(text, True, BLACK)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)


@dataclass
class LaserShot:
    rect: pygame.Rect
    speed: int = -12

    def update(self) -> None:
        self.rect.y += self.speed

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=2)


class ArkanoidGame:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Arkanoid - Python Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)
        self.big_font = pygame.font.SysFont("arial", 56, bold=True)

        paddle_rect = pygame.Rect(
            (WINDOW_WIDTH - PADDLE_WIDTH) // 2,
            WINDOW_HEIGHT - 60,
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
        )
        self.paddle = Paddle(paddle_rect)

        self.lives = INITIAL_LIVES
        self.score = 0
        self.level = 1
        self.bricks: List[Brick] = []
        self.balls: List[Ball] = []
        self.powerups: List[PowerUp] = []
        self.laser_shots: List[LaserShot] = []
        self.active_effects: Dict[str, int] = {}
        self.ball_speed = BALL_SPEED
        self.bricks_destroyed = 0
        self.paddle_speed = PADDLE_SPEED
        self.paddle_base_width = PADDLE_WIDTH
        self.sticky_enabled = False
        self.ball_speed_modifier = 1.0
        self.paddle_width_modifier = 1.0
        self.last_shot_time = 0
        self.laser_cooldown = 350
        self.running = True
        self.game_over = False

        self.create_level()
        self.reset_balls()

    # === CREACIÓN DE NIVELES Y ENTORNO ===
    def create_level(self) -> None:
        self.bricks.clear()
        self.powerups.clear()
        self.laser_shots.clear()
        self.bricks_destroyed = 0
        rng = random.Random(self.level)
        available_rows = (WINDOW_HEIGHT - BRICK_TOP_OFFSET - 200) // (
            BRICK_HEIGHT + BRICK_PADDING
        )
        rows = clamp(BRICK_ROWS + self.level - 1, 4, available_rows)
        pattern_type = (self.level - 1) % 5

        for row in range(int(rows)):
            base_color = get_row_color(row)
            for col in range(BRICK_COLUMNS):
                if not self.should_place_brick(pattern_type, row, col):
                    continue
                x = 40 + col * (BRICK_WIDTH + BRICK_PADDING)
                y = BRICK_TOP_OFFSET + row * (BRICK_HEIGHT + BRICK_PADDING)
                rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
                hit_points = 1 + (self.level - 1) // 4
                destructible = True
                explosive = False
                color = base_color

                if pattern_type == 2 and (col in (0, BRICK_COLUMNS - 1) or row % 3 == 0):
                    hit_points = 2 + (self.level // 5)
                if pattern_type == 3 and (row + col) % 6 == 0:
                    destructible = False
                    color = (120, 120, 140)
                if pattern_type == 4 and (row + col) % 5 == 0:
                    explosive = True
                    color = adjust_color(color, 1.2)
                if rng.random() < 0.08:
                    hit_points += 1

                self.bricks.append(Brick(rect, color, int(hit_points), destructible, explosive))

        self.apply_level_scaling()

    def should_place_brick(self, pattern_type: int, row: int, col: int) -> bool:
        if pattern_type == 0:
            return True
        if pattern_type == 1:
            return (row + col) % 3 != 0
        if pattern_type == 2:
            if row % 2 == 0:
                return True
            return col not in (row % BRICK_COLUMNS, BRICK_COLUMNS - 1 - (row % BRICK_COLUMNS))
        if pattern_type == 3:
            return not ((row % 4 == 1) and (col % 2 == 0))
        if pattern_type == 4:
            return (row + col) % 2 == 0 or row % 3 == 0
        return True

    def apply_level_scaling(self) -> None:
        self.ball_speed = BALL_SPEED + (self.level - 1) * BALL_SPEED_INCREMENT_LEVEL
        self.refresh_ball_speeds()

        self.paddle_speed = int(PADDLE_SPEED + (self.level - 1) * PADDLE_SPEED_INCREMENT)
        self.paddle.speed = self.paddle_speed

        self.paddle_base_width = max(
            PADDLE_MIN_WIDTH,
            PADDLE_WIDTH - (self.level - 1) * PADDLE_WIDTH_DECREMENT,
        )
        self.apply_paddle_width()

    def update_paddle_width(self, width: float) -> None:
        center = self.paddle.rect.centerx
        self.paddle.rect.width = int(width)
        self.paddle.rect.centerx = int(
            clamp(
                center,
                self.paddle.rect.width // 2,
                WINDOW_WIDTH - self.paddle.rect.width // 2,
            )
        )

    def apply_paddle_width(self) -> None:
        width = self.paddle_base_width * self.paddle_width_modifier
        self.update_paddle_width(width)

    def current_ball_speed(self) -> float:
        return self.ball_speed * self.ball_speed_modifier

    def refresh_ball_speeds(self) -> None:
        speed = self.current_ball_speed()
        for ball in self.balls:
            if not ball.attached:
                ball.set_speed(speed)

    def reset_balls(self) -> None:
        self.balls.clear()
        ball_rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        ball_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80)
        ball_velocity = pygame.Vector2(0, -self.current_ball_speed())
        ball = Ball(ball_rect, ball_velocity)
        if self.sticky_enabled:
            ball.attach_to_paddle(self.paddle)
            ball.follow_paddle(self.paddle)
        self.balls.append(ball)

    # === BUCLE PRINCIPAL DEL JUEGO ===
    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            if not self.game_over:
                self.update_game()
            self.draw()
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    # === ACTUALIZACIÓN DE LOS ELEMENTOS ===
    def update_game(self) -> None:
        self.cleanup_effects()
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1
        self.paddle.speed = self.paddle_speed
        self.paddle.move(direction)

        if self.sticky_enabled and keys[pygame.K_SPACE]:
            for ball in self.balls:
                if ball.attached:
                    ball.release_from_paddle(self.current_ball_speed())

        for ball in self.balls:
            if ball.attached:
                ball.follow_paddle(self.paddle)
            else:
                ball.update()

        self.handle_collisions()
        self.update_powerups()
        self.update_lasers(keys)

        if not self.bricks:
            self.level += 1
            self.create_level()
            self.apply_paddle_width()
            self.reset_balls()

    def handle_collisions(self) -> None:
        for ball in list(self.balls):
            self.handle_ball_collisions(ball)

    def handle_ball_collisions(self, ball: Ball) -> None:
        if ball.attached:
            return

        if ball.rect.left <= 0:
            ball.rect.left = 0
            ball.velocity.x = abs(ball.velocity.x)
        elif ball.rect.right >= WINDOW_WIDTH:
            ball.rect.right = WINDOW_WIDTH
            ball.velocity.x = -abs(ball.velocity.x)

        if ball.rect.top <= 0:
            ball.rect.top = 0
            ball.velocity.y = abs(ball.velocity.y)
        if ball.rect.top > WINDOW_HEIGHT:
            self.remove_ball(ball)
            return

        if ball.rect.colliderect(self.paddle.rect) and ball.velocity.y > 0:
            offset = (ball.rect.centerx - self.paddle.rect.centerx) / (
                self.paddle.rect.width / 2
            )
            offset = clamp(offset, -1, 1)
            direction = pygame.Vector2(offset, -1).normalize()
            ball.velocity = direction * self.current_ball_speed()
            ball.rect.bottom = self.paddle.rect.top - 1
            if self.sticky_enabled:
                ball.attach_to_paddle(self.paddle)
                ball.follow_paddle(self.paddle)

        iterations = 0
        while iterations < 6:
            hit_brick = next((b for b in self.bricks if b.rect.colliderect(ball.rect)), None)
            if not hit_brick:
                break
            self.resolve_ball_brick_collision(ball, hit_brick)
            iterations += 1

    def resolve_ball_brick_collision(self, ball: Ball, brick: Brick) -> None:
        overlap_left = ball.rect.right - brick.rect.left
        overlap_right = brick.rect.right - ball.rect.left
        overlap_top = ball.rect.bottom - brick.rect.top
        overlap_bottom = brick.rect.bottom - ball.rect.top
        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

        if min_overlap == overlap_left:
            ball.rect.right = brick.rect.left - 1
            ball.velocity.x = -abs(ball.velocity.x)
        elif min_overlap == overlap_right:
            ball.rect.left = brick.rect.right + 1
            ball.velocity.x = abs(ball.velocity.x)
        elif min_overlap == overlap_top:
            ball.rect.bottom = brick.rect.top - 1
            ball.velocity.y = -abs(ball.velocity.y)
        else:
            ball.rect.top = brick.rect.bottom + 1
            ball.velocity.y = abs(ball.velocity.y)

        if not brick.destructible:
            return

        brick.hit_points -= 1
        if brick.hit_points <= 0:
            self.destroy_brick(brick)

    def destroy_brick(self, brick: Brick) -> None:
        if brick not in self.bricks:
            return
        self.bricks.remove(brick)
        self.score += 10 * self.level
        self.bricks_destroyed += 1
        if brick.explosive:
            self.trigger_explosion(brick)
        if self.bricks_destroyed % BRICKS_PER_SPEEDUP == 0:
            self.increase_ball_speed(BALL_SPEED_INCREMENT_BRICK)
        self.maybe_spawn_powerup(brick)

    def increase_ball_speed(self, amount: float) -> None:
        self.ball_speed += amount
        self.refresh_ball_speeds()

    def trigger_explosion(self, brick: Brick) -> None:
        radius = BRICK_WIDTH * 1.5
        center = pygame.Vector2(brick.rect.center)
        for other in list(self.bricks):
            if other is brick:
                continue
            if not other.destructible:
                continue
            if pygame.Vector2(other.rect.center).distance_to(center) <= radius:
                other.hit_points = 0
                self.destroy_brick(other)

    def maybe_spawn_powerup(self, brick: Brick) -> None:
        drop_chance = 0.18 + min(0.02 * self.level, 0.12)
        if random.random() > drop_chance:
            return
        kind = random.choice(POWERUP_TYPES)
        size = 34
        rect = pygame.Rect(0, 0, size, size)
        rect.center = brick.rect.center
        self.powerups.append(PowerUp(rect, kind))

    def update_powerups(self) -> None:
        for powerup in list(self.powerups):
            powerup.update()
            if powerup.rect.top > WINDOW_HEIGHT:
                self.powerups.remove(powerup)
                continue
            if powerup.rect.colliderect(self.paddle.rect):
                self.powerups.remove(powerup)
                self.apply_powerup(powerup.kind)

    def update_lasers(self, keys: pygame.key.ScancodeWrapper) -> None:
        if self.is_effect_active("laser"):
            now = pygame.time.get_ticks()
            if keys[pygame.K_SPACE] and now - self.last_shot_time > self.laser_cooldown:
                self.spawn_laser_shots()
                self.last_shot_time = now

        for shot in list(self.laser_shots):
            shot.update()
            if shot.rect.bottom < 0:
                self.laser_shots.remove(shot)
                continue
            for brick in list(self.bricks):
                if not brick.destructible:
                    continue
                if shot.rect.colliderect(brick.rect):
                    self.destroy_brick(brick)
                    if shot in self.laser_shots:
                        self.laser_shots.remove(shot)
                    break

    def spawn_laser_shots(self) -> None:
        left_rect = pygame.Rect(0, 0, 6, 20)
        right_rect = pygame.Rect(0, 0, 6, 20)
        left_rect.midbottom = (self.paddle.rect.left + 10, self.paddle.rect.top)
        right_rect.midbottom = (self.paddle.rect.right - 10, self.paddle.rect.top)
        self.laser_shots.append(LaserShot(left_rect))
        self.laser_shots.append(LaserShot(right_rect))

    def apply_powerup(self, kind: str) -> None:
        if kind == "slow":
            self.ball_speed_modifier = 0.7
            self.refresh_ball_speeds()
            self.set_effect_timer(kind)
        elif kind == "widen":
            self.paddle_width_modifier = min(1.8, self.paddle_width_modifier + 0.35)
            self.apply_paddle_width()
            self.set_effect_timer(kind)
        elif kind == "multiball":
            self.spawn_multiball()
        elif kind == "sticky":
            self.sticky_enabled = True
            for ball in self.balls:
                if ball.velocity.y > 0 and ball.rect.bottom >= self.paddle.rect.top:
                    ball.attach_to_paddle(self.paddle)
                    ball.follow_paddle(self.paddle)
            self.set_effect_timer(kind)
        elif kind == "laser":
            self.last_shot_time = 0
            self.set_effect_timer(kind)
        elif kind == "1up":
            self.lives += 1

    def spawn_multiball(self) -> None:
        if not self.balls:
            return
        template = self.balls[0]
        if template.attached:
            template.release_from_paddle(self.current_ball_speed())
        for angle in (-20, 20):
            if len(self.balls) >= 6:
                break
            new_rect = template.rect.copy()
            new_rect.centerx += -10 if angle < 0 else 10
            velocity = template.velocity.rotate(angle)
            if velocity.length() == 0:
                velocity = pygame.Vector2(0, -self.current_ball_speed())
            else:
                velocity = velocity.normalize() * self.current_ball_speed()
            self.balls.append(Ball(new_rect, velocity))

    def set_effect_timer(self, kind: str) -> None:
        duration = POWERUP_DURATION_MS.get(kind)
        if duration is None:
            return
        self.active_effects[kind] = pygame.time.get_ticks() + duration

    def is_effect_active(self, kind: str) -> bool:
        expiry = self.active_effects.get(kind)
        if expiry is None:
            return False
        if pygame.time.get_ticks() >= expiry:
            self.end_effect(kind)
            return False
        return True

    def cleanup_effects(self) -> None:
        now = pygame.time.get_ticks()
        expired = [kind for kind, expiry in self.active_effects.items() if expiry <= now]
        for kind in expired:
            self.end_effect(kind)

    def end_effect(self, kind: str) -> None:
        if kind not in self.active_effects:
            return
        del self.active_effects[kind]
        if kind == "slow":
            self.ball_speed_modifier = 1.0
            self.refresh_ball_speeds()
        elif kind == "widen":
            self.paddle_width_modifier = 1.0
            self.apply_paddle_width()
        elif kind == "sticky":
            self.sticky_enabled = False
            for ball in self.balls:
                if ball.attached:
                    ball.release_from_paddle(self.current_ball_speed())
        elif kind == "laser":
            self.laser_shots.clear()

    def remove_ball(self, ball: Ball) -> None:
        if ball in self.balls:
            self.balls.remove(ball)
        if not self.balls:
            self.lose_life()

    def lose_life(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
            self.balls.clear()
            return
        self.reset_balls()
        self.paddle.rect.centerx = WINDOW_WIDTH // 2

    # === REPRESENTACIÓN VISUAL ===
    def draw(self) -> None:
        self.screen.fill(GREY)
        self.draw_background_grid()
        for brick in self.bricks:
            brick.draw(self.screen)
        for powerup in self.powerups:
            powerup.draw(self.screen)
        for shot in self.laser_shots:
            shot.draw(self.screen)
        self.paddle.draw(self.screen)
        for ball in self.balls:
            ball.draw(self.screen)
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self) -> None:
        score_surface = self.font.render(f"Puntaje: {self.score}", True, WHITE)
        lives_surface = self.font.render(f"Vidas: {self.lives}", True, WHITE)
        level_surface = self.font.render(f"Nivel: {self.level}", True, WHITE)
        self.screen.blit(score_surface, (20, 20))
        self.screen.blit(lives_surface, (WINDOW_WIDTH - 120, 20))
        self.screen.blit(level_surface, (WINDOW_WIDTH // 2 - 50, 20))

        effect_texts = []
        if self.is_effect_active("slow"):
            effect_texts.append("Slow")
        if self.is_effect_active("widen"):
            effect_texts.append("Ancho")
        if self.is_effect_active("sticky"):
            effect_texts.append("Pegajosa")
        if self.is_effect_active("laser"):
            effect_texts.append("Láser")
        if effect_texts:
            effects_surface = self.font.render(
                " | ".join(effect_texts), True, WHITE
            )
            self.screen.blit(effects_surface, (20, 50))

        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            game_over_surface = self.big_font.render("GAME OVER", True, WHITE)
            score_surface = self.font.render("Pulsa ESPACIO para reiniciar", True, WHITE)
            self.screen.blit(
                game_over_surface,
                (
                    (WINDOW_WIDTH - game_over_surface.get_width()) // 2,
                    WINDOW_HEIGHT // 2 - 60,
                ),
            )
            self.screen.blit(
                score_surface,
                (
                    (WINDOW_WIDTH - score_surface.get_width()) // 2,
                    WINDOW_HEIGHT // 2 + 10,
                ),
            )
            self.handle_restart_input()

    def handle_restart_input(self) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.reset_game()

    def reset_game(self) -> None:
        self.lives = INITIAL_LIVES
        self.score = 0
        self.level = 1
        self.game_over = False
        self.active_effects.clear()
        self.ball_speed = BALL_SPEED
        self.ball_speed_modifier = 1.0
        self.paddle_width_modifier = 1.0
        self.paddle_speed = PADDLE_SPEED
        self.sticky_enabled = False
        self.create_level()
        self.paddle.rect.centerx = WINDOW_WIDTH // 2
        self.reset_balls()

    def draw_background_grid(self) -> None:
        grid_color = (60, 60, 60)
        tile_size = 40
        for x in range(0, WINDOW_WIDTH, tile_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, tile_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (WINDOW_WIDTH, y))


def main() -> None:
    game = ArkanoidGame()
    game.run()


if __name__ == "__main__":
    main()
