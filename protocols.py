from PyQt6.QtCore import QObject


class Kenwood(QObject):
    def __init__(self, settingsDict, parent_window, serial_port):
        super().__init__()
        self.settingsDict = settingsDict
        self.parent_window = parent_window
        self.ser = serial_port

    def get_freq_mod_list(self):
        return [b"FA;", b"MD;"]

    def decoder_data(self, data_byte: bytes):
        try:
            response = data_byte.decode("ascii").strip().rstrip(";")
        except (AttributeError, UnicodeDecodeError):
            return

        if response.startswith("FA"):
            frequency = response[2:]
            if frequency.isdigit() and len(frequency) <= 11:
                self.parent_window.set_freq(frequency.lstrip("0") or "0")
            return

        mode_by_code = {
            "1": "lsb", "2": "usb", "3": "cw", "4": "nfm",
            "5": "am", "6": "digl", "7": "cw", "9": "digu",
        }
        if response.startswith("MD"):
            mode = mode_by_code.get(response[2:])
            if mode:
                self.parent_window.set_mode_tci(mode)

    def set_freq_rig(self, freq):
        freq = str(freq)
        if not freq.isdigit():
            return
        freq = freq.zfill(11)
        self.ser.write(b'FA' + freq.encode("utf-8") + b";")

    def set_mode_rig(self, mode):
        mode_code = {
            "LSB": "1", "USB": "2", "CW": "3", "NFM": "4",
            "AM": "5", "DIGL": "6", "DIGU": "9", "ERROR": "1",
        }.get(str(mode).upper())
        if mode_code:
            self.ser.write(f"MD{mode_code};".encode("ascii"))

class Icom(QObject):
    def __init__(self, settingsDict, parent_window, serial_port):
        super().__init__()
        self.settingsDict = settingsDict
        self.parent_window = parent_window
        self.ser = serial_port

    def get_freq_mod_list(self):
        # First command requests frequency; second requests operating mode.
        return [b"FEFE6C0003FD", b"FEFE6C0004FD"]

    def freq_to_bcd(self, i):
        frequency = str(i).strip()
        if not frequency.isdigit() or len(frequency) > 10:
            raise ValueError("Icom frequency must be an integer number of hertz")

        digits = frequency.zfill(10)
        # CI-V represents frequency as five packed-BCD bytes, least
        # significant byte first. Return hex text because this CAT profile
        # sends the command as an ASCII hexadecimal string.
        return "".join(digits[index:index + 2] for index in range(8, -1, -2))

    def decoder_data(self, data_byte: bytes):
        try:
            response = data_byte.decode("ascii").strip().upper()
        except (AttributeError, UnicodeDecodeError):
            return
        if not response.startswith("FEFE6C00") or not response.endswith("FD"):
            return

        command = response[8:10]
        payload = response[10:-2]
        if command == "03" and len(payload) == 10:
            if not all(character in "0123456789" for character in payload):
                return
            frequency_digits = "".join(payload[index:index + 2] for index in range(8, -1, -2))
            frequency = int(frequency_digits)
            self.parent_window.set_freq(str(frequency))
        elif command == "04" and len(payload) >= 2:
            mode_by_code = {
                "00": "lsb", "01": "usb", "03": "cw", "05": "nfm",
                "02": "am", "08": "digl", "11": "digl", "12": "digl", "04": "digl",
            }
            mode = mode_by_code.get(payload[:2])
            if mode:
                self.parent_window.set_mode_tci(mode)

    def set_freq_rig(self, freq):
        freq_in_hex = self.freq_to_bcd(freq)
        self.ser.write(b'FEFE6C0000' + freq_in_hex.encode("utf-8") + b"FD")

    def set_mode_rig(self, mode):

        mode_bytes = {
            "LSB": b"00", "USB": b"01", "CW": b"03",
            "NFM": b"05", "AM": b"02",
        }.get(str(mode).upper())
        if mode_bytes is not None:
            self.ser.write(b"FEFE6C0004" + mode_bytes + b"FD")
