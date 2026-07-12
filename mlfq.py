"""
Multilevel Feedback Queue (MLFQ) Scheduling
=============================================
Preemptive. Processes start in the highest-priority queue (level 0) and are
demoted to the next lower-priority queue if they don't finish within that
level's time quantum. Each level is scheduled Round-Robin using its own
quantum. Level 0 always has strict priority over level 1, level 1 over
level 2, and so on -- a process arriving (or being requeued) into a higher
level preempts whatever is currently running from a lower level.

    quantums = [4, 8, 12]
        level 0 quantum = 4
        level 1 quantum = 8
        level 2 quantum = 12  (lowest level, still Round-Robin here)

Returns a dict:
    {
        "schedule":  [(pid, start_time, end_time), ...],
        "processes": [Process, ...]   # with start/completion/waiting/
                                       # turnaround/response times set
    }
"""

from collections import deque


def mlfq(processes, quantums=None):
    if quantums is None:
        quantums = [4, 8, 12]
    if not quantums:
        raise ValueError("MLFQ requires at least one queue level/quantum")

    num_levels = len(quantums)

    # Reset run-time state on each process
    for p in processes:
        p.remaining_time = p.burst_time
        p.level = 0
        p.quantum_used = 0
        p.start_time = None
        p.completion_time = None

    pending_arrivals = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    queues = [deque() for _ in range(num_levels)]

    completed = []
    raw_schedule = []   # (pid, start, end) per 1-unit tick, merged afterwards

    current_time = 0
    running = None      # process currently on the CPU
    total = len(processes)

    def admit_arrivals(t):
        """Move any process with arrival_time == t into level-0 queue."""
        while pending_arrivals and pending_arrivals[0].arrival_time == t:
            proc = pending_arrivals.pop(0)
            queues[0].append(proc)

    def highest_ready_level():
        for lvl in range(num_levels):
            if queues[lvl]:
                return lvl
        return None

    # Prime t = 0 arrivals
    admit_arrivals(current_time)

    while len(completed) < total:
        # If nothing is running and nothing is ready, fast-forward to next arrival
        if running is None and highest_ready_level() is None:
            if pending_arrivals:
                current_time = pending_arrivals[0].arrival_time
                admit_arrivals(current_time)
            else:
                break  # nothing left to do
            continue

        # Preemption check: if something is running, see if a strictly
        # higher-priority (lower-numbered) queue now has a waiting process
        if running is not None:
            best_ready = highest_ready_level()
            if best_ready is not None and best_ready < running.level:
                # Preempt: requeue current process at the BACK of its own level
                queues[running.level].append(running)
                running = None

        # Pick a process to run if CPU is idle
        if running is None:
            lvl = highest_ready_level()
            running = queues[lvl].popleft()
            running.level = lvl
            running.quantum_used = 0

        if running.start_time is None:
            running.start_time = current_time

        # Execute one time unit
        raw_schedule.append((running.pid, current_time, current_time + 1))
        running.remaining_time -= 1
        running.quantum_used += 1
        current_time += 1

        # New arrivals at the new current_time join level 0
        admit_arrivals(current_time)

        if running.remaining_time == 0:
            # Process finished
            running.completion_time = current_time
            running.turnaround_time = running.completion_time - running.arrival_time
            running.waiting_time = running.turnaround_time - running.burst_time
            running.response_time = running.start_time - running.arrival_time
            completed.append(running)
            running = None
            continue

        level_quantum = quantums[running.level]
        if running.quantum_used >= level_quantum:
            # Time slice expired -> demote (unless already at the lowest level)
            next_level = min(running.level + 1, num_levels - 1)
            running.level = next_level
            running.quantum_used = 0
            queues[next_level].append(running)
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