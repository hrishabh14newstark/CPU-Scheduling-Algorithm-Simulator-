"""
Scheduling Metrics
====================
Computes and displays the standard CPU scheduling metrics:

    Waiting Time (WT)      = Turnaround Time - Burst Time
    Turnaround Time (TAT)  = Completion Time - Arrival Time
    Response Time (RT)     = Start Time (first dispatch) - Arrival Time

These are expected to already be set on each Process by the algorithm
that scheduled it (see algorithms/*.py); this module just aggregates
and pretty-prints them.
"""


def calculate_metrics(processes):
    """Return a list of per-process metric dicts plus aggregate averages.

    Assumes each process already has: pid, arrival_time, burst_time,
    completion_time, turnaround_time, waiting_time, response_time set.
    """
    rows = []
    for p in sorted(processes, key=lambda p: p.pid):
        rows.append({
            "pid": p.pid,
            "arrival_time": p.arrival_time,
            "burst_time": p.burst_time,
            "completion_time": p.completion_time,
            "turnaround_time": p.turnaround_time,
            "waiting_time": p.waiting_time,
            "response_time": p.response_time,
        })

    n = len(rows) or 1
    avg_wt = sum(r["waiting_time"] for r in rows) / n
    avg_tat = sum(r["turnaround_time"] for r in rows) / n
    avg_rt = sum(r["response_time"] for r in rows) / n

    last_completion = max((r["completion_time"] for r in rows), default=0)
    total_burst = sum(r["burst_time"] for r in rows)
    throughput = len(rows) / last_completion if last_completion else 0.0
    cpu_utilization = (total_burst / last_completion * 100) if last_completion else 0.0

    return {
        "rows": rows,
        "avg_waiting_time": avg_wt,
        "avg_turnaround_time": avg_tat,
        "avg_response_time": avg_rt,
        "throughput": throughput,
        "cpu_utilization": cpu_utilization,
    }


def print_metrics_table(metrics):
    rows = metrics["rows"]
    if not rows:
        print("\nNo processes to report.")
        return

    headers = ["PID", "AT", "BT", "CT", "TAT", "WT", "RT"]
    col_widths = [max(len(h), 6) for h in headers]

    def fmt_row(values):
        return "  ".join(str(v).rjust(w) for v, w in zip(values, col_widths))

    print("\nProcess Metrics:")
    print(fmt_row(headers))
    print("-" * (sum(col_widths) + 2 * (len(col_widths) - 1)))

    for r in rows:
        print(fmt_row([
            r["pid"],
            r["arrival_time"],
            r["burst_time"],
            r["completion_time"],
            r["turnaround_time"],
            r["waiting_time"],
            r["response_time"],
        ]))


def print_summary(metrics):
    print("\nSummary:")
    print(f"  Average Waiting Time    : {metrics['avg_waiting_time']:.2f}")
    print(f"  Average Turnaround Time : {metrics['avg_turnaround_time']:.2f}")
    print(f"  Average Response Time   : {metrics['avg_response_time']:.2f}")
    print(f"  Throughput              : {metrics['throughput']:.4f} processes/unit time")
    print(f"  CPU Utilization         : {metrics['cpu_utilization']:.2f}%")
    print()