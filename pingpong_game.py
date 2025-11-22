import pygame
import random
import sys
from pathlib import Path

# Window size (used for windowed mode)
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720

COLOR_TABLE_TOP    = (40, 90, 170)    # bright icy blue
COLOR_TABLE_BOTTOM = (10, 40, 90)     # deep cold blue
COLOR_BORDER       = (5, 20, 50)      # dark navy frame
COLOR_WHITE        = (230, 240, 255)  # icy white for ball/paddles
COLOR_NET          = (210, 230, 255)  # light ice white (net)
COLOR_SHADOW       = (0, 20, 80, 120) # cold blue-transparent shadow

# UI colors
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (255, 255, 255)
COLOR_RED = (220, 60, 60)
COLOR_GREEN = (80, 200, 120)
COLOR_BUTTON = (30, 120, 70)
COLOR_BUTTON_HOVER = (50, 150, 90)

# Gameplay settings
PADDLE_W, PADDLE_H = 12, 110
BALL_SIZE = 20
PADDLE_SPEED = 0.6           # pixels per ms (player)
AI_MAX_SPEED = 0.45          # max speed of AI paddle (pixels per ms)
BALL_BASE_SPEED = 0.35       # base speed factor (pixels per ms)
SPEED_INCREMENT = 1.05       # multiply speed on paddle hit

# Power-shot settings
POWER_MULTIPLIER = 1.6         # how much stronger the ball gets on a power-hit
POWER_COOLDOWN_MS = 3000       # cooldown after using power (ms)
POWER_WINDOW_MS = 250          # how long the "power active" window lasts after pressing key (ms)
POWER_BONUS_POINTS = 1         # immediate points awarded on successful power-hit

# Optional sound files (put these in the same folder or comment out sound code)
HIT_SOUND_FILE = "hit.wav"
SCORE_SOUND_FILE = "score.wav"
POWER_SOUND_FILE = "power.wav"

def load_sound(name):
    p = Path(name)
    if p.exists():
        try:
            return pygame.mixer.Sound(str(p))
        except Exception:
            return None
    return None

