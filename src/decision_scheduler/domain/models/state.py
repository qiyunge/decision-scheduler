from __future__ import annotations

from collections.abc import  KeysView, Mapping

from typing import Protocol

# local library
from .task import _TaskSpec, _TaskRuntime, TaskInit, TaskStatus
from .ids import TaskId, MachineId
from .resource import _MachineSpec, MachineInit
from ..support.exceptions import SchedulingException
from ..support.events import (DomainEvent,DomainInitiatedEvent,DomainCompletedEvent, NaturalProcessCompletedEvent, NaturalProcessInitiatedEvent,
                              TaskCreationInitiatedEvent,MachineCreationInitiatedEvent,
                              TaskDispatchInitiatedEvent, TaskReleasedEvent,TimeAdvanceInitiatedEvent,
                              
                               TaskCreatedEvent,MachineCreatedEvent, 
                                TaskDispatchedEvent,TimeAdvancedEvent,TaskCompletedEvent)
from ..support.results import  TaskCompletionResult, TimeAdvanceResult, NaturalEffects
from ..invariants.validators import validate_task_init, validate_machine_init


# =========================
# Auxiliary (stats/caches)
# =========================

class _SchedulingStateAuxiliary:
    _core: _SchedulingStateCore

    _cache_ready_tasks_version: int
    _cache_ready_tasks:frozenset[TaskId] | None

    _cache_completed_task_ids_version: int
    _cache_completed_task_ids:frozenset[TaskId] | None

    _cache_idle_machine_ids_version: int
    _cache_idle_machine_ids:frozenset[MachineId] | None

    _cache_min_running_tasks_completion_time_version: int
    _cache_min_running_tasks_completion_time: int | None

    _cache_next_release_time_version: int
    _cache_next_release_time: int | None

    __slots__ = (
        "_core",
        "_cache_ready_tasks_version",
        "_cache_completed_task_ids_version",
        "_cache_idle_machine_ids_version",
        "_cache_ready_tasks",
        "_cache_completed_task_ids",
        "_cache_idle_machine_ids",
        "_cache_min_running_tasks_completion_time_version",
        "_cache_min_running_tasks_completion_time",
        "_cache_next_release_time_version",
        "_cache_next_release_time"


    )

    def __init__(self, core: _SchedulingStateCore) -> None:
        self._core = core
        self._cache_ready_tasks_version = -1
        self._cache_ready_tasks = None
        self._cache_completed_task_ids_version = -1
        self._cache_completed_task_ids = None
        self._cache_idle_machine_ids_version = -1
        self._cache_idle_machine_ids = None
        self._cache_min_running_tasks_completion_time_version = -1
        self._cache_min_running_tasks_completion_time = None

        self._cache_next_release_time_version = -1
        self._cache_next_release_time = None


    @property
    def ready_task_ids(self) -> frozenset[TaskId] :
        if self._cache_ready_tasks is None or self._cache_ready_tasks_version != self._core.state_version:
            ready_task_ids = []
            for task_id in self._core.task_ids:
                if (self._core.task_status_of(task_id) == TaskStatus.PENDING and
                self._core.task_release_time_of(task_id) <= self._core.current_time):
                    ready_task_ids.append(task_id)

            self._cache_ready_tasks = frozenset(ready_task_ids)
            self._cache_ready_tasks_version = self._core.state_version

        return self._cache_ready_tasks

    @property
    def completed_task_ids(self) -> frozenset[TaskId]:
        if (
            self._cache_completed_task_ids is None
            or self._cache_completed_task_ids_version != self._core.state_version
        ):
            completed: list[TaskId] = []
            for task_id in self._core.task_ids:
                if self._core.task_status_of(task_id) == TaskStatus.COMPLETED:
                    completed.append(task_id)

            self._cache_completed_task_ids = frozenset(completed)
            self._cache_completed_task_ids_version = self._core.state_version

        return self._cache_completed_task_ids
    
    @property
    def idle_machine_ids(self) -> frozenset[MachineId]:
        if (
            self._cache_idle_machine_ids is None
            or self._cache_idle_machine_ids_version != self._core.state_version
        ):
            idle: list[MachineId] = []
            for machine_id in self._core.machine_ids:
                if self._core.task_id_of(machine_id) is None:
                    idle.append(machine_id)

            self._cache_idle_machine_ids = frozenset(idle)
            self._cache_idle_machine_ids_version = self._core.state_version

        return self._cache_idle_machine_ids    
    
    @property
    def min_running_tasks_completion_time(self) -> int | None:
        if (
            self._cache_min_running_tasks_completion_time is None
            or self._cache_min_running_tasks_completion_time_version != self._core.state_version
        ):
            min_time: int | None = None

            for machine_id in self._core.machine_ids:
                if self._core.task_id_of(machine_id) is not None:
                    until_time = self._core.busy_until_of(machine_id)
                    if min_time is None or until_time < min_time:
                        min_time = until_time

            self._cache_min_running_tasks_completion_time = min_time
            self._cache_min_running_tasks_completion_time_version = self._core.state_version

        return self._cache_min_running_tasks_completion_time
    
    @property
    def next_release_time(self) -> int | None:
        if self._cache_next_release_time_version != self._core.state_version:
            now = self._core.current_time
            next_release: int | None = None

            for task_id in self._core.task_ids:
                if self._core.task_status_of(task_id) == TaskStatus.PENDING:
                    release_time = self._core.task_release_time_of(task_id)
                    if release_time > now and (
                        next_release is None or release_time < next_release
                    ):
                        next_release = release_time

            self._cache_next_release_time = next_release
            self._cache_next_release_time_version = self._core.state_version

        return self._cache_next_release_time

