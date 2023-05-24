from oscilloscope import Tektronix
import matplotlib.pyplot as plt
import numpy as np

scope = Tektronix()

## initialise scope

scope.initialise_scope(timebase=0.0005)

## initialise each channel - in this case, channel 1

scope.initialise_channel(channel="CH1", v_range=0.2)

## measurement initialisation

scope.set_acquisition_mode()
scope.set_number_of_averages()

## do measurement

scope.set_acq_state("ON")
scope.set_data_source()
scope.set_data_encoding()
t0, delta_t, y_zero, y_mu, y_offset = scope.get_scaling_factors()
scope.scope.write("CURV?")
raw_data = scope.scope.read()

raw_data = np.array([float(x) for x in raw_data.split(',')])
data = (raw_data - y_offset)*y_mu + y_zero
time = np.arange(t0, len(data)*delta_t + t0 , delta_t)

fig, ax = plt.subplots()
ax.plot(time,data)
plt.show()

