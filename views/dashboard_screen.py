# =============================================================================
#  views/dashboard_screen.py
#  Sorumluluk : Ana menü (Dashboard) ekranı – Modül seçim kartları + KPI.
# =============================================================================

import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from qfluentwidgets import (
    SimpleCardWidget, StrongBodyLabel, CaptionLabel, BodyLabel,
    LargeTitleLabel, IconWidget, FluentIcon, CardWidget
)
from constants import BG_COLOR, CARD_BG, TEXT_MUTED, IKON_KLASORU, para_formatla
from services.urun_service import UrunService


# ── KPI Kartı ─────────────────────────────────────────────────────────────────

class KpiKart(CardWidget):
    """Tek bir sayısal gösterge kartı (KPI)."""

    def __init__(self, baslik: str, deger: str, renk: str, ikon: FluentIcon, on_click=None, parent=None):
        super().__init__(parent)
        self.on_click = on_click
        if self.on_click:
            self.setCursor(Qt.PointingHandCursor)
            
        self.setFixedHeight(80)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(14)

        # Sol: İkon
        ikon_lbl = IconWidget(ikon)
        ikon_lbl.setFixedSize(36, 36)
        layout.addWidget(ikon_lbl)

        # Sağ: Başlık + Değer
        metin_col = QVBoxLayout()
        metin_col.setSpacing(2)

        deger_lbl = StrongBodyLabel(deger)
        deger_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {renk};")
        metin_col.addWidget(deger_lbl)

        baslik_lbl = CaptionLabel(baslik)
        baslik_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        metin_col.addWidget(baslik_lbl)

        layout.addLayout(metin_col)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.on_click:
            self.on_click()
        super().mousePressEvent(event)


# ── Modül Seçim Kartı ─────────────────────────────────────────────────────────

