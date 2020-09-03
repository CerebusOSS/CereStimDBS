import sys
import os
import numpy as np
import qtpy
from qtpy import uic, QtGui, QtWidgets
from qtpy.QtWidgets import QApplication, QMainWindow, QWidget
from qtpy.QtCore import Qt, QTimer
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

        # Add indicator
        status_layout = self.findChild(QtWidgets.QVBoxLayout, 'status_verticalLayout')
        self.indicator = StatusIndicator()
        status_layout.addWidget(self.indicator)

        # Connect GUI signals to slots
        _refresh_pushButton = self.findChild(QtWidgets.QPushButton, 'refresh_pushButton')
        _refresh_pushButton.clicked.connect(self.refresh_devices)

        _connect_pushButton = self.findChild(QtWidgets.QPushButton, 'connect_pushButton')
        _connect_pushButton.clicked.connect(self.connect)

        _generate_pushButton = self.findChild(QtWidgets.QPushButton, 'generate_pushButton')
        _generate_pushButton.clicked.connect(self.generate)

        _start_pushButton = self.findChild(QtWidgets.QPushButton, 'start_pushButton')
        _start_pushButton.clicked.connect(self.start)

        self.show()

    def refresh_devices(self):
        _device_combo = self.findChild(QtWidgets.QComboBox, 'device_comboBox')
        _device_combo.clear()
        result, device_tuple = self.stimulator.scanForDevices()
        # result, device_tuple = cerestim.BStimulator_scanForDevices()
        if result == 0:
            for dev_id in device_tuple:
                _device_combo.addItem(str(dev_id))

    def connect(self):
        _device_combo = self.findChild(QtWidgets.QComboBox, 'device_comboBox')
        curr_dev_id = int(_device_combo.currentText())
        curr_dev_ix = _device_combo.currentIndex()
        self.stimulator.setDevice(curr_dev_ix)
        self.statusBar().showMessage(f"Connected to {curr_dev_id} at index {curr_dev_ix}.")
        self.indicator.setColor('yellow')

    def calculate_waveform(self, params):
        waveform = None
        n_reps = 0
        min_amp, max_amp = self.stimulator.getMinMaxAmplitude()
        p1_amp = max(min(params['amp'], max_amp), min_amp)
        min_interphase = 53  # It would be great to get this from API.
        cycle_dur_us = 1E6 / params['frequency']
        if params['polarity'].endswith('Mono'):
            p2_max_width = cycle_dur_us - params['width'] - 2 * min_interphase
            p2_amp = (params['width'] * p1_amp) / p2_max_width
            p2_amp = max(p2_amp, min_amp)
            p2_width = (params['width'] * p1_amp) / p2_amp
        else:
            p2_width = params['width']
            p2_amp = p1_amp

        if params['interphase'] == 'Max Sep':
            interphase = (cycle_dur_us - params['width'] - p2_width) / 2
        else:
            interphase = min_interphase

        # Configure final waveform
        n_pulses = np.ceil(params['duration'] * params['frequency'])
        if n_pulses > 255:
            n_reps = np.ceil(n_pulses / 255)
            n_pulses = 255
        else:
            n_reps = 1
        """
        waveform = {...
            'polarity', int16(stim_params.is_ana),...
            'pulses', n_pulses,...
            'amp1', stim_params.p1_amp,...
            'amp2', p2_amp,...
            'width1', stim_params.p1_width,...
            'width2', p2_width,...
            'interphase', interphase,...
            'frequency', stim_params.freq};
        """
        return waveform, n_reps

    def generate(self):
        self.statusBar().showMessage('TODO: generate()')
        stim_params = {
            'polarity': self.findChild(QtWidgets.QComboBox, 'polarity_comboBox').currentText(),
            'duration': self.findChild(QtWidgets.QDoubleSpinBox, 'dur_doubleSpinBox').value(),
            'ramp': self.findChild(QtWidgets.QDoubleSpinBox, 'ramp_doubleSpinBox').value(),
            'amp': self.findChild(QtWidgets.QSpinBox, 'amp_spinBox').value(),
            'interphase': self.findChild(QtWidgets.QComboBox, 'interphase_comboBox').currentText(),
            'width': self.findChild(QtWidgets.QSpinBox, 'width_spinBox').value(),
            'frequency': self.findChild(QtWidgets.QDoubleSpinBox, 'freq_doubleSpinBox').value(),
            'electrode': self.findChild(QtWidgets.QSpinBox, 'elec_spinBox').value(),
        }
        final_waveform, n_final_stims = self.calculate_waveform(stim_params)
        if final_waveform is not None and n_final_stims > 0:
            self.stimulator.setStimPattern('waveform', 15, final_waveform)
        """
            
            % Calculate ramp and add in waveform positions 1-14
            ramp_wfs = cell(0, 2);
            if app.RampDursEditField.Value > 0
                ramp_params = stim_params;
                ramp_params.dur = app.RampDursEditField.Value / 14;
                ramp_amps = round(linspace(min_amp, p1_amp, 15));
                ramp_wfs = cell(14, 2);
                for ramp_ix = 1:14
                    ramp_params.p1_amp = ramp_amps(ramp_ix);
                    [ramp_wfs{ramp_ix,1}, ramp_wfs{ramp_ix,2}] =...
                        app.calc_waveform(ramp_params);
                    app.stimulator.setStimPattern(...
                        'waveform', ramp_ix,...
                        ramp_wfs{ramp_ix,1}{:});
                end
            end
            % Add waveforms x reps to stimulator program.
            app.stimulator.beginSequence();
            % Add ramp stims
            for ramp_ix = 1:size(ramp_wfs, 1)
                for stim_ix = 1:ramp_wfs{ramp_ix, 2}
                    app.stimulator.autoStim(stim_params.elec, ramp_ix);
                end
            end
            % Add final-amp stims
            for final_ix = 1:n_final_stims
                app.stimulator.autoStim(stim_params.elec, 15);
            end
            app.stimulator.endSequence();
            
            app.StartButton.Enable = 'on';
            app.StatusLamp.Color = 'blue';
            
            delete(app.stim_timer);
            app.stim_timer = timer('StopFcn', @app.timer_callback,...
                'TimerFcn', @app.timer_callback,...
                'StartDelay', app.FinalDursEditField.Value);
        """
        self.indicator.setColor('blue')

    def start(self):
        # For safety: Always stop first, even if we intend to start.
        if self.stimulator is not None:
            self.stimulator.stop()

        if self.indicator.color == 'blue':
            self.statusBar().showMessage('TODO: start()::start')
            # self.stimulator.play(1)
            self.indicator.setColor('green')

        elif self.indicator.color == 'green':
            self.statusBar().showMessage('TODO: start()::stop')
            self.indicator.setColor('blue')
            # stop(self.stim_timer)  # Cancel timer, change lamp to blue.
            # delete(self.stim_timer)


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
