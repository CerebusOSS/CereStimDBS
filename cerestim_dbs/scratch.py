# Interactive mode?
import cerestim
import numpy as np


stimulator = cerestim.BStimulator()
result, device_tuple = stimulator.scanForDevices()
stimulator.setDevice(0)
max_min = stimulator.getMinMaxAmplitude()
# should be 16960, 100
max_amp, min_amp = max_min >> 16, max_min & 0x0F

p1_width = 100  # us
p1_amp = 500
dur = 30
freq = 300
min_interphase = 53

cycle_dur_us = 1e6 / freq
p2_max_width = cycle_dur_us - p1_width - 2*min_interphase
p2_amp = (p1_width * p1_amp) / p2_max_width
# p2_amp = max(p2_amp, min_amp)
p2_width = (p1_width * p1_amp) / p2_amp

# interphase = (cycle_dur_us - p1_width - p2_width) / 2  # max interphase
interphase = min_interphase
n_pulses = np.ceil(dur * freq)

if n_pulses > 255:
    n_reps = np.ceil(n_pulses / 255)
    n_pulses = 255
else:
    n_reps = 1

stimulator.configureStimulusPattern(cerestim.BCONFIG_15, cerestim.BWF_ANODIC_FIRST, n_pulses,
                                    np.uint16(p1_amp), np.uint16(p2_amp),
                                    np.uint16(p1_width), np.uint16(p2_width),
                                    np.uint32(freq), np.uint16(interphase))
# TODO: Add ramp configs 0-14

stimulator.beginningOfSequence()
# TODO: Add ramp stims
# Total ramp + n_reps < 128
for rep in range(n_reps):
    stimulator.autoStimulus(1, cerestim.BCONFIG_15)
stimulator.endOfSequence()
stimulator.play(1)
stimulator.disconnect()
