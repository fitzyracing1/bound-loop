"""bound_loop: a tiny bounded agent loop. No dependencies."""


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
    def __init__(self, bucket, oracle=None, driver=None, checker=None):
        self.bucket = bucket
        self.oracle = oracle or Oracle()
        self.driver = driver or Driver()
        self.checker = checker or Checker()
        self.memory = {}

    def step(self, goal):
        for action in self.oracle.propose(goal, self.memory):
            if self.bucket.steps >= self.bucket.max_steps:
                break
            if not self.bucket.permits(action):
                continue
            self.bucket.spend()
            light = self.checker.light(self.driver.run(action))
            self.memory[action["name"]] = light
            if light == "lit":
                return action
        return None