# =========================
# Core (state + invariants)
# =========================
class _SchedulingStateCore:
# region 1 --- field declarations / __slots__ ---
    # --- theta (immutable scenario) ---
    _task_specs: dict[TaskId, _TaskSpec]
    _machine_specs: dict[MachineId, _MachineSpec]

    # --- runtime ---
    # task-centered runtime truth
    _task_runtimes: dict[TaskId, _TaskRuntime]
    _current_time: int

    # redundant but for efficient
    _completed_task_count: int
    # redundant runtime indices for machine-centered queries and invariant checks
    _allocations: dict[MachineId, TaskId]
    _busy_until: dict[MachineId, int]

    # --- ids ---
    _next_task_id: TaskId
    _next_machine_id: MachineId

    # --- versions for invalidation ---
    _state_version: int

    __slots__ = (
        # theta (immutable scenario)
        "_task_specs",
        "_machine_specs",

        # runtime
        "_completed_task_count",
        "_task_runtimes",
        "_current_time",
        "_allocations",
        "_busy_until",

        # ids
        "_next_task_id",
        "_next_machine_id",

        # global mutation version for cache invalidation
        "_state_version",
    )

    def __init__(self, now :int = 0) -> None:
        # theta (immutable scenario)
        self._task_specs = {}
        self._machine_specs = {}

        # runtime
        self._completed_task_count = 0

        self._task_runtimes = {}
        self._current_time = now

        self._allocations = {}
        self._busy_until = {}

        # ids
        self._next_task_id = 0
        self._next_machine_id = 0

        # global mutation version for cache invalidation
        self._state_version = 0
# endregion 1. --- field declarations / __slots__  ---

# region 2. --- properties ---
    @property
    def state_version(self) -> int:
        return self._state_version
    
    @property
    def current_time(self) -> int:
        return self._current_time

    @property
    def task_ids(self) -> KeysView[TaskId]:
        return self._task_specs.keys()

    @property
    def machine_ids(self) -> KeysView[MachineId]:
        return self._machine_specs.keys()
    
    @property
    def completed_task_count(self) -> int:
        return self._completed_task_count
    
    @property
    def total_task_count(self) -> int:
        return len(self._task_specs)
# endregion 2. --- properties ---

