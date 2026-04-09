from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

from ..domain.dynamics.actions import WaitAction
from ..app.policies import Policy
from ..app.agent import SchedulerAgent
from ..domain.world.scheduler import SchedulerWorld, ExecutionResult


class StepStatus(Enum):
    ADVANCED = auto()
    FINISHED = auto()
    PAUSED = auto()


@dataclass(frozen=True)
class StepResult:
    status: StepStatus
    result: ExecutionResult | None = None


class Simulator:
    """
    Application service.

    Responsible for:
    - driving the world step by step
    - coordinating agent decision and world execution
    - optionally running until terminal / paused
    """

    def __init__(
        self,
        agent: SchedulerAgent | None = None,
        world: SchedulerWorld | None = None,
    ) -> None:
        self._agent = agent if agent is not None else SchedulerAgent()

        if world is not None:
            self._world = world
        else:
            self._world, _ = SchedulerWorld.create()

    def update_policy(self, policy: Policy) -> Simulator:
        self._agent.update_policy(policy)
        return self

    def init_environment(self, tasks, machines) -> Simulator:
        self._world.bootstrap(tasks, machines)
        return self

    def step(self) -> StepResult:
        """
        Run one simulation step.

        Step semantics:
        - if finished: return FINISHED
        - otherwise observe and decide
        - if agent waits: try natural advance
        - if no natural advance happens: return PAUSED
        - otherwise: return ADVANCED
        """
        if self._world.is_finished:
            return StepResult(status=StepStatus.FINISHED)

        obs = self._world.observe_decision()
        decision = self._agent.decide(obs)
        action = decision.action

        if isinstance(action, WaitAction):
            result = self._world.advance_naturally()
            if not result.initiated_events:
                return StepResult(status=StepStatus.PAUSED, result=result)
            return StepResult(status=StepStatus.ADVANCED, result=result)

        result = self._world.execute(action)
        return StepResult(status=StepStatus.ADVANCED, result=result)

    def run(self) -> StepStatus:
        """
        Run until finished or paused.
        """
        while True:
            result = self.step()

            if result.status == StepStatus.FINISHED:
                return StepStatus.FINISHED

            if result.status == StepStatus.PAUSED:
                return StepStatus.PAUSED