from __future__ import annotations

from collections.abc import Iterator, KeysView, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol

from .task import _TaskSpec, _TaskRuntime, TaskInit, TaskStatus, TaskView
from .ids import TaskId, MachineId
from .resource import _MachineSpec, MachineInit, MachineView
from ..invariants.exceptions import SchedulingException
from .mutations import TimeAdvanceRecord


# =========================
# Auxiliary (stats/caches)
# =========================

@dataclass(slots=True)
class _SchedulingStateAuxiliary:
    stat_completed_task_count: int = field(default=0, init=False)

    # task-view cache
    cache_task_state_version: int = field(default=-1, init=False)
    cache_task_views: Mapping[TaskId, TaskView] | None = field(default=None, init=False)

    # derived-set caches (you can add version gating later; for now invalidate on mutation)
    cache_ready_tasks: frozenset[TaskId] | None = field(default=None, init=False)
    cache_completed_tasks: frozenset[TaskId] | None = field(default=None, init=False)

    # idle machines cache
    cache_machine_state_version: int = field(default=-1, init=False)
    cache_idle_machine_ids: tuple[MachineId, ...] | None = field(default=None, init=False)

    def invalidate(self) -> None:
        # invalidate all derived caches (safe + simple)
        self.cache_task_views = None
        self.cache_ready_tasks = None
        self.cache_completed_tasks = None
        self.cache_idle_machine_ids = None


# =========================
# Core (state + invariants)
# =========================

