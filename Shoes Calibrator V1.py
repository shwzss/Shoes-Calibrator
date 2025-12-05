"""
Shoes Calibrator V1.py
Advanced Aim Calibrator & Trainer - Single-file program.

Features:
- Mouse + Controller support (toggle with C)
- First / Third person feel (toggle with P)
- Short / Long range
- Game sensitivity profiles + converter
- Deadzone measurement & recommended deadzone
- Moving targets, strafing bots, flick-only, tracking
- Infinite trainer & time trials
- Leaderboard & profiles (JSON), CSV/JSON export per run
- Local HTML dashboard + PNG charts via matplotlib (optional)
- Custom crosshair per-profile (size/gap/thickness/color/style)
"""

import pygame, sys, os, json, math, time, random, csv
from datetime import datetime

# Optional plotting for dashboard export
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB = True
except Exception:
    MATPLOTLIB = False

# ---------- Config ----------
WIN_W, WIN_H = 1280, 800
FPS = 144
DATA_DIR = "aim_data"
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboard.json")
EXPORT_DIR = os.path.join(DATA_DIR, "exports")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# controller tuning defaults
CONTROLLER_DEADZONE = 0.18
CONTROLLER_BASE_SPEED = 10.0
CONTROLLER_ACCEL = 1.4
USE_RADIAL = True

# recoil patterns basic
RECOIL_PATTERNS = {
    "assault": [(0, -2), (0.5, -1.4), (1.0, -1.0), (1.6, -0.6), (2.2, -0.2)],
    "sniper": [(0, -6), (0.6, -4), (1.2, -2)]
}

# game sensitivity base for conversion
GAME_SCALE = {"Valorant": 1.0, "CS2": 0.7, "Apex": 1.2, "Fortnite": 1.6, "Warzone": 1.8}

# ---------- Pygame init ----------
pygame.init()
SCREEN = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Aim Trainer & Calibrator — Full")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 18)
FONT_BIG = pygame.font.SysFont("Arial", 26, bold=True)

# joystick init
pygame.joystick.init()
JOYSTICKS = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for j in JOYSTICKS:
    j.init()

# ---------- utilities ----------
def draw_text(s, x, y, font=FONT, color=(230,230,230)):
    SCREEN.blit(font.render(str(s), True, color), (x, y))
def clamp(v, a, b): return max(a, min(b, v))
def dist(a,b): return math.hypot(a[0]-b[0], a[1]-b[1])

# ---------- persistence (profiles + leaderboard) ----------
def default_profile(name="Player"):
    return {
        "name": name,
        "preferred_game": "Valorant",
        "dpi": 800,
        "crosshair": {"size":12, "gap":3, "thickness":2, "color":[0,255,0], "style":"plus"},
        "sensitivity": {"mouse":0.5, "controller":9.0},
        "calibration": {}
    }

profiles = {}
leaderboard = []

def load_state():
    global profiles, leaderboard
    try:
        with open(PROFILES_FILE,"r") as f: profiles = json.load(f)
    except Exception:
        profiles = {"Player": default_profile("Player")}
    try:
        with open(LEADERBOARD_FILE,"r") as f: leaderboard[:] = json.load(f)
    except Exception:
        leaderboard[:] = []

def save_profiles():
    with open(PROFILES_FILE,"w") as f: json.dump(profiles, f, indent=2)

def save_leaderboard():
    with open(LEADERBOARD_FILE,"w") as f: json.dump(leaderboard, f, indent=2)

load_state()
current_profile_name = list(profiles.keys())[0] if profiles else "Player"
if current_profile_name not in profiles: profiles[current_profile_name] = default_profile(current_profile_name)

