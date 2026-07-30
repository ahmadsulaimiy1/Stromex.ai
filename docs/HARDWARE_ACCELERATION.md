# Hardware Acceleration Investigation

Phase 2 asked us to "investigate NDK / SIMD / ARM NEON / GPU acceleration for
real-time enhancement." This is that investigation. It ends in a
recommendation, not an implementation — see "Why not implemented now" below
for why that's the honest call here, rather than shipping an unverified
native port.

## Where the CPU time actually goes

Not all of SAJJIL's DSP is equally expensive, and acceleration only matters
where the cost actually is:

| Path | Cost shape | Hot? |
|---|---|---|
| Live recording chain (gate → EQ → de-esser → compressor → limiter) | O(1) per sample, ~15 multiply-adds/sample, runs at 1x realtime | No — this is trivially cheap per sample; JIT-compiled Kotlin handles it fine well under the audio callback deadline. |
| `SpectralNoiseReducer`, `Dereverberator`, `ReferenceMatcher`, `SpectrogramAnalyzer` | STFT: an N-point FFT (typically 1024–2048) every hop (256–512 samples) | Yes, for **offline/batch** use — Enhance, Master's echo removal and reference match, and Batch Qur'an Production all run these over full files, potentially many files back to back. |
| `BatchProcessor` | Chains the above across every file in a Surah/Juz/library selection | Yes — this is where wall-clock time is most visible to a user waiting for "Master 30 Recordings." |

So the acceleration question is really: **is the FFT/STFT path fast enough
on a mid-range Android device, especially in batch mode?** That's an
empirical question this sandbox can't answer — there's no Android device or
profiler available here, only a JVM. Any specific speedup number below is a
reasoned estimate, not a measurement, and should be treated as such until
someone runs Android Studio's CPU profiler on real hardware.

## NDK / C++

**What it would buy us:** Kotlin/JVM's JIT does a competent job on tight
numeric loops (the biquad and FFT inner loops are exactly the kind of
monomorphic, branch-light code the JIT optimizes well), so the realistic win
from porting to C++ is more modest than in an unmanaged-language rewrite. The
actual gains would come from:
1. Avoiding cold-start/short-burst JIT warmup cost — a 3-second Room Check
   probe or a short recording may finish before the JIT has fully optimized
   the hot method, unlike a long batch job.
2. Access to SIMD intrinsics (see NEON below) that Kotlin/JVM cannot express.

**Recommendation:** if profiling shows the STFT paths are genuinely a
bottleneck on target devices, port *only* those (`FFT`, and the STFT
frame/OLA loop shared by the noise reducer, dereverberator, and reference
matcher) behind a small JNI boundary, keeping the current Kotlin
implementation as the reference and correctness fallback — every existing
`core` unit test should be re-run against the native path to confirm
bit-for-bit-reasonable output before it ships as the default.

## ARM NEON / SIMD

This is where a real, measurable win is most plausible: the FFT's butterfly
stage and the biquad cascade's multiply-accumulate pattern are both
naturally vectorizable (independent lanes, no data-dependent branching).
Two viable paths, in order of effort:
1. Let the C++ compiler auto-vectorize a straightforward NDK port with
   `-O3` and NEON enabled (default on `arm64-v8a`) — often gets most of the
   available win with no hand-written intrinsics.
2. Hand-written NEON intrinsics for the FFT butterfly and the biquad
   direct-form-I update, if profiling shows auto-vectorization isn't
   kicking in (common when the compiler can't prove pointer aliasing —
   `restrict`-qualify the buffers).

A **known, credible alternative to a from-scratch NEON port**: use a vetted,
already-NEON-optimized FFT library (e.g. `KissFFT`, `pffft`, or Android's own
`fft` usage patterns) instead of hand-rolling one — lower risk, less code to
maintain, and the win is comparable.

## GPU (RenderScript / Vulkan compute / OpenGL ES compute shaders)

**Not recommended for the real-time path.** GPU dispatch latency (queueing
a compute shader, waiting for it to complete, reading results back) is
typically single-digit milliseconds at best on mobile — comparable to or
larger than the entire audio buffer duration SAJJIL processes at a time.
For a per-sample or small-per-buffer real-time chain, the GPU is the wrong
tool: it adds latency it's supposed to remove.

It's a **more plausible fit for large-scale batch mastering** — e.g.
dispatching many independent file-level STFTs in parallel when mastering an
entire Qur'an archive — where throughput matters more than per-item latency.
Even there, the engineering cost (Vulkan compute or OpenGL ES compute shader
pipeline, buffer management, a fallback path for devices/GPUs that don't
support it well) is high relative to the likely win once NEON is already in
place for the CPU path. RenderScript itself is deprecated by Google and
should not be used for new work.

**Recommendation:** skip GPU acceleration entirely for now. Revisit only if
profiling on real batch-mastering workloads (e.g. mastering a full 30-Juz
library on a low-end device) shows NEON-accelerated CPU throughput is
insufficient.

## Recommended path forward

1. **Profile first.** Before writing any native code, run Android Studio's
   CPU profiler against Record / Enhance / Master / Batch Production on at
   least one mid-range and one low-end target device. Confirm the STFT paths
   are actually the bottleneck rather than, say, I/O or WAV encoding.
2. **If confirmed:** port `FFT` and the shared STFT/OLA loop to an NDK
   module (`libsajjildsp.so`), targeting `arm64-v8a` NEON, either via
   auto-vectorized C++ or a vetted FFT library, exposed to Kotlin via a thin
   JNI boundary. Every `core` DSP test gets re-run against the native path
   before it becomes the default; the Kotlin implementation stays as the
   fallback for architectures/devices where the native library fails to
   load.
3. **Skip GPU** unless batch-mastering throughput on real hardware proves
   NEON-accelerated CPU insufficient.

## Why not implemented now

This sandbox has a JDK and Gradle but no Android SDK, no NDK toolchain, and
no physical or emulated device to profile — see the main README's "Building"
section. Writing native code here would mean guessing at hot spots and
shipping an unverified, uncompiled `.so` with no way to confirm it even
builds, let alone that it's faster. That's a worse outcome than a clear
recommendation someone can execute with the profiling data and hardware this
environment doesn't have.