@dataclass(slots=True)
class _SchedulingStateCore:
    # --- theta (immutable scenario) ---
    _task_specs: dict[TaskId, _TaskSpec] = field(default_factory=dict, init=False)
    _machine_specs: dict[MachineId, _MachineSpec] = field(default_factory=dict, init=False)

    # --- runtime ---
    _current_time: int = field(default=0, init=False)

    # versions for invalidation
    _task_state_version: int = field(default=0, init=False)
    _machine_state_version: int = field(default=0, init=False)

    # runtime objects
    _task_runtimes: dict[TaskId, _TaskRuntime] = field(default_factory=dict, init=False)

    # machine runtime facts
    _allocations: dict[MachineId, TaskId] = field(default_factory=dict, init=False)  # machine -> running task
    _busy_until: dict[MachineId, int] = field(default_factory=dict, init=False)      # machine -> busy until time

    # id generation
    _next_task_id: TaskId = field(default=0, init=False)
    _next_machine_id: MachineId = field(default=0, init=False)

    # -------- version helpers --------
    @property
    def task_state_version(self) -> int:
        return self._task_state_version

    @property
    def machine_state_version(self) -> int:
        return self._machine_state_version

    def _invalidate_task_state(self) -> None:
        self._task_state_version += 1

    def _invalidate_machine_state(self) -> None:
        self._machine_state_version += 1

    # -------- ids --------
    def _get_next_task_id(self) -> TaskId:
        tid = self._next_task_id
        self._next_task_id += 1
        return tid

    def _get_next_machine_id(self) -> MachineId:
        mid = self._next_machine_id
        self._next_machine_id += 1
        return mid

    # -------- queries (facts) --------
    @property
    def current_time(self) -> int:
        return self._current_time

    @property
    def task_ids(self) -> KeysView[TaskId]:
        return self._task_specs.keys()

    @property
    def machine_ids(self) -> KeysView[MachineId]:
        return self._machine_specs.keys()

    def allocated_machine_id(self, task_id: TaskId) -> MachineId | None:
        rt = self._task_runtimes.get(task_id)
        if rt is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return rt.machine_id if rt.status is TaskStatus.RUNNING else None

    def allocated_task_id(self, machine_id: MachineId) -> TaskId | None:
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        return self._allocations.get(machine_id)

    def busy_until(self, machine_id: MachineId) -> int:
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        return self._busy_until.get(machine_id, 0)

    def task_status(self, task_id: TaskId) -> TaskStatus:
        rt = self._task_runtimes.get(task_id)
        if rt is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return rt.status

    def task_release_time(self, task_id: TaskId) -> int:
        spec = self._task_specs.get(task_id)
        if spec is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return spec.release_time

    def task_deadline(self, task_id: TaskId) -> int | None:
        spec = self._task_specs.get(task_id)
        if spec is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return spec.deadline

    def task_duration(self, task_id: TaskId) -> int:
        spec = self._task_specs.get(task_id)
        if spec is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return spec.duration

    def task_start_time(self, task_id: TaskId) -> int | None:
        rt = self._task_runtimes.get(task_id)
        if rt is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return rt.start_time

    def task_finish_time(self, task_id: TaskId) -> int | None:
        rt = self._task_runtimes.get(task_id)
        if rt is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return rt.finish_time

    def task_view(self, task_id: TaskId) -> TaskView:
        rt = self._task_runtimes.get(task_id)
        spec = self._task_specs.get(task_id)
        if rt is None or spec is None:
            raise SchedulingException(f"Unknown task {task_id}.")
        return TaskView(
            id=task_id,
            release_time=spec.release_time,
            duration=spec.duration,
            status=rt.status,
            machine_id=rt.machine_id,
            start_time=rt.start_time,
            finish_time=rt.finish_time,
            deadline=spec.deadline
        )

    def machine_view(self, machine_id: MachineId) -> MachineView:
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        return MachineView(
            id=machine_id,
            availability_time=self._busy_until.get(machine_id, 0),
            task_id=self._allocations.get(machine_id),
        )

    # -------- mutations --------
    def create_task(self, task_init: TaskInit) -> TaskId:
        task_id = self._get_next_task_id()

        self._task_specs[task_id] = _TaskSpec(
            duration=task_init["duration"],
            release_time=task_init["release_time"],
            deadline=task_init["deadline"],
        )
        self._task_runtimes[task_id] = _TaskRuntime(
            id=task_id,
            status=TaskStatus.PENDING,
        )

        self._invalidate_task_state()
        return task_id

    def create_machine(self, machine_init: MachineInit) -> MachineId:
        machine_id = self._get_next_machine_id()
        self._machine_specs[machine_id] = _MachineSpec.from_init(machine_init)

        self._invalidate_machine_state()
        return machine_id

    def dispatch(self, *, machine_id: MachineId, task_id: TaskId) -> tuple[TaskId, MachineId, int]:
        # core only checks structural invariants + basic facts
        self._assert_can_dispatch(machine_id, task_id)
        self._start_task(task_id, machine_id)
        return (task_id, machine_id, self._current_time)

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

    def _start_task(self, task_id: TaskId, machine_id: MachineId) -> None:
        spec = self._task_specs[task_id]
        rt = self._task_runtimes[task_id]

        rt.status = TaskStatus.RUNNING
        rt.machine_id = machine_id
        rt.start_time = self._current_time
        rt.finish_time = None

        self._allocations[machine_id] = task_id
        self._busy_until[machine_id] = self._current_time + spec.duration

        self._invalidate_task_state()
        self._invalidate_machine_state()

    def advance_time_to(self, target_time: int) -> tuple[bool, int]:
        old_time = self._current_time
        if target_time < self._current_time:
            raise SchedulingException("Time cannot go backwards.")
        if target_time == self._current_time:
            return False, old_time

        self._current_time = target_time
        # time changes can affect readiness, deadlines, etc.
        self._invalidate_task_state()
        self._invalidate_machine_state()
        return True, old_time

    def complete_on_machine(self, machine_id: MachineId) -> tuple[TaskId, MachineId, int]:
        if machine_id not in self._machine_specs:
            raise SchedulingException(f"Unknown machine {machine_id}.")
        if machine_id not in self._allocations:
            raise SchedulingException(f"Machine {machine_id} is not currently allocated to any task.")
        if machine_id not in self._busy_until:
            raise SchedulingException(f"Inconsistent state: machine {machine_id} has allocation but no busy_until.")

        task_id = self._allocations.pop(machine_id)
        del self._busy_until[machine_id]

        rt = self._task_runtimes[task_id]
        rt.status = TaskStatus.COMPLETED
        rt.finish_time = self._current_time
        rt.machine_id = None  # optional: clear machine pointer

        self._invalidate_task_state()
        self._invalidate_machine_state()
        return (task_id, machine_id, self._current_time)

    def audit(self) -> None:
        # runtime-spec consistency
        if set(self._task_runtimes.keys()) != set(self._task_specs.keys()):
            raise SchedulingException("Inconsistent state: task runtimes and specs keys do not match.")

        # allocations <-> busy_until consistency
        for mid in self._allocations.keys():
            if mid not in self._busy_until:
                raise SchedulingException(f"Inconsistent state: machine {mid} has allocation but no busy_until.")
        for mid in self._busy_until.keys():
            if mid not in self._allocations:
                raise SchedulingException(f"Inconsistent state: machine {mid} has busy_until but no allocation.")

        # task status consistency with allocations
        for mid, tid in self._allocations.items():
            rt = self._task_runtimes[tid]
            if rt.status is not TaskStatus.RUNNING:
                raise SchedulingException(f"Inconsistent state: task {tid} allocated to machine {mid} but status is {rt.status}.")

        # time consistency
        if self._current_time < 0:
            raise SchedulingException(f"Inconsistent state: current_time {self._current_time} is negative.")


