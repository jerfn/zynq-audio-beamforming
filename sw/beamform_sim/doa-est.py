import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import scipy.signal as signal
from scipy.fft import rfft, irfft
import sounddevice as sd
from scipy.interpolate import interp1d
from extract_data import *
import time

PLOT_DEBUG = True

c = 343.0
fs = 22500
M = 4
d = 0.05

matplotlib.use('TKAgg')

mic_positions = np.arange(M) * d - (M-1) * d / 2  # center the array at 0
mic_positions = mic_positions - np.mean(mic_positions)

def hpbw_deg(f_hz): 
    '''Calculate the half-power beamwidth in degrees for uniform linear array at representative frequency f_hz'''
    l = c / f_hz
    return np.rad2deg(0.886 * (l / (M * d)))

def spatial_aliasing_limit(d):
    '''Calculate the spatial aliasing limit frequency for a given microphone spacing d'''
    return c / (2 * d)

def bandpass (x, fs, f_lo, f_hi, order=4): 
    b, a = signal.butter(order, [f_lo/(fs/2), f_hi/(fs/2)], btype='band')
    return signal.lfilter(b, a, x)

def normalize_gain (x): 
    for m in range(x.shape[0]):
        x[m] /= (np.max(np.abs(x[m])) + 1e-12)
    return x

def plot_beam_pattern(mic_positions, frequency, c=343, angles_deg=None, normalize=True):
    """
    Plot the beam pattern (array factor) for a given array geometry and frequency.
    """
    if angles_deg is None:
        angles_deg = np.linspace(-90, 90, 361)
    angles_rad = np.deg2rad(angles_deg)
    wavelength = c / frequency
    k = 2 * np.pi / wavelength

    # Array factor calculation
    AF = []
    for theta in angles_rad:
        steering = np.exp(1j * k * mic_positions * np.sin(theta))
        AF.append(np.abs(np.sum(steering)))
    AF = np.array(AF)
    if normalize:
        AF /= np.max(AF)

    plt.figure(figsize=(7, 4))
    plt.plot(angles_deg, 20 * np.log10(AF + 1e-12), '-b')
    plt.xlabel("Angle (deg)")
    plt.ylabel("Array response (dB)")
    plt.title(f"Beam pattern at {frequency/1000:.1f} kHz")
    plt.ylim(-40, 0)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Delay-and-sum beamformer DOA scan
def detect_first_arrival(X, threshold=0.2):
    """
    Detect the first significant arrival across the array.

    Parameters
    ----------
    X : ndarray, shape (M, N)
        Multichannel signal (microphones x time).
    threshold : float
        Energy threshold as a fraction of the maximum envelope energy.

    Returns
    -------
    idx_peak : int
        Sample index of the first detected arrival (based on array-averaged envelope).
    """
    # Average across microphones to get an array-wide signal
    x_avg = np.mean(X, axis=0)
    # Envelope via Hilbert transform
    env = np.abs(signal.hilbert(x_avg))
    # Normalize envelope
    env_norm = env / (np.max(env) + 1e-12)
    # Find first index where envelope exceeds threshold
    above = np.where(env_norm > threshold)[0]
    print(above)
    if len(above) == 0:
        # Fallback: just return the global maximum
        print('fallback to global max')
        return int(np.argmax(env_norm)), env_norm

    return int(above[0]), env_norm

def extract_gate(X, center_idx, fs, pre_ms=3.5, post_ms=0.5):
    """
    Extract a time gate around the detected direct arrival.

    Parameters
    ----------
    X : ndarray, shape (M, N)
        Multichannel signal (microphones x time).
    center_idx : int
        Index of the detected arrival (in samples).
    fs : float
        Sampling frequency (Hz).
    pre_ms : float
        Time before the center to include (milliseconds).
    post_ms : float
        Time after the center to include (milliseconds).

    Returns
    -------
    Xg : ndarray, shape (M, Ng)
        Gated multichannel signal.
    t_gate : ndarray, shape (Ng,)
        Time axis (seconds) relative to the gate start.
    """
    M, N = X.shape
    pre_samp = int(pre_ms * 1e-3 * fs)
    post_samp = int(post_ms * 1e-3 * fs)
    start = max(center_idx - pre_samp, 0)
    end = min(center_idx + post_samp, N)
    Xg = X[:, start:end]
    Ng = Xg.shape[1]
    t_gate = np.arange(Ng) / fs
    return Xg, t_gate

def das_peak_score(Xg, t_gate, x_pos, theta, c=343):
    """
    Returns peak-based coherence score for a given steering angle.
    """
    y = np.zeros(len(t_gate))
    M = len(x_pos)
    for m in range(len(x_pos)):
        tau = x_pos[m] * np.sin(theta) / c
        interp = interp1d(t_gate, Xg[m], kind='linear', bounds_error=False, fill_value=0)
        y += interp(t_gate - tau) # i have no idea why this sign is flipped LMAO

    return np.max(np.abs(y))


