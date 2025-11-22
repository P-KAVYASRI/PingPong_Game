import pygame
import random
import sys

# Window size
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Pong')
    clock = pygame.time.Clock()

    started = False

    # paddles: x, y, width, height
    paddle_w, paddle_h = 7, 100
    paddle_1_rect = pygame.Rect(30, (SCREEN_HEIGHT - paddle_h) // 2, paddle_w, paddle_h)
    paddle_2_rect = pygame.Rect(SCREEN_WIDTH - 30 - paddle_w, (SCREEN_HEIGHT - paddle_h) // 2, paddle_w, paddle_h)

    paddle_1_move = 0.0
    paddle_2_move = 0.0

    # ball size and center it properly
    ball_size = 25
    ball_rect = pygame.Rect((SCREEN_WIDTH - ball_size) // 2, (SCREEN_HEIGHT - ball_size) // 2, ball_size, ball_size)

    # speed: fairly small base, we'll multiply by delta_time (ms)
    ball_accel_x = random.randint(2, 4) * 0.1
    ball_accel_y = random.randint(2, 4) * 0.1
    if random.choice((True, False)):
        ball_accel_x *= -1
    if random.choice((True, False)):
        ball_accel_y *= -1

    font = pygame.font.SysFont('Consolas', 30)

    while True:
        screen.fill(COLOR_BLACK)

        # Start screen
        if not started:
            text = font.render('Press Space to Start', True, COLOR_WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, text_rect)
            pygame.display.flip()
            # Minimal event loop while waiting to start
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    started = True
            clock.tick(60)
            continue

        delta_time = clock.tick(60)  # ms since last frame

        # events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Player 1
                if event.key == pygame.K_w:
                    paddle_1_move = -0.5
                if event.key == pygame.K_s:
                    paddle_1_move = 0.5
                # Player 2
                if event.key == pygame.K_UP:
                    paddle_2_move = -0.5
                if event.key == pygame.K_DOWN:
                    paddle_2_move = 0.5

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_s):
                    paddle_1_move = 0.0
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    paddle_2_move = 0.0

        # move paddles (scaled by delta_time)
        paddle_1_rect.top += paddle_1_move * delta_time
        paddle_2_rect.top += paddle_2_move * delta_time

        # clamp paddles to screen
        if paddle_1_rect.top < 0:
            paddle_1_rect.top = 0
        if paddle_1_rect.bottom > SCREEN_HEIGHT:
            paddle_1_rect.bottom = SCREEN_HEIGHT

        if paddle_2_rect.top < 0:
            paddle_2_rect.top = 0
        if paddle_2_rect.bottom > SCREEN_HEIGHT:
            paddle_2_rect.bottom = SCREEN_HEIGHT

        # ball-wall collisions (top & bottom)
        if ball_rect.top <= 0:
            ball_accel_y *= -1
            ball_rect.top = 0
        if ball_rect.bottom >= SCREEN_HEIGHT:
            ball_accel_y *= -1
            ball_rect.bottom = SCREEN_HEIGHT

        # ball out of bounds -> end game for now (you can implement scoring/reset instead)
        if ball_rect.left <= 0 or ball_rect.right >= SCREEN_WIDTH:
            # simple end: show message and quit
            end_text = font.render('Game Over - Ball out of bounds', True, COLOR_WHITE)
            end_rect = end_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(end_text, end_rect)
            pygame.display.flip()
            pygame.time.delay(1500)
            pygame.quit()
            sys.exit()

        # paddle collisions
        if paddle_1_rect.colliderect(ball_rect) and ball_accel_x < 0:
            ball_accel_x *= -1
            # nudge the ball out so it won't stick
            ball_rect.left = paddle_1_rect.right + 1

            # optionally vary y velocity based on where it hit the paddle
            offset = (ball_rect.centery - paddle_1_rect.centery) / (paddle_h / 2)
            ball_accel_y += offset * 0.05

        if paddle_2_rect.colliderect(ball_rect) and ball_accel_x > 0:
            ball_accel_x *= -1
            ball_rect.right = paddle_2_rect.left - 1
            offset = (ball_rect.centery - paddle_2_rect.centery) / (paddle_h / 2)
            ball_accel_y += offset * 0.05

        # move the ball
        ball_rect.left += ball_accel_x * delta_time
        ball_rect.top += ball_accel_y * delta_time

        # draw
        pygame.draw.rect(screen, COLOR_WHITE, paddle_1_rect)
        pygame.draw.rect(screen, COLOR_WHITE, paddle_2_rect)
        pygame.draw.rect(screen, COLOR_WHITE, ball_rect)

        pygame.display.flip()

if __name__ == '__main__':
    main()
