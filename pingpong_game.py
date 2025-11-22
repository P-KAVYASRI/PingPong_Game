# pingpong_game.py
import pygame
import random
import sys
from pathlib import Path

# Window size
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (90, 90, 90)

# Gameplay settings
PADDLE_W, PADDLE_H = 10, 110
BALL_SIZE = 20
PADDLE_SPEED = 0.6           # pixels per ms (player)
AI_MAX_SPEED = 0.45          # max speed of AI paddle (pixels per ms)
BALL_BASE_SPEED = 0.35       # base speed factor (pixels per ms)
SPEED_INCREMENT = 1.05       # multiply speed on paddle hit

# Optional sound files (put these in the same folder or comment out sound code)
HIT_SOUND_FILE = "hit.wav"
SCORE_SOUND_FILE = "score.wav"

def load_sound(name):
    p = Path(name)
    if p.exists():
        try:
            return pygame.mixer.Sound(str(p))
        except Exception:
            return None
    return None

def reset_ball(ball_rect, ball_dir, speed):
    # center the ball and set direction (1 = right, -1 = left)
    ball_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    angle = random.uniform(-0.4, 0.4)  # small vertical angle
    ball_dir['x'] = speed * ball_dir['x']  # preserve sign
    ball_dir['y'] = speed * angle
    # ensure x direction magnitude
    if ball_dir['x'] == 0:
        ball_dir['x'] = speed * random.choice((1, -1))

