import sys

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication

import DB_driver
from PySide6.QtCore import Slot, QObject



class Test_initialisation_DB(QObject):

    def __init__(self):
        super().__init__()

        print("Run Test")
        self.test_db = DB_driver.DriverDB("UR4LGA", "UR4LGA")
        self.test_db.connecting_ok_signal.connect(self.connecting_ok)
        self.test_db.connecting_error_signal.connect(self.connecting_error)
        self.test_db.init_connection()

        #self.test_db
        print(self.test_db.callsign)

    @QtCore.Slot(object)
    def connecting_error(self, data):
        print(f"ERROR: {data}")

    @QtCore.Slot(object)
    def connecting_ok(self, data):
        print(f"Connection ok slot {data}")
        answer = self.test_db.get_all_qso()
        print(f"Test all_records\nStatus {answer.status}: {answer.message}\nType: {type(answer)}")
        self.test_db.close_db()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    test = Test_initialisation_DB()

