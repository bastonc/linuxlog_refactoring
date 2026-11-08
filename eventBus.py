from PyQt6.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    _instance = None

   # Signals pack
    update_response = pyqtSignal(object)
    real_time_signal = pyqtSignal(object)
    click_signal = pyqtSignal()
    change_mode_signal = pyqtSignal(object)
    dict_from_base = pyqtSignal(object)
    fill_complite = pyqtSignal()
    result = pyqtSignal(object)
    search_in_db_like_signal = pyqtSignal(object)


    def __new__(cls, *args, **kwargs):
        """Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            super(EventBus, cls._instance).__init__()
        return cls._instance

# Створюємо глобальний екземпляр шини для зручного імпорту
event_bus = EventBus()
