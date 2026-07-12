#!/usr/bin/env python3
"""
CPU Scheduling Algorithm Simulator
====================================
Entry point / CLI

Supports:
    FCFS            - First Come First Serve
    SJF             - Shortest Job First (non-preemptive)
    SJF (SRTF)      - Shortest Remaining Time First (preemptive)
    Priority        - Priority Scheduling (non-preemptive)
    Priority (P)    - Priority Scheduling (preemptive)
    Round Robin     - Round Robin
    MLQ             - Multilevel Queue
    MLFQ            - Multilevel Feedback Queue

Usage examples:
    python scheduler.py --list
    python scheduler.py --algo fcfs --file sample_data/processes.csv
    python scheduler.py --algo rr --quantum 4 --file sample_data/processes.csv
    python scheduler.py --algo mlfq --file sample_data/processes.csv
    python scheduler.py --algo sjf_p --manual
"""

import argparse
import csv
import sys
from pathlib import Path

# Local package imports (see algorithms/ and utils/)
from algorithms.fcfs import fcfs
from algorithms.sjf import sjf
from algorithms.priority import priority_scheduling
from algorithms.round_robin import round_robin
from algorithms.mlq import mlq
from algorithms.mlfq import mlfq

from utils.gantt_chart import render_gantt_chart
from utils.metrics import calculate_metrics, print_metrics_table, print_summary


# --------------------------------------------------------------------------- #
# Process model
# --------------------------------------------------------------------------- #

