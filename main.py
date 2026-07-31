# =============================================================================
#  main.py – Anıl Oto Otomasyon Sistemi
#  Giriş Noktası: Uygulamayı başlatır, veritabanını hazırlar, pencereyi açar.
#
#  Mimari : 3 Katmanlı Modüler Yapı
#  ┌─────────────────────────────────────────────────────────┐
#  │  views/          → Yalnızca PyQt5 / qfluentwidgets UI  │
#  │  services/       → İş mantığı (kod üretme, dosya vb.)  │
#  │  database/       → SQLite sorguları ve bağlantı         │
#  │  constants.py    → Uygulama geneli sabitler             │
#  └─────────────────────────────────────────────────────────┘
# =============================================================================

import sys
import os
import traceback
from PyQt5.QtCore import Qt, QSharedMemory
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from qfluentwidgets import setTheme, Theme

from constants import BG_COLOR, IDX_LOGIN, IDX_DASH, IDX_STOCK, IDX_FINANCE, IDX_ORDER, IDX_CRITICAL, get_data_path
from database.db_manager import DbManager
from views.login_screen import LoginScreen
from views.dashboard_screen import DashboardScreen
from views.stock_screen import StockScreen
from views.finance_screen import FinanceScreen
from views.order_screen import OrderScreen
from views.kritik_urunler import KritikUrunlerScreen
from views.islem_gecmisi_dialog import IslemGecmisiDialog
from views.islem_gecmisi_dialog import IslemGecmisiDialog


class MainWindow(QWidget):
    """Ana uygulama penceresi – ekranlar arası geçişi yönetir."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anıl Oto – Otomasyon Sistemi")
        self.resize(1150, 720)
        self.setMinimumSize(950, 600)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.stack = QStackedWidget(self)
        self.stack.setAttribute(Qt.WA_StyledBackground, True)
        self.stack.setStyleSheet(f"background-color: {BG_COLOR};")

        # ── Ekranları oluştur ────────────────────────────────────────────────
        self.screen_login   = LoginScreen(on_success=self._goto_dashboard)
        self.screen_dash    = DashboardScreen(
            go_stock=self._goto_stock,
            go_finance=self._goto_finance,
            go_order=self._goto_order,
            go_critical_stock=self._goto_critical_stock,
            go_islem_gecmisi=self._ac_islem_gecmisi,
        )
        self.screen_stock   = StockScreen(go_back=self._goto_dashboard)
        self.screen_finance = FinanceScreen(
            go_back=self._goto_dashboard,
            go_stock=self._goto_stock,
            go_order=self._goto_order,
        )
        self.screen_order   = OrderScreen(
            go_back=self._goto_dashboard,
            go_stock=self._goto_stock,
            go_finance=self._goto_finance,
        )
        self.screen_critical = KritikUrunlerScreen(go_back=self._goto_dashboard)

        # ── Stack'e ekle ─────────────────────────────────────────────────────
        for screen in (
            self.screen_login, self.screen_dash,
            self.screen_stock, self.screen_finance, self.screen_order,
            self.screen_critical
        ):
            self.stack.addWidget(screen)

        self.stack.setCurrentIndex(IDX_LOGIN)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.stack)

    # ── Ekran Geçişleri ───────────────────────────────────────────────────────

    def _switch(self, index: int):
        # Stok ekranına her geçişte veritabanını taze çek
        if index == IDX_STOCK:
            self.screen_stock.verileri_yukle()
        elif index == IDX_CRITICAL:
            self.screen_critical.verileri_yukle()
        elif index == IDX_FINANCE:
            self.screen_finance.verileri_yukle()
        self.stack.setCurrentIndex(index)

    def _goto_dashboard(self): self._switch(IDX_DASH)
    def _goto_stock(self):     self._switch(IDX_STOCK)
    def _goto_finance(self):   self._switch(IDX_FINANCE)
    def _goto_order(self):     self._switch(IDX_ORDER)
    
    def _goto_critical_stock(self):
        self._switch(IDX_CRITICAL)

    def _ac_islem_gecmisi(self):
        """İşlem Geçmişi dialogunu modal olarak açar."""
        dialog = IslemGecmisiDialog(parent=self)
        dialog.exec_()

    def closeEvent(self, event):
        """Uygulama kapatılırken temizlik yapar ve süreci sonlandırır."""
        # Varsa açık bağlantıları (pool vb) temizlemek için burada kod çalıştırılabilir.
        # SQLite with closing() kullandığı için ekstra DbManager kapatmasına gerek yok,
        # ancak sürecin tam sonlanmasını garanti ediyoruz:
        event.accept()
        QApplication.quit()
        sys.exit(0)


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Beklenmedik hataları yakalar, log dosyasına yazar ve kullanıcıya gösterir."""
    # Hata metnini oluştur
    hata_metni = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Log dosyasına yaz
    log_yolu = os.path.join(get_data_path(), "crash_log.txt")
    with open(log_yolu, "a", encoding="utf-8") as f:
        import datetime
        f.write(f"\n--- Çökme Raporu: {datetime.datetime.now()} ---\n")
        f.write(hata_metni)
        f.write("\n")
        
    # Kullanıcıya QMessageBox ile göster
    # (Eğer QApplication henüz oluşturulmadıysa QMessageBox çalışmayabilir, ancak genellikle çalışır haldeyken hata alırız)
    if QApplication.instance():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Kritik Hata")
        msg.setText("Uygulamada beklenmedik bir hata oluştu!")
        msg.setInformativeText(f"Hata detayı '{log_yolu}' dosyasına kaydedildi.\n\nHata mesajı: {exc_value}")
        msg.exec_()
    else:
        print(f"Kritik Hata: {exc_value}\nLog: {log_yolu}")
        
    sys.exit(1)


if __name__ == "__main__":
    # Global hata yakalayıcıyı ayarla
    sys.excepthook = global_exception_handler

    # HiDPI Desteği
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Tek Kopya (Single Instance) Kontrolü
    shared_mem = QSharedMemory("Traktor_Mete_Single_Instance")
    
    # Eğer daha önce çökme yaşandıysa hafızada takılı kalmış olabilir, temizlemeyi dene:
    if shared_mem.attach():
        shared_mem.detach()
        
    if not shared_mem.create(1):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Uyarı")
        msg.setText("Uygulama zaten çalışıyor!")
        msg.exec_()
        sys.exit(0)

    DbManager.baslat()          # Veritabanı + tablolar + örnek veri
    setTheme(Theme.LIGHT)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())