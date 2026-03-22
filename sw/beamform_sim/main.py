from machine import I2S, Pin
from time import sleep
import sys

led = Pin("LED", Pin.OUT)
vdd_pin = Pin(15, Pin.OUT)
vdd_pin.on()
sck_pin = Pin(16)
ws_pin = Pin(17)
sd_pin = Pin(18)

RECORDING_SIZE_IN_BYTES = 176400

mic_samples = bytearray(10000)
mic_samples_mv = memoryview(mic_samples)

num_sample_bytes_written = 0

for i in range(5):
    led.on()
    sleep(0.5)
    led.off()
    sleep(0.5)
    

print("START")  # Signal to computer script
sleep(1)
led.on()

audio_in = I2S(0,
               sck=sck_pin, ws=ws_pin, sd=sd_pin,
               mode=I2S.RX,
               bits=32,
               format=I2S.STEREO,
               rate=22050,
               ibuf=RECORDING_SIZE_IN_BYTES)

try:
    while num_sample_bytes_written < RECORDING_SIZE_IN_BYTES:
        num_bytes_read_from_mic = audio_in.readinto(mic_samples_mv)
        if num_bytes_read_from_mic > 0:
            num_bytes_to_send = min(
                num_bytes_read_from_mic, RECORDING_SIZE_IN_BYTES - num_sample_bytes_written
            )
            # Send binary data over USB serial
            sys.stdout.buffer.write(mic_samples_mv[:num_bytes_to_send])
            num_sample_bytes_written += num_bytes_to_send
    print("\nDONE")  # Signal completion
except (KeyboardInterrupt, Exception) as e:
    print("\ncaught exception {} {}".format(type(e).__name__, e))
finally:
    led.off()
    audio_in.deinit()