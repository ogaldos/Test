import pygame
from dataclasses import dataclass
from typing import List, Tuple


# === CONFIGURACIÓN GLOBAL ===
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
PADDLE_WIDTH = 110
PADDLE_HEIGHT = 20
PADDLE_SPEED = 7
BALL_SIZE = 16
BALL_SPEED = 5
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

BRICK_PALETTE: List[Color] = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]


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

    def update(self) -> None:
        self.rect.x += int(self.velocity.x)
        self.rect.y += int(self.velocity.y)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.ellipse(surface, WHITE, self.rect)

    def reset(self, position: Tuple[int, int]) -> None:
        self.rect.center = position
        self.velocity = pygame.Vector2(BALL_SPEED, -BALL_SPEED)


@dataclass
class Brick:
    rect: pygame.Rect
    color: Color
    hit_points: int = 1

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        pygame.draw.rect(surface, BLACK, self.rect, width=2, border_radius=4)


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

        ball_rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        ball_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80)
        self.ball = Ball(ball_rect, pygame.Vector2(BALL_SPEED, -BALL_SPEED))

        self.lives = INITIAL_LIVES
        self.score = 0
        self.level = 1
        self.bricks: List[Brick] = []
        self.running = True
        self.game_over = False

        self.create_level()

    # === CREACIÓN DE NIVELES Y ENTORNO ===
    def create_level(self) -> None:
        self.bricks.clear()
        rows = min(BRICK_ROWS + self.level - 1, len(BRICK_PALETTE))
        for row in range(rows):
            color = BRICK_PALETTE[row % len(BRICK_PALETTE)]
            for col in range(BRICK_COLUMNS):
                x = 40 + col * (BRICK_WIDTH + BRICK_PADDING)
                y = BRICK_TOP_OFFSET + row * (BRICK_HEIGHT + BRICK_PADDING)
                rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
                hit_points = 1 + (self.level - 1) // len(BRICK_PALETTE)
                self.bricks.append(Brick(rect, color, hit_points))

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
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1
        self.paddle.move(direction)
        self.ball.update()

        self.handle_collisions()

    def handle_collisions(self) -> None:
        # Colisiones con paredes
        if self.ball.rect.left <= 0 or self.ball.rect.right >= WINDOW_WIDTH:
            self.ball.velocity.x *= -1
        if self.ball.rect.top <= 0:
            self.ball.velocity.y *= -1
        if self.ball.rect.top > WINDOW_HEIGHT:
            self.lose_life()
            return

        # Colisión con la paleta
        if self.ball.rect.colliderect(self.paddle.rect) and self.ball.velocity.y > 0:
            offset = (self.ball.rect.centerx - self.paddle.rect.centerx) / (self.paddle.rect.width / 2)
            offset = clamp(offset, -1, 1)
            self.ball.velocity.x = BALL_SPEED * offset * 1.2
            self.ball.velocity.y *= -1
            self.ball.rect.bottom = self.paddle.rect.top - 1

        # Colisiones con ladrillos
        hit_brick = None
        for brick in self.bricks:
            if brick.rect.colliderect(self.ball.rect):
                hit_brick = brick
                break

        if hit_brick:
            self.resolve_ball_brick_collision(hit_brick)

        if not self.bricks:
            self.level += 1
            self.create_level()
            self.ball.reset((WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80))

    def resolve_ball_brick_collision(self, brick: Brick) -> None:
        overlap_left = self.ball.rect.right - brick.rect.left
        overlap_right = brick.rect.right - self.ball.rect.left
        overlap_top = self.ball.rect.bottom - brick.rect.top
        overlap_bottom = brick.rect.bottom - self.ball.rect.top
        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

        if min_overlap == overlap_left:
            self.ball.rect.right = brick.rect.left - 1
            self.ball.velocity.x = -abs(self.ball.velocity.x)
        elif min_overlap == overlap_right:
            self.ball.rect.left = brick.rect.right + 1
            self.ball.velocity.x = abs(self.ball.velocity.x)
        elif min_overlap == overlap_top:
            self.ball.rect.bottom = brick.rect.top - 1
            self.ball.velocity.y = -abs(self.ball.velocity.y)
        else:
            self.ball.rect.top = brick.rect.bottom + 1
            self.ball.velocity.y = abs(self.ball.velocity.y)

        brick.hit_points -= 1
        if brick.hit_points <= 0:
            self.bricks.remove(brick)
            self.score += 10 * self.level

    def lose_life(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            self.ball.reset((WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80))
            self.paddle.rect.centerx = WINDOW_WIDTH // 2

    # === REPRESENTACIÓN VISUAL ===
    def draw(self) -> None:
        self.screen.fill(GREY)
        self.draw_background_grid()
        for brick in self.bricks:
            brick.draw(self.screen)
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self) -> None:
        score_surface = self.font.render(f"Puntaje: {self.score}", True, WHITE)
        lives_surface = self.font.render(f"Vidas: {self.lives}", True, WHITE)
        level_surface = self.font.render(f"Nivel: {self.level}", True, WHITE)
        self.screen.blit(score_surface, (20, 20))
        self.screen.blit(lives_surface, (WINDOW_WIDTH - 120, 20))
        self.screen.blit(level_surface, (WINDOW_WIDTH // 2 - 50, 20))

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
        self.create_level()
        self.ball.reset((WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80))
        self.paddle.rect.centerx = WINDOW_WIDTH // 2

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