# ---------- crosshair rendering ----------
def render_crosshair(pos, ch):
    x,y = int(pos[0]), int(pos[1])
    size = ch.get("size",12)
    gap = ch.get("gap",3)
    thick = ch.get("thickness",2)
    color = tuple(ch.get("color",[0,255,0]))
    style = ch.get("style","plus")
    if style == "plus":
        pygame.draw.line(SCREEN, color, (x-size-gap, y), (x-gap, y), thick)
        pygame.draw.line(SCREEN, color, (x+gap, y), (x+gap+size, y), thick)
        pygame.draw.line(SCREEN, color, (x, y-size-gap), (x, y-gap), thick)
        pygame.draw.line(SCREEN, color, (x, y+gap), (x, y+gap+size), thick)
    elif style == "circle":
        pygame.draw.circle(SCREEN, color, (x,y), size, thick)
    elif style == "dot":
        pygame.draw.circle(SCREEN, color, (x,y), max(2,size//2))

# ---------- target class ----------
class Target:
    def __init__(self, x, y, radius=18, pattern=None, speed=120, lifespan=None):
        self.x = x; self.y = y
        self.radius = radius
        self.pattern = pattern
        self.speed = speed
        self.angle = random.uniform(0, 2*math.pi)
        self.spawn = time.perf_counter()
        self.lifespan = lifespan
        self.anchor = (x,y)
    def update(self, dt):
        if self.pattern == "strafe":
            self.x += math.cos(self.angle + math.pi/2) * self.speed * dt
            self.y += math.sin(self.angle + math.pi/2) * self.speed * dt
        elif self.pattern == "linear":
            self.x += math.cos(self.angle) * self.speed * dt
            self.y += math.sin(self.angle) * self.speed * dt
        elif self.pattern == "circle":
            self.angle += 1.0 * dt
            self.x = self.anchor[0] + math.cos(self.angle) * self.speed
            self.y = self.anchor[1] + math.sin(self.angle) * self.speed
        elif self.pattern == "random":
            self.x += (random.random()-0.5) * self.speed * dt
            self.y += (random.random()-0.5) * self.speed * dt
        self.x = clamp(self.x, 10, WIN_W-10)
        self.y = clamp(self.y, 10, WIN_H-10)
    def alive(self):
        if self.lifespan is None: return True
        return (time.perf_counter() - self.spawn) < self.lifespan
    def draw(self):
        pygame.draw.circle(SCREEN, (220,60,60), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(SCREEN, (140,40,40), (int(self.x), int(self.y)), self.radius+6, 2)

# ---------- modes ----------
MODES = [
    {"id":"static_short","name":"Static Short","range":220,"moving":False},
    {"id":"static_long","name":"Static Long","range":420,"moving":False},
    {"id":"strafe_short","name":"Strafing Bots Short","range":220,"moving":True,"pattern":"strafe","speed":140},
    {"id":"strafe_long","name":"Strafing Bots Long","range":420,"moving":True,"pattern":"strafe","speed":180},
    {"id":"flick","name":"Flick-Only","range":300,"moving":False,"flick":True,"flick_time":0.45},
    {"id":"tracking","name":"Tracking Mode","range":300,"moving":True,"pattern":"linear","speed":120},
    {"id":"time_trial","name":"Time Trial (60s)","range":300,"moving":True,"pattern":"random","trial_time":60},
    {"id":"infinite","name":"Infinite Trainer","range":300,"moving":True,"pattern":"random","infinite":True}
]

# ---------- sensitivity conversion ----------
def convert_sensitivity(value, from_game, to_game, dpi=800):
    f = GAME_SCALE.get(from_game,1.0)
    t = GAME_SCALE.get(to_game,1.0)
    return value * (t/f) * (dpi/800.0)

# ---------- recoil ----------
def apply_recoil(cursor, pattern_name="assault", intensity=1.0):
    pattern = RECOIL_PATTERNS.get(pattern_name)
    if not pattern: return cursor
    dx,dy = random.choice(pattern)
    cursor[0] += dx * intensity
    cursor[1] += dy * intensity
    cursor[0] = clamp(cursor[0], 0, WIN_W)
    cursor[1] = clamp(cursor[1], 0, WIN_H)
    return cursor

# ---------- controller mapping (virtual cursor) ----------
virtual_cursor = [WIN_W//2, WIN_H//2]
use_controller = False
CONTROLLER_DEADZONE_MEASURE = 1.5  # seconds to sample

def measure_deadzone(joy, axis_hint=2, sample_time=CONTROLLER_DEADZONE_MEASURE):
    samples = []
    start = time.perf_counter()
    while time.perf_counter() - start < sample_time:
        pygame.event.pump()
        try:
            ax = joy.get_axis(axis_hint) if axis_hint < joy.get_numaxes() else joy.get_axis(0)
            samples.append(abs(ax))
        except Exception:
            samples.append(0.0)
        CLOCK.tick(200)
    if samples:
        med = sorted(samples)[len(samples)//2]
        mean = sum(samples)/len(samples)
        stdev = (sum((x-mean)**2 for x in samples)/len(samples))**0.5 if len(samples)>1 else 0.0
        recommended = clamp(med + 2*stdev, 0.0, 0.45)
        return {"median":med,"mean":mean,"stdev":stdev,"recommended_deadzone":recommended}
    return {"median":0,"mean":0,"stdev":0,"recommended_deadzone":0.05}

def controller_to_cursor(joy, cursor):
    try:
        na = joy.get_numaxes()
        if na >= 4:
            ax = joy.get_axis(2); ay = joy.get_axis(3)
        else:
            ax = joy.get_axis(0); ay = joy.get_axis(1)
    except Exception:
        return cursor
    mag = math.hypot(ax, ay)
    if mag < CONTROLLER_DEADZONE:
        return cursor
    scaled = (mag - CONTROLLER_DEADZONE) / (1 - CONTROLLER_DEADZONE)
    scaled = clamp(scaled, 0.0, 1.0)
    if USE_RADIAL and mag != 0:
        nx = (ax / mag) * (scaled ** CONTROLLER_ACCEL)
        ny = (ay / mag) * (scaled ** CONTROLLER_ACCEL)
    else:
        nx = math.copysign(abs(ax) ** CONTROLLER_ACCEL, ax)
        ny = math.copysign(abs(ay) ** CONTROLLER_ACCEL, ay)
    dx = nx * CONTROLLER_BASE_SPEED
    dy = ny * CONTROLLER_BASE_SPEED
    cursor[0] += dx
    cursor[1] += dy * -1.0  # invert Y for stick
    cursor[0] = clamp(cursor[0], 0, WIN_W)
    cursor[1] = clamp(cursor[1], 0, WIN_H)
    return cursor

# ---------- export dashboard ----------
def export_run_to_html_png(run_summary):
    if not MATPLOTLIB:
        print("Matplotlib not installed — cannot export charts.")
        return None
    times = [(s['time'] - run_summary['start']) for s in run_summary['shots']]
    errs = [s['error'] for s in run_summary['shots']]
    if not times:
        print("No shots to export.")
        return None
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1,1, figsize=(8,4))
    ax.plot(times, errs, marker='o')
    ax.set_xlabel("seconds"); ax.set_ylabel("error px"); ax.set_title("Per-shot error")
    fname = os.path.join(EXPORT_DIR, f"run_{run_summary['player']}_{int(time.time())}")
    png = fname + ".png"
    html = fname + ".html"
    fig.savefig(png); plt.close(fig)
    with open(html, "w") as f:
        f.write(f"<html><body><h2>Run: {run_summary['player']}</h2><p>Mode: {run_summary['mode']}</p><p>Score: {run_summary['score']}</p>")
        f.write(f"<img src='{os.path.basename(png)}'/>")
        f.write("</body></html>")
    print("Exported:", html)
    return html

# ---------- runner & UI ----------
def generate_targets(mode, count=20):
    center = (WIN_W//2, WIN_H//2)
    ring = mode.get("range",300)
    return generate_targets_at(center, ring, count, mode)

def generate_targets_at(center, ring_radius, count, mode):
    targets = []
    for _ in range(count):
        ang = random.uniform(0, 2*math.pi)
        r = random.uniform(ring_radius*0.6, ring_radius)
        x = center[0] + math.cos(ang) * r
        y = center[1] + math.sin(ang) * r
        pattern = mode.get("pattern") if mode.get("moving") else None
        lifespan = mode.get("flick_time") if mode.get("flick") else None
        t = Target(x,y, radius=mode.get("target_radius",18), pattern=pattern, speed=mode.get("speed",120), lifespan=lifespan)
        targets.append(t)
    return targets

def run_mode(mode):
    global virtual_cursor, use_controller, current_profile_name, profiles
    mode_name = mode['name']
    targets = generate_targets(mode, count=20)
    shots = []
    score = 0
    start = time.time()
    running = True
    infinite = bool(mode.get("infinite", False))
    trial_time = mode.get("trial_time", None)
    # if flick mode, spawn periodically
    flick_spawn_timer = 0.0
    while running:
        dt = CLOCK.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                save_profiles(); save_leaderboard(); pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False; break
                if ev.key == pygame.K_c:
                    use_controller = not use_controller
                if ev.key == pygame.K_s:
                    save_profiles(); save_leaderboard()
                if ev.key == pygame.K_d:
                    # measure deadzone quickly if controller present
                    if JOYSTICKS:
                        dz = measure_deadzone(JOYSTICKS[0])
                        profiles[current_profile_name]['calibration']['deadzone_measure'] = dz
                        save_profiles()
                        print("Deadzone measured:", dz)

        SCREEN.fill((18,18,18))
        draw_text(f"Mode: {mode_name}  (ESC to exit)", 16, 8, font=FONT_BIG)
        draw_text(f"Profile: {current_profile_name}  Score: {score} Shots: {len(shots)}", 16, 48)
        draw_text("C: toggle controller | S: save state | D: measure deadzone | E: export last run", 16, WIN_H-28)

        # cursor input
        if use_controller and JOYSTICKS:
            virtual_cursor = controller_to_cursor(JOYSTICKS[0], virtual_cursor)
            cursor = (int(virtual_cursor[0]), int(virtual_cursor[1]))
        else:
            cursor = pygame.mouse.get_pos()
            virtual_cursor = list(cursor)

        # update targets
        for t in list(targets):
            if t.pattern:
                t.update(dt)
            if t.lifespan and not t.alive():
                try: targets.remove(t)
                except: pass

        # flick spawn
        if mode.get('flick'):
            flick_spawn_timer -= dt
            if flick_spawn_timer <= 0:
                flick_spawn_timer = random.uniform(0.25, 0.9)
                targets.extend(generate_targets_at((WIN_W//2,WIN_H//2), mode.get('range',300), 1, mode))

        # draw targets
        for t in targets:
            t.draw()

        # crosshair (first vs third person feel influences style)
        ch = profiles[current_profile_name]['crosshair']
        render_crosshair(cursor, ch)

        # click detection (mouse or controller button)
        clicked = False
        if pygame.mouse.get_pressed()[0]:
            clicked = True
        if use_controller and JOYSTICKS:
            try:
                j = JOYSTICKS[0]
                for b in range(j.get_numbuttons()):
                    if j.get_button(b):
                        clicked = True
                        break
            except Exception:
                pass

        if clicked:
            now = time.time()
            hit = None
            for t in list(targets):
                if dist((t.x,t.y), cursor) <= t.radius:
                    hit = t; break
            if hit:
                error_px = dist((hit.x,hit.y), cursor)
                pts = max(0, int((hit.radius - error_px) * 10) + 50)
                shots.append({'time':now,'pos':cursor,'target':(hit.x,hit.y),'error':error_px,'pts':pts})
                score += pts
                try: targets.remove(hit)
                except: pass
                # apply recoil if desired (not enabled by default)
                if mode.get('apply_recoil'):
                    virtual_cursor = apply_recoil(virtual_cursor, mode.get('recoil','assault'))
            else:
                shots.append({'time':now,'pos':cursor,'target':None,'error':None,'pts':0})
            # debounce
            pygame.time.wait(120)

        # trial timer
        if trial_time:
            elapsed = time.time() - start
            draw_text(f"Time: {int(elapsed)} / {trial_time}s", WIN_W-220, 16)
            if elapsed >= trial_time:
                running = False

        # end conditions
        if (not infinite) and (len(targets) == 0) and (not mode.get('flick', False)):
            running = False

        pygame.display.flip()

    # run finished: export, record leaderboard
    run_summary = {'player':current_profile_name,'mode':mode_name,'start':start,'end':time.time(),'shots':shots,'score':score}
    leaderboard.append({'player':current_profile_name,'mode':mode_name,'score':score,'shots':len(shots),'time':datetime.utcnow().isoformat()})
    save_leaderboard()

    # CSV export per-run
    csv_path = os.path.join(EXPORT_DIR, f"run_{current_profile_name}_{int(time.time())}.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["time","x","y","tx","ty","error_px","pts"])
        for s in shots:
            if s['target']:
                w.writerow([s['time'], s['pos'][0], s['pos'][1], s['target'][0], s['target'][1], s['error'], s['pts']])
            else:
                w.writerow([s['time'], s['pos'][0], s['pos'][1], None, None, None, 0])

    # minimal end screen
    SCREEN.fill((18,18,18))
    draw_text("Run complete!", 40, 40, FONT_BIG)
    draw_text(f"Score: {score}  Shots: {len(shots)}", 40, 96)
    draw_text("Press any key to continue...", 40, 140)
    pygame.display.flip()
    wait_for_key()
    # attach run_summary for export if user presses E later
    globals()['last_run'] = run_summary
    return run_summary

def wait_for_key():
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                save_profiles(); save_leaderboard(); pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                return
        CLOCK.tick(30)

# ---------- profile manager ----------
def profile_manager():
    global current_profile_name, profiles
    keys = list(profiles.keys())
    if not keys:
        profiles["Player"] = default_profile("Player")
        save_profiles(); keys = list(profiles.keys())
    idx = 0
    while True:
        SCREEN.fill((16,16,16))
        draw_text("Profiles (Enter select / N new / D delete / Esc back)", 20, 12, font=FONT_BIG)
        for i, name in enumerate(keys):
            color = (255,255,0) if i==idx else (200,200,200)
            draw_text(f"{'> ' if i==idx else '   '}{name}", 40, 80 + i*32, color=color)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                save_profiles(); save_leaderboard(); pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_DOWN: idx = (idx+1) % len(keys)
                if ev.key == pygame.K_UP: idx = (idx-1) % len(keys)
                if ev.key == pygame.K_RETURN:
                    current_profile_name = keys[idx]; return
                if ev.key == pygame.K_n:
                    name = "Player_" + datetime.utcnow().strftime("%H%M%S")
                    profiles[name] = default_profile(name); keys = list(profiles.keys()); idx = keys.index(name); save_profiles()
                if ev.key == pygame.K_d:
                    to_del = keys[idx]
                    if to_del in profiles and to_del != current_profile_name:
                        del profiles[to_del]; keys = list(profiles.keys()); idx = 0; save_profiles()
                if ev.key == pygame.K_ESCAPE:
                    return
        CLOCK.tick(30)

# ---------- leaderboard UI ----------
def show_leaderboard():
    sorted_lb = sorted(leaderboard, key=lambda x: x.get('score',0), reverse=True)[:50]
    page = 0; per_page = 10
    while True:
        SCREEN.fill((12,12,12))
        draw_text("Leaderboard (N/P next/prev, Esc back)", 20, 12, font=FONT_BIG)
        start = page * per_page
        for i, entry in enumerate(sorted_lb[start:start+per_page]):
            y = 80 + i*36
            draw_text(f"{start+i+1}. {entry['player']} | {entry['mode']} | Score: {entry['score']} | Shots: {entry['shots']}", 40, y)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                save_profiles(); save_leaderboard(); pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: return
                if ev.key == pygame.K_n: page = min(page+1, max(0,(len(sorted_lb)-1)//per_page))
                if ev.key == pygame.K_p: page = max(0, page-1)
        CLOCK.tick(30)

# ---------- post-run advice ----------
def advice_after_run(run_summary):
    shots = run_summary.get('shots',[])
    errs = [s['error'] for s in shots if s['error'] is not None]
    avg_err = sum(errs)/len(errs) if errs else 0
    SCREEN.fill((16,16,16))
    draw_text("Run Summary & Advice", 20, 12, font=FONT_BIG)
    draw_text(f"Player: {run_summary['player']}", 20, 60)
    draw_text(f"Mode: {run_summary['mode']}  Score: {run_summary['score']}", 20, 96)
    draw_text(f"Average error (px): {avg_err:.1f}", 20, 132)
    y = 170
    if avg_err <= 10:
        draw_text("- Excellent precision. Focus on consistency and tracking.", 20, y); y += 28
    elif avg_err <= 25:
        draw_text("- Good. Consider slightly lowering sensitivity for micro adjustments.", 20, y); y += 28
    else:
        draw_text("- High error. Lower sensitivity / DPI and practice short-range micro drills.", 20, y); y += 28
    draw_text("- Exercises: 5 min tracking, 5 min flicks, 5 min time trials.", 20, y+28)
    draw_text("Press any key to continue...", 20, y+60)
    pygame.display.flip()
    wait_for_key()

# ---------- main menu ----------
def main_menu():
    mode_idx = 0
    global current_profile_name
    while True:
        SCREEN.fill((10,10,10))
        draw_text("Aim Trainer & Calibrator — Main Menu", 20, 12, font=FONT_BIG)
        draw_text("TAB cycle modes • ENTER start • P profiles • L leaderboard • Q quit", 20, 48)
        for i, m in enumerate(MODES):
            color = (255,255,0) if i==mode_idx else (200,200,200)
            draw_text(f"{'> ' if i==mode_idx else '   '}{m['name']}", 40, 120 + i*36, color=color)
        draw_text(f"Current profile: {current_profile_name}", 40, WIN_H-60)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                save_profiles(); save_leaderboard(); pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_TAB:
                    mode_idx = (mode_idx + 1) % len(MODES)
                if ev.key == pygame.K_RETURN:
                    run_summary = run_mode(MODES[mode_idx])
                    globals()['last_run'] = run_summary
                    advice_after_run(run_summary)
                if ev.key == pygame.K_p:
                    profile_manager()
                if ev.key == pygame.K_l:
                    show_leaderboard()
                if ev.key == pygame.K_q:
                    save_profiles(); save_leaderboard(); pygame.quit(); sys.exit()
        CLOCK.tick(30)

# ---------- startup ----------
if __name__ == "__main__":
    if not profiles:
        profiles["Player"] = default_profile("Player")
        save_profiles()
    print("Aim Trainer & Calibrator — starting")
    print("Controls: TAB cycle modes -> ENTER start, P profiles, L leaderboard, Q quit.")
    main_menu()
