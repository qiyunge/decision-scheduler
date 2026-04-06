from dataclasses import dataclass
from typing import NewType

## the place to use taskid will always not be a resourceid, 
## so we dont need to inherit from a common base to reduce code duplication. 

# @dataclass(frozen=True)
# class TaskId:
#     value: str

# @dataclass(frozen=True)
# class ResourceId:
#     value: str

# @dataclass(frozen=True)
# class AllocationId:
#     value: str

TaskId = NewType('TaskId', int)
MachineId = NewType('MachineId', int)
ResourceId = NewType('ResourceId', int)
AllocationId = NewType('AllocationId', int)