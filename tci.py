#!/usr/bin/python3
# -*- coding: utf-8 -*-

#from websocket import WebSocket
import time

import websocket
import std
import traceback
from PyQt6.QtCore import QThread,  pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore



class tci_connect:

    def __init__(self, settingsDict, log_form, parent=None):
        super().__init__()
        self.settingsDict = settingsDict
        self.log_form = log_form
        self.settingsDisct = settingsDict


    def get_mode(self):
        return self.log_form.get_mode()

    def start_tci(self, host, port):
        self.tci_reciever = Tci_reciever(host + ":" + port,
                                         log_form=self.log_form, settingsDict=self.settingsDict)
        self.tci_reciever.status_changed.connect(self.log_form.set_tci_stat)
        self.tci_reciever.frequency_changed.connect(self.log_form.set_freq)
        self.tci_reciever.mode_changed.connect(self.log_form.set_mode_tci)
        self.tci_reciever.signal_strength_changed.connect(self.log_form.set_rs_s)
        self.tci_reciever.transmit_state_changed.connect(self.log_form.trx_enable)
        self.tci_reciever.restart_requested.connect(self.log_form.restart_tci_sender)
        self.tci_reciever.spot_clicked.connect(self.log_form.handle_tci_spot)
        self.tci_reciever.set_flag("run")
        self.tci_reciever.start()
        # self.tci_reciever_stream_port = Tci_reciever(host + ":" + "50040", log_form=self.log_form, settingsDict=self.settingsDict)
        # self.tci_reciever_stream_port.set_flag("run")
        # self.tci_reciever_stream_port.start()

    def stop_tci(self):
        if not hasattr(self, "tci_reciever"):
            print("TCI don't started")
            return
        self.tci_reciever.stop()
        if self.tci_reciever.isRunning():
            self.tci_reciever.wait(5000)


