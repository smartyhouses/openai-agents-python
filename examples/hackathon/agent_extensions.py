from agents.agent import Agent
from examples.hackathon.types import TestCase


def add_method(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator

@add_method(Agent)
def generate_tests(self, test_cases: list[TestCase]):
    pass
