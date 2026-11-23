"""Exponential backoff with jitter."""
import random


def backoff_delay(attempt, base=4.0, cap=300.0):
    return min(cap, base * 2 ** attempt) * random.uniform(0.8, 1.2)
