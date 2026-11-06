"""
drone_detect_laptop.py  -  Part A (laptop version) of the Drone Detector + Tracking Turret
Version 3: harmonic detection

Detects a drone's propeller buzz in an audio recording. No hardware needed.

Why version 3: versions 1-2 only checked HOW LOUD the 200-2500 Hz band was.
Decoy tests showed loudness alone can't tell a drone from a lawnmower, traffic,
or speech. Version 3 checks WHAT THE SOUND LOOKS LIKE instead:

  1. Harmonic pattern: a drone's propellers make a main tone (the "blade-pass"
     frequency, ~100-450 Hz) plus evenly spaced harmonics at 2x, 3x, 4x, 5x.
     For each 0.5 s frame, the script tries every candidate main tone and scores
     how much stronger the spectrum is AT its harmonics than BETWEEN them.
  2. Steady pitch: a hovering drone's main tone stays nearly constant. Speech
     and traffic jump around. The pitch must stay within 8% over ~1 s.
  3. Duration: the pattern must hold for 1 s (4 frames in a row) to switch ON,
     and detection stays ON until the harmonic score drops below a lower OFF
     level (hysteresis, so small dips don't cause flicker).

No background-noise calibration is needed, so it no longer matters how the
recording starts.

Usage:
  python3 drone_detect_laptop.py --demo            # fake drone sound test
  python3 drone_detect_laptop.py my_recording.wav  # your own recording

Install first:
  pip3 install numpy scipy matplotlib
"""

import argparse

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.ndimage import median_filter, uniform_filter1d
from scipy.signal import spectrogram

# ---------------- Settings you can tune ----------------
FRAME_SEC = 0.5          # analysis window (longer = finer frequency detail)
HOP_SEC = 0.25           # time step between frames
F0_MIN_HZ = 100          # lowest main tone to consider (blade-pass frequency)
F0_MAX_HZ = 450          # highest main tone to consider
N_HARMONICS = 5          # how many harmonics to check (1x ... 5x)
SCORE_ON = 16.0          # harmonic score needed to switch detection ON
SCORE_OFF = 10.0         # detection stays ON until the score drops below this
PITCH_STEADY = 0.08      # main tone must vary less than 8% over ~1 s
MIN_FRAMES = 4           # frames in a row needed to switch ON (4 x 0.25 s = 1 s)
# -------------------------------------------------------