class DashboardCard(SimpleCardWidget):
    """Modül seçim kartı."""

    def __init__(self, icon_filename, fallback_icon, title, subtitle, on_click, parent=None):
        super().__init__(parent)
        self.on_click = on_click
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(170)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            f"SimpleCardWidget {{ background-color: {CARD_BG}; border-radius: 14px; }}"
            "SimpleCardWidget:hover { background-color: #F0F6FF; }"
        )

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(18)
        self._shadow.setYOffset(4)
        self._shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(self._shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(8)

        # ── İkon alanı ────────────────────────────────────────────────────────
        icon_path = os.path.join(IKON_KLASORU, icon_filename)
        icon_container = QHBoxLayout()
        icon_container.setAlignment(Qt.AlignCenter)

        if os.path.exists(icon_path):
            img_lbl = QLabel()
            pixmap = QPixmap(icon_path)
            pixmap = pixmap.scaled(54, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_lbl.setPixmap(pixmap)
            img_lbl.setAlignment(Qt.AlignCenter)
            img_lbl.setStyleSheet("background: transparent;")
            icon_container.addWidget(img_lbl)
        else:
            icon_widget = IconWidget(fallback_icon)
            icon_widget.setFixedSize(54, 54)
            icon_container.addWidget(icon_widget)

        layout.addLayout(icon_container)

        t_lbl = StrongBodyLabel(title)
        t_lbl.setAlignment(Qt.AlignCenter)
        t_lbl.setWordWrap(True)
        layout.addWidget(t_lbl)

        s_lbl = CaptionLabel(subtitle)
        s_lbl.setAlignment(Qt.AlignCenter)
        s_lbl.setWordWrap(True)
        s_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        layout.addWidget(s_lbl)
        layout.addStretch()

    def enterEvent(self, event):
        self._shadow.setBlurRadius(32)
        self._shadow.setColor(QColor(0, 120, 212, 55))
        self._shadow.setYOffset(8)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(18)
        self._shadow.setColor(QColor(0, 0, 0, 30))
        self._shadow.setYOffset(4)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_click()
        super().mousePressEvent(event)


# ── Ana Dashboard ─────────────────────────────────────────────────────────────

class DashboardScreen(QWidget):
    """Hoş geldiniz / modül seçim ekranı."""

    def __init__(self, go_stock, go_finance, go_order, go_critical_stock=None, go_islem_gecmisi=None, parent=None):
        super().__init__(parent)
        self._service = UrunService()
        self._go_islem_gecmisi = go_islem_gecmisi
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(50, 40, 50, 50)
        root.setSpacing(0)

        # ── Başlık ────────────────────────────────────────────────────────────
        title = LargeTitleLabel("Depo ve Stok Kontrol Paneli")
        root.addWidget(title)

        sub = BodyLabel("Sistemdeki güncel stok varlıklarını, kritik uyarıları ve operasyonel modülleri buradan yönetebilirsiniz.")
        sub.setStyleSheet(f"color: {TEXT_MUTED};")
        root.addWidget(sub)
        root.addSpacing(24)

        # ── KPI Satırı ────────────────────────────────────────────────────────
        self._kpi_satir = QHBoxLayout()
        self._kpi_satir.setSpacing(20)

        # Placeholder KPI kartları (sonra güncellenir)
        self._kpi_urun  = KpiKart("Toplam Ürün Çeşidi", "—", "#1D4ED8", FluentIcon.MARKET)
        self._kpi_deger = KpiKart("Depo Varlık Değeri",  "—", "#065F46", FluentIcon.PIE_SINGLE)
        self._kpi_kritik = KpiKart("Kritik Stok",        "—", "#991B1B", FluentIcon.FLAG, on_click=go_critical_stock)

        for kpi in (self._kpi_urun, self._kpi_deger, self._kpi_kritik):
            self._kpi_satir.addWidget(kpi, stretch=1)

        root.addLayout(self._kpi_satir)
        root.addSpacing(32)

        # ── Modül Kartları ────────────────────────────────────────────────────
        card_row = QHBoxLayout()
        card_row.setSpacing(20)

        cards_data = [
            ("stok.png",    FluentIcon.MARKET,        "Ürün & Stok\nYönetimi",    "Stok seviyelerini\nyönet ve takip et.",   go_stock),
            ("finans.png",  FluentIcon.PIE_SINGLE,    "Gelir & Gider\nTakibi",    "Finansal hareketleri\ngörüntüle.",          go_finance),
            ("siparis.png", FluentIcon.SHOPPING_CART, "Yeni Sipariş\nOluştur",   "Hızlıca yeni bir\nsipariş oluştur.",     go_order),
            ("gecmis.png",  FluentIcon.HISTORY,       "İşlem\nGeçmişi",          "Tüm stok hareketlerini\nfiltreli görüntüle.", self._go_islem_gecmisi),
        ]

        for icon_file, fallback, ttl, stl, cb in cards_data:
            card_row.addWidget(DashboardCard(icon_file, fallback, ttl, stl, cb), stretch=1)

        root.addLayout(card_row)
        root.addStretch()

        # İlk KPI yüklemesini yap
        self.kpi_yenile()

    def kpi_yenile(self):
        """Veritabanından güncel KPI verilerini çekip kartları günceller."""
        try:
            kpi = self._service.kpi_getir()
            toplam  = kpi.get("toplam_urun", 0)
            deger   = kpi.get("depo_degeri", 0.0)
            kritik  = kpi.get("kritik_stok", 0)

            # Başlık label'larını güncelle (ilk StrongBodyLabel)
            self._kpi_urun_lbl(str(toplam))
            self._kpi_deger_lbl(para_formatla(deger))
            self._kpi_kritik_lbl(f"{kritik} ürün")
        except Exception:
            pass  # Hata durumunda sessizce geç

    def _kpi_urun_lbl(self, text: str):
        self._kpi_urun.findChild(StrongBodyLabel).setText(text)

    def _kpi_deger_lbl(self, text: str):
        self._kpi_deger.findChild(StrongBodyLabel).setText(text)

    def _kpi_kritik_lbl(self, text: str):
        self._kpi_kritik.findChild(StrongBodyLabel).setText(text)
