from __future__ import annotations

from decision_scheduler.domain.models.state import SchedulingState


from matplotlib import pyplot as plt

def save_gantt(state: SchedulingState, filename: str, title:str|None) -> None:
    """
    Save a Gantt chart representation of the scheduling state to a file.
    """
    allocations = state.allocations
    if not allocations:
        return
    
    resource_groups = {}
    for mid, task_id in allocations.items():
        resource_groups.setdefault(mid, []).append(task_id)

    fig, ax = plt.subplots(figsize=(10, 6))

    y_positions = {rid:i for i, rid in enumerate(sorted(resource_groups.keys()))}

    for rid, allocs in resource_groups.items():
        for alloc in sorted(allocs, key=lambda a: state.task_runtimes[a].start_time):
            rt = state.task_runtimes[alloc]
            ax.barh(y_positions[rid], rt.end_time - rt.start_time, left=rt.start_time, height=0.4)
            ax.text(rt.start_time , y_positions[rid],f"T{rt.task_id}", va='center', ha='left', color='white', fontsize=8)
    
    ax.set_yticks([y_positions[rid] for rid in sorted(resource_groups.keys())],
                  [f"R{rid}" for rid in sorted(resource_groups.keys())])
    ax.set_xlabel("Time")
    ax.set_ylabel("Resources")
    ax.set_title(title if title else "Gantt Chart")

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
