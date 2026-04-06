

from decision_scheduler.domain.models.state import SchedulingState

from decision_scheduler.infra.gantt import save_gantt
from decision_scheduler.app.simulation.metrics.metrics import Metrics   
from decision_scheduler.domain.models.task import TaskInit
from decision_scheduler.domain.models.resource import MachineInit

from decision_scheduler.app.policies import FIFOPolicy
from decision_scheduler.app.policies import SPTPolicy
from decision_scheduler.app.policies import EDDPolicy
from decision_scheduler.app.simulation import Simulator
from decision_scheduler.domain.dynamics.transitions import ActionDrivenTransition
from decision_scheduler.app.planning.planners import Planner


def demo_tasks():
    return [
        TaskInit( duration=3, release_time=0, deadline=6),
        TaskInit( duration=2, release_time=1, deadline=5),
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

    state = SchedulingState.from_scenario(tasks, resources)
    state.debug_dump()  # Optional: print initial state for debugging
    sim = Simulator(state=state, planner=Planner( ), transition=ActionDrivenTransition())
    final_state,_ = sim.run( policy)

    print("\n--- FINAL ---")
    print("final_state id:", id(final_state), "same?", final_state is state)
    final_state.debug_dump()  # Optional: print final state for debugging

    print(f"\n====={policy.__class__.__name__}=====")
    
    
    # final_state = run_simulation(tasks, resources, policy)

  #  metrics = Metrics.evaluate(final_state)

    # print(f"\n====={policy}=====")
    # for k,v in metrics.items():
    #     print(f"{k}: {v}")

    #save_gantt(final_state, f"{policy}_gantt.png", title=f"Gantt Chart - {policy}")

if __name__ == "__main__":
    print("Starting FIFO demo...")
    run(FIFOPolicy())
    print("finished FIFO")
    run(SPTPolicy())
    print("finished SPT")
    run(    EDDPolicy())
    print("finished EDD")