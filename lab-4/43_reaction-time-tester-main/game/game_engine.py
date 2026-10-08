import math
from array import array

import pygame
from .round import Round

# Game Engine

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)
RED = (190, 60, 60)

# Difficulty settings: wait-time range (ms) and number of rounds.
# Easy: longer but narrow (predictable) waits, fewer rounds.
# Hard: wide (unpredictable) waits, more rounds.
DIFFICULTIES = {
    "Easy":   {"min_wait_ms": 2000, "max_wait_ms": 3000, "rounds": 3},
    "Medium": {"min_wait_ms": 1000, "max_wait_ms": 3000, "rounds": 5},
    "Hard":   {"min_wait_ms": 500,  "max_wait_ms": 5000, "rounds": 10},
}

# Keys on the difficulty menu (main row and keypad).
DIFFICULTY_KEYS = {
    pygame.K_1: "Easy", pygame.K_KP1: "Easy",
    pygame.K_2: "Medium", pygame.K_KP2: "Medium",
    pygame.K_3: "Hard", pygame.K_KP3: "Hard",
}


class SoundEffects:
    """Generates the three sound effects in code (no audio files needed).

    If the mixer can't be initialised or a sound can't be built, `enabled`
    stays False and every play_* call quietly does nothing.
    """

    def __init__(self):
        self.enabled = False
        self.beep = None
        self.buzz = None
        self.jingle = None
        try:
            # pygame.init() normally starts the mixer already; try once more if not.
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            mixer_settings = pygame.mixer.get_init()
            if mixer_settings is None:
                return
            self.sample_rate, sample_format, self.channels = mixer_settings
            if sample_format != -16:  # only signed 16-bit output is generated here
                return

            # Sounds are built once at startup, so nothing is computed at "go" time.
            self.beep = self._build([(880, 120)], "sine", 0.30)
            self.buzz = self._build([(140, 260)], "square", 0.20)
            self.jingle = self._build(
                [(523, 110), (659, 110), (784, 110), (1047, 260)], "sine", 0.30
            )
            self.enabled = True
        except Exception:
            # No audio device, driver problem, etc.: carry on without sound.
            self.enabled = False
            self.beep = self.buzz = self.jingle = None

    def _build(self, notes, wave, volume):
        """Build a pygame Sound from a list of (frequency_hz, duration_ms) notes."""
        samples = array("h")
        ramp = max(1, int(self.sample_rate * 0.005))  # 5 ms fade in/out avoids clicks
        for freq, duration_ms in notes:
            count = int(self.sample_rate * duration_ms / 1000)
            for i in range(count):
                value = math.sin(2 * math.pi * freq * i / self.sample_rate)
                if wave == "square":
                    value = 1.0 if value >= 0 else -1.0
                envelope = min(1.0, i / ramp, (count - i) / ramp)
                sample = int(32767 * volume * envelope * value)
                for _ in range(self.channels):  # duplicate for stereo mixers
                    samples.append(sample)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _play(self, sound):
        if not self.enabled or sound is None:
            return
        try:
            sound.play()  # non-blocking: returns immediately
        except pygame.error:
            pass

    def play_go(self):
        self._play(self.beep)

    def play_false_start(self):
        self._play(self.buzz)

    def play_complete(self):
        self._play(self.jingle)


