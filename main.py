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
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget
from qfluentwidgets import setTheme, Theme

from constants import BG_COLOR, IDX_LOGIN, IDX_DASH, IDX_STOCK, IDX_FINANCE, IDX_ORDER, IDX_CRITICAL
from database.db_manager import DbManager
from views.login_screen import LoginScreen
from views.dashboard_screen import DashboardScreen
from views.stock_screen import StockScreen
from views.placeholder_screens import FinanceScreen
from views.order_screen import OrderScreen
from views.kritik_urunler import KritikUrunlerScreen
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


if __name__ == "__main__":
    DbManager.baslat()          # Veritabanı + tablolar + örnek veri
    setTheme(Theme.LIGHT)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())