"""
Shortest Job First (SJF) Scheduling
======================================
Two modes:
    preemptive=False -> classic SJF (non-preemptive): once a process starts
                         running it runs to completion, chosen by shortest
                         BURST time among processes that have arrived.
    preemptive=True  -> Shortest Remaining Time First (SRTF): at every
                         instant the process with the shortest REMAINING
                         time runs; a running process is preempted the
                         instant a shorter job arrives.

Ties are broken by arrival time, then by original input order.

Returns a dict:
    {
        "schedule":  [(pid, start_time, end_time), ...],
        "processes": [Process, ...]   # with start/completion/waiting/
                                       # turnaround/response times set
    }
"""


def sjf(processes, preemptive=False):
    if preemptive:
        return _srtf(processes)
    return _sjf_non_preemptive(processes)


# --------------------------------------------------------------------------- #
# Non-preemptive SJF
# --------------------------------------------------------------------------- #

def _sjf_non_preemptive(processes):
    remaining = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    for p in remaining:
        p.remaining_time = p.burst_time
        p.start_time = None
        p.completion_time = None

    schedule = []
    completed = []
    current_time = 0

    while remaining:
        ready = [p for p in remaining if p.arrival_time <= current_time]

        if not ready:
            current_time = min(p.arrival_time for p in remaining)
            continue

        # Pick shortest burst time; ties -> earlier arrival, then input order
        next_proc = min(ready, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
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

    completed_by_pid = {p.pid: p for p in completed}
    ordered_processes = [completed_by_pid[p.pid] for p in processes]

    return {
        "schedule": schedule,
        "processes": ordered_processes,
    }


# --------------------------------------------------------------------------- #
# Preemptive SJF (Shortest Remaining Time First)
# --------------------------------------------------------------------------- #

def _srtf(processes):
    for p in processes:
        p.remaining_time = p.burst_time
        p.start_time = None
        p.completion_time = None

    pending_arrivals = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    ready = []
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

        # Shortest remaining time; ties -> earlier arrival, then input order
        running = min(ready, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))

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
        # else: stays in `ready`; next tick re-evaluates the shortest
        # remaining-time process (could be preempted by a new arrival)

    schedule = []
    for pid, start, end in raw_schedule:
        if schedule and schedule[-1][0] == pid and schedule[-1][2] == start:
            schedule[-1] = (pid, schedule[-1][1], end)
        else:
            schedule.append((pid, start, end))

    completed_by_pid = {p.pid: p for p in completed}
    ordered_processes = [completed_by_pid[p.pid] for p in processes]

    return {
        "schedule": schedule,
        "processes": ordered_processes,
    }