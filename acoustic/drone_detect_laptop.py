"""
drone_detect_laptop.py  -  Part A (laptop version) of the Drone Detector + Tracking Turret

Detects a drone's propeller buzz in an audio recording. No hardware needed.

How it works (same idea as the Raspberry Pi version):
  1. Split the audio into short frames (0.25 s each).
  2. For each frame, measure the sound energy in the drone band (200-2500 Hz).
  3. Learn the background noise level from the first few (drone-free) seconds.
  4. Turn detection ON when band energy rises well above background,
     and OFF only when it falls back near background (hysteresis = no flicker).
  5. Plot everything so you can SEE the drone's buzz.

Usage:
  python drone_detect_laptop.py --demo                 # makes a fake drone sound and tests on it
  python drone_detect_laptop.py my_recording.wav       # runs on your own recording
  python drone_detect_laptop.py my_recording.wav --noise-sec 2   # background from first 2 s

Install first:
  pip install numpy scipy matplotlib
"""

import argparse

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import spectrogram

# ---------------- Settings you can tune ----------------
BAND_LOW_HZ = 200        # bottom of the drone frequency band
BAND_HIGH_HZ = 2500      # top of the band (matches the Pi version's limit)
FRAME_SEC = 0.25         # length of each analysis frame
THRESHOLD_ON_DB = 6.0    # switch detection ON this far above background (6 dB = 4x the energy)
THRESHOLD_OFF_DB = 3.0   # switch it OFF only below this level (hysteresis: stops flicker)
NOISE_SEC = 3.0          # learn the background from the first N seconds (keep them drone-free)
                         # set to 0 to guess from the quietest 20% of the whole clip instead
NOISE_PERCENTILE = 20    # used only when NOISE_SEC = 0
MIN_FRAMES = 2           # need this many frames in a row above ON to confirm a detection
# -------------------------------------------------------


