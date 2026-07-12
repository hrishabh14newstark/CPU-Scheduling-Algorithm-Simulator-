"""
Round Robin (RR) Scheduling
==============================
Preemptive, single ready queue, fixed time quantum. Each process gets the
CPU for at most `quantum` time units; if it doesn't finish, it goes to the
BACK of the ready queue. Newly arrived processes join the back of the
queue in order of arrival.

Returns a dict:
    {
        "schedule":  [(pid, start_time, end_time), ...],
        "processes": [Process, ...]   # with start/completion/waiting/
                                       # turnaround/response times set
    }
"""

from collections import deque


def round_robin(processes, quantum):
    if quantum is None or quantum <= 0:
        raise ValueError("Round Robin requires a positive --quantum")

    for p in processes:
        p.remaining_time = p.burst_time
        p.start_time = None
        p.completion_time = None

    pending_arrivals = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    ready_queue = deque()
    completed = []
    schedule = []   # built directly as contiguous slices (one per dispatch)

    current_time = 0
    total = len(processes)

    def admit_arrivals(t):
        while pending_arrivals and pending_arrivals[0].arrival_time == t:
            ready_queue.append(pending_arrivals.pop(0))

    admit_arrivals(current_time)

    while len(completed) < total:
        if not ready_queue:
            # CPU idle -> jump to next arrival
            if pending_arrivals:
                current_time = pending_arrivals[0].arrival_time
                admit_arrivals(current_time)
            else:
                break
            continue

        proc = ready_queue.popleft()

        if proc.start_time is None:
            proc.start_time = current_time

        run_time = min(quantum, proc.remaining_time)
        start_time = current_time
        end_time = start_time + run_time

        # Admit any process that arrives strictly during this run, in
        # order, BEFORE this process (if it doesn't finish) is requeued --
        # that's the standard RR convention: arrivals at the exact tick
        # this slice ends are also admitted first.
        for t in range(start_time + 1, end_time + 1):
            admit_arrivals(t)

        proc.remaining_time -= run_time
        current_time = end_time

        schedule.append((proc.pid, start_time, end_time))

        if proc.remaining_time == 0:
            proc.completion_time = current_time
            proc.turnaround_time = proc.completion_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time
            proc.response_time = proc.start_time - proc.arrival_time
            completed.append(proc)
        else:
            ready_queue.append(proc)

    # Preserve original process order in the output
    completed_by_pid = {p.pid: p for p in completed}
    ordered_processes = [completed_by_pid[p.pid] for p in processes]

    return {
        "schedule": schedule,
        "processes": ordered_processes,
    }