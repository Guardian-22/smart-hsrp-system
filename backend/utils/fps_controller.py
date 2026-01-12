import time
# Note currently unit testing is only applied to TimeBasedFPSController.

class TimeBasedFPSController:
    def __init__(self, target_fps=8):
        self.interval = 1.0 / target_fps  # seconds per frame
        self.last_time = 0

    def should_process(self):
        now = time.time()
        if self.last_time == 0:   # This avoids skipping the first frame.
            self.last_time = now
            return True
        
        if now - self.last_time >= self.interval:
            self.last_time = now
            return True
        return False


class FrameSkipController:
    def __init__(self, input_fps=30, target_fps=8):
        self.skip_every = input_fps // target_fps
        self.counter = 0

    def should_process(self):
        self.counter += 1
        if self.counter >= self.skip_every:
            self.counter = 0
            return True
        return False
