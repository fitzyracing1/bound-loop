# bound-loop

A tiny, dependency-free Python loop for letting an AI try fixes safely.

## The four parts

- **Bucket** – the fence. It lists which targets may be touched and how many steps may be taken. Anything outside the fence is skipped.
- **Oracle** – the idea maker. It wraps an LLM call and proposes actions. It sees what was tried before (memory).
- **Driver** – the hands. It runs one action.
- **Checker** – the light. A result of `success` is **lit**; anything else is **dark**.

The **Loop** ties them together: ask the Oracle, skip what the Bucket forbids, spend a step, run it, read the light, remember it, and stop at the first lit action (or return `None`).

## Usage

```python
from bound_loop import Bucket, Oracle, Loop

def ask(goal, memory):
    return [{"name": "bump_dep", "target": "ci", "fn": lambda: "success"}]

loop = Loop(Bucket({"ci"}, max_steps=3), Oracle(ask))
print(loop.step("make the CI light lit"))  # the lit action
print(loop.memory)                          # {'bump_dep': 'lit'}
```

Run tests: `python -m unittest discover -s tests -v`

## Tenets report

Every `Loop.step()` run is measured against the [Four Tenets of AI](https://github.com/fitzyracing1/ai-tenets) (Cost, Bridge, Work, Theory — each as low as possible) with a vendored, zero-dependency `tenets_meter.py`. Each Oracle call and Driver run counts as a hop, each spent Bucket step as work, and a run that finds no lit action leaves an unproven claim.

```python
loop.step("make the CI light lit")
print(loop.tenets["code"], loop.tenets["status"])  # 0000 AI online
```

Pass `limits={"cost": ..., "bridge": ..., "work": ..., "theory": ...}` to `Loop`; `work` defaults to the Bucket's `max_steps`.
