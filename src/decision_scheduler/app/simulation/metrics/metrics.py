from __future__ import annotations

from ....domain.models.state import SchedulingState

class Metrics:
    """
    Evaluation functions J(s_final)
    """
    @staticmethod
    def evaluate(state: SchedulingState) -> dict:
        if not state.allocations:
            return {}
        
        task_map = {t.id:t for t in state.completed_tasks}

        completion_times = {alloc.task_id: alloc.end_time for alloc in state.allocations}

        makespan = max(completion_times.values())

        flow_time = []
        tardiness = []

        for task_id, completion_time in completion_times.items():
            task = task_map[task_id]
            flow_time.append(completion_time - task.release_time)

            if task.deadline is not None:
                lateness = completion_time - task.deadline
                tardiness.append(max(0, lateness))

        avg_flow = sum(flow_time) / len(flow_time) if flow_time else 0
        avg_tardiness = sum(tardiness) / len(tardiness) if tardiness else 0
        max_tardiness = max(tardiness) if tardiness else 0
        
        return {
            'makespan': makespan,
            'avg_flow_time': round(avg_flow,3),
            'avg_tardiness': round(avg_tardiness,3),
            'max_tardiness': max_tardiness
        }