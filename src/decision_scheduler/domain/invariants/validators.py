# validators.py
from  ..models.state import TaskInit
from ..models.resource import MachineInit
from ..support.exceptions import InvalidTaskInitError

def validate_task_init(task_init: TaskInit) -> None:
    duration = task_init["duration"]
    release_time = task_init["release_time"]
    deadline = task_init.get("deadline")

    if duration <= 0:
        raise InvalidTaskInitError("duration must be > 0")

    if release_time < 0:
        raise InvalidTaskInitError("release_time must be >= 0")

    if deadline is not None and deadline < release_time:
        raise InvalidTaskInitError("deadline must be >= release_time")
    
def validate_machine_init(machine_init:MachineInit) -> None:
    # For now, we don't have any parameters in MachineInit, but this function can be extended in the future if needed.
    pass