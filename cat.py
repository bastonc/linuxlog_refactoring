#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serial
import time
import std
import protocols
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

class Cat_reciever(QThread):

    data_cat_signal = pyqtSignal(bytes)
    error_cat_signal = pyqtSignal(str)

    def __init__(self, settingsDict, serial_port, protocol_list):
        super().__init__()
        self.settingsDict = settingsDict
        self.status_flag_reciever = 1
        self.request_list = protocol_list
        self.ser = serial_port

    def run(self):
        try:
            while self.status_flag_reciever == 1:
                for command in self.request_list:
                    if self.status_flag_reciever != 1:
                        break
                    try:
                        self.ser.write(command)
                        time.sleep(0.2)
                        response = self.ser.read(100)
                    except (OSError, serial.SerialException) as error:
                        self.status_flag_reciever = 0
                        self.error_cat_signal.emit(str(error))
                        break
                    if response:
                        self.data_cat_signal.emit(response)
                    time.sleep(0.2)

                for _ in range(20):
                    if self.status_flag_reciever != 1:
                        break
                    self.msleep(100)
        finally:
            try:
                self.ser.close()
            except (OSError, serial.SerialException):
                pass
    def stop_cat_reciever(self):
        self.status_flag_reciever = 0


class Cat_start(QObject):
    def __init__(self, settingsDict, parent_window):
        super().__init__()
        self.settingsDict = settingsDict
        self.parent_window = parent_window
        self.ser = None
        self.reciever_cat = None
        parity_by_name = {
            'None': serial.PARITY_NONE,
            'Odd': serial.PARITY_ODD,
            'Even': serial.PARITY_EVEN,
            'Mark': serial.PARITY_MARK,
            'Space': serial.PARITY_SPACE,
        }
        parity = parity_by_name.get(self.settingsDict.get('cat-parity'), serial.PARITY_NONE)

        try:
            self.ser = serial.Serial('/dev/' + self.settingsDict['cat-port'],
                                 int(self.settingsDict['speed-cat']),
                                 timeout=int(self.settingsDict['timeout-cat']),
                                 parity=parity, rtscts=1)
            self.protocol_command_list = self.protocol_cat() # list of commands for models TRX
            self.start_reciever_cat()
            self.parent_window.set_cat_label(True)

        except Exception:
            if self.ser is not None:
                try:
                    self.ser.close()
                except Exception:
                    pass
            std.std.message(self.parent_window, "Can't open "+self.settingsDict['cat-port'], "Error CAT system")
            self.parent_window.set_cat_label(False)

    def protocol_cat(self):
        protocol_by_name = {
            'Kenwood': protocols.Kenwood,
            'ExpertSDR': protocols.Kenwood,
            'Icom': protocols.Icom,
        }
        protocol_class = protocol_by_name.get(self.settingsDict.get('cat-protocol'))
        if protocol_class is None:
            raise ValueError(f"Unsupported CAT protocol: {self.settingsDict.get('cat-protocol')}")

        self.protocol_decoder = protocol_class(self.settingsDict, self.parent_window, self.ser)
        return self.protocol_decoder.get_freq_mod_list()

    def start_reciever_cat(self):
        self.reciever_cat = Cat_reciever(self.settingsDict, self.ser, self.protocol_command_list)
        self.reciever_cat.data_cat_signal.connect(self.set_freq_cat)
        self.reciever_cat.error_cat_signal.connect(self.cat_receiver_error)
        self.reciever_cat.start()

    @pyqtSlot(str)
    def cat_receiver_error(self, message):
        print(f"CAT connection lost: {message}")
        self.parent_window.set_cat_label(False)

    def stop_cat(self):
        if self.reciever_cat is None:
            return
        self.reciever_cat.stop_cat_reciever()
        if self.ser is not None:
            try:
                self.ser.cancel_read()
            except (AttributeError, OSError, serial.SerialException):
                pass
        if self.reciever_cat.isRunning():
            stopped = self.reciever_cat.wait(5000)
            if not stopped and self.ser is not None:
                try:
                    self.ser.close()
                except (OSError, serial.SerialException):
                    pass
                self.reciever_cat.wait(1000)

    @pyqtSlot(bytes)
    def set_freq_cat(self, data_byte):
        self.protocol_decoder.decoder_data(data_byte)

    def sender_cat(self, freq=None, mode=None):
        if freq != None: # if we have freq

            freq_string = freq
            print("freq_string", freq_string)
            self.protocol_decoder.set_freq_rig(freq_string)
            std_value = std.std()
            band = std_value.get_std_band(freq)
            mode = std_value.mode_band_plan(band, freq)
            print(mode)
            time.sleep(0.2)

            self.protocol_decoder.set_mode_rig(mode)
