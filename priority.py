"""
Priority Scheduling
=====================
Lower `priority` value = higher priority (e.g. priority 0 runs before
priority 5). Ties are broken by arrival time, then by original input order.

Two modes:
    preemptive=False  -> classic Priority Scheduling (non-preemptive):
                          once a process starts running it runs to
                          completion, uninterrupted by later arrivals.
    preemptive=True   -> Preemptive Priority Scheduling:
                          a running process is preempted the instant a
                          higher-priority process arrives.

Returns a dict:
    {
        "schedule":  [(pid, start_time, end_time), ...],
        "processes": [Process, ...]   # with start/completion/waiting/
                                       # turnaround/response times set
    }
"""


def priority_scheduling(processes, preemptive=False):
    if preemptive:
        return _priority_preemptive(processes)
    return _priority_non_preemptive(processes)


# --------------------------------------------------------------------------- #
# Non-preemptive
# --------------------------------------------------------------------------- #

def _priority_non_preemptive(processes):
    remaining = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    for p in remaining:
        p.remaining_time = p.burst_time
        p.start_time = None
        p.completion_time = None

    schedule = []
    completed = []
    current_time = 0

    while remaining:
        # Processes that have arrived by current_time
        ready = [p for p in remaining if p.arrival_time <= current_time]

        if not ready:
            # CPU idle -> jump to the next arrival
            current_time = min(p.arrival_time for p in remaining)
            continue

        # Pick highest priority (lowest number) among ready processes;
        # ties -> earlier arrival, then original input order
        next_proc = min(ready, key=lambda p: (p.priority, p.arrival_time, p.pid))
        remaining.remove(next_proc)

        start_time = current_time
        end_time = start_time + next_proc.burst_time

        next_proc.start_time = start_time
        next_proc.completion_time = end_time
        next_proc.turnaround_time = next_proc.completion_time - next_proc.arrival_time
        next_proc.waiting_time = next_proc.turnaround_time - next_proc.burst_time
        next_proc.response_time = next_proc.start_time - next_proc.arrival_time
        next_proc.remaining_time = 0

        schedule.append((next_proc.pid, start_time, end_time))
        completed.append(next_proc)
        current_time = end_time

    # Preserve original process order in the output
    completed_by_pid = {p.pid: p for p in completed}
    ordered_processes = [completed_by_pid[p.pid] for p in processes]

    return {
        "schedule": schedule,
        "processes": ordered_processes,
    }


# --------------------------------------------------------------------------- #
# Preemptive
# --------------------------------------------------------------------------- #

def _priority_preemptive(processes):
    for p in processes:
        p.remaining_time = p.burst_time
        p.start_time = None
        p.completion_time = None

    pending_arrivals = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    ready = []          # processes that have arrived but not finished
    completed = []
    raw_schedule = []   # (pid, start, end) per 1-unit tick, merged afterwards

    current_time = 0
    total = len(processes)

    def admit_arrivals(t):
        while pending_arrivals and pending_arrivals[0].arrival_time == t:
            ready.append(pending_arrivals.pop(0))

    admit_arrivals(current_time)

    while len(completed) < total:
        if not ready:
            if pending_arrivals:
                current_time = pending_arrivals[0].arrival_time
                admit_arrivals(current_time)
            else:
                break
            continue

        # Highest priority (lowest number) ready process; ties -> earlier
        # arrival, then original input order
        running = min(ready, key=lambda p: (p.priority, p.arrival_time, p.pid))

        if running.start_time is None:
            running.start_time = current_time

        raw_schedule.append((running.pid, current_time, current_time + 1))
        running.remaining_time -= 1
        current_time += 1

        admit_arrivals(current_time)

        if running.remaining_time == 0:
            running.completion_time = current_time
            running.turnaround_time = running.completion_time - running.arrival_time
            running.waiting_time = running.turnaround_time - running.burst_time
            running.response_time = running.start_time - running.arrival_time
            ready.remove(running)
            completed.append(running)
        # else: leave it in `ready`; next loop iteration re-evaluates the
        # highest-priority ready process (may be the same one, or a
        # newly-arrived higher-priority one that just preempted it)

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