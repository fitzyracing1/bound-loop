import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bound_loop import Bucket, Oracle, Driver, Checker, Loop


def actions(log):
    def mk(name, target, result):
        def fn():
            log.append(name)
            return result
        return {"name": name, "target": target, "fn": fn}
    return [mk("rm_prod", "prod", "success"),
            mk("dark_fix", "ci", "failure"),
            mk("lit_fix", "ci", "success")]


class TestLoop(unittest.TestCase):
    def test_dark_ci_turns_lit(self):
        log, seen = [], []
        def ask(goal, memory):
            seen.append(memory)
            return actions(log)
        loop = Loop(Bucket({"ci"}, 5), Oracle(ask))
        got = loop.step("light the CI")
        self.assertEqual(got["name"], "lit_fix")
        self.assertEqual(loop.memory, {"dark_fix": "dark", "lit_fix": "lit"})
        self.assertNotIn("rm_prod", log)
        self.assertEqual(loop.bucket.steps, 2)
        loop.step("again")
        self.assertIn("dark_fix", seen[1])  # memory fed back

    def test_max_steps_stops(self):
        log = []
        loop = Loop(Bucket({"ci"}, 1), Oracle(lambda g, m: actions(log)))
        self.assertIsNone(loop.step("light the CI"))
        self.assertEqual(log, ["dark_fix"])
        self.assertEqual(loop.bucket.steps, 1)

    def test_defaults(self):
        self.assertEqual(Oracle().propose("g", {}), [])
        self.assertEqual(Checker().light("success"), "lit")
        self.assertEqual(Checker().light("nope"), "dark")
        self.assertEqual(Driver().run({"fn": lambda: 7}), 7)
        b = Bucket({"ci"}, 1); b.spend()
        self.assertRaises(RuntimeError, b.spend)


if __name__ == "__main__":
    unittest.main()