class Tci_reciever(QThread):
    tx_flag = QtCore.pyqtSignal(str)
    status_changed = QtCore.pyqtSignal(str)
    frequency_changed = QtCore.pyqtSignal(str)
    mode_changed = QtCore.pyqtSignal(str)
    signal_strength_changed = QtCore.pyqtSignal(str)
    transmit_state_changed = QtCore.pyqtSignal(str)
    restart_requested = QtCore.pyqtSignal()
    spot_clicked = QtCore.pyqtSignal(str, str, str)
    tx = "Disable"

    def __init__(self, uri, log_form, settingsDict, parent=None):
        super().__init__()
        self.uri = uri
        self.log_form = log_form
        #print("uri:_>", self.uri)
        self.active_rx = 0
        self.active_vfo = 0
        self.ws = websocket.WebSocket()
        self.settingsDict = settingsDict
        self.mode = self.settingsDict['mode']
        self.flag = "stop"

    def set_flag(self, flag):
        #print("set_flag:", flag)
        self.flag = flag

    def stop(self):
        self.flag = "stop"
        try:
            self.ws.close()
        except Exception:
            pass

    def get_mode(self):
        return self.mode

    def tci_send_command(self, string_command):
        try:
            self.ws.send(string_command)
        except Exception:
            print(f"Error send command: {string_command}")

    def run(self):

        while self.flag == "run":
            try:
                self.ws = websocket.WebSocket()
                self.ws.settimeout(2)
                self.ws.connect(self.uri, timeout=3)
                self.ws.settimeout(2)
                self.restart_requested.emit()
                self.status_changed.emit('•TCI')

                break
                #time.sleep(3)
            except Exception:
                # self.log_form.set_tci_label_found()
                # print("Tci_reciever: Except connection")
                # self.log_form.set_tci_stat('--', "#ff5555")
                QThread.sleep(2)

                continue
        old_reciever = ""
        while self.flag == "run":
            try:
                #print("Connect to ")
                #
                reciever = self.ws.recv()
                # print("Tci_reciever.run: from socket (esdr):_>", reciever)
                if reciever != old_reciever:
                    # print("Tci_reciever.run: from socket (esdr):_>", reciever)
                    tci_string=reciever.split(":")
                    # reciev vfo (freq)
                    if tci_string[0] == "ready;":
                        #print("send RX_SENSOR_ENABLE")
                        #if bool(self.settingsDict["rs-from-tci"]):
                         self.tci_send_command("RX_SENSORS_ENABLE:" + self.settingsDict["rs-from-tci"] + "," + self.settingsDict["rs-time-update"] + ";")

                    if tci_string[0] == "ecoder_switch_rx":
                        self.active_rx = str(tci_string[1]).split(",")[-1].replace(";","")
                        self.active_vfo = str(tci_string[1]).split(",")[0]
                        self.tci_send_command(f"VFO:{self.active_rx},{self.active_vfo};")

                    if tci_string[0] == "ecoder_switch_channel":
                        self.active_vfo = str(tci_string[1]).split(",")[-1].replace(";","")
                        self.tci_send_command(f"VFO:{self.active_rx},{self.active_vfo};")
                        #self.active_rx = str(tci_string[1]).split(",")[0]

                    if tci_string[0] == "rx_channel_sensors":
                        dBm = str(tci_string[1]).split(",")[-1].replace(";","")
                        rx = str(tci_string[1]).split(",")[0]
                        vfo = str(tci_string[1]).split(",")[1]
                        if rx == self.active_rx and vfo == self.active_vfo:
                        #print(f"dBm: {dBm}")
                            self.signal_strength_changed.emit(dBm)

                    if tci_string[0] == 'trx':
                        #self.tx = 'Enable'
                        values = tci_string[1].split(",")
                        #print("TRX:_>", values[1])
                        if values[1] == 'true;':
                            #print(values[1])
                            self.transmit_state_changed.emit('tx')

                        elif values[1] == 'false;':
                            #print(values[1])
                            self.transmit_state_changed.emit('rx')


                    if tci_string[0] == 'vfo':
                        values = tci_string[1].split(",")
                        if values[1] == self.active_vfo and values[0] == self.active_rx:
                            #print("set freq:")
                            self.frequency_changed.emit(values[2].replace(';', ''))

                    # reciev protocol
                            #print("Частота:", values[2])
                    if tci_string[0] == 'protocol':
                        self.version_tci = tci_string[1].split(",")[1].replace(";","")

                        values = tci_string[1].replace(',', ' ')
                        values = values.replace(";", "")

                        #print("Version protocol:", self.version_tci)
                        self.status_changed.emit('•TCI: '+ values)

                    # reciev mode
                    if tci_string[0] == 'modulation':
                         values = tci_string[1].split(",")
                         if values[0] == '0':
                            #if self.version_tci == "1.4":
                            self.mode_changed.emit(values[1].replace(';', ''))
                            self.mode = values[1].replace(';', '')
                            #if self.version_tci == '1.5':
                            #    self.log_form.set_mode_tci(values[1].replace(';', ''))
                            #    self.mode = values[1].replace(';', '')

                            print(">", tci_string)

                    #if tci_string[0] == 'ready':
                    #     print("server: ready;")
                    #     self.log_form.sendMesageToTCI("ready;")


                    # reciev spot call
                    if tci_string[0] == 'clicked_on_spot':
                        print("clicked_on_spot:_>", tci_string)
                        values = tci_string[1].split(",")
                        print("clicked_on_spot:_>", values)
                        call = values[0].strip()
                        band = std.std().get_std_band(values[1].strip().replace(";",""))
                        print("band>", band)
                        mode = std.std().mode_band_plan(band, values[1].strip().replace(";",""))
                        print("mode>", mode)
                        mode = mode[0] if isinstance(mode, tuple) else mode
                        self.spot_clicked.emit(
                            call,
                            values[1].strip().replace(";", ""),
                            mode.lower(),
                        )
                    old_reciever = reciever



                time.sleep(0.002)

            except websocket.WebSocketTimeoutException:
                continue
            except Exception as error:
                print("Tci_reciever: Exception in listen port loop", error)
                self.status_changed.emit('')
                #self.log_form.set_tci_label_found()
                try:
                    self.ws.close()
                    self.ws = websocket.WebSocket()
                    self.ws.settimeout(2)
                    self.ws.connect(self.uri, timeout=3)
                    self.ws.settimeout(2)
                    self.status_changed.emit("•TCI")
                    self.restart_requested.emit()

                except Exception:
                    QThread.sleep(2)
                    # self.log_form.set_tci_label_found()
                    #time.sleep(2)
                    continue

        #else:
            #self.ws.close()
        try:
            self.ws.close()
        except Exception:
            pass