# region 3.--- public queries (facts) ---
    def machine_id_of(self, task_id: TaskId) -> MachineId | None:
        rt = self._task_runtimes.get(task_id)
        if rt is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return rt.machine_id if rt.status is TaskStatus.RUNNING else None

    def task_id_of(self, machine_id: MachineId) -> TaskId | None:
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        return self._allocations.get(machine_id)

    def busy_until_of(self, machine_id: MachineId) -> int:
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        return self._busy_until.get(machine_id, self._current_time)

    def task_status_of(self, task_id: TaskId) -> TaskStatus:
        rt = self._task_runtimes.get(task_id)
        if rt is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return rt.status

    def task_release_time_of(self, task_id: TaskId) -> int:
        spec = self._task_specs.get(task_id)
        if spec is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return spec.release_time

    def task_deadline_of(self, task_id: TaskId) -> int | None:
        spec = self._task_specs.get(task_id)
        if spec is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return spec.deadline

    def task_duration_of(self, task_id: TaskId) -> int:
        spec = self._task_specs.get(task_id)
        if spec is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return spec.duration

    def task_start_time_of(self, task_id: TaskId) -> int | None:
        rt = self._task_runtimes.get(task_id)
        if rt is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return rt.start_time

    def task_finish_time_of(self, task_id: TaskId) -> int | None:
        rt = self._task_runtimes.get(task_id)
        if rt is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return rt.finish_time

  

# endregion 3.--- public queries (facts) ---

# region 4. --- public mutations (commands) ---

    def complete(self, event: DomainInitiatedEvent)-> tuple[DomainCompletedEvent,...]:
        
        if isinstance(event, TaskCreationInitiatedEvent):
            task_id = self._create_task(event.task_init)
            return (TaskCreatedEvent(time=self.current_time, task_id=task_id, task_init=event.task_init),)

        elif isinstance(event, MachineCreationInitiatedEvent):
            machine_id = self._create_machine(event.machine_init)
            return (MachineCreatedEvent(time=self.current_time, machine_id=machine_id, machine_init=event.machine_init),)   

        elif isinstance(event, TaskDispatchInitiatedEvent):
            self._dispatch(machine_id=event.machine_id, task_id=event.task_id)
            return (TaskDispatchedEvent(time=self.current_time, machine_id=event.machine_id, task_id=event.task_id),)

        elif isinstance(event, TimeAdvanceInitiatedEvent):
            old_time = self._advance_time_to(event.new_time)
            return (TimeAdvancedEvent(time=self.current_time, old_time=old_time, new_time=event.new_time),)
        
        elif isinstance(event, NaturalProcessInitiatedEvent):
            released_task_ids =  event.scheduled_effects.released_task_ids
            completed_task_ids = event.scheduled_effects.completed_task_ids
            new_time = event.new_time

            released_events = []
            completed_events = []

            self._advance_time_to(new_time) # step 1: advance time, which may trigger natural effects
            for task_id in released_task_ids: # step 2: validate and apply releases
                if self.task_status_of(task_id) != TaskStatus.PENDING:
                    raise SchedulingException(
                        f"Cannot release task {task_id} as part of natural process at time {self.current_time} "
                        f"because its status is {self.task_status_of(task_id)}."
                    )
                released_events.append(TaskReleasedEvent(time=self.current_time, task_id=task_id))
            for task_id in completed_task_ids: # step 3: validate and apply completions
                machine_id = self._complete_task_by_task_id(task_id)
                completed_events.append(TaskCompletedEvent(time=self.current_time, task_id=task_id, machine_id=machine_id))

            return (NaturalProcessCompletedEvent(time=self.current_time, natural_effects=event.scheduled_effects, released_events=tuple(released_events), completed_events=tuple(completed_events)),)

        else:
            raise SchedulingException(f"Unknown event type: {type(event)}.")

# endregion 4. --- public mutations (commands) ---

# region 5. --- auduit/ validateion ---
    def audit(self) -> None:
        self._audit_task_spec_runtime_keys()
        self._audit_machine_index_consistency()
        self._audit_allocation_task_status_consistency()
        self._audit_time_consistency()
        self._audit_completed_task_consistency()
        self._audit_task_machine_pointer_consistency()  
        self._audit_completed_task_count()    
# endregion 5. --- auduit/ validateion ---

