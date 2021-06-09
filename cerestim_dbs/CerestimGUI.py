import sys
import numpy as np
import qtpy
from qtpy import uic, QtGui, QtWidgets
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget
from qtpy.QtCore import Qt, QTimer
import pyqtgraph as pg
import cerestim


class StatusIndicator(QWidget):
    def __init__(self, *args, size=20, **kwargs):
        super(StatusIndicator, self).__init__(*args, **kwargs)
        self.color = 'red'
        self.size = size

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor(self.color))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)
        painter.drawEllipse(0, 0, self.size, self.size)

    def setColor(self, color):
        assert color in ['red', 'blue', 'green', 'yellow']
        self.color = color
        self.update()


class CerestimGUI(QMainWindow):

    def __init__(self):
        super(CerestimGUI, self).__init__()
        self.stimulator = cerestim.BStimulator()
        uic.loadUi('mainwindow.ui', self)
        self._connected = False
        self._generated = False

        # Add indicator
        status_layout = self.findChild(QtWidgets.QVBoxLayout, 'status_verticalLayout')
        self.indicator = StatusIndicator()
        status_layout.addWidget(self.indicator)

        # Add plot widget
        plot_widget = self.findChild(QtWidgets.QWidget, "plot_widget")
        plot_widget.setLayout(QtWidgets.QHBoxLayout())
        self._pg = pg.GraphicsLayoutWidget(show=True, title="Pulse Waveform")
        plot_widget.layout().addWidget(self._pg)

        # Connect GUI signals to slots
        _refresh_pushButton = self.findChild(QtWidgets.QPushButton, 'refresh_pushButton')
        _refresh_pushButton.clicked.connect(self.refresh_devices)

        _connect_pushButton = self.findChild(QtWidgets.QPushButton, 'connect_pushButton')
        _connect_pushButton.clicked.connect(self.connect)

        _generate_pushButton = self.findChild(QtWidgets.QPushButton, 'generate_pushButton')
        _generate_pushButton.clicked.connect(self.generate)

        _start_pushButton = self.findChild(QtWidgets.QPushButton, 'start_pushButton')
        _start_pushButton.clicked.connect(self.start)

        for spinboxstr in ['dur_doubleSpinBox', 'width_spinBox', 'ramp_doubleSpinBox', 'freq_spinBox',
                           'amp_spinBox', 'elec_spinBox']:
            sb = self.findChild(QtWidgets.QAbstractSpinBox, spinboxstr)
            sb.valueChanged.connect(self.handle_value_changed)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(500)

        self.show()

    def closeEvent(self, event):
        if self._connected:
            self.stimulator.disconnect()
        event.accept()

    def handle_bresult(self, res, expect_disconnected=False, caller=''):
        if res == cerestim.BSUCCESS:
            return 0
        if res == cerestim.BDISCONNECTED and not expect_disconnected:
            raise ConnectionError("Cerestim is disconnected.")
        res_str = str(res)
        if res == cerestim.BINVALIDFREQUENCY:
            res_str = "Invalid Frequency"
        elif res == cerestim.BPHASEGREATMAX:
            res_str = "Amplitude too high"
        msg = f"Caller {caller} was not successful. Result: {res_str}"  # TODO: Strings for each known result.
        print(msg)
        self.statusBar().showMessage(msg)
        return res

    def get_status(self) -> str:
        _status = cerestim.BSequenceStatus()
        res = self.stimulator.readSequenceStatus(_status)
        self.handle_bresult(res, caller='get_status::readSequenceStatus')
        state = {0: 'stopped', 1: 'paused', 2: 'playing', 3: 'writing', 4: 'waiting'}[_status.status]
        return state

    def update_graph(self):
        stim_pattern = cerestim.BStimulusConfiguration()
        self.stimulator.readStimulusPattern(stim_pattern, 15)
        xy = [(0, 0), (0, stim_pattern.amp1), (stim_pattern.width1, stim_pattern.amp1), (stim_pattern.width1, 0),
              (stim_pattern.width1 + stim_pattern.interphase, 0),
              (stim_pattern.width1 + stim_pattern.interphase, -stim_pattern.amp2),
              (stim_pattern.width1 + stim_pattern.interphase + stim_pattern.width2, -stim_pattern.amp2),
              (stim_pattern.width1 + stim_pattern.interphase + stim_pattern.width2, 0),
              (1e6 / stim_pattern.frequency, 0)]
        xy = np.array(xy)
        if stim_pattern.anodicFirst == 1:  # When this value is 1, it is CathodicFirst. 0 is anodicFirst. Confusing.
            xy[:, 1] *= -1.0
        p1 = self._pg.getItem(0, 0)
        if not p1:
            p1 = self._pg.addPlot(row=0, col=0)
            p1.plot(x=xy[:, 0], y=xy[:, 1])
            p1.setLabel('bottom', text='Time (μs)')
            p1.setLabel('left', text='Stim. (μA)')
        else:
            pdi = p1.items[0]
            pdi.setData(xy)

    def update_status(self):
        if not self._connected:
            self.indicator.setColor('red')
            return
        start_pb = self.findChild(QtWidgets.QPushButton, "start_pushButton")
        start_pb.setText("Start")
        status = self.get_status()
        if status == 'playing':
            self.indicator.setColor('green')
            start_pb.setEnabled(True)
            start_pb.setText("Stop")
            self.statusBar().showMessage(f"Now stimulating...")
        elif self._generated:
            start_pb.setEnabled(True)
            self.indicator.setColor('blue')
            self.statusBar().showMessage(f"Waiting.")
        else:
            start_pb.setEnabled(False)
            self.indicator.setColor('yellow')
            self.statusBar().showMessage(f"Settings changed. Please Generate.")

    def handle_value_changed(self, value):
        self._generated = False
        self.update_status()

    def refresh_devices(self):
        _device_combo = self.findChild(QtWidgets.QComboBox, 'device_comboBox')
        _device_combo.clear()
        result, device_tuple = cerestim.BStimulator_scanForDevices()
        if result == cerestim.BSUCCESS:
            for dev_id in device_tuple:
                _device_combo.addItem(str(dev_id))

    def connect(self):
        _device_combo = self.findChild(QtWidgets.QComboBox, 'device_comboBox')
        curr_dev_id = int(_device_combo.currentText())
        curr_dev_ix = _device_combo.currentIndex()
        self.stimulator = cerestim.BStimulator()
        res = self.stimulator.setDevice(curr_dev_ix)
        self.handle_bresult(res, caller='connect::setDevice')

        usbParams = cerestim.BUsbParams()
        usbParams.timeout = 1000  # msec
        usbParams.pid = cerestim.PN7655
        res = self.stimulator.connect(cerestim.BINTERFACE_DEFAULT, usbParams)
        self.handle_bresult(res, caller='connect::connect')

        self._connected = res == cerestim.BSUCCESS
        self.statusBar().showMessage(f"Connected to {curr_dev_id} at index {curr_dev_ix}.")

        self.update_status()
        min_freq = self.stimulator.getMinHardFrequency()
        max_freq = self.stimulator.getMaxHardFrequency()
        self._freq_lim = (min_freq, max_freq)
        self._max_width = self.stimulator.getMaxHardWidth()
        self._max_interphase = self.stimulator.getMaxHardInterphase()

    def _stim_min_max(self):
        # Would love to get these from the device:
        # stim_min_max = self.stimulator.getMinMaxAmplitude()
        # max_amp, min_amp = stim_min_max >> 12, stim_min_max & 0x0F
        # print("max,min:", max_amp, min_amp)  # 271360, 4 !?
        # Bt it doesn't seem to return the correct values. Use Matlab's:
        max_amp, min_amp = 16960, 100
        return min_amp, max_amp

    def calculate_waveform(self, params: dict):
        """
        The CereStim is capable of storing 16 different waveform patterns, with ids: BCONFIG_0 ... BCONFIG_15
        Each pattern is set with configureStimulusPattern(configID: 'BConfig', afcf: 'BWFType', pulses: 'UINT8',
                                                        amp1: 'UINT16', amp2: 'UINT16', width1: 'UINT16',
                                                        width2: 'UINT16', frequency: 'UINT32', interphase: 'UINT16')
            where BWFType is an enum: anodic_first=0, cathodic_first, invalid

        :param params:
        :return: waveform, n_reps
        """
        # Get variables from device
        min_interphase = 53  # It would be great to get this from API.
        min_amp, max_amp = self._stim_min_max()
        p1_amp = max(min(params['amp'], max_amp), min_amp)

        cycle_dur_us = 1E6 / params['frequency']
        if params['polarity'].endswith('Mono'):
            p2_max_width = cycle_dur_us - params['width'] - 2 * min_interphase
            p2_amp = (params['width'] * p1_amp) / p2_max_width
            p2_amp = int(max(p2_amp, min_amp))
            p2_width = int((params['width'] * p1_amp) / p2_amp)
        else:
            p2_width = params['width']
            p2_amp = p1_amp

        if params['interphase'] == 'Max Sep':
            interphase = int(np.floor((cycle_dur_us - params['width'] - p2_width) / 2))
        else:
            interphase = min_interphase

        # Configure final waveform
        n_pulses = np.ceil(params['duration'] * params['frequency'])
        if n_pulses > 255:
            n_reps = int(np.ceil(n_pulses / 255))
            n_pulses = 255
        else:
            n_reps = 1

        is_ano = params['polarity'].lower().startswith('an')
        waveform = {
            'afcf': cerestim.BWF_ANODIC_FIRST if is_ano else cerestim.BWF_CATHODIC_FIRST,
            'pulses': n_pulses,
            'amp1': params['amp'],
            'amp2': p2_amp,
            'width1': params['width'],
            'width2': p2_width,
            'frequency': params['frequency'],
            'interphase': interphase,
        }
        return waveform, n_reps

    def generate(self):
        self.statusBar().showMessage('Generating...')

        # Pull the stimulus parameters from the GUI widgets
        stim_params = {
            'polarity': self.findChild(QtWidgets.QComboBox, 'polarity_comboBox').currentText(),
            'duration': self.findChild(QtWidgets.QDoubleSpinBox, 'dur_doubleSpinBox').value(),
            'amp': self.findChild(QtWidgets.QSpinBox, 'amp_spinBox').value(),
            'interphase': self.findChild(QtWidgets.QComboBox, 'interphase_comboBox').currentText(),
            'width': self.findChild(QtWidgets.QSpinBox, 'width_spinBox').value(),
            'frequency': self.findChild(QtWidgets.QSpinBox, 'freq_spinBox').value(),
            'electrode': self.findChild(QtWidgets.QSpinBox, 'elec_spinBox').value(),
        }

        # Program the ramp waveforms
        ramp_dur = self.findChild(QtWidgets.QDoubleSpinBox, 'ramp_doubleSpinBox').value()
        ramp_wf_reps = []
        if ramp_dur > 0:
            min_amp, max_amp = self._stim_min_max()
            ramp_params = stim_params.copy()
            ramp_params['duration'] = ramp_dur / 14
            ramp_amps = np.round(np.linspace(min_amp, stim_params['amp'], 15))
            for ramp_ix, ramp_amp in enumerate(ramp_amps):
                ramp_params['amp'] = ramp_amp
                ramp_wf, n_ramp_reps = self.calculate_waveform(ramp_params)
                res = self.stimulator.configureStimulusPattern(configID=ramp_ix+1, **ramp_wf)
                self.handle_bresult(res, caller='generate::configureStimulusPattern')
                ramp_wf_reps.append(n_ramp_reps)

        # Create the final stimulus waveform and store it in the device in configID 15 (the last one).
        final_waveform, n_final_stims = self.calculate_waveform(stim_params)
        if final_waveform is not None and n_final_stims > 0:
            res = self.stimulator.configureStimulusPattern(configID=15, **final_waveform)
            if self.handle_bresult(res, caller='generate::configureStimulusPattern'):
                return

        # Set waveforms x reps in the stimulator sequences
        self.stimulator.beginningOfSequence()
        for ramp_ix, ramp_reps in enumerate(ramp_wf_reps):
            for rep_ix in range(ramp_reps):
                self.stimulator.autoStimulus(stim_params['electrode'], ramp_ix + 1)
        for _ in range(n_final_stims):
            self.stimulator.autoStimulus(stim_params['electrode'], 15)
        self.stimulator.endOfSequence()

        self._generated = True
        self.update_graph()
        self.statusBar().showMessage(f"Generated sequence.")
        self.update_status()

    def start(self):
        status = self.get_status()

        # For safety: Always stop first, even if we intend to start.
        if self.stimulator is not None:
            res = self.stimulator.stop()
            self.handle_bresult(res, caller="start::stop")
            self.statusBar().showMessage(f"Stopped")

        if status == 'stopped':
            res = self.stimulator.play(1)
            self.handle_bresult(res, caller="start::play")
            if res == cerestim.BSUCCESS:
                self.statusBar().showMessage(f"Now stimulating")

        self.update_status()


def main():
    _ = QApplication(sys.argv)
    window = CerestimGUI()
    timer = QTimer()
    timer.timeout.connect(window.update)
    timer.start(1)

    if (sys.flags.interactive != 1) or not hasattr(qtpy.QtCore, 'PYQT_VERSION'):
        QApplication.instance().exec_()


if __name__ == '__main__':
    main()
