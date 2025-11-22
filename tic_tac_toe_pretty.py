# tic_tac_toe_pretty.py
import pygame, sys, random, math, time

# ---------- Config ----------
WIDTH, HEIGHT = 600, 760   # 600x600 board + UI area
BOARD_SIZE = 600
FPS = 60
LINE_COLOR = (40, 40, 40)
UI_BG = (245, 245, 248)
ACCENT = (30, 120, 190)
X_COLOR = (220, 60, 60)
O_COLOR = (60, 130, 220)
PREVIEW_COLOR = (180, 180, 180)
BG_TOP = (18, 24, 30)
BG_BOTTOM = (36, 54, 68)
FONT_NAME = "Consolas"

# Optional sound file names (place in same folder or comment these lines)
HIT_SOUND_FILE = None  # e.g. "click.wav"
WIN_SOUND_FILE = None  # e.g. "win.wav"

# ---------- Utilities ----------
def load_sound_if(name):
    if not name: return None
    try:
        return pygame.mixer.Sound(name)
    except Exception:
        return None

# ---------- Game logic (same as earlier) ----------
def check_winner(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], (a,b,c)
    if all(board[i] is not None for i in range(9)):
        return "Draw", None
    return None, None

def minimax(board, player):
    winner, _ = check_winner(board)
    if winner == 'X': return -1, None
    if winner == 'O': return 1, None
    if winner == 'Draw': return 0, None

    moves = []
    for i in range(9):
        if board[i] is None:
            board[i] = player
            score, _ = minimax(board, 'X' if player == 'O' else 'O')
            moves.append((score, i))
            board[i] = None
    if player == 'O':
        return max(moves, key=lambda x: x[0])
    else:
        return min(moves, key=lambda x: x[0])

# ---------- Visual helpers ----------
def lerp(a,b,t): return a + (b-a)*t
def lerp_color(c1,c2,t):
    return (int(lerp(c1[0],c2[0],t)), int(lerp(c1[1],c2[1],t)), int(lerp(c1[2],c2[2],t)))

# Animated X: draw two lines with progress 0..1
def draw_x(surface, rect, color, progress, width=10):
    x1,y1 = rect.topleft
    x2,y2 = rect.bottomright
    x3,y3 = rect.bottomleft
    x4,y4 = rect.topright
    # First stroke progress 0..0.5, Second 0.5..1
    p1 = min(1, progress*2)
    p2 = max(0, (progress-0.5)*2)
    if p1>0:
        end = (lerp(x1,x2,p1), lerp(y1,y2,p1))
        pygame.draw.line(surface, color, (x1,y1), end, width)
    if p2>0:
        end = (lerp(x3,x4,p2), lerp(y3,y4,p2))
        pygame.draw.line(surface, color, (x3,y3), end, width)

# Animated O: draw circle arc with progress 0..1
def draw_o(surface, center, radius, color, progress, width=10):
    # draw multiple small arcs approximating progress
    rect = pygame.Rect(0,0,radius*2,radius*2)
    rect.center = center
    # calculate angle
    start_angle = -math.pi/2
    end_angle = start_angle + progress * (2*math.pi)
    # draw many small segments for smoothness
    segments = max(10, int(40*progress))
    for i in range(segments):
        a1 = start_angle + (i/segments) * (end_angle-start_angle)
        a2 = start_angle + ((i+1)/segments) * (end_angle-start_angle)
        pygame.draw.arc(surface, color, rect, a1, a2, width)

# Confetti particle system
class Particle:
    def __init__(self,x,y):
        self.pos = [x,y]
        ang = random.uniform(0,2*math.pi)
        speed = random.uniform(2,8)
        self.vel = [math.cos(ang)*speed, math.sin(ang)*speed]
        self.life = random.randint(40,90)
        self.size = random.randint(4,8)
        self.col = random.choice([X_COLOR, O_COLOR, ACCENT, (255,230,120)])
    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.vel[1] += 0.25  # gravity
        self.life -= 1
    def draw(self, surf):
        alpha = max(0, int(255 * (self.life / 90)))
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        s.fill((*self.col, alpha))
        surf.blit(s, (self.pos[0], self.pos[1]))

# ---------- UI elements ----------
def rounded_rect(surface, rect, color, radius=10, width=0):
    pygame.draw.rect(surface, color, rect, border_radius=radius, width=width)

