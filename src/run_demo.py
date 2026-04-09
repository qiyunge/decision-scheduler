

from decision_scheduler.domain.models.state import SchedulingState

from decision_scheduler.infra.gantt import save_gantt
from decision_scheduler.simulation.metrics.metrics import Metrics   
from decision_scheduler.domain.models.task import TaskInit
from decision_scheduler.domain.models.resource import MachineInit

from decision_scheduler.app.policies import FIFOPolicy
from decision_scheduler.app.policies import SPTPolicy
from decision_scheduler.app.policies import EDDPolicy
from decision_scheduler.simulation import Simulator
from decision_scheduler.domain.dynamics.transitions import ActionDrivenTransition
from decision_scheduler.app.planning.planners import Planner


def demo_tasks():
    return [
        TaskInit( duration=2, release_time=0, deadline=6),
        TaskInit( duration=1, release_time=1, deadline=5),
        TaskInit( duration=4, release_time=2, deadline=10),
        TaskInit( duration=1, release_time=0, deadline=3),
        TaskInit( duration=2, release_time=4, deadline=8),     
    ]

def demo_resources():
    return [
        MachineInit( ),
        MachineInit( ),
    ]

def run(policy):
    tasks = demo_tasks()
    resources = demo_resources()

    sim = Simulator().init_environment(tasks, resources)
    sim.update_policy(policy)

    status = sim.run()

    print(f"\n====={policy.__class__.__name__}=====")
    print(f"run status: {status.name}")
    return status

if __name__ == "__main__":
    print("Starting FIFO demo...")
    status = run(FIFOPolicy())
    print(f"FIFO ended with status: {status.name}")

    status = run(SPTPolicy())
    print(f"SPT ended with status: {status.name}")

    status = run(EDDPolicy())
    print(f"EDD ended with status: {status.name}")