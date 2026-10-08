import random
import pygame

class Round:
    def __init__(self, min_wait_ms=1000, max_wait_ms=3000):
        self.wait_delay_ms = random.randint(min_wait_ms, max_wait_ms)
        self.state = "waiting"  # "waiting" -> "go" -> "result"
        self.start_time = pygame.time.get_ticks()
        self.go_time = None
        self.reaction_ms = None
        self.false_start = False  # True if the player reacted during the grey wait screen

    def update(self):
        if self.state == "waiting":
            now = pygame.time.get_ticks()
            if now - self.start_time >= self.wait_delay_ms:
                self.state = "go"
                self.go_time = now

    def register_input(self):
        """Handle a click/Space press.

        Returns the reaction time in ms for a genuine reaction (after "go"),
        or None if the input was a false start (during the "waiting" phase)
        or the round is already finished.
        """
        if self.state == "waiting":
            # Reacted before the screen turned green: no time is recorded.
            self.false_start = True
            self.state = "result"
            return None

        if self.state == "go":
            # Measure from the moment the screen turned green.
            now = pygame.time.get_ticks()
            self.reaction_ms = now - self.go_time
            self.state = "result"
            return self.reaction_ms

        return None