class GameEngine:
    def __init__(self, width, height, rounds_total=5, min_wait_ms=1000, max_wait_ms=3000):
        self.width = width
        self.height = height

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        self.round = Round(self.min_wait_ms, self.max_wait_ms)
        self.reaction_times = []
        self.false_starts = 0

        self.result_shown_at = None
        self.result_pause_ms = 800  # brief pause on the result screen between rounds

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)
        self.small_font = pygame.font.SysFont("Arial", 24)
        self.game_over = False

        # Results screen: ignore input briefly so a stray key/click right as the
        # screen appears can't trigger an option before it has been seen.
        self.game_over_at = None
        self.game_over_input_delay_ms = 500
        self.in_menu = False  # True while the difficulty menu is showing
        self.quit_requested = False

        self.sounds = SoundEffects()

    def _start_session(self, difficulty_name):
        """Start a fresh session with the chosen difficulty."""
        settings = DIFFICULTIES[difficulty_name]
        self.rounds_total = settings["rounds"]
        self.min_wait_ms = settings["min_wait_ms"]
        self.max_wait_ms = settings["max_wait_ms"]

        self.reaction_times = []
        self.false_starts = 0
        self.result_shown_at = None
        self.game_over = False
        self.game_over_at = None
        self.in_menu = False
        self.round = Round(self.min_wait_ms, self.max_wait_ms)

    def _handle_results_key(self, key):
        now = pygame.time.get_ticks()
        if now - self.game_over_at < self.game_over_input_delay_ms:
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.in_menu = True
        elif key == pygame.K_ESCAPE:
            self.quit_requested = True

    def _handle_menu_key(self, key):
        if key == pygame.K_ESCAPE:
            self.quit_requested = True
        elif key in DIFFICULTY_KEYS:
            self._start_session(DIFFICULTY_KEYS[key])

    def handle_event(self, event):
        is_click = event.type == pygame.MOUSEBUTTONDOWN
        is_space = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
        is_key = event.type == pygame.KEYDOWN

        if self.game_over:
            # Results screen and difficulty menu are keyboard-driven.
            if is_key:
                if self.in_menu:
                    self._handle_menu_key(event.key)
                else:
                    self._handle_results_key(event.key)
            return

        if (is_click or is_space) and self.round.state != "result":
            reaction_ms = self.round.register_input()
            # Only genuine reactions (after "go") are recorded; a false start
            # returns None and is not stored, so that round gets replayed.
            if reaction_ms is not None:
                self.reaction_times.append(reaction_ms)
            else:
                self.false_starts += 1
                self.sounds.play_false_start()  # buzz, once per false start
            self.result_shown_at = pygame.time.get_ticks()

    def handle_input(self):
        # Reserved for continuously-held-key input; every action here
        # is a discrete click/keypress, handled in handle_event.
        pass

    def update(self):
        if self.game_over:
            return

        previous_state = self.round.state
        self.round.update()
        if previous_state == "waiting" and self.round.state == "go":
            # The screen turns green on this frame: play the go beep exactly once.
            self.sounds.play_go()

        if self.round.state == "result":
            now = pygame.time.get_ticks()
            if now - self.result_shown_at >= self.result_pause_ms:
                self._start_next_round()

    def _start_next_round(self):
        if len(self.reaction_times) >= self.rounds_total:
            self.game_over = True
            self.game_over_at = pygame.time.get_ticks()
            self.sounds.play_complete()  # jingle, once, as the results screen begins
            return
        # After a false start nothing was recorded, so this replays the same round number.
        self.round = Round(self.min_wait_ms, self.max_wait_ms)

    def average_reaction_ms(self):
        if not self.reaction_times:
            return 0
        return round(sum(self.reaction_times) / len(self.reaction_times))

    def _render_results(self, screen):
        screen.fill(BLUE)

        title = self.big_font.render("Session Complete", True, WHITE)
        screen.blit(title, title.get_rect(center=(self.width // 2, 45)))

        # One line per recorded reaction time; use two columns for long sessions.
        times = self.reaction_times
        columns = 2 if len(times) > 6 else 1
        per_column = (len(times) + columns - 1) // columns
        for i, ms in enumerate(times):
            col, row = divmod(i, per_column)
            x = self.width * (2 * col + 1) // (2 * columns)
            line = self.font.render(f"Round {i + 1}: {ms} ms", True, WHITE)
            screen.blit(line, line.get_rect(center=(x, 100 + row * 32)))

        avg = self.font.render(f"Average: {self.average_reaction_ms()} ms", True, WHITE)
        screen.blit(avg, avg.get_rect(center=(self.width // 2, self.height - 100)))

        fs = self.small_font.render(f"False starts: {self.false_starts}", True, WHITE)
        screen.blit(fs, fs.get_rect(center=(self.width // 2, self.height - 65)))

        prompt = self.small_font.render("ENTER: play again    ESC: exit", True, WHITE)
        screen.blit(prompt, prompt.get_rect(center=(self.width // 2, self.height - 30)))

    def _render_menu(self, screen):
        screen.fill(BLUE)

        title = self.big_font.render("Choose Difficulty", True, WHITE)
        screen.blit(title, title.get_rect(center=(self.width // 2, 55)))

        y = 135
        for number, (name, s) in enumerate(DIFFICULTIES.items(), start=1):
            wait_lo = s["min_wait_ms"] / 1000
            wait_hi = s["max_wait_ms"] / 1000
            text = f"{number} - {name}: {wait_lo:.1f}-{wait_hi:.1f} s wait, {s['rounds']} rounds"
            line = self.font.render(text, True, WHITE)
            screen.blit(line, line.get_rect(center=(self.width // 2, y)))
            y += 55

        prompt = self.small_font.render("Press 1, 2 or 3 to start    ESC: exit", True, WHITE)
        screen.blit(prompt, prompt.get_rect(center=(self.width // 2, self.height - 30)))

    def render(self, screen):
        if self.game_over:
            if self.in_menu:
                self._render_menu(screen)
            else:
                self._render_results(screen)
            return

        if self.round.state == "waiting":
            bg = GRAY
            message = "Wait for green..."
        elif self.round.state == "go":
            bg = GREEN
            message = "Click now!"
        elif self.round.false_start:
            bg = RED
            message = "False start!"
        else:
            bg = BLUE
            message = f"{self.round.reaction_ms} ms"

        screen.fill(bg)

        text_surf = self.big_font.render(message, True, WHITE)
        text_rect = text_surf.get_rect(center=(self.width // 2, self.height // 2))
        screen.blit(text_surf, text_rect)

        round_num = min(len(self.reaction_times) + 1, self.rounds_total)
        round_text = self.font.render(f"Round {round_num}/{self.rounds_total}", True, WHITE)
        screen.blit(round_text, (10, 10))

        avg_text = self.font.render(f"Avg: {self.average_reaction_ms()} ms", True, WHITE)
        screen.blit(avg_text, (self.width - 190, 10))