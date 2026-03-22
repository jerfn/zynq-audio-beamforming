import numpy as np
import sounddevice as sd 
import matplotlib.pyplot as plt


def shift_bits_left(data, shift=1):
    shifted_left = data << shift
    overflow = np.roll(data, -1) >> (32 - shift)
    return (shifted_left | overflow).view(np.uint32).astype(np.uint32)

def convert_audio(filename1):
    raw_data = np.load(filename1)
    # print(raw_data.shape)
    raw_data = raw_data.view(np.uint32)
    # print(raw_data.shape)
    audio_datas = [raw_data[0::2], raw_data[1::2]]
    audio_combine = []
    for audio_data in audio_datas:
        corrected_data = shift_bits_left(audio_data, 3)
        corrected_data = corrected_data.astype(np.int32) << 1
        corrected_data = corrected_data.astype(np.int32) >> 8
        corrected_data = corrected_data.reshape(-1, 2)
        audio_float = corrected_data.astype(np.float32) / (2**23 - 1) # Normalize to [-1, 1]
        gain_db = 40
        gain = 10 ** (gain_db / 20)
        audio_float *= gain
        audio_combine.append(audio_float)
        # print(audio_float.shape)
    
    res = np.hstack((audio_combine[0],audio_combine[1]))
    # print(res.shape)
    return res

# #example 
# audio = convert_audio('left_data_0.npy', 'left_data_1.npy')
# print(audio.shape)
# print(audio[:, 0:2].shape)
# sd.play(audio[:, 0:2], samplerate=22500)
# sd.wait()
'''
this should print
(65536, 4)
(65536, 2)
'''

