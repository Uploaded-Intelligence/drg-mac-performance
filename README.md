# Deep Rock Galactic on an M4 MacBook Air: measuring before tuning

**Work in progress — no verified optimization or renderer winner yet.**

Hardware: M4 MacBook Air, 16 GB RAM. Software: macOS 27, Mac Steam → NotProton → CrossOver 26.3, DX12 through D3DMetal. Game render resolution: 1280 × 832.

One passive 59.7-second sample on 29 October 2026 recorded:

| Average FPS | p5 one-second FPS | Worst one-second FPS | GPU time/frame | GPU busy |
|---:|---:|---:|---:|---:|
| 45.2 | 24.76 | 1.64 | 6.26 ms | 28% |

Scene and foreground focus were unverified because computer capture failed. These figures are **not a controlled benchmark**, a performance promise, or evidence that a change helped. One-second lows are not per-frame 1% lows. System swap used at collection was about 5.6 GiB.

The useful diagnostic distinction: GPU execution time and wall-clock frame intervals can differ substantially. Lowering resolution may not address a bottleneck elsewhere. This sample alone cannot identify the cause.

## Reproducible comparison still needed

1. Fix the Space Rig camera view, bring the game fullscreen into the foreground, and allow loading to settle.
2. Capture two consecutive 60-second samples with DX12/D3DMetal.
3. Compare DX11/DXMT at the same settings and view; verify the renderer from live loaded libraries. Include a separate warm launch.
4. Compare average FPS and p5/worst one-second FPS; report memory/swap and shader warmup conditions.
5. Tune the winning renderer, then verify performance in combat.

No settings changes were retained during this measurement session. No renderer recommendation is justified yet.

## Measurement tool

`tools/metal-measure.py` extracts a single process’s largest Metal layer from the macOS Metal performance recorder. Requires Python 3 and an available `metalperftrace` command. It reads the **past** interval; hold the controlled view for the full interval before invoking it. Availability on other macOS versions has not been tested.

```sh
pgrep -f FSD-Win64-Shipping
python3 tools/metal-measure.py dx12-space-rig-1 60 YOUR_GAME_PID results
```

Replace YOUR_GAME_PID with the live game process ID. Capture a second non-overlapping interval under identical conditions. The tool writes JSON and a raw trace locally. Raw traces may include machine/process metadata: review them before sharing.

The tool was inherited from the existing Mac gaming investigation; this repository publishes a standalone copy. It is not affiliated with Ghost Ship Games, Valve, CodeWeavers or Apple.
