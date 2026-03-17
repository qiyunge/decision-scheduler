from email import policy

from core.scheduling.models.scheduling_state import SchedulingState

# from core.scheduling.models.state import SchedulingState
# from core.scheduling.models.allocation import Allocation
from shared.utils.gantt import save_gantt
from core.scheduling.metrics.metrics import Metrics   
from core.scheduling.models.task import TaskInit
from core.scheduling.models.resource import MachineInit

from app.planning.policies.fifo import FIFOPolicy
from app.planning.policies.spt  import SPTPolicy
from app.planning.policies.edd import EDDPolicy
from app.simulation.simulator import Simulator
from core.scheduling.decisions.scheduling_transition import RuleBasedTransition
# from core.scheduling.transitions.event_driven_transition import EventDrivenTransition
from app.planning.planner import Planner


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
    sim = Simulator(planner=Planner( ), transition=RuleBasedTransition())
    final_state,_ = sim.run(state, policy)

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