import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bound_loop import Bucket, Oracle, Loop


def act(name, result, target="ci"):
    return {"name": name, "target": target, "fn": lambda: result}


class TenetsReport(unittest.TestCase):
    def test_lit_run_is_online(self):
        loop = Loop(Bucket({"ci"}, 3), Oracle(lambda g, m: [act("a", "success")]))
        self.assertIsNotNone(loop.step("g"))
        self.assertEqual(loop.tenets["code"], "0000")
        self.assertEqual(loop.tenets["status"], "AI online")
        self.assertEqual(loop.tenets["totals"]["steps"], 1)

    def test_no_lit_action_darkens_theory(self):
        loop = Loop(Bucket({"ci"}, 3), Oracle(lambda g, m: [act("a", "fail")]))
        self.assertIsNone(loop.step("g"))
        self.assertEqual(loop.tenets["code"][3], "1")

    def test_bridge_limit(self):
        acts = [act("a", "fail"), act("b", "success")]
        loop = Loop(Bucket({"ci"}, 5), Oracle(lambda g, m: acts), limits={"bridge": 1})
        loop.step("g")
        self.assertEqual(loop.tenets["code"], "0100")

    def test_report_each_run(self):
        loop = Loop(Bucket({"ci"}, 5), Oracle(lambda g, m: [act("a", "success")]))
        loop.step("g"); loop.step("g")
        self.assertEqual(loop.tenets["totals"]["steps"], 1)


if __name__ == "__main__":
    unittest.main()
