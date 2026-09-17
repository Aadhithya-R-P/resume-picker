"""Small, process-local limits for a single-worker portfolio deployment."""

from collections import deque
from threading import Lock
from time import monotonic

MAX_JD_CHARACTERS = 10_000
MAX_RESUME_CHARACTERS = 30_000
MAX_PDF_PAGES = 10


class UsageLimiter:
    """Atomically reserve one attempt across all rolling time windows."""

    def __init__(self, windows, clock=monotonic):
        self.windows = [(limit, seconds, deque()) for limit, seconds in windows]
        self.clock = clock
        self.lock = Lock()

    def reserve(self):
        with self.lock:
            now = self.clock()
            for _, seconds, attempts in self.windows:
                while attempts and attempts[0] <= now - seconds:
                    attempts.popleft()
            if any(len(attempts) >= limit for limit, _, attempts in self.windows):
                return False
            for _, _, attempts in self.windows:
                attempts.append(now)
            return True


class AnalysisAdmission:
    def __init__(self):
        self.usage = UsageLimiter([(10, 60)])
        self.slot = Lock()


analysis_admission = AnalysisAdmission()
ai_usage = UsageLimiter([(2, 60), (15, 24 * 60 * 60)])
