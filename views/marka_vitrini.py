# =============================================================================
#  views/marka_vitrini.py
#  Sorumluluk : "Marka Vitrini" – 1. Sayfa
#               9 ana marka + Diğer + Tüm Markalar kutularını grid'de gösterir.
#               Bir marka seçildiğinde on_marka_sec(marka) callback'i çağrılır.
# =============================================================================

import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QScrollArea, QFrame
)
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from qfluentwidgets import (
    SimpleCardWidget, StrongBodyLabel, CaptionLabel,
    SubtitleLabel, PushButton, SearchLineEdit
)
from constants import (
    BG_COLOR, CARD_BG, TEXT_MUTED,
    ANA_MARKALAR, MARKA_TEMA, VITRIN_DIGER_RENK, VITRIN_TUM_RENK,
    LOGOLAR_KLASORU
)
from services.urun_service import UrunService


class MarkaKarti(SimpleCardWidget):
    """Tek bir markayı temsil eden tıklanabilir vitrin kartı."""

    def __init__(self, marka_adi: str, emoji: str,
                 bg: str, fg: str, urun_sayisi: int,
                 on_click, parent=None):
        super().__init__(parent)
        self.marka_adi_val = marka_adi
        self._on_click = on_click
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(280, 200)  # Daha büyük ve dikkat çekici boyutlar
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Beyaz arkaplan ile şeffaflık izlerini gizleyip uyumlu hale getiriyoruz
        self.setStyleSheet(
            f"SimpleCardWidget {{ background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E5E7EB; }}"
            f"SimpleCardWidget:hover {{ background-color: #F9FAFB; border: 1px solid #D1D5DB; }}"
        )

        # Gölge efekti
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setYOffset(6)
        self._shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(self._shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)

        # ── Logo veya Emoji İkonu ─────────────────────────────────────────────
        dosya_adi = marka_adi.lower().replace(" ", "_").replace("ç", "c").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ı", "i") + ".png"
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_yolu = os.path.join(base_dir, LOGOLAR_KLASORU, dosya_adi)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if os.path.exists(logo_yolu):
            pixmap = QPixmap(logo_yolu)
            if not pixmap.isNull():
                # Logo kartın %50'sini kapsayacak şekilde 2-3 kat büyütüldü
                pixmap = pixmap.scaled(200, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(pixmap)
            else:
                icon_lbl.setText(emoji)
                icon_lbl.setStyleSheet("font-size: 72px; background: transparent;")
        else:
            # Logo yoksa emoji kullan (büyük bir varsayılan yapı)
            icon_lbl.setText(emoji)
            icon_lbl.setStyleSheet("font-size: 72px; background: transparent;")

        layout.addWidget(icon_lbl)

        # ── Marka Adı ve Sayı ────────────────────────────────────────────────
        ad_lbl = StrongBodyLabel(marka_adi)
        ad_lbl.setAlignment(Qt.AlignCenter)
        ad_lbl.setWordWrap(True)
        ad_lbl.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1F2937; background: transparent;"
        )
        layout.addWidget(ad_lbl)

        sayi_text = f"{urun_sayisi} ürün" if urun_sayisi > 0 else "Ürün yok"
        sayi_lbl = CaptionLabel(sayi_text)
        sayi_lbl.setAlignment(Qt.AlignCenter)
        sayi_lbl.setStyleSheet(
            "color: #6B7280; background: transparent; font-size: 13px;"
        )
        layout.addWidget(sayi_lbl)

    @staticmethod
    def _darken(hex_color: str) -> str:
        """Hover için rengi biraz koyulaştırır."""
        try:
            r = max(0, int(hex_color[1:3], 16) - 15)
            g = max(0, int(hex_color[3:5], 16) - 15)
            b = max(0, int(hex_color[5:7], 16) - 15)
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return hex_color

    def enterEvent(self, event):
        self._shadow.setBlurRadius(26)
        self._shadow.setColor(QColor(0, 0, 0, 50))
        self._shadow.setYOffset(8)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(14)
        self._shadow.setColor(QColor(0, 0, 0, 28))
        self._shadow.setYOffset(4)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_click()
        super().mousePressEvent(event)