# region 6.1 --- internal  mutations ---
    
    
    # --- advance time ---

    def _advance_time_to(self, target_time: int) -> int:
        """
        Low-level time mutation primitive.
        Usually called by transition logic or simulator control flow.
        This method validates monotonicity and performs the actual time update,
        but it does not decide what the next valid target time should be.
        """

        old_time = self._current_time
        if target_time < old_time:
            raise SchedulingException("Time cannot go backwards.")
        if target_time == old_time:
            return old_time

        self._current_time = target_time

        self._invalidate_state()
        return old_time
    
    # --- complete on machine ---
    def _complete_running_task_on_machine(self, machine_id: MachineId) -> TaskId:
        """
        Low-level task completion mutation primitive.
        Usually called by transition logic or simulator control flow when a task's completion time is reached.
        """
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        if machine_id not in self._allocations:
            raise SchedulingException(f"Machine {machine_id} is not currently allocated to any task.")
        if machine_id not in self._busy_until:
            raise SchedulingException(f"Inconsistent state: machine {machine_id} has allocation but no busy_until.")
        
        if self._busy_until[machine_id] != self._current_time:
            raise SchedulingException(
            f"Machine {machine_id} cannot complete at time {self._current_time}; "
            f"expected completion time is {self._busy_until[machine_id]}."
    )

        

        task_id = self._allocations.pop(machine_id)
        del self._busy_until[machine_id]

        self._unsafe_mark_task_completed(task_id=task_id)

        self._invalidate_state()
       
        return task_id
    
    def _complete_task_by_task_id(self, task_id: TaskId) -> MachineId:
        machine_id = self.machine_id_of(task_id)
        completed_task_id = self._complete_running_task_on_machine(machine_id)

        if completed_task_id != task_id:
            raise SchedulingException(
                f"Inconsistent state: expected task {task_id} to complete on machine "
                f"{machine_id}, but completed task {completed_task_id}."
            )
        return machine_id
    
    # --- dispatch task ---
    def _dispatch(self, *, machine_id: MachineId, task_id: TaskId) ->None:
        # core only checks structural invariants + basic facts
        
        self._assert_can_dispatch(machine_id, task_id)
        self._unsafe_start_task(task_id, machine_id)
        self._invalidate_state()
       
    # --- create task ---
    def _create_task(self, task_init: TaskInit) ->TaskId:
        validate_task_init(task_init)

        def create_task() -> TaskId:
            task_id = self._get_next_task_id()

            task_spec =  _TaskSpec(
                duration=task_init["duration"],
                release_time=task_init["release_time"],
                deadline=task_init["deadline"],
            )
            task_runtime =  _TaskRuntime(
                id=task_id,
                status=TaskStatus.PENDING,
            )
            
            self._task_runtimes[task_id] = task_runtime
            self._task_specs[task_id] = task_spec

            return task_id


        task_id = create_task()

        self._invalidate_state()

        return task_id

    def _create_machine(self, machine_init: MachineInit) -> MachineId:
        validate_machine_init(machine_init)

        def create_machine() -> MachineId:
            machine_id = self._get_next_machine_id()
            machine_spec = _MachineSpec.from_init(machine_init) 
            self._machine_specs[machine_id] = machine_spec

            return machine_id

        machine_id = create_machine()

        self._invalidate_state()
        return machine_id

  
    
    def _unsafe_start_task(self, task_id: TaskId, machine_id: MachineId) -> None:
        spec = self._task_specs[task_id]
        rt = self._task_runtimes[task_id]

        rt.status = TaskStatus.RUNNING
        rt.machine_id = machine_id
        rt.start_time = self._current_time
        rt.finish_time = None

        self._allocations[machine_id] = task_id
        self._busy_until[machine_id] = self.current_time + spec.duration

    def _unsafe_mark_task_completed(self, task_id: TaskId) -> None:
        rt = self._task_runtimes[task_id]
        if rt.status != TaskStatus.RUNNING:
            raise SchedulingException(f"Task {task_id} is not running.")

        rt.status = TaskStatus.COMPLETED
        rt.finish_time = self._current_time
        rt.machine_id = None
        self._completed_task_count += 1
       

    # --- create machine ---

    

    


# endregion 6.1 --- internal mutations ---