class Tci_sender (QtCore.QObject):

    def __init__(self, uri, tx_flag, log_form, settings_dict):
        super().__init__()
        self.log_form = log_form
        self.settings_dict = settings_dict
        self.tx_flag = tx_flag
        self.uri = uri
        self.ws = websocket.WebSocket()
        self.web_socket_init(self.uri)
        #self.rs_from_tci()

    def web_socket_init(self, uri):
        try:
            self.ws.settimeout(10)
            self.ws.connect(uri, timeout=10)
            # self.ws.send("READY;")
        except Exception:
            self.log_form.set_tci_stat('· TCI', color="#aaaaaa")
            result = traceback.format_exc()
            print("> Tci_sender: Not connect", uri)


    def update_tx_tci(self):
        try:
            self.ws.close()
        except Exception:
            pass
        self.ws = websocket.WebSocket()
        try:
            self.ws.settimeout(10)
            self.ws.connect(self.uri, timeout=10)
        except Exception:
            result = traceback.format_exc()
            print(result)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass

    def send_command(self, string_command):
        if self.tx_flag != "Enable":
            self._send_command(string_command)

    def _send_command(self, string_command):
        try:
            self.ws.send(string_command)
            return True
        except (websocket.WebSocketException, OSError) as error:
            print(f"Exception send command: {string_command}: {error}")
            return False

    def rs_from_tci(self):
        print(f"rs-from-tci: {self.settings_dict['rs-from-tci'], type(self.settings_dict['rs-from-tci'])}")
        if bool(self.settings_dict["rs-from-tci"]):
            if 30 < int(self.settings_dict["rs-time-update"]) < 1000:
                self.send_command("RX_SENSORS_ENABLE:true;")
                print(f"time_update: {self.settings_dict['rs-time-update']}")
            else:
                print(f"time_update not in range (30 - 1000): {self.settings_dict['rs-time-update']}")


    def set_freq(self, freq):
        print("set_freq:", freq)
        freq_string = std.std().std_freq(freq)
        if not freq_string:
            return
        self._send_command(f"VFO:0,0,{freq_string};")

 ### spots

    def set_spot(self, call, freq, color="12711680"):
        #print("TX stat:", self.tx_flag)
        # check enable TX mode
        if self.tx_flag != "Enable":
            string_command = "SPOT:"+str(call)+", ,"+str(freq)+","+color+", ;"
            self._send_command(string_command)

    def del_spot(self, call):
        if self.tx_flag != "Enable":
            string_command = "SPOT_DELETE:"+str(call)+";"
            self._send_command(string_command)

    def change_color_spot(self, call, freq, color="21711680"):
        if self.tx_flag != "Enable":
            string_command = "SPOT_DELETE:"+str(call)+";"
            self._send_command(string_command)
            string_command = "SPOT:"+str(call)+", ,"+str(freq)+","+color+", ;"
            self._send_command(string_command)

##########

    def set_mode(self, reciever, mode):
        string_command = "MODULATION:"+str(reciever)+","+str(mode)+";"
        self._send_command(string_command)
