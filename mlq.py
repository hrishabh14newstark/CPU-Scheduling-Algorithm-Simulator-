"""
Multilevel Queue (MLQ) Scheduling
====================================
Preemptive, strict priority between queues, Round-Robin within each queue.

Unlike MLFQ, processes are permanently assigned to a queue (via
`process.queue`, e.g. 0 = system/high priority, 1 = interactive,
2 = batch/low priority) and NEVER move between queues -- there is no
demotion/promotion. Queue 0 always has strict priority over queue 1,
queue 1 over queue 2, and so on: a process becoming ready in a
higher-priority queue preempts whatever is currently running from a
lower-priority queue.

Each queue is scheduled Round-Robin using the same time quantum.
If a process doesn't specify `queue`, it defaults to 0.

Returns a dict:
    {
        "schedule":  [(pid, start_time, end_time), ...],
        "processes": [Process, ...]   # with start/completion/waiting/
                                       # turnaround/response times set
    }
"""

from collections import deque


def mlq(processes, quantum=4):
    if quantum is None or quantum <= 0:
        raise ValueError("MLQ requires a positive --quantum")

    # Reset run-time state and determine number of queue levels
    max_queue = 0
    for p in processes:
        p.remaining_time = p.burst_time
        p.queue = getattr(p, "queue", 0) or 0
        p.quantum_used = 0
        p.start_time = None
        p.completion_time = None
        max_queue = max(max_queue, p.queue)

    num_levels = max_queue + 1
    pending_arrivals = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    queues = [deque() for _ in range(num_levels)]

    completed = []
    raw_schedule = []   # (pid, start, end) per 1-unit tick, merged afterwards

    current_time = 0
    running = None
    total = len(processes)

    def admit_arrivals(t):
        """Move any process with arrival_time == t into its assigned queue."""
        while pending_arrivals and pending_arrivals[0].arrival_time == t:
            proc = pending_arrivals.pop(0)
            queues[proc.queue].append(proc)

    def highest_ready_level():
        for lvl in range(num_levels):
            if queues[lvl]:
                return lvl
        return None

    admit_arrivals(current_time)

    while len(completed) < total:
        # Fast-forward if CPU idle and nothing is ready
        if running is None and highest_ready_level() is None:
            if pending_arrivals:
                current_time = pending_arrivals[0].arrival_time
                admit_arrivals(current_time)
            else:
                break
            continue

        # Preemption: a higher (lower-numbered) queue became ready
        if running is not None:
            best_ready = highest_ready_level()
            if best_ready is not None and best_ready < running.queue:
                queues[running.queue].append(running)
                running.quantum_used = 0
                running = None

        # Pick next process if CPU idle
        if running is None:
            lvl = highest_ready_level()
            running = queues[lvl].popleft()
            running.quantum_used = 0

        if running.start_time is None:
            running.start_time = current_time

        # Execute one time unit
        raw_schedule.append((running.pid, current_time, current_time + 1))
        running.remaining_time -= 1
        running.quantum_used += 1
        current_time += 1

        admit_arrivals(current_time)

        if running.remaining_time == 0:
            running.completion_time = current_time
            running.turnaround_time = running.completion_time - running.arrival_time
            running.waiting_time = running.turnaround_time - running.burst_time
            running.response_time = running.start_time - running.arrival_time
            completed.append(running)
            running = None
            continue

        if running.quantum_used >= quantum:
            # Time slice expired -> requeue at the back of the SAME queue
            queues[running.queue].append(running)
            running.quantum_used = 0
            running = None

    # Merge consecutive 1-unit ticks of the same pid into contiguous slices
    schedule = []
    for pid, start, end in raw_schedule:
        if schedule and schedule[-1][0] == pid and schedule[-1][2] == start:
            schedule[-1] = (pid, schedule[-1][1], end)
        else:
            schedule.append((pid, start, end))

    # Preserve original process order in the output
    completed_by_pid = {p.pid: p for p in completed}
    ordered_processes = [completed_by_pid[p.pid] for p in processes]

    return {
        "schedule": schedule,
        "processes": ordered_processes,
    }