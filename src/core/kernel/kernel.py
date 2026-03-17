from typing import Protocol, TypeVar, Generic

S = TypeVar("S")  # State
A = TypeVar("A")  # Action
O = TypeVar("O")  # Observation


class Transition(Protocol[S, A]):
    def __call__(self, state: S, action: A) -> S:
        ...


class Observation(Protocol[S, O]):
    def __call__(self, state: S) -> O:
        ...


class Policy(Protocol[O, A]):
    def __call__(self, observation: O) -> A:
        ...