# =============================================================================
#  core/events.py
#  Sorumluluk : Tüm ekranlar arasındaki sinyalleri yöneten EventBus.
# =============================================================================

from PyQt5.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    """
    Uygulama genelinde modüllerin birbirini tetiklemesi için kullanılan global Signal/Slot merkezi.
    Singleton (Tekil) tasarım deseni ile çalışır.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EventBus, cls).__new__(cls, *args, **kwargs)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        super().__init__()
        self.__initialized = True

    # ── Sinyaller ─────────────────────────────────────────────────────────────
    urun_degisti = pyqtSignal()
    stok_degisti = pyqtSignal()
    satis_yapildi = pyqtSignal()
    islem_silindi = pyqtSignal()

# Global nesne
event_bus = EventBus()
