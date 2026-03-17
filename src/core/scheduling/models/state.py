from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from .task import _TaskSpec,_TaskRuntime, TaskInit, TaskStatus, TaskView
from .ids import TaskId, MachineId 
from .resource import _MachineRuntime, _MachineSpec, MachineInit
from .events import Event, TimeAdvanceEvent, TaskCompletedEvent, TaskStartedEvent

# from types import MappingProxyType

from ..invariants.exceptions import SchedulingException

@dataclass(slots=True)
class _StateAuxiliary:
    '''
    Auxiliary class to engineering help
    - stats
    - caches
    - indexes
    This is to keep the main SchedulingState class cleaner and more focused on the data structure and public interface.
    '''
    stat_completed_task_count: int = field(default=0, init=False)
    cache_ready_tasks: frozenset[TaskId]|None = field(default=None, init=False)
    cache_completed_tasks: frozenset[TaskId]|None = field(default=None, init=False)

    def invalidate(self) -> None:
        self.cache_ready_tasks = None
        self.cache_completed_tasks = None  

@dataclass
class SchedulingState:
    '''
    Aggregate root of the scheduling system.
    Represents the entire runtime state of the system.
    Priciple of encapsulation: state update = state constraint validation + state mutation.
    '''
    _debug: bool = field(default=False, init=False)
    # ---theta(immutable scenario)---
    _task_specs: dict[TaskId, _TaskSpec] = field(default_factory=dict, init=False) # theta, immutable information
    _machine_specs:dict[MachineId,_MachineSpec] = field(default_factory=dict, init=False) # immutable information
    # ---runtime---
    _current_time :int = field(default=0, init=False)
    ## task state
    _task_runtimes: dict[TaskId, _TaskRuntime] = field(default_factory=dict,init=False) #state mutable information
    # _machine_runtimes: dict[MachineId, _MachineRuntime] = field(default_factory=dict, init=False) #state mutable information
    # machine -> current running task
    _allocations: dict[MachineId,TaskId] = field(default_factory=dict, init=False) # state mutable information
    _busy_until: dict[MachineId,int] = field(default_factory=dict, init=False) # machine -> busy until when (timestamp)
    # For optimization: 
    _state_aux: _StateAuxiliary = field(default_factory=_StateAuxiliary, init=False, repr=False)

    # --- taskId ---
    # ----resourceId ---
    _next_task_id:TaskId = field(default=0, init=False)
    _next_machine_id:MachineId = field(default=0, init=False)

    def _get_next_task_id(self) -> TaskId:
        tid = self._next_task_id
        self._next_task_id += 1
        return tid
    
    def _get_next_machine_id(self) -> MachineId:
        mid = self._next_machine_id
        self._next_machine_id += 1
        return mid
    
    # --- properties for read-only access ---
    @property
    def current_time(self) -> int:
        return self._current_time
    
    # @property
    # def task_specs(self) -> dict[TaskId, _TaskSpec]:
    #     return self._task_specs
 
    # --- derived state ---
    @property
    def total_tasks(self) -> int:
        return len(self._task_specs)
    

    ## resource state

    #-------------------
    # Factory method to create initial state from scenario specifications.      
    #-------------------
    @classmethod
    def from_scenario(cls:type["SchedulingState"], task_specs: list[TaskInit], machine_specs:list[MachineInit],now:int) -> "SchedulingState":
        '''
        Factory method to create initial state from scenario specifications.
        '''
        state = cls()
        state._current_time = now

        for t in task_specs: 
            state.create_task(t)
        
        for m in machine_specs:
            state.create_machine(m)
        
        state.audit()
        return state
   
    #-------------------
    # Queries
    #-------------------
    
    def task_view(self,task_id: TaskId) -> TaskView:
        rt = self._task_runtimes[task_id]
        spec = self._task_specs[task_id]
        return TaskView(id=task_id, 
                        release_time=spec.release_time, 
                        duration=spec.duration, 
                        status=rt.status, 
                        machine_id=rt.machine_id, 
                        start_time=rt.start_time ,
                        finish_time=rt.finish_time)
    
    def iter_task_views(self) -> Iterator[TaskView]:
        for task_id in self._task_specs.keys():
            yield self.task_view(task_id)

    def snapshot_task_views(self) -> tuple[TaskView,...]:
        return tuple(self.iter_task_views())
    
    def iter_idle_machine_ids(self) -> Iterator[MachineId]:
        return (machine_id for machine_id in self._machine_specs.keys() if machine_id not in self._allocations)
    
    def snapshot_idle_machine_ids(self) -> tuple[MachineId,...]:
        return tuple(self.iter_idle_machine_ids())
  
    def iter_pending_task_ids(self) -> Iterator[TaskId]:
        return (task_id for task_id, runtime in self._task_runtimes.items() if runtime.status == TaskStatus.PENDING)
    
    def snapshot_pending_task_ids(self) -> frozenset[TaskId]:
        return frozenset(self.iter_pending_task_ids())
    
    
    def iter_completed_task_ids(self) -> Iterator[TaskId]:
        return (task_id for task_id, runtime in self._task_runtimes.items() if runtime.status == TaskStatus.COMPLETED)
    
    def snapshot_completed_task_ids(self) -> frozenset[TaskId]:
        if self._state_aux.cache_completed_tasks is not None:
            return self._state_aux.cache_completed_tasks           
        self._state_aux.cache_completed_tasks = frozenset(self.iter_completed_task_ids())
        return self._state_aux.cache_completed_tasks
    
    def iter_ready_task_ids(self) -> Iterator[TaskId]:
        return (task_id for task_id in self.iter_pending_task_ids()
                 if self.is_task_ready(task_id))
    
    def snapshot_ready_task_ids(self) -> frozenset[TaskId]:
        if self._state_aux.cache_ready_tasks is not None:
            return self._state_aux.cache_ready_tasks
        now = self.current_time
        specs = self._task_specs
        self._state_aux.cache_ready_tasks = frozenset(tid for tid ,rt in self._task_runtimes.items()
                                                       if rt.status == TaskStatus.PENDING and specs[tid].release_time <= now)
        return self._state_aux.cache_ready_tasks

    def _get_task(self, task_id: TaskId) -> tuple[_TaskSpec,_TaskRuntime]:
        return self._task_specs[task_id], self._task_runtimes[task_id]
    
    def is_task_ready(self, task_id: TaskId) -> bool:
        spec, rt = self._get_task(task_id)
        return rt.status == TaskStatus.PENDING and spec.release_time <= self.current_time

    def is_finished(self) -> bool:
        # for rt in self._task_runtimes.values():
        #     if rt.status != TaskStatus.COMPLETED:
        #         return False
        # return True
        # todo: optimize by maintaining a completed_count variable that increments whenever a task is completed, 
        # and compare it with total task count.
        return self._state_aux.stat_completed_task_count == self.total_tasks
    
    #-------------------
    # S mutation(atomic) + local invariant checking(I)
    #-------------------
    def create_task(self, task_init:TaskInit) -> TaskId:
        task_id = self._get_next_task_id()
        self._task_specs[task_id] = _TaskSpec(
            duration=task_init["duration"],
            release_time=task_init["release_time"],
            deadline=task_init["deadline"]
        )
        self._task_runtimes[task_id] = _TaskRuntime(
            id=task_id,
            status=TaskStatus.PENDING
        )

        self._state_aux.invalidate() # invalidate caches
        return task_id
    
    def create_machine(self, machine_init:MachineInit ) -> MachineId:
        machine_id = self._get_next_machine_id()
        self._machine_specs[machine_id] = _MachineSpec.from_init(machine_init)
        # self._machine_runtimes[machine_id] = _MachineRuntime(
        #     id=machine_id,
        #     availability_time=0
        # )
        self._state_aux.invalidate() # invalidate caches
        return machine_id

    def dispatch(self, *, machine_id: MachineId, task_id: TaskId) -> list[Event]:
        '''
        Dispatch a task to a machine, which involves state mutation.
        '''
        self._assert_can_dispatch( machine_id, task_id)
        self._start_task(task_id, machine_id)

        if self._debug:
            self.audit()

        return [TaskStartedEvent(task_id=task_id, machine_id=machine_id, time=self.current_time)]

    def _start_task(self, task_id: TaskId, machine_id: MachineId) -> None: 
        '''
        Internal helper method to start a task on a machine without validation or event generation.
        Used for testing and debugging purposes.
        '''
        spec,rt = self._get_task(task_id)

        rt.status = TaskStatus.RUNNING
        rt.machine_id = machine_id
        rt.start_time = self.current_time

        self._allocations[machine_id] = task_id
        self._busy_until[machine_id] = self.current_time + spec.duration

        self._state_aux.invalidate() # invalidate caches

    def _assert_can_dispatch(self,  machine_id: MachineId, task_id: TaskId)->None:
        if machine_id in self._allocations:
            raise SchedulingException(f"Machine {machine_id} is already allocated to task {self._allocations[machine_id]}.")
        # task must exist
        if task_id not in self._task_runtimes or task_id not in self._task_specs:
            raise SchedulingException(f"Unknown task {task_id}.")
        # task must be READY (derived): PENDING + released
        if not self.is_task_ready(task_id):
            raise SchedulingException(f"Task {task_id} is not ready to be dispatched.")

        # consistency check: allocations <-> busy_until
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        if (machine_id in self._busy_until) != (machine_id in self._allocations):   
            raise SchedulingException(
                    f"Inconsistent state: allocations/busy_until mismatch for machine {machine_id}.")
        
    def advance_to_next_completion(self) -> list[Event]:
        """
        Event-driven time advance:
        - jump 'now' to the earliest busy_until among running machines
        - mark any tasks finishing at that time as COMPLETED, free those machines
        """
        if not self._busy_until:
            return []
        
        events = []
        t0 = self._current_time
        t1 = min(self._busy_until.values())

        self._current_time = t1
        events.append(TimeAdvanceEvent(from_time=t0, to_time=t1))

        finished_machines = [machine_id for machine_id, busy_until in self._busy_until.items() if busy_until == t1]
        for machine_id in finished_machines:
            tid = self._allocations[machine_id]
            _, rt = self._get_task(tid)

            rt.status = TaskStatus.COMPLETED
            rt.finish_time = t1
            rt.machine_id = machine_id

            del self._allocations[machine_id]
            del self._busy_until[machine_id] 

            # Increment completed task count for optimization
            self._state_aux.stat_completed_task_count += 1

            events.append(TaskCompletedEvent(task_id=tid, machine_id=machine_id, time=t1))

        self._state_aux.invalidate() # invalidate caches
        if self._debug:
            self.audit()
        return events
        
    def audit(self) -> None:
        '''
        Check internal consistency of the state. Raise exception if any invariant is violated.
        '''
        # 1. runtime-spec consistency: every task in runtime should have a corresponding spec and vice versa 
        if set(self._task_runtimes.keys()) != set(self._task_specs.keys()):
            raise SchedulingException(f"Inconsistent state: task runtimes and specs keys do not match.")
        # 2. allocations <-> busy_until consistency
        for machine_id in self._allocations.keys():
            if machine_id not in self._busy_until:
                raise SchedulingException(f"Inconsistent state: machine {machine_id} has allocation but no busy_until.")
        for machine_id in self._busy_until.keys():
            if machine_id not in self._allocations:
                raise SchedulingException(f"Inconsistent state: machine {machine_id} has busy_until but no allocation.")
        
        # 3. task status consistency with allocations
        for machine_id, task_id in self._allocations.items():
            rt = self._task_runtimes[task_id]
            if rt.status != TaskStatus.RUNNING:
                raise SchedulingException(f"Inconsistent state: task {task_id} allocated to machine {machine_id} but status is {rt.status}.")
        
        # 4. time consistency: current_time should be non-negative
        if self._current_time < 0:
            raise SchedulingException(f"Inconsistent state: current_time {self._current_time} is negative.")  
        
        # 5. completed task count consistency check
        actual_completed_count = sum(1 for rt in self._task_runtimes.values() if rt.status == TaskStatus.COMPLETED)
        if self._state_aux.stat_completed_task_count != actual_completed_count:
            raise SchedulingException(f"Inconsistent state: completed_task_count {self._state_aux.stat_completed_task_count} does not match actual completed tasks {actual_completed_count}.")
        
       

   
   
    # def advance_to_next_release_if_idle(self) -> list[Event]:
    #         '''
    #         If there is no running task, we can jump to the next release time of pending tasks.
    #         '''
    #         if self._busy_until or self.is_finished():
    #             return []
            
    #         future_releases = []
    #         for tid,spec in self._task_specs.items():
    #             rt = self._task_runtimes[tid]
    #             if rt.status == TaskStatus.PENDING and spec.release_time > self._current_time:
    #                 future_releases.append(spec.release_time)

    #         if not future_releases:
    #             return []
            
    #         t0 = self._current_time
    #         t1 = min(future_releases)

    #         self._current_time = t1
    #         return [TimeAdvanceEvent(from_time=t0, to_time=t1)  ]
           
    #-------------------
    # State mutation + constraint validation(invariant checking)
    #-------------------

def initialize_scheduling_state(task_specs: list[ TaskInit], machine_specs:list[MachineInit],now:int) -> SchedulingState:
    '''
    Factory method to create initial state from scenario specifications.
    '''
    return SchedulingState.from_scenario(task_specs=task_specs, machine_specs=machine_specs, now=now)