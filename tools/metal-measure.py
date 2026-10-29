#!/usr/bin/env python3
"""Measure one game's frame pacing from macOS's always-on Metal recorder.

usage: metal-measure.py <label> <seconds> <pid> [outdir]

Collects the last <seconds> with `metalperftrace collect`, filters to <pid>,
and appends one JSON line to <outdir>/results.jsonl (default: runs/metal).
The recorder only has per-second buckets, so "low" figures are per-second:
worst_1s_fps and p5_1s_fps (5th percentile of 1-second buckets, time-weighted).
"""
import glob, json, os, subprocess, sys, time

label, secs, pid = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
out = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "runs", "metal")
os.makedirs(out, exist_ok=True)
tdir = os.path.join(out, "traces", f"{label}-{time.strftime('%Y%m%d-%H%M%S')}")

subprocess.run(["metalperftrace", "collect", "--last", f"{secs}s", tdir],
               check=True, capture_output=True)
trace = sorted(glob.glob(os.path.join(tdir, "*.atrc")))[-1]
ov = json.loads(subprocess.run(
    ["metalperftrace", "overview", "--json", "--json-include-timeline",
     "--predicate", f"pid == {pid}", trace],
    check=True, capture_output=True, text=True).stdout)

procs = [p for p in ov if p.get("Layers")]
if not procs:
    sys.exit(f"no Metal layers for pid {pid} in the last {secs}s")
# Largest layer by presented frames = the game's swapchain.
layer = max((l for p in procs for l in p["Layers"]),
            key=lambda l: l["Total Session Stats"]["Presented Frame Stats"]["Frame Count"])
tot = layer["Total Session Stats"]
pf = tot["Presented Frame Stats"]
buckets = [(b["Presented Frame Stats"]["FPS"], b["Total Duration (sec)"])
           for b in layer["Stats Timeline"] if b["Total Duration (sec)"] > 0.5]
fps_sorted = sorted(buckets)
acc, need, p5 = 0.0, 0.05 * sum(w for _, w in buckets), None
for f, w in fps_sorted:
    acc += w
    if acc >= need:
        p5 = f
        break
cfg = layer["Configuration Timeline"][-1]
shader = layer["Stats Timeline"][-1]["Presented Frame Stats"].get("Shader Compiler", {})


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


row = {
    "label": label, "pid": pid, "start": tot["Start Date"], "end": tot["End Date"],
    "seconds": round(tot["Total Duration (sec)"], 1),
    "resolution": f'{cfg["Width (pixels)"]}x{cfg["Height (pixels)"]}',
    "frames": pf["Frame Count"], "fps_avg": round(pf["FPS"], 2),
    "worst_1s_fps": round(fps_sorted[0][0], 2) if fps_sorted else None,
    "p5_1s_fps": round(p5, 2) if p5 is not None else None,
    "frame_interval_avg_ms": round(tot["Frame-On-Glass Interval Stats"]["Average (ms)"], 2),
    "frame_interval_max_ms": round(tot["Frame-On-Glass Interval Stats"]["Max (ms)"], 2),
    "gpu_ms_per_frame": round(pf["On-GPU Walltime Stats"]["Average (ms)"], 2),
    "gpu_busy_pct": round(100 * pf["On-GPU Walltime Stats"]["Total (ms)"]
                          / (1000 * tot["Total Duration (sec)"]), 1),
    "shader_compiles_total": shader.get("Total Shader Compilations"),
    "swap": sh("sysctl -n vm.swapusage"),
    "mem_free": sh("memory_pressure | tail -1"),
    "trace": trace,
}
with open(os.path.join(out, "results.jsonl"), "a") as f:
    f.write(json.dumps(row) + "\n")
print(json.dumps(row, indent=1))