# =========================
# Aggregate root (facade)
# =========================

@dataclass
class SchedulingState:
    _debug: bool = field(default=False, init=False)
    _state_core: _SchedulingStateCore = field(default_factory=_SchedulingStateCore, init=False, repr=False)
    _state_aux: _SchedulingStateAuxiliary = field(default_factory=_SchedulingStateAuxiliary, init=False, repr=False)

    # ---- factory ----
    @classmethod
    def from_scenario(
        cls: type["SchedulingState"],
        task_specs: list[TaskInit],
        machine_specs: list[MachineInit],
        now: int = 0,
    ) -> "SchedulingState":
        state = cls()
        state._state_core._current_time = now

        for t in task_specs:
            state._state_core.create_task(t)
        for m in machine_specs:
            state._state_core.create_machine(m)

        state.audit()
        return state

    # ---- basic properties ----
    @property
    def current_time(self) -> int:
        return self._state_core.current_time

    @property
    def total_tasks(self) -> int:
        return len(self._state_core.task_ids)

    # ---- queries ----
    def task_view(self, task_id: TaskId) -> TaskView:
        return self._state_core.task_view(task_id)

    def machine_view(self, machine_id: MachineId) -> MachineView:
        return self._state_core.machine_view(machine_id)

    def iter_task_views(self) -> Iterator[TaskView]:
        for tid in tuple(self._state_core.task_ids):
            yield self.task_view(tid)

    def snapshot_task_views(self) -> Mapping[TaskId, TaskView]:
        core_ver = self._state_core.task_state_version
        if (self._state_aux.cache_task_views is not None and
            self._state_aux.cache_task_state_version == core_ver):
            return self._state_aux.cache_task_views

        task_ids = tuple(self._state_core.task_ids)
        d = {tid: self.task_view(tid) for tid in task_ids}
        snap = MappingProxyType(d)

        self._state_aux.cache_task_views = snap
        self._state_aux.cache_task_state_version = core_ver
        return snap

    def iter_idle_machine_ids(self) -> Iterator[MachineId]:
        for mid in tuple(self._state_core.machine_ids):
            if self._state_core.allocated_task_id(mid) is None:
                yield mid

    def snapshot_idle_machine_ids(self) -> tuple[MachineId, ...]:
        core_ver = self._state_core.machine_state_version
        if (self._state_aux.cache_idle_machine_ids is not None and
            self._state_aux.cache_machine_state_version == core_ver):
            return self._state_aux.cache_idle_machine_ids

        snap = tuple(self.iter_idle_machine_ids())
        self._state_aux.cache_idle_machine_ids = snap
        self._state_aux.cache_machine_state_version = core_ver
        return snap

    def iter_pending_task_ids(self) -> Iterator[TaskId]:
        for tid in tuple(self._state_core.task_ids):
            if self._state_core.task_status(tid) is TaskStatus.PENDING:
                yield tid

    def snapshot_pending_task_ids(self) -> frozenset[TaskId]:
        return frozenset(self.iter_pending_task_ids())

    def iter_completed_task_ids(self) -> Iterator[TaskId]:
        for tid in tuple(self._state_core.task_ids):
            if self._state_core.task_status(tid) is TaskStatus.COMPLETED:
                yield tid

    def snapshot_completed_task_ids(self) -> frozenset[TaskId]:
        # simple cache (invalidate on mutation)
        if self._state_aux.cache_completed_tasks is not None:
            return self._state_aux.cache_completed_tasks
        snap = frozenset(self.iter_completed_task_ids())
        self._state_aux.cache_completed_tasks = snap
        return snap

    def is_task_ready(self, task_id: TaskId) -> bool:
        return (
            self._state_core.task_status(task_id) is TaskStatus.PENDING
            and self._state_core.task_release_time(task_id) <= self._state_core.current_time
        )

    def iter_ready_task_ids(self) -> Iterator[TaskId]:
        for tid in self.iter_pending_task_ids():
            if self.is_task_ready(tid):
                yield tid

    def snapshot_ready_task_ids(self) -> frozenset[TaskId]:
        if self._state_aux.cache_ready_tasks is not None:
            return self._state_aux.cache_ready_tasks
        snap = frozenset(self.iter_ready_task_ids())
        self._state_aux.cache_ready_tasks = snap
        return snap
    
    def next_completion_time(self) -> int | None:
        times = []
        for mid in self._state_core.machine_ids:
            if self._state_core.allocated_task_id(mid) is not None:
                times.append(self._state_core.busy_until(mid))
        return min(times) if times else None
    
    def next_release_time(self) -> int | None:
        now = self.current_time
        times: list[int] = []
        for tid in self._state_core.task_ids:
            if self._state_core.task_status(tid) is TaskStatus.PENDING:
                rt = self._state_core.task_release_time(tid)
                if rt > now:
                    times.append(rt)
        return min(times) if times else None

    def is_finished(self) -> bool:
        return self._state_aux.stat_completed_task_count == self.total_tasks

    # ---- mutations (facade) ----
    def dispatch(self, *, machine_id: MachineId, task_id: TaskId) -> tuple[TaskId, MachineId, int]:
        # policy/semantic check lives here (ready rule)
        if not self.is_task_ready(task_id):
            raise SchedulingException(f"Task {task_id} is not ready to be dispatched.")
        result = self._state_core.dispatch(machine_id=machine_id, task_id=task_id)

        # invalidate derived caches
        self._state_aux.invalidate()
        return result

    def advance_time_to(self, target_time: int) -> TimeAdvanceRecord | None:
        changed, old_time = self._state_core.advance_time_to(target_time)
        if changed:
            self._state_aux.invalidate()
        return TimeAdvanceRecord(from_time=old_time, to_time=target_time) if changed else None

    def complete_on_machine(self, machine_id: MachineId) -> tuple[TaskId, MachineId, int]:
        result = self._state_core.complete_on_machine(machine_id)

        # stats update
        self._state_aux.stat_completed_task_count += 1
        # invalidate derived caches
        self._state_aux.invalidate()
        return result
    
    def task_query(self) -> TaskQuery:
        return _TaskQueryImpl(self._state_core)
    
    def debug_dump(self) -> None:
        print("=== SchedulingState Debug Dump ===")
        print(f"Current time: {self.current_time}")
        print("Tasks:")
        for tid in self._state_core.task_ids:
            tv = self.task_view(tid)
            print(f"  Task {tid}: release={tv.release_time}, duration={tv.duration}, "
                  f"status={tv.status}, machine={tv.machine_id}, "
                  f"start={tv.start_time}, finish={tv.finish_time}")
        print("Machines:")
        for mid in self._state_core.machine_ids:
            mv = self.machine_view(mid)
            print(f"  Machine {mid}: available_at={mv.availability_time}, task={mv.task_id}")
        print("=== End of Debug Dump ===")

    def audit(self) -> None:
        self._state_core.audit()
        # aux stat consistency check
        actual_completed = sum(1 for tid in self._state_core.task_ids
                               if self._state_core.task_status(tid) is TaskStatus.COMPLETED)
        if self._state_aux.stat_completed_task_count != actual_completed:
            raise SchedulingException(
                f"Inconsistent aux: completed_task_count {self._state_aux.stat_completed_task_count} "
                f"!= actual {actual_completed}"
            )


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
        return self._core.task_release_time(task_id)

    def duration(self, task_id: TaskId) -> int:
        return self._core.task_duration(task_id)

    def deadline(self, task_id: TaskId) -> int | None:
        return self._core.task_deadline(task_id)

    def status(self, task_id: TaskId) -> TaskStatus:
        return self._core.task_status(task_id)

    def machine_id(self, task_id: TaskId) -> MachineId | None:
        return self._core.allocated_machine_id(task_id)

    def start_time(self, task_id: TaskId) -> int | None:
        return self._core.task_start_time(task_id)

    def finish_time(self, task_id: TaskId) -> int | None:
        return self._core.task_finish_time(task_id)
    
def initialize_scheduling_state(
    task_specs: list[TaskInit],
    machine_specs: list[MachineInit],
    now: int,
) -> SchedulingState:
    return SchedulingState.from_scenario(task_specs=task_specs, machine_specs=machine_specs, now=now)