class MarkaVitrini(QWidget):
    """
    Marka Vitrini – StockScreen'in 1. sayfası.
    9 ana marka + Diğer + Tüm Markalar kutularını gösterir.
    """

    SUTUN_SAYISI = 3   # Grid sütun sayısı

    def __init__(self, go_back, on_marka_sec, on_filtre_vitrini_sec, parent=None):
        """
        on_marka_sec(marka: str | None) callback:
          - marka = "Tüm Markalar"  → hepsini göster
          - marka = "Diğer Markalar" → diğerleri
          - marka = "Fiat" vb.       → o markayı filtrele
        """
        super().__init__(parent)
        self._go_back = go_back
        self._on_marka_sec = on_marka_sec
        self._on_filtre_vitrini_sec = on_filtre_vitrini_sec
        self._service = UrunService()

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 10, 28, 20)
        root.setSpacing(10)

        # ── Header / Navbar Alanı ──────────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setAttribute(Qt.WA_StyledBackground, True)
        header_frame.setStyleSheet("""
            QFrame#HeaderFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
                border-radius: 10px;
            }
        """)
        
        # Hafif gölge efekti
        shadow = QGraphicsDropShadowEffect(header_frame)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 3)
        header_frame.setGraphicsEffect(shadow)

        top_bar = QHBoxLayout(header_frame)
        top_bar.setContentsMargins(20, 12, 20, 12)  # İç boşluklar (padding)
        top_bar.setSpacing(24)  # Buton ile başlık arası boşluk
        top_bar.setAlignment(Qt.AlignVCenter)

        btn_geri = PushButton("← Ana Menü")
        btn_geri.setFixedHeight(38)
        btn_geri.clicked.connect(go_back)
        top_bar.addWidget(btn_geri, alignment=Qt.AlignVCenter)

        baslik = SubtitleLabel("Marka Vitrini")
        baslik.setStyleSheet("font-weight: bold; color: #1A1A2E; background: transparent;")
        top_bar.addWidget(baslik, alignment=Qt.AlignVCenter)

        top_bar.addStretch()

        self.arama_kutusu = SearchLineEdit()
        self.arama_kutusu.setPlaceholderText("Marka filtrele...")
        self.arama_kutusu.setFixedWidth(280)
        self.arama_kutusu.setFixedHeight(38)
        self.arama_kutusu.setStyleSheet("""
            SearchLineEdit {
                border-radius: 19px;
                border: 1px solid #D1D5DB;
                background-color: #F9FAFB;
                padding-left: 12px;
            }
            SearchLineEdit:focus {
                border: 1.5px solid #3B82F6;
                background-color: #FFFFFF;
            }
        """)
        self.arama_kutusu.textChanged.connect(self._filtrele)
        top_bar.addWidget(self.arama_kutusu, alignment=Qt.AlignVCenter)

        root.addWidget(header_frame)

        # ── Scroll Area ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea, #qt_scrollarea_viewport {{ border: none; background-color: {BG_COLOR}; }}"
        )

        self._icerik = QWidget()
        self._icerik.setAttribute(Qt.WA_StyledBackground, True)
        self._icerik.setStyleSheet(f"background-color: {BG_COLOR};")
        self._grid_layout = QGridLayout(self._icerik)
        self._grid_layout.setSpacing(18)
        self._grid_layout.setContentsMargins(4, 8, 4, 24)

        scroll.setWidget(self._icerik)
        root.addWidget(scroll)

        self.yenile()

    def _filtrele(self, metin):
        metin = metin.lower()
        for i in range(self._grid_layout.count()):
            item = self._grid_layout.itemAt(i)
            if item and item.widget():
                kart = item.widget()
                if hasattr(kart, "marka_adi_val"):
                    if metin in kart.marka_adi_val.lower():
                        kart.show()
                    else:
                        kart.hide()

    def yenile(self):
        """Vitrin kartlarını veritabanındaki sayılarla günceller."""
        # Mevcut widget'ları temizle
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sayilar = self._service.marka_sayilarini_getir()

        # Tüm ürün sayısı
        toplam = sum(sayilar.values())

        # Diğer markalar sayısı (ana markalar dışındakiler)
        diger_sayisi = sum(
            v for k, v in sayilar.items() if k not in ANA_MARKALAR
        )

        # ── 9 Ana Marka (3'lü grid) ───────────────────────────────────────────
        for i, marka in enumerate(ANA_MARKALAR):
            bg, fg, emoji = MARKA_TEMA.get(marka, (CARD_BG, "#1A1A2E", "🚜"))
            sayi = sayilar.get(marka, 0)
            kart = MarkaKarti(
                marka_adi=marka,
                emoji=emoji,
                bg=bg,
                fg=fg,
                urun_sayisi=sayi,
                on_click=lambda m=marka: self._on_marka_sec(m),
            )
            satir = i // self.SUTUN_SAYISI
            sutun = i % self.SUTUN_SAYISI
            self._grid_layout.addWidget(kart, satir, sutun)

        # ── Özel Kutular Satırı ────────────────────────────────────────────────
        ozel_satir = (len(ANA_MARKALAR) + self.SUTUN_SAYISI - 1) // self.SUTUN_SAYISI

        bg_d, fg_d, em_d = VITRIN_DIGER_RENK
        kart_diger = MarkaKarti(
            marka_adi="Diğer Markalar",
            emoji=em_d,
            bg=bg_d,
            fg=fg_d,
            urun_sayisi=diger_sayisi,
            on_click=lambda: self._on_marka_sec("Diğer Markalar"),
        )

        bg_t, fg_t, em_t = VITRIN_TUM_RENK
        kart_tum = MarkaKarti(
            marka_adi="Tüm Markalar",
            emoji=em_t,
            bg=bg_t,
            fg=fg_t,
            urun_sayisi=toplam,
            on_click=lambda: self._on_marka_sec("Tüm Markalar"),
        )

        kart_filtreler = MarkaKarti(
            marka_adi="⚙️ Filtre Çeşitleri",
            emoji="⚙️",
            bg="#fef3c7", # Dikkat çekici sıcak bir renk
            fg="#92400e",
            urun_sayisi=0, # Sayı göstermeye gerek yok
            on_click=self._on_filtre_vitrini_sec,
        )

        self._grid_layout.addWidget(kart_diger, ozel_satir, 0)
        self._grid_layout.addWidget(kart_tum,   ozel_satir, 1)
        self._grid_layout.addWidget(kart_filtreler, ozel_satir, 2)

        # Sütunlara eşit genişlik ver
        for c in range(self.SUTUN_SAYISI):
            self._grid_layout.setColumnStretch(c, 1)
