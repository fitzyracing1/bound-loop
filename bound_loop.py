"""bound_loop: a tiny bounded agent loop. No dependencies."""

from tenets_meter import Meter


class Bucket:
    """Limits what the loop may touch and how many steps it may take."""

    def __init__(self, allowed_targets, max_steps):
        self.allowed_targets = set(allowed_targets)
        self.max_steps = max_steps
        self.steps = 0

    def permits(self, action):
        return (action.get("target") in self.allowed_targets
                and self.steps < self.max_steps)

    def spend(self):
        if self.steps >= self.max_steps:
            raise RuntimeError("bucket empty")
        self.steps += 1


class Oracle:
    """Wraps an LLM callable: ask(goal, memory) -> list of actions."""

    def __init__(self, ask=None):
        self.ask = ask or (lambda goal, memory: [])

    def propose(self, goal, memory):
        return list(self.ask(goal, dict(memory)))


class Driver:
    """Runs an action by calling action['fn']()."""

    def run(self, action):
        return action["fn"]()


class Checker:
    """Reads the light: 'lit' on success, otherwise 'dark'."""

    def light(self, result):
        return "lit" if result == "success" else "dark"


class Loop:
    def __init__(self, bucket, oracle=None, driver=None, checker=None, limits=None):
        self.bucket = bucket
        self.oracle = oracle or Oracle()
        self.driver = driver or Driver()
        self.checker = checker or Checker()
        self.memory = {}
        self.limits = dict(limits or {})
        self.limits.setdefault("work", bucket.max_steps)
        self.meter = None
        self.tenets = None

    def step(self, goal):
        """Run one bounded pass; afterwards self.tenets holds the run's tenets report."""
        self.meter = Meter(self.limits)
        try:
            return self._run(goal)
        finally:
            self.tenets = self.meter.report()

    def _run(self, goal):
        m = self.meter
        m.hop()  # oracle call
        for action in self.oracle.propose(goal, self.memory):
            if self.bucket.steps >= self.bucket.max_steps:
                break
            if not self.bucket.permits(action):
                continue
            self.bucket.spend()
            m.step()
            m.hop()  # driver run
            light = self.checker.light(self.driver.run(action))
            m.claim(verified=True)  # result was read by the Checker
            self.memory[action["name"]] = light
            if light == "lit":
                return action
        m.claim(verified=False)  # no lit action: the goal is still unproven
        return None
