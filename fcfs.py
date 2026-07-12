"""
First Come First Serve (FCFS) Scheduling
==========================================
Non-preemptive. Processes are executed strictly in order of arrival time.
If two processes arrive at the same time, the one with the lower pid
(input order) goes first.

Returns a dict:
    {
        "schedule":  [(pid, start_time, end_time), ...],
        "processes": [Process, ...]   # with start/completion/waiting/
                                       # turnaround/response times set
    }
"""


def fcfs(processes):
    # Sort by arrival time; ties broken by original input order (stable sort)
    ordered = sorted(processes, key=lambda p: p.arrival_time)

    schedule = []
    current_time = 0

    for process in ordered:
        # CPU sits idle if next process hasn't arrived yet
        if current_time < process.arrival_time:
            current_time = process.arrival_time

        start_time = current_time
        end_time = start_time + process.burst_time

        process.start_time = start_time
        process.completion_time = end_time
        process.turnaround_time = process.completion_time - process.arrival_time
        process.waiting_time = process.turnaround_time - process.burst_time
        process.response_time = process.start_time - process.arrival_time
        process.remaining_time = 0

        schedule.append((process.pid, start_time, end_time))
        current_time = end_time

    return {
        "schedule": schedule,
        "processes": ordered,
    }