def make_demo_audio(fs=16000, seconds=10, seed=0):
    """Create a fake recording: background noise, then a drone buzz from 3 s to 8 s."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(fs * seconds)) / fs
    noise = 0.05 * rng.standard_normal(len(t))
    f0 = 180 + 5 * np.sin(2 * np.pi * 0.3 * t)          # ~180 Hz, slight drift
    phase = 2 * np.pi * np.cumsum(f0) / fs
    buzz = sum((0.6 / k) * np.sin(k * phase) for k in range(1, 9))
    envelope = np.clip((t - 3) / 1.0, 0, 1) * np.clip((8 - t) / 1.0, 0, 1)
    audio = noise + 0.25 * envelope * buzz
    return fs, audio.astype(np.float32)


def load_audio(path):
    """Load a WAV file, convert to mono floating point between -1 and 1."""
    fs, data = wavfile.read(path)
    data = data.astype(np.float64)
    if data.ndim > 1:                     # stereo -> mono
        data = data.mean(axis=1)
    peak = np.max(np.abs(data))
    if peak > 0:
        data /= peak
    return fs, data


def harmonic_score(audio, fs):
    """For each frame, find the main tone with the strongest harmonic pattern.

    Returns frame times, the best harmonic score (dB), and the main tone (Hz).
    """
    n = int(FRAME_SEC * fs)
    hop = int(HOP_SEC * fs)
    window = np.hanning(n)
    freqs = np.fft.rfftfreq(n, d=1 / fs)
    df = freqs[1]
    top = np.searchsorted(freqs, N_HARMONICS * F0_MAX_HZ * 1.05 + 50)
    f0_candidates = np.arange(F0_MIN_HZ, F0_MAX_HZ, 2.0)

    # Pre-compute which frequency bins to check for every candidate:
    # a small window AT each harmonic (k * f0) and BETWEEN harmonics ((k + 0.5) * f0)
    def bin_range(center, tol):
        return np.searchsorted(freqs, center - tol), np.searchsorted(freqs, center + tol) + 1

    def tol(k, f0):
        return max(0.03 * k * f0, 3 * df)

    ranges = [[(bin_range(k * f0, tol(k, f0)), bin_range((k + 0.5) * f0, tol(k, f0)))
               for k in range(1, N_HARMONICS + 1)] for f0 in f0_candidates]

    times, scores, pitches = [], [], []
    for start in range(0, len(audio) - n, hop):
        spectrum_db = 20 * np.log10(np.abs(np.fft.rfft(audio[start:start + n] * window))[:top] + 1e-9)
        spectrum_db = uniform_filter1d(spectrum_db, 3)
        envelope = median_filter(spectrum_db, size=int(150 / df) | 1)
        peaks_db = spectrum_db - envelope            # how far each bin sticks out above its neighborhood

        best_score, best_f0 = -99.0, 0.0
        for f0, harmonics in zip(f0_candidates, ranges):
            at = np.mean([peaks_db[a:b].max() for (a, b), _ in harmonics])
            between = np.mean([peaks_db[a:b].mean() for _, (a, b) in harmonics])
            if at - between > best_score:
                best_score, best_f0 = at - between, f0
        times.append((start + n / 2) / fs)
        scores.append(best_score)
        pitches.append(best_f0)

    scores = median_filter(np.array(scores), 3)      # smooth out single-frame blips
    return np.array(times), scores, np.array(pitches)


def pitch_is_steady(pitches):
    """True where the main tone stays within PITCH_STEADY over about 1 s (5 frames)."""
    steady = np.zeros(len(pitches), dtype=bool)
    for i in range(len(pitches)):
        nearby = pitches[max(0, i - 2):i + 3]
        steady[i] = np.ptp(nearby) / np.median(nearby) < PITCH_STEADY
    return steady


def detect(scores, steady):
    """ON: strong harmonic pattern + steady pitch for MIN_FRAMES in a row.
    Stays ON until the harmonic score drops below SCORE_OFF."""
    detected = np.zeros(len(scores), dtype=bool)
    active, run = False, 0
    for i in range(len(scores)):
        if not active:
            run = run + 1 if (scores[i] > SCORE_ON and steady[i]) else 0
            if run >= MIN_FRAMES:
                active = True
                detected[i - MIN_FRAMES + 1:i + 1] = True
        elif scores[i] < SCORE_OFF:
            active, run = False, 0
        else:
            detected[i] = True
    return detected


def print_events(times, detected):
    events, start = [], None
    for t, d in zip(times, detected):
        if d and start is None:
            start = t - HOP_SEC / 2
        elif not d and start is not None:
            events.append((start, t - HOP_SEC / 2))
            start = None
    if start is not None:
        events.append((start, times[-1] + HOP_SEC / 2))
    if not events:
        print("No drone detected.")
    for s, e in events:
        print(f"DRONE DETECTED from {s:5.2f} s to {e:5.2f} s  ({e - s:.2f} s long)")
    return events


def plot(audio, fs, times, scores, pitches, steady, detected, title):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 9), sharex=True,
                                        gridspec_kw={"height_ratios": [2, 1, 1.4]})

    # 1. Spectrogram: a drone shows up as evenly spaced bright horizontal lines
    f, t, S = spectrogram(audio, fs, nperseg=2048, noverlap=1536)
    ax1.pcolormesh(t, f, 10 * np.log10(S + 1e-12), shading="auto", cmap="magma")
    ax1.set_ylim(0, 2000)
    ax1.set_ylabel("Frequency (Hz)")
    ax1.set_title(f"{title}: spectrogram (drone = evenly spaced horizontal lines)")

    # 2. Main tone over time: steady = drone-like, scattered = noise/speech
    ax2.scatter(times[~steady], pitches[~steady], s=6, color="lightgray", label="Pitch jumping")
    ax2.scatter(times[steady], pitches[steady], s=8, color="tab:green", label="Pitch steady")
    ax2.set_ylim(F0_MIN_HZ - 20, F0_MAX_HZ + 20)
    ax2.set_ylabel("Main tone (Hz)")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(alpha=0.3)

    # 3. Harmonic score vs thresholds, detections shaded
    ax3.plot(times, scores, color="tab:blue", label="Harmonic score")
    ax3.axhline(SCORE_ON, color="red", linestyle="--", label="ON threshold")
    ax3.axhline(SCORE_OFF, color="orange", linestyle="--", label="OFF threshold")
    lo, hi = min(scores.min(), SCORE_OFF) - 2, max(scores.max(), SCORE_ON) + 2
    ax3.fill_between(times, lo, hi, where=detected, color="red", alpha=0.15, label="Drone detected")
    ax3.set_ylim(lo, hi)
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Score (dB)")
    ax3.legend(loc="upper right", fontsize=8)
    ax3.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig("detection_plot.png", dpi=120)
    print("Saved plot to detection_plot.png")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Detect drone sound in a recording.")
    parser.add_argument("wav", nargs="?", help="path to a .wav file")
    parser.add_argument("--demo", action="store_true", help="use a generated fake drone sound")
    args = parser.parse_args()

    if args.demo or not args.wav:
        print("Demo mode: fake drone buzz from 3 s to 8 s")
        fs, audio = make_demo_audio()
        wavfile.write("demo_drone.wav", fs, audio)
        title = "Demo"
    else:
        fs, audio = load_audio(args.wav)
        title = args.wav

    print(f"Sample rate: {fs} Hz | Length: {len(audio) / fs:.1f} s | analyzing...")
    times, scores, pitches = harmonic_score(audio, fs)
    steady = pitch_is_steady(pitches)
    detected = detect(scores, steady)
    print(f"Pitch steady in {100 * steady.mean():.0f}% of frames | "
          f"max harmonic score {scores.max():.1f} (ON at {SCORE_ON})")
    print_events(times, detected)
    plot(audio, fs, times, scores, pitches, steady, detected, title)


if __name__ == "__main__":
    main()