# region 6.2 --- internal helper ---
    def _invalidate_state(self) -> None:
        self._state_version += 1

    #  --- ids ---
    def _get_next_task_id(self) -> TaskId:
        tid = self._next_task_id
        self._next_task_id += 1
        return tid

    def _get_next_machine_id(self) -> MachineId:
        mid = self._next_machine_id
        self._next_machine_id += 1
        return mid
    

# endregion 6.2 --- internal helper ---

# region 7 --- internal helpers (for audit/validation) ---
    # --- dispatch task ---
    def _assert_can_dispatch(self, machine_id: MachineId, task_id: TaskId) -> None:
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        if task_id not in self._task_specs or task_id not in self._task_runtimes:
            raise SchedulingException(f"Unknown task {task_id}.")
        if machine_id in self._allocations:
            raise SchedulingException(f"Machine {machine_id} is already allocated to task {self._allocations[machine_id]}.")

        # allocations <-> busy_until consistency
        if (machine_id in self._busy_until) != (machine_id in self._allocations):
            raise SchedulingException(f"Inconsistent state: allocations/busy_until mismatch for machine {machine_id}.")
        
        # task must be pending and released to be dispatched
        rt = self._task_runtimes[task_id]
        spec = self._task_specs[task_id]

        if rt.status is not TaskStatus.PENDING:
            raise SchedulingException(f"Task {task_id} is not pending.")
        if spec.release_time > self._current_time:
            raise SchedulingException(f"Task {task_id} is not yet ready for dispatch.")

    def _audit_task_spec_runtime_keys(self) -> None:
        if set(self._task_specs.keys()) != set(self._task_runtimes.keys()):
            raise SchedulingException(f"Inconsistent state: task specs and runtimes keys do not match.")
        
    def _audit_machine_index_consistency(self) -> None:
        for mid in self._allocations:
            if mid not in self._machine_specs:
                raise SchedulingException(
                    f"Inconsistent state: allocation references unknown machine {mid}."
                )
        for mid in self._busy_until:
            if mid not in self._machine_specs:
                raise SchedulingException(
                    f"Inconsistent state: busy_until references unknown machine {mid}."
                )
        for mid in self._allocations:
            if mid not in self._busy_until:
                raise SchedulingException(
                    f"Inconsistent state: machine {mid} has allocation but no busy_until."
                )
        for mid in self._busy_until:
            if mid not in self._allocations:
                raise SchedulingException(
                    f"Inconsistent state: machine {mid} has busy_until but no allocation."
                )
        for mid, tid in self._allocations.items():
            if tid not in self._task_runtimes:
                raise SchedulingException(
                    f"Inconsistent state: allocation on machine {mid} references unknown task {tid}."
                )
            
    def _audit_allocation_task_status_consistency(self) -> None:
        for mid, tid in self._allocations.items():
            rt = self._task_runtimes[tid]
            if rt.status is not TaskStatus.RUNNING:
                raise SchedulingException(
                    f"Inconsistent state: task {tid} allocated to machine {mid} "
                    f"but status is {rt.status}."
                )

        running_task_ids = {
            tid
            for tid, rt in self._task_runtimes.items()
            if rt.status is TaskStatus.RUNNING
        }
        allocated_task_ids = set(self._allocations.values())

        if running_task_ids != allocated_task_ids:
            raise SchedulingException(
                "Inconsistent state: running tasks and allocated tasks do not match."
            )
                

    def _audit_time_consistency(self) -> None:
        if self._current_time < 0:
            raise SchedulingException(
                f"Inconsistent state: current_time {self._current_time} is negative."
            )

        for mid, busy_until in self._busy_until.items():
            if busy_until < self._current_time:
                raise SchedulingException(
                    f"Inconsistent state: machine {mid} has busy_until={busy_until} "
                    f"earlier than current_time={self._current_time}."
                )

    def _audit_completed_task_consistency(self) -> None:
        for tid, rt in self._task_runtimes.items():
            if rt.status is TaskStatus.COMPLETED:
                if rt.finish_time is None:
                    raise SchedulingException(
                        f"Inconsistent state: completed task {tid} has no finish_time."
                    )

                if rt.finish_time > self._current_time:
                    raise SchedulingException(
                        f"Inconsistent state: completed task {tid} has finish_time={rt.finish_time} "
                        f"later than current_time={self._current_time}."
                    ) 
    def _audit_task_machine_pointer_consistency(self) -> None:
        for tid, rt in self._task_runtimes.items():
            if rt.status is TaskStatus.RUNNING:
                if rt.machine_id is None:
                    raise SchedulingException(
                        f"Inconsistent state: running task {tid} has no machine_id."
                    )

                if rt.machine_id not in self._allocations:
                    raise SchedulingException(
                        f"Inconsistent state: running task {tid} points to machine {rt.machine_id}, "
                        "but that machine has no allocation."
                    )

                if self._allocations[rt.machine_id] != tid:
                    raise SchedulingException(
                        f"Inconsistent state: running task {tid} machine pointer does not match allocations."
                    )
            else:
                if rt.machine_id is not None:
                    raise SchedulingException(
                        f"Inconsistent state: non-running task {tid} still has machine_id={rt.machine_id}."
                    )   
    def _audit_completed_task_count(self) -> None:
        actual = 0
        for task_id in self._task_runtimes:
            if self.task_status_of(task_id) == TaskStatus.COMPLETED:
                actual += 1

        if actual != self._completed_task_count:
            raise SchedulingException(
                f"Inconsistent completed_task_count: expected {actual}, got {self._completed_task_count}."
            )                    
                