# ---------- Visual helper functions ----------
def draw_table(surface):
    """Draws the green table with border, gradient, center dashed line and gloss."""
    w, h = surface.get_size()

    # border
    pygame.draw.rect(surface, COLOR_BORDER, (0, 0, w, h), border_radius=18)

    # gradient cloth area (we draw lines to create vertical gradient)
    inner_rect = pygame.Rect(12, 12, w - 24, h - 24)
    grad = pygame.Surface((inner_rect.width, inner_rect.height))
    for y in range(inner_rect.height):
        t = y / inner_rect.height
        r = int(COLOR_TABLE_TOP[0] * (1 - t) + COLOR_TABLE_BOTTOM[0] * t)
        g = int(COLOR_TABLE_TOP[1] * (1 - t) + COLOR_TABLE_BOTTOM[1] * t)
        b = int(COLOR_TABLE_TOP[2] * (1 - t) + COLOR_TABLE_BOTTOM[2] * t)
        pygame.draw.line(grad, (r, g, b), (0, y), (inner_rect.width, y))
    surface.blit(grad, inner_rect.topleft)

    # thin inner border
    inner_border_color = (255, 255, 255, 30)
    tmp = pygame.Surface((inner_rect.width, inner_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(tmp, inner_border_color, tmp.get_rect(), 2, border_radius=12)
    surface.blit(tmp, inner_rect.topleft)

    # center dashed line
    cx = w // 2
    y = 30
    dash_h = 14
    gap = 12
    line_color = (255, 255, 255, 170)
    while y < h - 30:
        pygame.draw.rect(surface, line_color, (cx - 2, y, 4, dash_h))
        y += dash_h + gap

    # subtle gloss
    gloss = pygame.Surface((inner_rect.width, 40), pygame.SRCALPHA)
    gloss.fill((255, 255, 255, 12))
    surface.blit(gloss, (inner_rect.left, inner_rect.top))

def draw_paddle(surface, rect):
    """Draws a rounded paddle with end-caps and light inner shadow."""
    pygame.draw.rect(surface, COLOR_WHITE, rect, border_radius=8)
    cap_r = max(6, rect.width // 2 + 2)
    left_center = (rect.left + cap_r // 2, rect.centery)
    right_center = (rect.right - cap_r // 2, rect.centery)
    pygame.draw.circle(surface, COLOR_WHITE, left_center, cap_r)
    pygame.draw.circle(surface, COLOR_WHITE, right_center, cap_r)
    inner = rect.inflate(-4, -8)
    if inner.width > 0 and inner.height > 0:
        s = pygame.Surface((inner.width, inner.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 18), s.get_rect(), border_radius=6)
        surface.blit(s, inner.topleft)

def draw_ball(surface, rect):
    """Draw ball with shadow, glow and highlight to look real."""
    shadow_surf = pygame.Surface((rect.width * 3, rect.height * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 90), shadow_surf.get_rect())
    surface.blit(shadow_surf, (rect.left - rect.width // 1.5, rect.top + rect.height // 1.5))

    glow_surf = pygame.Surface((rect.width * 4, rect.height * 4), pygame.SRCALPHA)
    pygame.draw.ellipse(glow_surf, (255, 255, 255, 24), glow_surf.get_rect())
    surface.blit(glow_surf, (rect.left - rect.width * 1.5, rect.top - rect.height * 1.5))

    pygame.draw.ellipse(surface, COLOR_WHITE, rect)
    hl_w, hl_h = max(2, rect.width // 2), max(2, rect.height // 2)
    highlight = pygame.Surface((hl_w, hl_h), pygame.SRCALPHA)
    pygame.draw.ellipse(highlight, (255, 255, 255, 180), highlight.get_rect())
    surface.blit(highlight, (rect.left + rect.width * 0.12, rect.top + rect.height * 0.08))

def draw_button(surface, rect, text, font, mouse_pos):
    """Draw a rounded button, return True if mouse is hovering (for click handling externally)."""
    hover = rect.collidepoint(mouse_pos)
    color = COLOR_BUTTON_HOVER if hover else COLOR_BUTTON
    pygame.draw.rect(surface, color, rect, border_radius=12)
    pygame.draw.rect(surface, (255,255,255,20), rect, 2, border_radius=12)  # subtle border
    txt = font.render(text, True, COLOR_WHITE)
    surface.blit(txt, txt.get_rect(center=rect.center))
    return hover

# ---------- End visuals ----------

def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    pygame.display.set_allow_screensaver(False)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption('Pong - Power Shot (E/K) — Visual Table')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Consolas', 32)
    small_font = pygame.font.SysFont('Consolas', 18)
    button_font = pygame.font.SysFont('Consolas', 28)

    # paddles and ball (initial positions)
    paddle_1_rect = pygame.Rect(30, (SCREEN_HEIGHT - PADDLE_H) // 2, PADDLE_W, PADDLE_H)
    paddle_2_rect = pygame.Rect(SCREEN_WIDTH - 30 - PADDLE_W, (SCREEN_HEIGHT - PADDLE_H) // 2, PADDLE_W, PADDLE_H)
    ball_rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
    ball_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    # ball velocity vector (pixels per ms)
    ball_speed = BALL_BASE_SPEED
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

    # power-shot state for left (player 1) and right (player 2)
    now = pygame.time.get_ticks()
    power_ready_left = True
    power_ready_right = True
    power_active_left = False
    power_active_right = False
    power_cooldown_end_left = 0
    power_cooldown_end_right = 0
    power_active_end_left = 0
    power_active_end_right = 0

    # load sounds (optional)
    hit_sound = load_sound(HIT_SOUND_FILE)
    score_sound = load_sound(SCORE_SOUND_FILE)
    power_sound = load_sound(POWER_SOUND_FILE)

    show_debug = False

    # game over state
    game_over = False
    winner_name = None

    while True:
        now = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()

        # update power readiness from cooldowns
        if (not power_ready_left) and now >= power_cooldown_end_left:
            power_ready_left = True
            power_active_left = False
        if (not power_ready_right) and now >= power_cooldown_end_right:
            power_ready_right = True
            power_active_right = False

        # also expire "active window" automatically
        if power_active_left and now >= power_active_end_left:
            power_active_left = False
        if power_active_right and now >= power_active_end_right:
            power_active_right = False

        clicked = False
        click_pos = None

        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True
                click_pos = event.pos

            if event.type == pygame.KEYDOWN:
                # movement keys
                if event.key == pygame.K_w:
                    paddle_1_move = -PADDLE_SPEED
                if event.key == pygame.K_s:
                    paddle_1_move = PADDLE_SPEED
                if not use_ai:
                    if event.key == pygame.K_UP:
                        paddle_2_move = -PADDLE_SPEED
                    if event.key == pygame.K_DOWN:
                        paddle_2_move = PADDLE_SPEED

                # start / pause / toggles
                if event.key == pygame.K_SPACE:
                    if not started and not game_over:
                        started = True
                    elif paused:
                        paused = False
                if event.key == pygame.K_p:
                    paused = not paused
                if event.key == pygame.K_TAB:
                    use_ai = not use_ai   # toggle AI control

                # fullscreen toggle
                if event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

                # reset
                if event.key == pygame.K_r:
                    score_left = 0
                    score_right = 0
                    ball_speed = BALL_BASE_SPEED
                    ball_dir = {'x': ball_speed * random.choice((1, -1)), 'y': 0}
                    ball_rect.center = (screen.get_width() // 2, screen.get_height() // 2)
                    started = False
                    game_over = False
                    winner_name = None

                # debug toggle
                if event.key == pygame.K_d:
                    show_debug = not show_debug

                # POWER-SHOT KEYS:
                if event.key == pygame.K_e:
                    if power_ready_left and not game_over:
                        power_active_left = True
                        power_ready_left = False
                        power_active_end_left = now + POWER_WINDOW_MS
                        power_cooldown_end_left = now + POWER_COOLDOWN_MS
                        if power_sound:
                            power_sound.play()
                if event.key == pygame.K_k:
                    if power_ready_right and not game_over:
                        power_active_right = True
                        power_ready_right = False
                        power_active_end_right = now + POWER_WINDOW_MS
                        power_cooldown_end_right = now + POWER_COOLDOWN_MS
                        if power_sound:
                            power_sound.play()

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_s):
                    paddle_1_move = 0.0
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    paddle_2_move = 0.0

        # Draw background & UI (use visual table)
        screen.fill(COLOR_BORDER)  # fallback border color
        sw, sh = screen.get_size()

        # draw table visuals into screen
        draw_table(screen)

        # Start screen if not started and not game_over
        if not started and not game_over:
            # Draw instructions and a Start button
            title = font.render('PONG', True, COLOR_WHITE)
            screen.blit(title, title.get_rect(center=(sw // 2, sh // 2 - 120)))
            hint = small_font.render('W/S for left; Up/Down for right (when AI off). E = Power (left)  K = Power (right). R reset.', True, COLOR_GRAY)
            screen.blit(hint, (10, sh - 30))
            instr = small_font.render('Press SPACE or click START. TAB toggles AI. P = Pause. F = Fullscreen', True, COLOR_GRAY)
            screen.blit(instr, instr.get_rect(center=(sw // 2, sh // 2 - 80)))

            # start button dimensions
            btn_w, btn_h = 220, 60
            btn_rect = pygame.Rect(0, 0, btn_w, btn_h)
            btn_rect.center = (sw // 2, sh // 2)
            hovered = draw_button(screen, btn_rect, "START", button_font, mouse_pos)

            # handle click on start button
            if clicked and click_pos and btn_rect.collidepoint(click_pos):
                started = True

            pygame.display.flip()
            clock.tick(60)
            continue

        # If game over, show winner + restart button
        if game_over:
            # overlay dim
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            win_text = font.render(f"{winner_name} Wins!", True, COLOR_WHITE)
            screen.blit(win_text, win_text.get_rect(center=(sw // 2, sh // 2 - 60)))

            sub = small_font.render("Click RESTART or press R to play again", True, COLOR_GRAY)
            screen.blit(sub, sub.get_rect(center=(sw // 2, sh // 2 - 20)))

            # restart button
            btn_w, btn_h = 260, 64
            btn_rect = pygame.Rect(0, 0, btn_w, btn_h)
            btn_rect.center = (sw // 2, sh // 2 + 60)
            hovered = draw_button(screen, btn_rect, "RESTART", button_font, mouse_pos)

            if clicked and click_pos and btn_rect.collidepoint(click_pos):
                # reset everything
                score_left = 0
                score_right = 0
                ball_speed = BALL_BASE_SPEED
                ball_dir = {'x': ball_speed * random.choice((1, -1)), 'y': 0}
                ball_rect.center = (sw // 2, sh // 2)
                started = False
                game_over = False
                winner_name = None

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

        # move paddles (scaled by dt)
        paddle_1_rect.top += paddle_1_move * dt
        paddle_2_rect.top += paddle_2_move * dt

        # AI movement for right paddle
        if use_ai:
            diff = ball_rect.centery - paddle_2_rect.centery
            if abs(diff) > 8:
                direction = diff / abs(diff)
                move_amount = min(AI_MAX_SPEED * dt, abs(diff))
                paddle_2_rect.top += direction * move_amount

        # clamp paddles to current screen height
        if paddle_1_rect.top < 12:
            paddle_1_rect.top = 12
        if paddle_1_rect.bottom > sh - 12:
            paddle_1_rect.bottom = sh - 12

        if paddle_2_rect.top < 12:
            paddle_2_rect.top = 12
        if paddle_2_rect.bottom > sh - 12:
            paddle_2_rect.bottom = sh - 12

        # update ball position
        ball_rect.left += ball_dir['x'] * dt
        ball_rect.top += ball_dir['y'] * dt

        # top/bottom collision (respect 12px inner margin)
        if ball_rect.top <= 12:
            ball_rect.top = 12
            ball_dir['y'] *= -1
        if ball_rect.bottom >= sh - 12:
            ball_rect.bottom = sh - 12
            ball_dir['y'] *= -1

        # left/right out of bounds -> point scored
        if ball_rect.left <= 0:
            score_right += 1
            if score_sound:
                score_sound.play()
            ball_speed = BALL_BASE_SPEED
            ball_dir = {'x': ball_speed * 1, 'y': random.uniform(-0.3, 0.3)}
            ball_rect.center = (sw // 2, sh // 2)
            started = False  # wait for space or click to serve
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
            if power_active_left:
                ball_dir['x'] *= -1 * POWER_MULTIPLIER
                ball_dir['y'] *= POWER_MULTIPLIER
                score_left += POWER_BONUS_POINTS
                power_active_left = False
            else:
                ball_dir['x'] *= -1
                rel = (ball_rect.centery - paddle_1_rect.centery) / (PADDLE_H / 2)
                ball_dir['y'] += rel * 0.18
                ball_dir['x'] *= SPEED_INCREMENT
                ball_dir['y'] *= SPEED_INCREMENT
            if hit_sound:
                hit_sound.play()
            ball_rect.left = paddle_1_rect.right + 1

        # paddle collisions (right)
        if paddle_2_rect.colliderect(ball_rect) and ball_dir['x'] > 0:
            if power_active_right:
                ball_dir['x'] *= -1 * POWER_MULTIPLIER
                ball_dir['y'] *= POWER_MULTIPLIER
                score_right += POWER_BONUS_POINTS
                power_active_right = False
            else:
                ball_dir['x'] *= -1
                rel = (ball_rect.centery - paddle_2_rect.centery) / (PADDLE_H / 2)
                ball_dir['y'] += rel * 0.18
                ball_dir['x'] *= SPEED_INCREMENT
                ball_dir['y'] *= SPEED_INCREMENT
            if hit_sound:
                hit_sound.play()
            ball_rect.right = paddle_2_rect.left - 1

        # draw paddles and ball (visual functions)
        draw_paddle(screen, paddle_1_rect)
        draw_paddle(screen, paddle_2_rect)
        draw_ball(screen, ball_rect)

        # draw score
        score_text = font.render(f"{score_left}   -   {score_right}", True, COLOR_WHITE)
        screen.blit(score_text, score_text.get_rect(center=(sw // 2, 40)))

        # draw power UI (left and right)
        left_power_label = small_font.render("Left Power (E):", True, COLOR_WHITE)
        screen.blit(left_power_label, (10, 60))
        if power_ready_left and not power_active_left:
            status = small_font.render("READY", True, COLOR_GREEN)
            screen.blit(status, (160, 60))
        elif power_active_left:
            status = small_font.render("POWER ACTIVE!", True, COLOR_RED)
            screen.blit(status, (160, 60))
        else:
            rem = max(0, (power_cooldown_end_left - now) / 1000.0)
            status = small_font.render(f"CD: {rem:.1f}s", True, COLOR_GRAY)
            screen.blit(status, (160, 60))

        right_power_label = small_font.render("Right Power (K):", True, COLOR_WHITE)
        screen.blit(right_power_label, (sw - 260, 60))
        if power_ready_right and not power_active_right:
            status = small_font.render("READY", True, COLOR_GREEN)
            screen.blit(status, (sw - 100, 60))
        elif power_active_right:
            status = small_font.render("POWER ACTIVE!", True, COLOR_RED)
            screen.blit(status, (sw - 140, 60))
        else:
            rem = max(0, (power_cooldown_end_right - now) / 1000.0)
            status = small_font.render(f"CD: {rem:.1f}s", True, COLOR_GRAY)
            screen.blit(status, (sw - 140, 60))

        # draw small UI state
        mode = "AI" if use_ai else "2P"
        ui = small_font.render(f"Mode: {mode}    P=Pause    TAB=Toggle AI    F=Fullscreen    R=Reset    D=Debug", True, COLOR_GRAY)
        screen.blit(ui, (10, 10))

        if show_debug:
            dbg = small_font.render(f"Ball vel: ({ball_dir['x']:.2f},{ball_dir['y']:.2f})   FPS: {clock.get_fps():.1f}", True, COLOR_GRAY)
            screen.blit(dbg, (10, 80))

        # check for win
        if score_left >= max_score or score_right >= max_score:
            # name mapping for clarity
            if score_left > score_right:
                winner_name = "Player 1"
            else:
                winner_name = "Player 2"
            game_over = True
            started = False
            # display the win message for the next frame via the game_over branch
            pygame.display.flip()
            continue

        pygame.display.flip()

if __name__ == '__main__':
    main()