class Process:
    """Represents a single process/job to be scheduled."""

    def __init__(self, pid, arrival_time, burst_time, priority=0, queue=0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        self.queue = queue                 # used by MLQ / MLFQ
        self.remaining_time = burst_time   # used by preemptive algorithms

        # Filled in after scheduling
        self.start_time = None
        self.completion_time = None
        self.waiting_time = None
        self.turnaround_time = None
        self.response_time = None

    def __repr__(self):
        return (f"Process({self.pid}, AT={self.arrival_time}, "
                f"BT={self.burst_time}, PR={self.priority})")


# --------------------------------------------------------------------------- #
# Input loading
# --------------------------------------------------------------------------- #

def load_processes_from_csv(filepath):
    """Load processes from a CSV file.

    Expected columns (case-insensitive, flexible naming):
        pid / PID
        arrival_time / AT
        burst_time / BT
        priority / PR      (optional, default 0)
        queue / Q           (optional, default 0)
    """
    processes = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        # normalize header keys to lowercase for lookups
        for row in reader:
            row = {k.strip().lower(): v for k, v in row.items() if k}
            pid = row.get("pid") or row.get("process") or f"P{len(processes) + 1}"
            arrival = int(row.get("arrival_time") or row.get("at") or 0)
            burst = int(row.get("burst_time") or row.get("bt") or 0)
            priority = int(row.get("priority") or row.get("pr") or 0)
            queue = int(row.get("queue") or row.get("q") or 0)
            processes.append(Process(pid, arrival, burst, priority, queue))
    return processes


def input_processes_manually():
    """Prompt the user to enter process data interactively."""
    processes = []
    try:
        n = int(input("Enter number of processes: "))
    except ValueError:
        print("Invalid number.")
        sys.exit(1)

    for i in range(n):
        print(f"\n--- Process P{i + 1} ---")
        pid = f"P{i + 1}"
        try:
            arrival = int(input("Arrival Time: ") or 0)
            burst = int(input("Burst Time: "))
            priority = int(input("Priority (lower number = higher priority, default 0): ") or 0)
        except ValueError:
            print("Invalid input, please enter integers only.")
            sys.exit(1)
        processes.append(Process(pid, arrival, burst, priority))

    return processes


# --------------------------------------------------------------------------- #
# Algorithm registry
# --------------------------------------------------------------------------- #

ALGORITHMS = {
    "fcfs":       "First Come First Serve",
    "sjf":        "Shortest Job First (Non-preemptive)",
    "sjf_p":      "Shortest Remaining Time First (Preemptive SJF)",
    "priority":   "Priority Scheduling (Non-preemptive)",
    "priority_p": "Priority Scheduling (Preemptive)",
    "rr":         "Round Robin",
    "mlq":        "Multilevel Queue",
    "mlfq":       "Multilevel Feedback Queue",
}


def run_algorithm(name, processes, args):
    """Dispatch to the correct algorithm implementation.

    Each algorithm module is expected to return a dict:
        {
            "schedule":  [(pid, start_time, end_time), ...],  # for Gantt chart
            "processes": [Process, ...]  # completed, with completion_time set
        }
    """
    if name == "fcfs":
        return fcfs(processes)

    elif name == "sjf":
        return sjf(processes, preemptive=False)

    elif name == "sjf_p":
        return sjf(processes, preemptive=True)

    elif name == "priority":
        return priority_scheduling(processes, preemptive=False)

    elif name == "priority_p":
        return priority_scheduling(processes, preemptive=True)

    elif name == "rr":
        if not args.quantum:
            print("Error: Round Robin requires --quantum <n>")
            sys.exit(1)
        return round_robin(processes, quantum=args.quantum)

    elif name == "mlq":
        return mlq(processes, quantum=args.quantum or 4)

    elif name == "mlfq":
        return mlfq(processes, quantums=args.mlfq_quantums or [4, 8, 12])

    else:
        raise ValueError(f"Unknown algorithm: {name}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def print_banner():
    print("=" * 60)
    print("        CPU SCHEDULING ALGORITHM SIMULATOR")
    print("=" * 60)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="scheduler.py",
        description="CPU Scheduling Algorithm Simulator - simulate and "
                     "visualize classic CPU scheduling algorithms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scheduler.py --list
  python scheduler.py --algo fcfs --file sample_data/processes.csv
  python scheduler.py --algo rr --quantum 4 --file sample_data/processes.csv
  python scheduler.py --algo mlfq --file sample_data/processes.csv
  python scheduler.py --algo sjf_p --manual
        """,
    )
    parser.add_argument(
        "--algo", choices=list(ALGORITHMS.keys()),
        help="Scheduling algorithm to run"
    )
    parser.add_argument(
        "--file", type=str,
        help="Path to a CSV file with process data (pid, arrival_time, burst_time, priority, queue)"
    )
    parser.add_argument(
        "--manual", action="store_true",
        help="Enter process data manually via prompts"
    )
    parser.add_argument(
        "--quantum", type=int,
        help="Time quantum, required for Round Robin, used as default level quantum for MLQ"
    )
    parser.add_argument(
        "--mlfq-quantums", dest="mlfq_quantums", type=int, nargs="+",
        help="Per-level time quantums for MLFQ, e.g. --mlfq-quantums 4 8 12"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List all supported algorithms and exit"
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.list:
        print_banner()
        print("\nSupported Algorithms:\n")
        for key, desc in ALGORITHMS.items():
            print(f"  {key:<12} - {desc}")
        print()
        return

    print_banner()

    if not args.algo:
        parser.print_help()
        sys.exit(1)

    # ---- Load processes ---- #
    if args.manual:
        processes = input_processes_manually()
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        processes = load_processes_from_csv(path)
    else:
        default_path = Path(__file__).resolve().parent / "sample_data" / "processes.csv"
        if default_path.exists():
            print(f"No --file or --manual given. Using default dataset: {default_path}\n")
            processes = load_processes_from_csv(default_path)
        else:
            print("Error: No process input provided. Use --file <path>, --manual, "
                  "or place a CSV at sample_data/processes.csv")
            sys.exit(1)

    if not processes:
        print("Error: No processes were loaded.")
        sys.exit(1)

    print(f"Algorithm : {ALGORITHMS[args.algo]}")
    print(f"Processes : {len(processes)}\n")

    for p in processes:
        print(f"  {p}")

    # ---- Run scheduling algorithm ---- #
    result = run_algorithm(args.algo, processes, args)

    schedule = result["schedule"]      # [(pid, start_time, end_time), ...]
    completed = result["processes"]    # Process objects with completion_time set

    # ---- Output ---- #
    print("\nGantt Chart:")
    render_gantt_chart(schedule)

    metrics = calculate_metrics(completed)
    print_metrics_table(metrics)
    print_summary(metrics)


if __name__ == "__main__":
    main()