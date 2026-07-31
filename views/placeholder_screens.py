# =============================================================================
#  views/placeholder_screens.py
#  Sorumluluk : Geliştirme aşamasındaki modül ekranları.
#               FinanceScreen (Ekran 3) ve OrderScreen (Ekran 4).
# =============================================================================

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import TitleLabel, BodyLabel, PushButton
from constants import BG_COLOR, TEXT_MUTED


class FinanceScreen(QWidget):
    """Gelir & Gider Takibi – geliştirme aşamasında."""

    def __init__(self, go_back, go_stock, go_order, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 20, 30, 30)
        root.setSpacing(12)

        # ── Navigasyon Bar ────────────────────────────────────────────────────
        nav = QHBoxLayout()
        btn_geri = PushButton("← Ana Menü")
        btn_geri.setFixedHeight(38)
        btn_geri.setFixedWidth(130)
        btn_geri.clicked.connect(go_back)
        nav.addWidget(btn_geri)
        nav.addStretch()

        btn_stok = PushButton("📦 Stok")
        btn_stok.setFixedHeight(38)
        btn_stok.clicked.connect(go_stock)
        nav.addWidget(btn_stok)

        btn_siparis = PushButton("Sipariş ›")
        btn_siparis.setFixedHeight(38)
        btn_siparis.clicked.connect(go_order)
        nav.addWidget(btn_siparis)

        root.addLayout(nav)
        root.addStretch(1)

        icon_lbl = QLabel("💰")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 80px; background: transparent; margin-bottom: 10px;")
        root.addWidget(icon_lbl)

        title_lbl = TitleLabel("Gelir & Gider Takibi")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold;")
        root.addWidget(title_lbl)

        body_lbl = BodyLabel("Bu modül çok yakında aktif edilecektir.")
        body_lbl.setAlignment(Qt.AlignCenter)
        body_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; margin-top: 8px;")
        root.addWidget(body_lbl)
        root.addStretch(2)


class OrderScreen(QWidget):
    """Yeni Sipariş Oluştur – geliştirme aşamasında."""

    def __init__(self, go_back, go_stock, go_finance, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 20, 30, 30)
        root.setSpacing(12)

        # ── Navigasyon Bar ────────────────────────────────────────────────────
        nav = QHBoxLayout()
        btn_geri = PushButton("← Ana Menü")
        btn_geri.setFixedHeight(38)
        btn_geri.setFixedWidth(130)
        btn_geri.clicked.connect(go_back)
        nav.addWidget(btn_geri)
        nav.addStretch()

        btn_stok = PushButton("📦 Stok")
        btn_stok.setFixedHeight(38)
        btn_stok.clicked.connect(go_stock)
        nav.addWidget(btn_stok)

        btn_finance = PushButton("‹ Gelir/Gider")
        btn_finance.setFixedHeight(38)
        btn_finance.clicked.connect(go_finance)
        nav.addWidget(btn_finance)

        root.addLayout(nav)
        root.addStretch(1)

        icon_lbl = QLabel("🛒")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 80px; background: transparent; margin-bottom: 10px;")
        root.addWidget(icon_lbl)

        title_lbl = TitleLabel("Yeni Sipariş Oluştur")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold;")
        root.addWidget(title_lbl)

        body_lbl = BodyLabel("Bu modül çok yakında aktif edilecektir.")
        body_lbl.setAlignment(Qt.AlignCenter)
        body_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; margin-top: 8px;")
        root.addWidget(body_lbl)
        root.addStretch(2)