# endregion 7 --- internal helpers (for audit/validation) ---

# region 8 --- dunder/protocols ---
    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"time={self._current_time}, "
            f"tasks={len(self._task_specs)}, "
            f"machines={len(self._machine_specs)}, "
            f"version={self._state_version}"
            f")"
        )

# endregion 8 --- dunder/protocols ---
  


# =========================
# Aggregate root (facade)
# =========================


class SchedulingState:
  
    _state_core: _SchedulingStateCore
    _state_aux: _SchedulingStateAuxiliary
    _task_query: TaskQuery

   
    __slots__ = ( "_state_core", "_state_aux", "_task_query")

    def __init__(self, now: int = 0) -> None:
        self._state_core = _SchedulingStateCore(now=now)
        self._state_aux = _SchedulingStateAuxiliary(self._state_core)
        self._task_query = _TaskQueryImpl(self._state_core)

    @classmethod
    def from_scenario(
        cls: type["SchedulingState"],
        task_specs: list[TaskInit],
        machine_specs: list[MachineInit],
        now: int = 0,
    ) -> "SchedulingState":
        state = cls(now=now)

        for t in task_specs:
            state._bootstrap_create_task(t)
        for m in machine_specs:
            state._bootstrap_create_machine(m)

        state.audit()
        return state

    def _bootstrap_create_task(self, task_init: TaskInit) -> None:
        self._state_core._create_task(task_init)

    def _bootstrap_create_machine(self, machine_init: MachineInit) -> None:
        self._state_core._create_machine(machine_init)

    # ---- basic properties ----
    @property
    def current_time(self) -> int:
        return self._state_core.current_time

    @property
    def total_tasks(self) -> int:
        return len(self._state_core.task_ids)
    
    @property
    def ready_task_ids(self) -> frozenset[TaskId]:
        return self._state_aux.ready_task_ids

    @property
    def completed_task_ids(self) -> frozenset[TaskId]:
        return self._state_aux.completed_task_ids

    @property
    def idle_machine_ids(self) -> frozenset[MachineId]:
        return self._state_aux.idle_machine_ids
    
    @property
    def machine_ids(self) -> KeysView[MachineId]:
        return self._state_core.machine_ids
    
    @property
    def task_ids(self) -> KeysView[TaskId]:
        return self._state_core.task_ids
    
    @property
    def task_query(self) -> TaskQuery:
        return self._task_query

    @property
    def next_completion_time(self) -> int | None:
        return self._state_aux.min_running_tasks_completion_time

    @property
    def next_release_time(self) -> int | None:
        return self._state_aux.next_release_time

    @property
    def is_finished(self) -> bool:
        return self._state_core.completed_task_count == self._state_core.total_task_count
    
    # ---- queries ----
 
    def is_task_ready(self, task_id: TaskId) -> bool:
        return (
            self._state_core.task_status_of(task_id) is TaskStatus.PENDING
            and self._state_core.task_release_time_of(task_id) <= self._state_core.current_time
        )
    
    def natural_effects_at(self, time: int) -> NaturalEffects:
        released: list[TaskId] = []
        completed: list[TaskId] = []

        for tid in self._state_core.task_ids:
            status = self.task_query.status(tid)

            if status == TaskStatus.PENDING:
                if self.task_query.release_time(tid) == time:
                    released.append(tid)

            elif status == TaskStatus.RUNNING:
                start_time = self.task_query.start_time(tid)
                machine_id = self.task_query.machine_id(tid)

                if (
                    machine_id is not None
                    and start_time is not None
                    and start_time + self.task_query.duration(tid) == time
                ):
                    completed.append(tid)

        return NaturalEffects(
            released_task_ids=tuple(released),
            completed_task_ids=tuple(completed),
        )

    # --- pulic mutations (facade) ---
    def complete(self, event: DomainInitiatedEvent) ->tuple[DomainCompletedEvent,...]:
        return self._state_core.complete(event)

    
    def debug_dump(self) -> str:
       
        lines: list[str] = []

        lines.append("=== SchedulingState Debug Dump ===")
        lines.append(f"Current time: {self.current_time}")

        lines.append("Tasks:")
        for tid in self._state_core.task_ids:
            tv = self.task_query
            lines.append(
                f"  Task {tid}: release={tv.release_time(tid)}, duration={tv.duration(tid)}, "
                f"status={tv.status(tid)}, machine={tv.machine_id(tid)}, "
                f"start={tv.start_time(tid)}, finish={tv.finish_time(tid)}"
            )

        # lines.append("Machines:")
        # for mid in self._state_core.machine_ids:
        #     mv = self.machine_view(mid)
        #     lines.append(
        #         f"  Machine {mid}: available_at={mv.availability_time}, task={mv.task_id}"
        #     )

        lines.append("=== End of Debug Dump ===")

        lines.append("=== Auxiliary Caches ===")
        lines.append(f"Ready tasks: {self.ready_task_ids}")
        lines.append(f"Completed tasks: {self.completed_task_ids}")
        lines.append(f"Idle machines: {self.idle_machine_ids}")
        lines.append(f"Min running task completion time: {self.next_completion_time()}")
        lines.append(f"Next release time: {self.next_release_time()}")
        lines.append("=== End of Auxiliary Caches ===")

        return "\n".join(lines)

    def audit(self) -> None:
        self._state_core.audit()
       