# ---------- Main ----------
def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tic-Tac-Toe • Pretty")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, 20)
    bigfont = pygame.font.SysFont(FONT_NAME, 36)
    tiny = pygame.font.SysFont(FONT_NAME, 14)

    hit_sound = load_sound_if(HIT_SOUND_FILE)
    win_sound = load_sound_if(WIN_SOUND_FILE)

    board = [None]*9
    anim_progress = [0.0]*9   # per-cell animation progress (0..1)
    anim_speed = 0.06         # how fast X/O draw animates
    turn = 'X'
    mode = "VS_COMPUTER"      # or "2P"
    game_over = False
    winner = None
    win_line = None
    particles = []

    hover = None
    last_click_t = 0
    autoplay_delay = 0.2  # small pause before AI plays

    def reset():
        nonlocal board, anim_progress, turn, game_over, winner, win_line, particles
        board = [None]*9
        anim_progress = [0.0]*9
        turn = 'X'
        game_over = False
        winner = None
        win_line = None
        particles = []

    reset()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse = pygame.mouse.get_pos()
        mx,my = mouse

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset()
                if event.key == pygame.K_m:
                    mode = "2P" if mode == "VS_COMPUTER" else "VS_COMPUTER"
                    reset()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
                # board click?
                if my <= BOARD_SIZE:
                    cell_w = BOARD_SIZE/3
                    c = int(mx // cell_w)
                    r = int(my // cell_w)
                    idx = r*3 + c
                    if 0 <= idx < 9 and board[idx] is None:
                        board[idx] = turn
                        anim_progress[idx] = 0.001
                        last_click_t = time.time()
                        if hit_sound: hit_sound.play()
                        # switch
                        turn = 'O' if turn == 'X' else 'X'
                # UI buttons
                else:
                    # Mode button area & Restart button area (simple rects)
                    if WIDTH-220 <= mx <= WIDTH-40 and BOARD_SIZE+20 <= my <= BOARD_SIZE+60:
                        mode = "2P" if mode == "VS_COMPUTER" else "VS_COMPUTER"
                        reset()
                    if 40 <= mx <= 180 and BOARD_SIZE+20 <= my <= BOARD_SIZE+60:
                        reset()

        # AI move if enabled
        if not game_over and mode == "VS_COMPUTER" and turn == 'O':
            # small delay to make AI feel natural
            if time.time() - last_click_t > autoplay_delay:
                _, move = minimax(board[:], 'O')
                if move is not None:
                    board[move] = 'O'
                    anim_progress[move] = 0.001
                    last_click_t = time.time()
                    if hit_sound: hit_sound.play()
                turn = 'X'

        # update animations
        for i in range(9):
            if board[i] is not None and anim_progress[i] < 1.0:
                anim_progress[i] = min(1.0, anim_progress[i] + anim_speed)

        # update particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # check winner
        if not game_over:
            w, line = check_winner(board)
            if w:
                game_over = True
                winner = w
                win_line = line
                # spawn confetti
                if winner != "Draw":
                    cx = WIDTH/2
                    cy = BOARD_SIZE/2
                    for _ in range(60):
                        particles.append(Particle(cx + random.uniform(-80,80), cy + random.uniform(-80,80)))
                if win_sound: win_sound.play()

        # ---------- draw ----------
        # background gradient
        for y in range(HEIGHT):
            t = y / HEIGHT
            pygame.draw.line(screen, lerp_color(BG_TOP, BG_BOTTOM, t), (0,y),(WIDTH,y))

        # draw board area with subtle rounded bg
        board_rect = pygame.Rect(10,10, BOARD_SIZE-20, BOARD_SIZE-20)
        rounded_rect(screen, (10,10,BOARD_SIZE-20,BOARD_SIZE-20), (20,20,20), radius=14)
        # draw faded inner panel for grid
        inner = pygame.Surface((BOARD_SIZE-40, BOARD_SIZE-40))
        inner.fill((30,30,30))
        screen.blit(inner, (20,20))

        # grid lines
        cell = BOARD_SIZE/3
        offset = 20
        for i in range(1,3):
            # vertical
            x = offset + i*cell
            pygame.draw.line(screen, LINE_COLOR, (x, offset), (x, offset+BOARD_SIZE-40), 4)
            # horizontal
            y = offset + i*cell
            pygame.draw.line(screen, LINE_COLOR, (offset, y), (offset+BOARD_SIZE-40, y), 4)

        # cell rectangles for calculations
        def cell_rect(index):
            r = index // 3
            c = index % 3
            x = offset + c*cell
            y = offset + r*cell
            pad = cell * 0.12
            return pygame.Rect(x+pad, y+pad, cell-2*pad, cell-2*pad)

        # hover index
        hover = None
        if my <= BOARD_SIZE and not game_over:
            if mx >= offset and mx <= offset+BOARD_SIZE-40 and my >= offset and my <= offset+BOARD_SIZE-40:
                col = int((mx - offset) // cell)
                row = int((my - offset) // cell)
                if 0<=col<3 and 0<=row<3:
                    hi = row*3 + col
                    if board[hi] is None:
                        hover = hi

        # draw X/O with animations and preview
        for i in range(9):
            rect = cell_rect(i)
            val = board[i]
            if val == 'X':
                draw_x(screen, rect, X_COLOR, anim_progress[i], width=int(cell*0.06))
            elif val == 'O':
                center = rect.center
                radius = rect.width/2
                draw_o(screen, center, int(radius), O_COLOR, anim_progress[i], width=int(cell*0.06))
            else:
                if hover == i and not game_over:
                    # preview faint with pulsing alpha
                    pulse = (math.sin(pygame.time.get_ticks()/300)+1)/2
                    a = 70 + int(60*pulse)
                    s = pygame.Surface((int(rect.width), int(rect.height)), pygame.SRCALPHA)
                    s.fill((PREVIEW_COLOR[0],PREVIEW_COLOR[1],PREVIEW_COLOR[2], a))
                    screen.blit(s, rect.topleft)
                    # small preview symbol center
                    if turn == 'X':
                        draw_x(screen, rect, (220,220,220), min(0.9, 0.4+0.6*pulse), width=int(cell*0.04))
                    else:
                        draw_o(screen, rect.center, int(rect.width/2), (220,220,220), min(0.9, 0.4+0.6*pulse), width=int(cell*0.04))

        # if game over and winner, animate win line overlay
        if game_over and winner != "Draw" and win_line:
            # compute line endpoints from cell centers, then animate drawing of line
            a,b,c = win_line
            idxs = [a,c]  # endpoints
            r0,c0 = divmod(idxs[0],3)
            r1,c1 = divmod(idxs[1],3)
            cx0 = offset + r0*cell + cell/2
            cy0 = offset + c0*cell + cell/2
            sx = offset + (idxs[0]%3)*cell + cell/2
            sy = offset + (idxs[0]//3)*cell + cell/2
            ex = offset + (idxs[1]%3)*cell + cell/2
            ey = offset + (idxs[1]//3)*cell + cell/2
            # simple animated progression based on time
            t = min(1.0, (pygame.time.get_ticks() % 1000) / 1000.0)
            # but we want it to draw once; just draw full strong line
            pygame.draw.line(screen, (250, 220, 40), (sx, sy), (ex, ey), 12)

        # draw confetti
        for p in particles:
            p.draw(screen)

        # bottom UI panel
        ui_y = BOARD_SIZE + 20
        ui_h = HEIGHT - ui_y - 20
        rounded_rect(screen, (20, ui_y, WIDTH-40, ui_h), (245,245,248), radius=12)
        # title
        ttxt = bigfont.render("Tic-Tac-Toe", True, (30,30,30))
        screen.blit(ttxt, (40, ui_y+12))
        # mode / restart buttons
        btn_w = 140
        btn_h = 40
        # Restart (left)
        rrect = pygame.Rect(40, ui_y+12+48, btn_w, btn_h)
        rounded_rect(screen, rrect, (230,230,230), radius=10)
        screen.blit(font.render("Restart (R)", True, (40,40,40)), (rrect.x+16, rrect.y+10))
        # Mode toggle (right)
        mrect = pygame.Rect(WIDTH-220, ui_y+12+48, btn_w, btn_h)
        rounded_rect(screen, mrect, ACCENT, radius=10)
        screen.blit(font.render(("2P" if mode=="2P" else "VS Computer"), True, (255,255,255)), (mrect.x+12, mrect.y+10))
        # show turn or result
        status = ""
        if not game_over:
            status = f"Turn: {turn}    Mode: {mode}"
        else:
            if winner == "Draw":
                status = "Result: Draw"
            else:
                status = f"Winner: {winner}"
        status_surf = font.render(status, True, (60,60,60))
        screen.blit(status_surf, (40+btn_w+24, ui_y+12+54))

        # footer small text
        foot = tiny.render("M = toggle mode • R = restart • Click cells to play", True, (90,90,90))
        screen.blit(foot, (40, ui_y + ui_h - 28))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
