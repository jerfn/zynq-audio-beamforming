import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt

audio_data = np.load('correct.npy')

# with open('recording.raw', 'rb') as f:
#     raw_data = f.read()
#     audio_data = np.frombuffer(raw_data, dtype=np.uint32)
#     audio_data = audio_data << 1
#     audio_data = audio_data.astype(np.int32) >> 8
#     audio_data = audio_data.reshape(-1, 2)

print(audio_data.shape)
print(audio_data[:20])

audio_float = audio_data.astype(np.float32) / (2**23 - 1)  # Normalize to [-1, 1]
gain_db = 40
gain = 10 ** (gain_db / 20)
audio_float *= gain

plt.figure()
plt.plot(audio_float[1000:, 0], label='Left Channel')
plt.plot(audio_float[1000:, 1], label='Right Channel')
plt.legend()
plt.show()

print("Playing audio...")
sd.play(audio_float, samplerate=22050)
sd.wait()
