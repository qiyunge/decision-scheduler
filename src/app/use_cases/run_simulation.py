# from __future__ import annotations
# from dataclasses import dataclass
# from core.scheduling.models.events import Event
# from core.scheduling.models.state import SchedulingState, initialize_state
# from core.scheduling.policies import FIFOPolicy, EDDPolicy,SPTPolicy
# from core.scheduling.termination.terminal import check_terminal_condition
# from core.scheduling.decisions.observation import create_observation
# from core.scheduling.transitions.transition import apply_action, advance_environment



# @dataclass
# class SimulationResult:
#     policy_name:str
#     steps:int
#     events:list[Event]
#     makespan:int

# def run_simulation(task_specs: dict, machine_specs: dict, policy_name:str, now:int = 0,max_steps:int = 100000,) -> SimulationResult:
#     state = initialize_state(task_specs, machine_specs, now)
#     if policy_name.upper() == "FIFO":
#         policy = FIFOPolicy()
#     elif policy_name.upper() == "EDD":
#         policy = EDDPolicy(state)
#     elif policy_name.upper() == "SPT":
#         policy = SPTPolicy(state)
#     else:
#         raise ValueError(f"Unknown policy: {policy_name}")
    
#     all_events = []
#     steps = 0
    
#     while steps < max_steps and not (check_terminal_condition(state).is_terminal):

#         obs = create_observation(state)
#         if not obs.ready_tasks:
#             # No ready tasks, must wait for environment to advance time
#             ev2 = advance_environment(state)
#             all_events.extend(ev2)
#             if not ev2:
#                 # No future events, simulation ends
#                 break
            
#             steps += 1
#             continue

#         action = policy.decide(obs)
#         chosen = action.task_id
#         spec, rt = state.get_task(chosen)
#         print("DEBUG",
#     "now", state.current_time,
#     "chosen_task", action.task_id, type(action.task_id),
#     "chosen_machine", action.machine_id, type(action.machine_id),
#     "is_ready(chosen_task)", state.is_task_ready(action.task_id),
#     "obs.ready", [t for t in obs.ready_tasks])

#         events = apply_action(state,action)

#         all_events.extend(events)

#         ev2 = advance_environment(state)
#         all_events.extend(ev2)

#         steps += 1
    
#     makespan = state.current_time

#     return SimulationResult(
#         policy_name=policy_name,
#         steps=steps,
#         events=all_events,
#         makespan=makespan
#     )