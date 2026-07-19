# CPU Scheduling Algorithm Simulator

A Python CLI simulator that implements and visualizes the core CPU scheduling
algorithms taught in every Operating Systems course — built to actually
*run* the scheduling logic instead of just describing it, with a console
Gantt chart and full performance metrics for every run.

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

---

## Table of Contents

- [Why This Project Exists](#why-this-project-exists)
- [Impact / What It Demonstrates](#impact--what-it-demonstrates)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [CSV Format](#csv-format)
- [Algorithms Implemented](#algorithms-implemented)
- [System Design & Logic](#system-design--logic)
- [Metrics Explained](#metrics-explained)
- [Example Output](#example-output)
- [Roadmap](#roadmap)
- [Extending the Simulator](#extending-the-simulator)
- [Tech Stack](#tech-stack)
- [Author](#author)

---

## Why This Project Exists

CPU scheduling is one of the most fundamental — and most abstract — topics
in Operating Systems. Textbooks show static Gantt charts for FCFS, SJF,
Priority, and Round Robin, but rarely let you:

- Feed in **your own workload** (arrival times, burst times, priorities) and see
  exactly how each algorithm handles it
- Compare **preemptive vs non-preemptive** variants of the same algorithm
  side by side
- Watch **multi-level scheduling** (MLQ, MLFQ) — the algorithms real
  operating systems like Windows and older UNIX schedulers actually used —
  play out tick by tick, including queue demotion and preemption
- Get **quantitative feedback** (average waiting time, turnaround time,
  response time, throughput, CPU utilization) instead of just a diagram

This project closes that gap: it's a correctness-focused, from-scratch
implementation of scheduler simulation logic, not a wrapper around an
existing library. Every algorithm was implemented and independently
sanity-checked against hand-calculated Gantt charts before being wired
into the CLI.

## Impact / What It Demonstrates

Beyond being a working tool, this project is meant to demonstrate:

- **Systems-level thinking**: modeling CPU/process state machines,
  preemption, and time-sliced execution — the same conceptual muscles used
  in RTOS design, hypervisor scheduling, and GPU work-queue scheduling
- **Simulation design**: building both event-driven (non-preemptive) and
  tick-driven (preemptive) simulation loops, and knowing when each is the
  right tool
- **Correctness discipline**: every algorithm was validated against known
  textbook examples with matching WT/TAT/RT numbers before being trusted
- **Clean software architecture**: a common `{schedule, processes}`
  contract across all 6 algorithm modules means new algorithms plug into
  the CLI with zero changes to `scheduler.py`'s dispatch logic
- **Practical CLI tooling**: `argparse`-based UX with CSV ingestion, manual
  entry, sensible defaults, and a `--list` discovery flag — the same shape
  as production developer tooling

It's built as a portfolio piece for roles touching systems programming,
performance engineering, and low-level scheduling (OS internals, RTOS,
GPU/accelerator scheduling) — areas where understanding *how* a scheduler
makes decisions matters more than memorizing the algorithm names.

## Features

- 8 scheduling modes across 6 algorithm families, preemptive and
  non-preemptive where applicable
- CSV-based batch input or interactive manual entry
- Console Gantt chart renderer with aligned time markers
- Full metrics: per-process WT / TAT / RT, plus average WT, average TAT,
  average RT, throughput, and CPU utilization
- Zero external dependencies — pure Python standard library
- Consistent internal contract so new algorithms are a drop-in addition

## Project Structure

```
cpu-scheduling-simulator/
├── scheduler.py          # Entry point / CLI — argument parsing, dispatch, output
├── algorithms/
│   ├── fcfs.py            # First Come First Serve
│   ├── sjf.py              # SJF (non-preemptive) + SRTF (preemptive)
│   ├── priority.py         # Priority Scheduling (non-preemptive + preemptive)
│   ├── round_robin.py      # Round Robin
│   ├── mlq.py               # Multilevel Queue (fixed queue assignment)
│   └── mlfq.py              # Multilevel Feedback Queue (dynamic demotion)
├── utils/
│   ├── gantt_chart.py      # Console Gantt chart renderer
│   └── metrics.py           # WT / TAT / RT + summary statistics
├── sample_data/
│   └── processes.csv        # Sample workload for testing
└── README.md
```

## Installation

Requires Python 3.7+, no external dependencies.

```bash
git clone https://github.com/hrishabh14newstark/CPU-Scheduling-Algorithm-Simulator-
cd cpu-scheduling-simulator
python scheduler.py --list
```

## Usage

```bash
# Discover all supported algorithms
python scheduler.py --list

# Non-preemptive algorithms
python scheduler.py --algo fcfs --file sample_data/processes.csv
python scheduler.py --algo sjf --file sample_data/processes.csv
python scheduler.py --algo priority --file sample_data/processes.csv

# Preemptive variants
python scheduler.py --algo sjf_p --file sample_data/processes.csv
python scheduler.py --algo priority_p --file sample_data/processes.csv

# Round Robin / MLQ (require a time quantum)
python scheduler.py --algo rr --quantum 4 --file sample_data/processes.csv
python scheduler.py --algo mlq --quantum 4 --file sample_data/processes.csv

# MLFQ (per-level quantums, defaults to 4 8 12)
python scheduler.py --algo mlfq --mlfq-quantums 4 8 12 --file sample_data/processes.csv

# Manual entry instead of CSV
python scheduler.py --algo fcfs --manual

# No --file given -> falls back to sample_data/processes.csv automatically
python scheduler.py --algo fcfs
```

## CSV Format

| Column          | Required | Description                                                     |
|-----------------|----------|-------------------------------------------------------------------|
| `pid`           | No       | Process ID (auto-generated `P1`, `P2`... if omitted)              |
| `arrival_time`  | No       | Time the process enters the ready queue (default `0`)             |
| `burst_time`    | Yes      | Total CPU time required                                            |
| `priority`      | No       | Lower number = higher priority (default `0`)                      |
| `queue`         | No       | Fixed queue level for MLQ / initial level for MLFQ (default `0`)  |

```csv
pid,arrival_time,burst_time,priority,queue
P1,0,7,3,0
P2,1,5,1,0
P3,2,10,4,1
P4,3,3,2,0
```

Headers are matched case-insensitively; `AT` / `BT` / `PR` / `Q` shorthand
is also accepted.

## Algorithms Implemented

| Flag          | Algorithm                          | Preemptive | Selection Rule                                  |
|---------------|--------------------------------------|:----------:|--------------------------------------------------|
| `fcfs`        | First Come First Serve               | No         | Earliest arrival                                  |
| `sjf`         | Shortest Job First                   | No         | Smallest burst time among arrived processes       |
| `sjf_p`       | Shortest Remaining Time First (SRTF) | Yes        | Smallest *remaining* time, re-evaluated every tick|
| `priority`    | Priority Scheduling                  | No         | Lowest priority number among arrived processes    |
| `priority_p`  | Priority Scheduling (Preemptive)     | Yes        | Lowest priority number, re-evaluated every tick   |
| `rr`          | Round Robin                          | Yes        | FIFO queue, fixed time quantum per turn           |
| `mlq`         | Multilevel Queue                     | Yes        | Strict priority across fixed, permanent queues    |
| `mlfq`        | Multilevel Feedback Queue            | Yes        | Strict priority across queues + dynamic demotion  |

## System Design & Logic

The simulator uses two different simulation strategies depending on
whether an algorithm is preemptive:

**Event-driven simulation** (FCFS, SJF, non-preemptive Priority) — the
next process to run is chosen once, and the simulation clock jumps
directly to that process's completion time. This is O(n log n) and exact,
since nothing can interrupt a running process.

**Tick-driven simulation** (SRTF, preemptive Priority, Round Robin, MLQ,
MLFQ) — the simulation clock advances one time unit at a time. At every
tick, the algorithm re-evaluates *whether the currently running process
should be preempted* by a newly arrived or newly-ready process. This is
the only way to get exact preemption timing when arrivals can interrupt
mid-burst.

For MLQ and MLFQ specifically:

- Each queue level maintains its own FIFO ready queue
- A single loop always dispatches from the **highest non-empty queue**
- MLQ processes stay in their assigned queue forever (no promotion or
  demotion) — it models a system with fixed process classes (e.g. system
  vs. interactive vs. batch)
- MLFQ processes start at level 0 and are **demoted** one level whenever
  they exhaust their level's quantum without finishing — it models
  adaptive, self-tuning scheduling where CPU-bound jobs are automatically
  pushed to lower priority over time

All algorithms converge on the same output contract:

```python
{
    "schedule": [(pid, start_time, end_time), ...],  # for the Gantt chart
    "processes": [Process, ...]  # completion_time, turnaround_time,
                                  # waiting_time, response_time all set
}
```

This contract is what lets `scheduler.py` stay algorithm-agnostic — it
doesn't know or care *how* an algorithm made its decisions, only that it
returns a valid schedule and a fully annotated process list.

## Metrics Explained

- **Waiting Time (WT)** = Turnaround Time − Burst Time
  (time spent in the ready queue, not running)
- **Turnaround Time (TAT)** = Completion Time − Arrival Time
  (total time from arrival to finish)
- **Response Time (RT)** = Time of first dispatch − Arrival Time
  (how long until the process first got the CPU — matters most for
  interactive workloads)
- **Throughput** = processes completed ÷ total elapsed time
- **CPU Utilization** = total burst time ÷ total elapsed time × 100

## Example Output

```
Gantt Chart:
      P1      P2       P3       P4     P5
  |---------|-----|----------|------|-------|
  0     8         12     21      26      32

Process Metrics:
   PID      AT      BT      CT     TAT      WT      RT
------------------------------------------------------
    P1       0       8       8       8       0       0
    P2       1       4      12      11       7       7
    ...

Summary:
  Average Waiting Time    : 11.40
  Average Turnaround Time : 17.80
  Average Response Time   : 11.40
  Throughput              : 0.1562 processes/unit time
  CPU Utilization         : 100.00%
```

## Roadmap

**Near-term**
- [ ] Unit test suite (`pytest`) covering every algorithm against known
      textbook Gantt charts, including edge cases (ties, zero-burst,
      simultaneous arrivals)
- [ ] `--compare` mode: run every algorithm on the same workload and print
      a side-by-side metrics comparison table
- [ ] `--export csv/json` to save results for external analysis
- [ ] Colorized terminal Gantt chart (per-process ANSI colors)

**Mid-term**
- [ ] Matplotlib/Plotly Gantt chart export (`--chart output.png`)
- [ ] Aging support for Priority Scheduling (prevent starvation)
- [ ] Configurable MLQ scheduling policy per level (e.g. FCFS for the
      lowest queue instead of Round Robin)
- [ ] Web-based visualizer (Flask/FastAPI backend reusing the same
      algorithm modules, React/Canvas frontend for animated Gantt charts)

**Long-term**
- [ ] Multi-core / multi-CPU scheduling simulation (load balancing,
      processor affinity)
- [ ] I/O burst modeling (alternating CPU/IO bursts, not just a single
      CPU burst per process) for a more realistic process lifecycle
- [ ] Lottery Scheduling and Completely Fair Scheduler (CFS)-style
      vruntime-based algorithm as additional modules
- [ ] Package as a pip-installable CLI (`pip install cpu-scheduler-sim`)

## Extending the Simulator

Every algorithm in `algorithms/` follows the same contract. To add a new
one:

1. Create `algorithms/your_algo.py` with a function that takes a list of
   `Process` objects and returns `{"schedule": [...], "processes": [...]}`
2. Set `start_time`, `completion_time`, `turnaround_time`,
   `waiting_time`, and `response_time` on each process
3. Register it in `ALGORITHMS` and `run_algorithm()` in `scheduler.py`

No other file needs to change — the Gantt chart renderer and metrics
module work off the schedule/process contract alone.

## Tech Stack

- **Language**: Python 3.7+ (standard library only — `argparse`, `csv`,
  `collections.deque`, `pathlib`)
- **Testing**: manual + scripted validation against textbook Gantt charts
  (formal `pytest` suite on the roadmap)
- **No external dependencies** — runs anywhere Python runs

## Author

Built by **Hrishabh** — Manufacturing Associate at Micron Semiconductor
Technology India, B.Tech ECE (AKTU), pursuing systems/hardware-adjacent
roles (Design Verification, GPU Performance, FPGA/Accelerator, Systems
Engineering). Part of an ongoing portfolio of embedded systems, VLSI/RTL,
and systems-programming projects.

GitHub: [@hrishabh14newstark](https://github.com/hrishabh14newstark)

## License

MIT License — free to use, modify, and distribute.