def estimate_doa_das(X, fs, x_pos, angles):
    # 1) Detect first arrival on the array-averaged envelope
    idx, env_norm = detect_first_arrival(X, 0.5)
    # 2) Extract a short window around that arrival to suppress late multipath
    Xg, t_gate = extract_gate(X, idx, fs)

    scores = []
    for th in angles:
        scores.append(das_peak_score(Xg, t_gate, x_pos, th))
    scores = np.array(scores)
    # Normalize scores for numerical stability / plotting
    scores /= (np.max(np.abs(scores)) + 1e-12)

    return angles[np.argmax(scores)], scores, idx, Xg, t_gate, env_norm



#------------------------------------------------------------

print (f"Array HPBW at 3 kHz: {hpbw_deg(3000):.2f} deg")
print(f"Spatial aliasing limit: {spatial_aliasing_limit(d):.1f} Hz")

# plot_beam_pattern(mic_positions, frequency=3000)

# data = convert_audio('right_3k.npy')
data = convert_audio('left_3k.npy')
# data = convert_audio('center_3k.npy')

X = data.T 
print(X.shape)

X = X[[1, 0, 3, 2], fs*1:]

X_filtered = []
for x in X: 
    x = bandpass(x, fs, 2700, 3300)
    X_filtered.append(x)
X_filtered = np.array(X_filtered)
X_filtered = normalize_gain(X_filtered)

# plt.figure(2)
# plt.plot(np.fft.fftshift(np.fft.fftfreq(X_filtered[0, :].size, 1/fs)), np.abs(np.fft.fftshift(np.fft.fft(X_filtered[0, :]))))


# Perform DOA scan
scan_angles = np.deg2rad(np.linspace(-90, 90, 181))  # scan from -90 to 90 degrees
angle_est, scores, idx, Xg, t_gate, env_norm = estimate_doa_das(X_filtered, fs, mic_positions, scan_angles)
print(f"Estimated DOA: {np.rad2deg(angle_est):.2f} deg")

if PLOT_DEBUG: 
    plt.figure(figsize=(8, 6))
    plt.subplot(3,1,1)
    t = np.arange(X.shape[1]) / fs
    plt.plot(t[:fs], X[0, :fs])
    plt.axvline(idx/fs, color="r", linestyle="--", label="Detected arrival")
    plt.title("Time Domain Signal (mic0)")
    plt.xlabel("Seconds")
    plt.legend()
    plt.subplot(3,1,2)
    plt.plot(t[:fs], env_norm[:fs])
    plt.axvline(idx/fs, color="r", linestyle="--", label="Detected arrival")
    plt.title("Array-wide Envelope (normalized)")
    plt.xlabel("Seconds")
    plt.legend()
    plt.subplot(3,1,3)
    plt.plot(t_gate, Xg[0, :])
    plt.title("Gated Signal (mic0)")
    plt.xlabel("Seconds")
    plt.tight_layout()

    plt.figure(figsize=(8, 6))
    plt.subplot(2,1,1)
    plt.plot(np.fft.fftshift(np.fft.fftfreq(X[0, :].size, 1/fs)), np.abs(np.fft.fftshift(np.fft.fft(X[0, :]))))
    plt.title("FFT (mic0)")
    plt.xlabel("Frequency (Hz)")
    plt.xticks(np.arange(-np.ceil(fs/2000)*1000, fs/2+1, 2000))
    plt.grid(True)
    plt.subplot(2,1,2)
    plt.plot(np.fft.fftshift(np.fft.fftfreq(X_filtered[0, :].size, 1/fs)), np.abs(np.fft.fftshift(np.fft.fft(X_filtered[0, :]))))
    plt.title("Filtered FFT (mic0)")
    plt.xlabel("Frequency (Hz)")
    plt.xticks(np.arange(-np.ceil(fs/2000)*1000, fs/2+1, 2000))
    plt.grid(True)
    plt.tight_layout()

    plt.figure(figsize=(8, 4))
    for m in range(M):
        plt.plot(t_gate * 1e3, Xg[m] + m * 2, label=f"Mic {m}")  # offset for visualization
    plt.xlabel("Time (ms)")
    plt.ylabel("Amplitude (offset per mic)")
    plt.title("Gated Microphone Signals")
    plt.tight_layout()
    plt.legend()

    sd.play(Xg[2:].T, samplerate=fs)
    time.sleep(1)
    sd.play(Xg[:2].T, samplerate=fs)


# plt.figure(figsize=(7, 4))
# plt.plot(np.rad2deg(scan_angles), scores, "-b")
# # plt.axvline(theta_deg, color="r", linestyle="--", label="True DOA")
# plt.xlabel("Scan angle (deg)")
# plt.ylabel("Normalized output power")
# plt.title("Delay-and-sum beamformer DOA response")
# plt.grid(True)
# plt.legend()
# plt.tight_layout()

plt.figure(figsize=(6,6))
ax = plt.subplot(111, polar=True)
theta_polar = scan_angles
ax.plot(theta_polar, scores, "-b")
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_title("Normalized DOA score")
ax.set_thetamin(-90)
ax.set_thetamax(90)
plt.tight_layout()
plt.show()