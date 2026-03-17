
from abc import ABC, abstractmethod
from  ..models.state import SchedulingState
from ..decisions.action import Action, WaitAction,DispatchAction
from ..models.events import Event, SysFinishedEvent,TimeAdvanceEvent

from ..invariants.exceptions import SchedulingException
from ..models.task import TaskStatus

class Transition(ABC):
    @abstractmethod
    def apply(self, state: SchedulingState, action: Action) -> list[Event]:...
    
    @abstractmethod
    def advance(self,state: SchedulingState) -> list[Event]:...



def apply_action(state: SchedulingState, action: Action) -> list[Event]:
    ''' execute action that mutates state atomically'''

    if isinstance(action, WaitAction):
        return []
    elif isinstance(action, DispatchAction):
        if action.task_id is None or action.machine_id is  None:
            raise SchedulingException("Task ID and Machine ID must be provided for DispatchAction")
        return state.dispatch(machine_id=action.machine_id, task_id=action.task_id)
    else:
        raise SchedulingException("Unknown action type")
    
def advance_environment(state: SchedulingState) -> list[Event]:
    ''' environment time progression rule.
    - if there are running tasks, jump to next completion time
    - else if idle and there are future releases ,jump to next release 
    - else  no advance (idle forever)
    '''
    if state.is_finished():
        return []
    if state.busy_until:
        return state.advance_to_next_completion()
    
    

    future = [
    spec.release_time
    for tid, spec in state.task_specs.items()
    if tid in state.task_runtimes
    and state.task_runtimes[tid].status == TaskStatus.PENDING
    and spec.release_time > state.current_time
]

    if not future:
        return []
    
    t0 = state.current_time
    t1 = min(future)
    if t1 < t0:
        raise SchedulingException("Next release time cannot be in the past")
    state.current_time = t1
    return [TimeAdvanceEvent(from_time=t0, to_time=t1)]