def make_demo_audio(fs=16000, seconds=10, seed=0):
    """Create a fake recording: background noise, then a drone buzz from 3 s to 8 s."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(fs * seconds)) / fs

    noise = 0.05 * rng.standard_normal(len(t))      # room / street noise

    # A drone's buzz = a "blade-pass" tone plus its harmonics, with a slight wobble
    f0 = 180 + 5 * np.sin(2 * np.pi * 0.3 * t)       # ~180 Hz, drifting as the motors adjust
    phase = 2 * np.pi * np.cumsum(f0) / fs
    buzz = sum((0.6 / k) * np.sin(k * phase) for k in range(1, 9))

    # Drone flies in (fade up), hovers, then flies away (fade down)
    envelope = np.clip((t - 3) / 1.0, 0, 1) * np.clip((8 - t) / 1.0, 0, 1)
    audio = noise + 0.25 * envelope * buzz
    return fs, audio.astype(np.float32)


def load_audio(path):
    """Load a WAV file, convert to mono floating point between -1 and 1."""
    fs, data = wavfile.read(path)
    data = data.astype(np.float32)
    if data.ndim > 1:                    # stereo or multi-channel -> average to mono
        data = data.mean(axis=1)
    peak = np.max(np.abs(data))
    if peak > 0:
        data /= peak
    return fs, data


def band_energy_per_frame(audio, fs):
    """Return the time of each frame and its energy (in dB) inside the drone band."""
    frame_len = int(FRAME_SEC * fs)
    n_frames = len(audio) // frame_len
    freqs = np.fft.rfftfreq(frame_len, d=1 / fs)
    in_band = (freqs >= BAND_LOW_HZ) & (freqs <= BAND_HIGH_HZ)
    window = np.hanning(frame_len)

    times, energy_db = [], []
    for i in range(n_frames):
        frame = audio[i * frame_len:(i + 1) * frame_len] * window
        spectrum = np.abs(np.fft.rfft(frame)) ** 2
        energy = spectrum[in_band].sum() + 1e-12     # tiny number avoids log(0)
        times.append((i + 0.5) * FRAME_SEC)
        energy_db.append(10 * np.log10(energy))
    return np.array(times), np.array(energy_db)


def detect(energy_db, noise_sec=NOISE_SEC):
    """Compare each frame to the background level.

    Background: the average of the first `noise_sec` seconds (like the Pi version's
    "stay quiet for 3 seconds"), or the quietest frames if noise_sec is 0.
    Hysteresis: turn ON above the ON threshold (for MIN_FRAMES in a row),
    stay ON until the level drops below the lower OFF threshold.
    """
    n_noise = int(noise_sec / FRAME_SEC)
    if n_noise > 0 and n_noise < len(energy_db):
        background_db = np.median(energy_db[:n_noise])
    else:
        background_db = np.percentile(energy_db, NOISE_PERCENTILE)
    on_db = background_db + THRESHOLD_ON_DB
    off_db = background_db + THRESHOLD_OFF_DB

    detected = np.zeros(len(energy_db), dtype=bool)
    active, run = False, 0
    for i, e in enumerate(energy_db):
        if not active:
            run = run + 1 if e > on_db else 0
            if run >= MIN_FRAMES:
                active = True
                detected[i - MIN_FRAMES + 1:i + 1] = True
        else:
            if e < off_db:
                active, run = False, 0
            else:
                detected[i] = True
    return detected, background_db, on_db, off_db


def print_events(times, detected):
    """Print when each detection starts and stops."""
    events, start = [], None
    for t, d in zip(times, detected):
        if d and start is None:
            start = t - FRAME_SEC / 2
        elif not d and start is not None:
            events.append((start, t - FRAME_SEC / 2))
            start = None
    if start is not None:
        events.append((start, times[-1] + FRAME_SEC / 2))

    if not events:
        print("No drone detected.")
    for s, e in events:
        print(f"DRONE DETECTED from {s:5.2f} s to {e:5.2f} s  ({e - s:.2f} s long)")
    return events


def plot(audio, fs, times, energy_db, detected, threshold_db, off_db, background_db, title):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    # Top: spectrogram - the drone shows up as bright horizontal lines (its harmonics)
    f, t, S = spectrogram(audio, fs, nperseg=1024, noverlap=768)
    ax1.pcolormesh(t, f, 10 * np.log10(S + 1e-12), shading="auto", cmap="magma")
    ax1.axhspan(BAND_LOW_HZ, BAND_HIGH_HZ, color="cyan", alpha=0.08)
    ax1.set_ylim(0, min(4000, fs / 2))
    ax1.set_ylabel("Frequency (Hz)")
    ax1.set_title(f"{title}: spectrogram (shaded = drone band)")

    # Bottom: band energy vs threshold, with detections shaded
    ax2.plot(times, energy_db, label="Energy in drone band", color="tab:blue")
    ax2.axhline(threshold_db, color="red", linestyle="--", label="ON threshold")
    ax2.axhline(off_db, color="orange", linestyle="--", label="OFF threshold")
    ax2.axhline(background_db, color="gray", linestyle=":", label="Background level")
    ax2.fill_between(times, energy_db.min() - 3, energy_db.max() + 3,
                     where=detected, color="red", alpha=0.15, label="Drone detected")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Energy (dB)")
    ax2.legend(loc="upper right")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig("detection_plot.png", dpi=120)
    print("Saved plot to detection_plot.png")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Detect drone sound in a recording.")
    parser.add_argument("wav", nargs="?", help="path to a .wav file")
    parser.add_argument("--demo", action="store_true", help="use a generated fake drone sound")
    parser.add_argument("--noise-sec", type=float, default=NOISE_SEC,
                        help="seconds at the start to learn background from (0 = auto)")
    args = parser.parse_args()

    if args.demo or not args.wav:
        print("Demo mode: fake drone buzz from 3 s to 8 s")
        fs, audio = make_demo_audio()
        wavfile.write("demo_drone.wav", fs, audio)   # so you can listen to it
        title = "Demo"
    else:
        fs, audio = load_audio(args.wav)
        title = args.wav

    times, energy_db = band_energy_per_frame(audio, fs)
    detected, background_db, threshold_db, off_db = detect(energy_db, args.noise_sec)
    print(f"Sample rate: {fs} Hz | Length: {len(audio) / fs:.1f} s")
    print(f"Background: {background_db:.1f} dB | ON: {threshold_db:.1f} dB | OFF: {off_db:.1f} dB")
    print_events(times, detected)
    plot(audio, fs, times, energy_db, detected, threshold_db, off_db, background_db, title)


if __name__ == "__main__":
    main()