def main():
    pygame.init()
    # Optional mixer init for sounds
    try:
        pygame.mixer.init()
    except Exception:
        pass

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption('Pong - Advanced')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Consolas', 32)
    small_font = pygame.font.SysFont('Consolas', 18)

    # paddles and ball
    paddle_1_rect = pygame.Rect(30, (SCREEN_HEIGHT - PADDLE_H) // 2, PADDLE_W, PADDLE_H)
    paddle_2_rect = pygame.Rect(SCREEN_WIDTH - 30 - PADDLE_W, (SCREEN_HEIGHT - PADDLE_H) // 2, PADDLE_W, PADDLE_H)
    ball_rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
    ball_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    # ball velocity vector (pixels per ms)
    ball_speed = BALL_BASE_SPEED
    # start with random horizontal direction
    ball_dir = {'x': ball_speed * random.choice((1, -1)), 'y': ball_speed * random.uniform(-0.3, 0.3)}

    paddle_1_move = 0.0
    paddle_2_move = 0.0

    # state
    started = False   # whether gameplay started
    paused = False
    use_ai = True     # AI controls right paddle if True
    fullscreen = False

    score_left = 0
    score_right = 0
    max_score = 7     # first to 7 wins (example)

    # load sounds (optional)
    hit_sound = load_sound(HIT_SOUND_FILE)
    score_sound = load_sound(SCORE_SOUND_FILE)

    show_debug = False

    while True:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE:
                # handle window resize: update screen surface
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    paddle_1_move = -PADDLE_SPEED
                if event.key == pygame.K_s:
                    paddle_1_move = PADDLE_SPEED
                if not use_ai:
                    if event.key == pygame.K_UP:
                        paddle_2_move = -PADDLE_SPEED
                    if event.key == pygame.K_DOWN:
                        paddle_2_move = PADDLE_SPEED

                if event.key == pygame.K_SPACE:
                    if not started:
                        started = True
                    elif paused:
                        paused = False

                if event.key == pygame.K_p:
                    paused = not paused

                if event.key == pygame.K_TAB:
                    use_ai = not use_ai   # toggle AI control

                if event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

                if event.key == pygame.K_r:
                    # reset everything
                    score_left = 0
                    score_right = 0
                    ball_speed = BALL_BASE_SPEED
                    reset_ball(ball_rect, {'x': random.choice((1,-1)), 'y': 0}, ball_speed)
                    started = False

                if event.key == pygame.K_d:
                    show_debug = not show_debug

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_s):
                    paddle_1_move = 0.0
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    paddle_2_move = 0.0

        # Draw background & UI
        screen.fill(COLOR_BLACK)
        sw, sh = screen.get_size()

        # center dashed line
        dash_h = 15
        gap = 10
        x_center = sw // 2
        y = 0
        while y < sh:
            pygame.draw.rect(screen, COLOR_GRAY, (x_center - 2, y, 4, dash_h))
            y += dash_h + gap

        # Start screen if not started
        if not started:
            text = font.render('Press SPACE to Start    (TAB toggle AI)    P = Pause    F = Fullscreen', True, COLOR_WHITE)
            rect = text.get_rect(center=(sw // 2, sh // 2))
            screen.blit(text, rect)
            # show small hint
            hint = small_font.render('W/S for left; Up/Down for right (when AI off). R to reset scores. D show debug.', True, COLOR_GRAY)
            screen.blit(hint, (10, sh - 30))
            pygame.display.flip()
            clock.tick(60)
            continue

        # time delta
        dt = clock.tick(60)  # ms

        if paused:
            pause_text = font.render('PAUSED', True, COLOR_WHITE)
            screen.blit(pause_text, pause_text.get_rect(center=(sw // 2, sh // 2)))
            pygame.display.flip()
            continue

        # move paddles
        paddle_1_rect.top += paddle_1_move * dt
        paddle_2_rect.top += paddle_2_move * dt

        # AI movement for right paddle
        if use_ai:
            # simple proportional movement toward ball center with max speed
            diff = ball_rect.centery - paddle_2_rect.centery
            if abs(diff) > 8:
                direction = diff / abs(diff)
                move_amount = min(AI_MAX_SPEED * dt, abs(diff))
                paddle_2_rect.top += direction * move_amount

        # clamp paddles
        if paddle_1_rect.top < 0:
            paddle_1_rect.top = 0
        if paddle_1_rect.bottom > sh:
            paddle_1_rect.bottom = sh

        if paddle_2_rect.top < 0:
            paddle_2_rect.top = 0
        if paddle_2_rect.bottom > sh:
            paddle_2_rect.bottom = sh

        # update ball position
        ball_rect.left += ball_dir['x'] * dt
        ball_rect.top += ball_dir['y'] * dt

        # top/bottom collision
        if ball_rect.top <= 0:
            ball_rect.top = 0
            ball_dir['y'] *= -1
        if ball_rect.bottom >= sh:
            ball_rect.bottom = sh
            ball_dir['y'] *= -1

        # left/right out of bounds -> point scored
        if ball_rect.left <= 0:
            score_right += 1
            if score_sound:
                score_sound.play()
            # reset ball toward scoring player (right serves)
            ball_speed = BALL_BASE_SPEED
            ball_dir = {'x': ball_speed * 1, 'y': random.uniform(-0.3, 0.3)}
            ball_rect.center = (sw // 2, sh // 2)
            started = False  # wait for space to serve
            # brief flash (optional)
            pygame.time.delay(250)

        if ball_rect.right >= sw:
            score_left += 1
            if score_sound:
                score_sound.play()
            ball_speed = BALL_BASE_SPEED
            ball_dir = {'x': ball_speed * -1, 'y': random.uniform(-0.3, 0.3)}
            ball_rect.center = (sw // 2, sh // 2)
            started = False
            pygame.time.delay(250)

        # paddle collisions (left)
        if paddle_1_rect.colliderect(ball_rect) and ball_dir['x'] < 0:
            # reflect
            ball_dir['x'] *= -1
            # vary y velocity based on hit position
            rel = (ball_rect.centery - paddle_1_rect.centery) / (PADDLE_H / 2)
            ball_dir['y'] += rel * 0.18
            # speed up
            ball_dir['x'] *= SPEED_INCREMENT
            ball_dir['y'] *= SPEED_INCREMENT
            if hit_sound:
                hit_sound.play()
            # nudge out
            ball_rect.left = paddle_1_rect.right + 1

        # paddle collisions (right)
        if paddle_2_rect.colliderect(ball_rect) and ball_dir['x'] > 0:
            ball_dir['x'] *= -1
            rel = (ball_rect.centery - paddle_2_rect.centery) / (PADDLE_H / 2)
            ball_dir['y'] += rel * 0.18
            ball_dir['x'] *= SPEED_INCREMENT
            ball_dir['y'] *= SPEED_INCREMENT
            if hit_sound:
                hit_sound.play()
            ball_rect.right = paddle_2_rect.left - 1

        # draw paddles and ball (scale positions if window resized)
        # we used absolute positions so just draw them
        pygame.draw.rect(screen, COLOR_WHITE, paddle_1_rect)
        pygame.draw.rect(screen, COLOR_WHITE, paddle_2_rect)
        pygame.draw.ellipse(screen, COLOR_WHITE, ball_rect)

        # draw score
        score_text = font.render(f"{score_left}   -   {score_right}", True, COLOR_WHITE)
        screen.blit(score_text, score_text.get_rect(center=(sw // 2, 40)))

        # draw small UI state
        mode = "AI" if use_ai else "2P"
        ui = small_font.render(f"Mode: {mode}    P=Pause    TAB=Toggle AI    F=Fullscreen    R=Reset    D=Debug", True, COLOR_GRAY)
        screen.blit(ui, (10, 10))

        if show_debug:
            dbg = small_font.render(f"Ball vel: ({ball_dir['x']:.2f},{ball_dir['y']:.2f})   FPS: {clock.get_fps():.1f}", True, COLOR_GRAY)
            screen.blit(dbg, (10, 40))

        # check for win
        if score_left >= max_score or score_right >= max_score:
            winner = "Left" if score_left > score_right else "Right"
            win_text = font.render(f"{winner} Player Wins!  (R to restart)", True, COLOR_WHITE)
            screen.blit(win_text, win_text.get_rect(center=(sw // 2, sh // 2)))
            pygame.display.flip()
            # stop gameplay until reset
            started = False
            # wait until user presses R or QUIT (we'll keep looping)
            # do not auto-quit
            clock.tick(60)
            continue

        pygame.display.flip()

if __name__ == '__main__':
    main()
