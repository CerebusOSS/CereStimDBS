# Interactive mode?
import cerestim
import numpy as np


stimulator = cerestim.BStimulator()
result, device_tuple = stimulator.scanForDevices()
stimulator.setDevice(0)
stimulator.connect(cerestim.BINTERFACE_DEFAULT, None)  # ["003F", 5000, "04D8"])
max_min = stimulator.getMinMaxAmplitude()
# should be 16960, 100
max_amp, min_amp = max_min >> 16, max_min & 0x0F
min_amp = max(min_amp, 100)

p1_width = 100  # us; 44-65535
p1_amp = 500    # 100-10000
dur = 30
freq = 300  # 4-5000
min_interphase = 53
max_interphase = 65535

cycle_dur_us = 1e6 / freq
p2_max_width = cycle_dur_us - p1_width - 2*min_interphase
p2_min_amp = (p1_width * p1_amp) / p2_max_width
p2_amp = int(np.ceil(max(p2_min_amp, min_amp)))
p2_width = (p1_width * p1_amp) / p2_amp

# interphase = (cycle_dur_us - p1_width - p2_width) / 2  # max interphase
interphase = min_interphase
n_pulses = int(np.ceil(dur * freq))

if n_pulses > 255:
    n_reps = int(np.ceil(n_pulses / 255))
    n_pulses = 255
else:
    n_reps = 1

stimulator.configureStimulusPattern(cerestim.BCONFIG_15, cerestim.BWF_ANODIC_FIRST, n_pulses,
                                    p1_amp, p2_amp,
                                    p1_width, int(np.round(p2_width)),
                                    freq, interphase)
# TODO: Add ramp configs 0-14

stimulator.beginningOfSequence()
# TODO: Add ramp stims
# Total ramp + n_reps < 128
for rep in range(n_reps):
    stimulator.autoStimulus(1, cerestim.BCONFIG_15)
stimulator.endOfSequence()
stimulator.play(1)
stimulator.disconnect()
