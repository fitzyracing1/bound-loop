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

## Plans

This project is free, and its license stays as is. Support it through [GitHub Sponsors](https://github.com/sponsors/fitzyracing1):

- **Free**: use the code, community support.
- **Pro ($49/month)**: priority issues and support.
- **Team ($199/month)**: priority support for your team plus early access.
