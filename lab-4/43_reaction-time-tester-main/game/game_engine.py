import pygame
from .round import Round

# Game Engine

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)
RED = (190, 60, 60)

class GameEngine:
    def __init__(self, width, height, rounds_total=5, min_wait_ms=1000, max_wait_ms=3000):
        self.width = width
        self.height = height

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        self.round = Round(self.min_wait_ms, self.max_wait_ms)
        self.reaction_times = []

        self.result_shown_at = None
        self.result_pause_ms = 800  # brief pause on the result screen between rounds

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)
        self.small_font = pygame.font.SysFont("Arial", 24)
        self.game_over = False

        # Results screen: ignore input briefly so a stray click right as the
        # screen appears can't dismiss it, then wait for a key/click to close.
        self.game_over_at = None
        self.game_over_input_delay_ms = 500
        self.quit_requested = False

    def handle_event(self, event):
        is_click = event.type == pygame.MOUSEBUTTONDOWN
        is_space = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
        is_key = event.type == pygame.KEYDOWN

        if self.game_over:
            # Any key press or click on the results screen closes the game.
            if is_click or is_key:
                now = pygame.time.get_ticks()
                if now - self.game_over_at >= self.game_over_input_delay_ms:
                    self.quit_requested = True
            return

        if (is_click or is_space) and self.round.state != "result":
            reaction_ms = self.round.register_input()
            # Only genuine reactions (after "go") are recorded; a false start
            # returns None and is not stored, so that round gets replayed.
            if reaction_ms is not None:
                self.reaction_times.append(reaction_ms)
            self.result_shown_at = pygame.time.get_ticks()

    def handle_input(self):
        # Reserved for continuously-held-key input; every action here
        # is a discrete click/keypress, handled in handle_event.
        pass

    def update(self):
        if self.game_over:
            return

        self.round.update()

        if self.round.state == "result":
            now = pygame.time.get_ticks()
            if now - self.result_shown_at >= self.result_pause_ms:
                self._start_next_round()

    def _start_next_round(self):
        if len(self.reaction_times) >= self.rounds_total:
            self.game_over = True
            self.game_over_at = pygame.time.get_ticks()
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

        # One line per recorded reaction time.
        y = 100
        for i, ms in enumerate(self.reaction_times, start=1):
            line = self.font.render(f"Round {i}: {ms} ms", True, WHITE)
            screen.blit(line, line.get_rect(center=(self.width // 2, y)))
            y += 32

        avg = self.font.render(f"Average: {self.average_reaction_ms()} ms", True, WHITE)
        screen.blit(avg, avg.get_rect(center=(self.width // 2, self.height - 90)))

        prompt = self.small_font.render("Press any key or click to exit", True, WHITE)
        screen.blit(prompt, prompt.get_rect(center=(self.width // 2, self.height - 35)))

    def render(self, screen):
        if self.game_over:
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