class TaskQuery(Protocol):
    def release_time(self, task_id: TaskId) -> int: ...
    def duration(self, task_id: TaskId) -> int: ...
    def deadline(self, task_id: TaskId) -> int | None: ...
    def status(self, task_id: TaskId) -> TaskStatus: ...
    def machine_id(self, task_id: TaskId) -> MachineId | None: ...
    def start_time(self, task_id: TaskId) -> int | None: ...
    def finish_time(self, task_id: TaskId) -> int | None: ...


class _TaskQueryImpl:
    __slots__ = ("_core",)

    def __init__(self, core: "_SchedulingStateCore"):
        self._core = core

    def release_time(self, task_id: TaskId) -> int:
        return self._core.task_release_time_of(task_id)

    def duration(self, task_id: TaskId) -> int:
        return self._core.task_duration_of(task_id)

    def deadline(self, task_id: TaskId) -> int | None:
        return self._core.task_deadline_of(task_id)

    def status(self, task_id: TaskId) -> TaskStatus:
        return self._core.task_status_of(task_id)

    def machine_id(self, task_id: TaskId) -> MachineId | None:
        return self._core.machine_id_of(task_id)

    def start_time(self, task_id: TaskId) -> int | None:
        return self._core.task_start_time_of(task_id)

    def finish_time(self, task_id: TaskId) -> int | None:
        return self._core.task_finish_time_of(task_id)
    
def initialize_scheduling_state(
    task_specs: list[TaskInit],
    machine_specs: list[MachineInit],
    now: int,
) -> SchedulingState:
    return SchedulingState.from_scenario(task_specs=task_specs, machine_specs=machine_specs, now=now)