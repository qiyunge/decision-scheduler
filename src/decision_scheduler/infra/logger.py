import logging
import json
from decision_scheduler.domain.models.state import SchedulingState 
from decision_scheduler.domain.decisions.observation import Observation
from decision_scheduler.domain.decisions.action import Action
from domain.scheduling.policies import Policy

def setup_logging(lel =logging.INFO, log_file:str="log/engine.log"):
    logging.basicConfig(
        level=lel,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


replay_logger = logging.getLogger("engine.replay")
def replay_log_step(step:int, state:SchedulingState, obs:Observation, action:Action, policy:Policy,next_state:SchedulingState) -> None:
    replay_logger.info(json.dumps({
        "step":step,
        "time":state.current_time,
        "ready":[t for t in obs.ready_task_ids],
        "idle_machines":[m for m in obs.idle_machine_ids],
        "action": {"name": action.__class__.__name__, "args": action.__dict__},
        "policy":policy.__class__.__name__,
        "next_time":next_state.current_time,
        "running":[(m, t) for m, t in next_state.running_tasks.items()]
        
    }))

