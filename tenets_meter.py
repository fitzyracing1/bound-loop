# Vendored from https://github.com/fitzyracing1/ai-tenets (tenets_meter 0.1.0), MIT.
"""tenets_meter: measure an AI run against the Four Tenets (Cost, Bridge, Work, Theory).

Zero dependencies. MIT (c) 2026 Joshua Almeida. https://github.com/fitzyracing1/ai-tenets

Active-low 4-bit code, MSB->LSB Cost Bridge Work Theory: 0 = lit (at its minimum), 1 = dark.
Extended byte: 2 bits per tenet: 00 none, 01 low (within limit), 10 high (over limit),
11 over limit (more than 2x the limit). A tenet is dark when its pair is 10 or 11.
"""
import functools

__version__ = "0.1.0"
TENETS = ("cost", "bridge", "work", "theory")
LEVELS = ("none", "low", "high", "over limit")
DEFAULT_LIMITS = {"cost": 1.0, "tokens": None, "bridge": 3, "work": 10, "theory": 0}


def level(value, limit):
    """Return the 2-bit level (0..3) of a value against its limit."""
    if not value:
        return 0
    if limit is None:
        return 1
    if value <= limit:
        return 1
    if value <= 2 * limit:
        return 2
    return 3


def decode4(code):
    code = str(code).zfill(4)
    out = {t: ("dark" if code[i] == "1" else "lit") for i, t in enumerate(TENETS)}
    dark = [t for i, t in enumerate(TENETS) if code[i] == "1"]
    out["status"] = status_of(code, dark)
    return out


def decode8(byte):
    if isinstance(byte, str):
        byte = int(byte, 16) if byte.lower().startswith("0x") else int(byte, 2)
    pairs = [(byte >> (6 - 2 * i)) & 3 for i in range(4)]
    out = {t: LEVELS[p] for t, p in zip(TENETS, pairs)}
    out["code4"] = "".join("1" if p >= 2 else "0" for p in pairs)
    return out


def status_of(code, dark):
    if code == "0000":
        return "AI online"
    if code == "1111":
        return "fully dark"
    return "dark: " + ", ".join(dark)


class Meter:
    """Record a run; read .code (4-bit), .byte (8-bit int), .status, .report().

    Use as a context manager (`with Meter() as m:`) or decorator (`@Meter(...)`).
    """

    def __init__(self, limits=None):
        self.limits = dict(DEFAULT_LIMITS)
        self.limits.update(limits or {})
        self.reset()

    def reset(self):
        self.usd = 0.0
        self.tokens = 0
        self.hops = 0
        self.steps = 0
        self.unverified = 0
        self.verified = 0

    # recording
    def cost(self, usd=0.0, tokens=0):
        self.usd += usd
        self.tokens += tokens

    def hop(self, n=1):
        self.hops += n

    def step(self, n=1):
        self.steps += n

    def claim(self, verified=False):
        if verified:
            self.verified += 1
        else:
            self.unverified += 1

    # reading
    def levels(self):
        c = max(level(self.usd, self.limits["cost"]),
                level(self.tokens, self.limits.get("tokens")))
        return {
            "cost": c,
            "bridge": level(self.hops, self.limits["bridge"]),
            "work": level(self.steps, self.limits["work"]),
            "theory": 0 if not self.unverified else
            (1 if self.unverified <= self.limits["theory"] else
             (3 if self.unverified > 2 * max(self.limits["theory"], 1) else 2)),
        }

    @property
    def byte(self):
        lv = self.levels()
        b = 0
        for t in TENETS:
            b = (b << 2) | lv[t]
        return b

    @property
    def code(self):
        return decode8(self.byte)["code4"]

    @property
    def status(self):
        c = self.code
        return status_of(c, [t for i, t in enumerate(TENETS) if c[i] == "1"])

    @property
    def online(self):
        return self.code == "0000"

    def report(self):
        return {
            "code": self.code,
            "byte": "0x%02x" % self.byte,
            "bits8": format(self.byte, "08b"),
            "status": self.status,
            "levels": {t: LEVELS[v] for t, v in self.levels().items()},
            "totals": {"usd": self.usd, "tokens": self.tokens, "hops": self.hops,
                       "steps": self.steps, "unverified_claims": self.unverified,
                       "verified_claims": self.verified},
        }

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __call__(self, fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            self.reset()
            return fn(*a, **kw)
        wrapper.meter = self
        return wrapper

    @classmethod
    def from_log(cls, log):
        """Build a Meter from a run log dict: {"limits": {...}, "events": [...]} or totals."""
        m = cls(log.get("limits"))
        for e in log.get("events", []):
            t = e.get("type")
            if t == "cost":
                m.cost(e.get("usd", 0.0), e.get("tokens", 0))
            elif t == "hop":
                m.hop(e.get("n", 1))
            elif t == "step":
                m.step(e.get("n", 1))
            elif t == "claim":
                m.claim(bool(e.get("verified", False)))
        tot = log.get("totals", {})
        m.cost(tot.get("usd", 0.0), tot.get("tokens", 0))
        m.hop(tot.get("hops", 0))
        m.step(tot.get("steps", 0))
        m.unverified += tot.get("unverified_claims", 0)
        return m
