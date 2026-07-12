"""
Console Gantt Chart Renderer
===============================
Renders a text-based Gantt chart from a schedule of
    [(pid, start_time, end_time), ...]
as produced by every algorithm in algorithms/*.py.

Example output:

     P1        P2      P1              P3
  |------|--------|------|----------------|
  0      3        7      9               17
"""


def render_gantt_chart(schedule):
    if not schedule:
        print("  (empty schedule)")
        return

    # Each block is drawn with a minimum width so short slices stay readable
    MIN_WIDTH = 6

    segments = []  # (pid, start, end, width)
    for pid, start, end in schedule:
        duration = end - start
        width = max(MIN_WIDTH, duration + 2)
        segments.append((pid, start, end, width))

    # --- Build the top row: centered pid labels ---
    top_line = "  "
    for pid, _, _, width in segments:
        label = str(pid)
        top_line += label.center(width)
    print(top_line)

    # --- Build the bar row ---
    bar_line = "  |"
    for _, _, _, width in segments:
        bar_line += "-" * (width - 1) + "|"
    print(bar_line)

    # --- Build the bottom row: time markers aligned to block boundaries ---
    bottom_line = "  "
    cursor = 0
    for i, (_, start, end, width) in enumerate(segments):
        marker = str(start)
        if i == 0:
            bottom_line += marker
            cursor = len(bottom_line)
        else:
            # pad to align marker with the block boundary
            pad = cursor + width - len(bottom_line) - len(marker)
            bottom_line += " " * max(pad, 1) + marker
            cursor = len(bottom_line)

    # Final end-time marker for the very last block
    last_pid, last_start, last_end, last_width = segments[-1]
    final_marker = str(last_end)
    pad = cursor + last_width - len(bottom_line) - len(final_marker)
    bottom_line += " " * max(pad, 1) + final_marker

    print(bottom_line)
    print()