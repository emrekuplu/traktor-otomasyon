# =============================================================================
#  views/filtre_vitrini.py
#  Sorumluluk : "Filtre Vitrini" – Alt kategori (Hava, Yağ vb.) seçim ekranı.
# =============================================================================

import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QScrollArea, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from qfluentwidgets import (
    SimpleCardWidget, StrongBodyLabel, CaptionLabel,
    LargeTitleLabel, PushButton, IconWidget, FluentIcon
)
from constants import BG_COLOR, TEXT_MUTED, get_resource_path


class FiltreKarti(SimpleCardWidget):
    """Tek bir filtre tipini temsil eden vitrin kartı."""

    def __init__(self, filtre_adi: str, subtitle: str, icon_path: str, on_click, parent=None):
        super().__init__(parent)
        self._on_click = on_click
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(320, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Hover efektinde border rengini canlandırarak modern bir görünüm katıyoruz.
        self.setStyleSheet(
            "SimpleCardWidget { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E5E7EB; }"
            "SimpleCardWidget:hover { background-color: #F9FAFB; border: 1.5px solid #3B82F6; }"
        )

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setYOffset(6)
        self._shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(self._shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(12)

        # ── İkon Alanı ───────────────────────────────────────────────────────
        if os.path.exists(icon_path):
            self.icon_lbl = QLabel()
            self.icon_lbl.setAlignment(Qt.AlignCenter)
            self.icon_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            pixmap = QPixmap(icon_path).scaled(
                80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.icon_lbl.setPixmap(pixmap)
            self.icon_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(self.icon_lbl)
        else:
            # Görsel bulunamazsa şık bir varsayılan FluentIcon kullan
            self.icon_widget = IconWidget(FluentIcon.SETTING)
            self.icon_widget.setFixedSize(64, 64)
            # İkonu merkeze hizala
            icon_layout = QHBoxLayout()
            icon_layout.addStretch()
            icon_layout.addWidget(self.icon_widget)
            icon_layout.addStretch()
            layout.addLayout(icon_layout)

        # ── Başlık Alanı ─────────────────────────────────────────────────────
        ad_lbl = StrongBodyLabel(filtre_adi)
        ad_lbl.setAlignment(Qt.AlignCenter)
        ad_lbl.setWordWrap(True)
        ad_lbl.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #1F2937; background: transparent;"
        )
        layout.addWidget(ad_lbl)

        # ── Alt Başlık (Subtitle) Alanı ──────────────────────────────────────
        sub_lbl = CaptionLabel(subtitle)
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(
            "font-size: 13px; color: #6B7280; background: transparent;"
        )
        layout.addWidget(sub_lbl)
        
        layout.addStretch()

    def enterEvent(self, event):
        self._shadow.setBlurRadius(26)
        self._shadow.setColor(QColor(0, 0, 0, 50))
        self._shadow.setYOffset(8)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(20)
        self._shadow.setColor(QColor(0, 0, 0, 30))
        self._shadow.setYOffset(6)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_click()
        super().mousePressEvent(event)


class FiltreVitrini(QWidget):
    """
    Filtre Vitrini ekranı.
    Marka vitrinindeki "Filtreler" kutusuna basılınca açılır.
    """

    def __init__(self, go_back, on_filtre_sec, parent=None):
        super().__init__(parent)
        self._go_back = go_back
        self._on_filtre_sec = on_filtre_sec

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(18)

        # ── Üst Bar ──────────────────────────────────────────────────────────
        top_bar = QHBoxLayout()
        btn_geri = PushButton("⬅ Ana Vitrine Dön")
        btn_geri.setFixedHeight(38)
        btn_geri.clicked.connect(go_back)
        top_bar.addWidget(btn_geri)
        top_bar.addStretch()
        root.addLayout(top_bar)

        # ── Başlık ───────────────────────────────────────────────────────────
        baslik = LargeTitleLabel("Filtre Çeşitleri")
        baslik.setStyleSheet("font-family: 'Segoe UI', Arial, sans-serif; font-weight: bold; color: #1A1A2E;")
        root.addWidget(baslik)

        alt_baslik = CaptionLabel("Görüntülemek istediğiniz filtre tipini seçiniz.")
        alt_baslik.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px;")
        root.addWidget(alt_baslik)

        # ── Scroll Area ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea, #qt_scrollarea_viewport {{ border: none; background-color: {BG_COLOR}; }}"
        )

        icerik = QWidget()
        icerik.setAttribute(Qt.WA_StyledBackground, True)
        icerik.setStyleSheet(f"background-color: {BG_COLOR};")
        
        # Grid Layout 2x2 düzeni için
        grid_layout = QGridLayout(icerik)
        grid_layout.setSpacing(24)
        grid_layout.setContentsMargins(4, 24, 4, 24)

        scroll.setWidget(icerik)
        root.addWidget(scroll)

        # ── Filtre Kartları ───────────────────────────────────────────────────
        filtreler = [
            ("Hava Filtresi", "Motor ve kabin içi hava akış sistemleri", get_resource_path("resources/icons/filters/air_filter.png")),
            ("Yağ Filtresi", "Motor karter ve şanzıman yağ filtreleri", get_resource_path("resources/icons/filters/oil_filter.png")),
            ("Mazot Filtresi", "Yakıt enjeksiyon ve ayırıcı filtreler", get_resource_path("resources/icons/filters/fuel_filter.png")),
            ("Hidrolik Filtresi", "Hidrolik lift ve sistem filtreleri", get_resource_path("resources/icons/filters/hydraulic_filter.png"))
        ]

        for i, (ad, subtitle, icon_path) in enumerate(filtreler):
            kart = FiltreKarti(
                filtre_adi=ad,
                subtitle=subtitle,
                icon_path=icon_path,
                on_click=lambda f=ad: self._on_filtre_sec(f)
            )
            satir = i // 2
            sutun = i % 2
            grid_layout.addWidget(kart, satir, sutun)
