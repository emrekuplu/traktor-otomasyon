# =============================================================================
#  views/urun_karti.py
#  Sorumluluk : Tek bir ürünü kart olarak gösteren widget.
#               Stok +/− butonları ve düzenleme diyalogu burada başlar.
#  ÖNEMLİ     : Bu modülde sqlite3 veya doğrudan DB kodu BULUNMAZ.
#               Veritabanı işlemleri UrunService üzerinden yapılır.
# =============================================================================

import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication
)
from qfluentwidgets import (
    SimpleCardWidget, StrongBodyLabel, CaptionLabel,
    PushButton, InfoBar
)
from constants import CARD_BG, TEXT_MUTED, para_formatla
from services.urun_service import UrunService
from views.urun_ekle_dialog import UrunDuzenleDialog


# =============================================================================
#  Tıklanabilir Resim Etiketi
# =============================================================================

class ClickableResimLabel(QLabel):
    """Tıklama sinyali yayan QLabel — kart içi resim için kullanılır."""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# =============================================================================
#  Resim Önizleme Modalı
# =============================================================================

class _ImageCard(QFrame):
    """Overlay'in üzerine oturan beyaz kart — tıklamayı overlay'e iletmez."""
    def mousePressEvent(self, event):
        event.accept()   # Overlay'e propagate etme


class ResimOnizlemeDialog(QDialog):
    """
    Tam ekran karartılmış arka plan üzerine ürün resmini büyük gösteren modal.
    Kapatma: X butonu veya resim dışına (overlay) tıklama.
    """

    def __init__(self, resim_yolu: str, urun_adi: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        # Ana pencere boyutuna genişlet
        win = parent.window() if parent else None
        if win:
            self.setGeometry(win.geometry())
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.setGeometry(screen)

        # ── Karanlık Overlay (tıklamak kapatır) ──────────────────────────────
        overlay = QFrame(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 210);")
        overlay.mousePressEvent = lambda e: self.reject()

        # ── Resim Kartı (merkeze hizalanmış, tıklama absorbe eder) ───────────
        kart = _ImageCard(overlay)
        kart.setStyleSheet(
            "background-color: #111827; border-radius: 16px;"
            " border: 1px solid #374151;"
        )
        kart_layout = QVBoxLayout(kart)
        kart_layout.setContentsMargins(20, 16, 20, 20)
        kart_layout.setSpacing(12)

        # ── Başlık Satırı ──────────────────────────────────────────────────────
        baslik_satir = QHBoxLayout()
        urun_lbl = QLabel(urun_adi)
        urun_lbl.setStyleSheet(
            "color: #F9FAFB; font-size: 14px; font-weight: bold; background: transparent;"
        )
        baslik_satir.addWidget(urun_lbl)
        baslik_satir.addStretch()

        btn_kapat = PushButton("✕")
        btn_kapat.setFixedSize(34, 34)
        btn_kapat.setCursor(Qt.PointingHandCursor)
        btn_kapat.setStyleSheet(
            "PushButton { background: #374151; color: #F9FAFB; border: none;"
            " border-radius: 8px; font-size: 16px; font-weight: bold; }"
            "PushButton:hover { background: #EF4444; color: #FFFFFF; }"
        )
        btn_kapat.clicked.connect(self.reject)
        baslik_satir.addWidget(btn_kapat)
        kart_layout.addLayout(baslik_satir)

        # ── Resim ────────────────────────────────────────────────────────────
        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet("background: transparent;")

        MAX_W, MAX_H = 820, 580
        pixmap = QPixmap(resim_yolu)
        if not pixmap.isNull():
            scaled = pixmap.scaled(MAX_W, MAX_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaled = QPixmap(MAX_W, MAX_H)
        img_lbl.setPixmap(scaled)
        img_lbl.setFixedSize(scaled.width(), scaled.height())
        kart_layout.addWidget(img_lbl, 0, Qt.AlignCenter)

        # Kartı overlay'e ortala
        kart.adjustSize()
        kart_w = kart.sizeHint().width() + 40
        kart_h = kart.sizeHint().height() + 40
        ov_w, ov_h = overlay.width(), overlay.height()
        kart.setGeometry(
            (ov_w - kart_w) // 2,
            (ov_h - kart_h) // 2,
            kart_w,
            kart_h,
        )

    def keyPressEvent(self, event):
        """ESC tuşuyla da kapatılabilsin."""
        if event.key() == Qt.Key_Escape:
            self.reject()
        super().keyPressEvent(event)



class UrunKarti(SimpleCardWidget):
    """
    Tek bir ürünü temsil eden kart widget.
    Stok güncelleme ve düzenleme işlemleri UrunService aracılığıyla yapılır.
    """

    def __init__(self, urun_id, urun_adi, urun_kodu, kategori, stok_adedi,
                 resim_yolu="", marka="Diğer",
                 alis_fiyati: float = 0.0, satis_fiyati: float = 0.0,
                 alt_kategori: str = "Yok",
                 on_refresh=None, parent=None):
        super().__init__(parent)
        self.urun_id     = urun_id
        self.urun_adi    = urun_adi
        self.urun_kodu   = urun_kodu
        self.kategori    = kategori
        self.stok_adedi  = stok_adedi
        self._resim_yolu = resim_yolu
        self.marka       = marka
        self.alis_fiyati  = alis_fiyati
        self.satis_fiyati = satis_fiyati
        self.alt_kategori = alt_kategori
        self._on_refresh = on_refresh
        self._service = UrunService()

        self.setFixedSize(240, 390)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._guncelle_kart_stili()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 10)
        layout.setSpacing(4)

        # ── Üst satır: boşluk + düzenleme butonu ────────────────────────────
        top_row = QHBoxLayout()
        top_row.addStretch()
        self.btn_duzenle = PushButton("✏")
        self.btn_duzenle.setFixedSize(26, 26)
        self.btn_duzenle.setToolTip("Ürünü Düzeyle")
        self.btn_duzenle.setStyleSheet(
            "PushButton { border-radius: 6px; font-size: 13px;"
            " background-color: #EFF6FF; color: #1D4ED8;"
            " border: 1px solid #BFDBFE; padding: 0px; }"
            "PushButton:hover { background-color: #DBEAFE; }"
        )
        self.btn_duzenle.clicked.connect(self._duzenle_ac)
        top_row.addWidget(self.btn_duzenle)
        layout.addLayout(top_row)

        # ── Ürün görseli ─────────────────────────────────────────────────────
        self.resim = ClickableResimLabel()
        self.resim.setFixedSize(216, 160)
        self.resim.setAlignment(Qt.AlignCenter)
        self.resim.setStyleSheet(
            "background-color: #F3F6FB; border-radius: 10px;"
        )

        if resim_yolu and os.path.exists(resim_yolu):
            pixmap = QPixmap(resim_yolu)
            pixmap = pixmap.scaled(
                216, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.resim.setPixmap(pixmap)
            # Tıklanabilir: pointer cursor + onizleme aç
            self.resim.setCursor(Qt.PointingHandCursor)
            self.resim.setToolTip("Büyüt")
            self.resim.clicked.connect(
                lambda: ResimOnizlemeDialog(resim_yolu, urun_adi, parent=self).exec_()
            )
        else:
            self.resim.setText("📦")
            self.resim.setStyleSheet(
                "background-color: #F3F6FB; border-radius: 10px; font-size: 48px;"
            )
        layout.addWidget(self.resim, 0, Qt.AlignHCenter)

        # ── Marka ────────────────────────────────────────────────────────────
        marka_lbl = CaptionLabel(marka)
        marka_lbl.setAlignment(Qt.AlignCenter)
        marka_lbl.setStyleSheet(
            "color: #6D28D9; font-weight: bold; font-size: 10px;"
        )
        layout.addWidget(marka_lbl)

        # ── Ürün adı ─────────────────────────────────────────────────────────
        ad_lbl = StrongBodyLabel(urun_adi)
        ad_lbl.setAlignment(Qt.AlignCenter)
        ad_lbl.setWordWrap(True)
        ad_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #1A1A2E;")
        layout.addWidget(ad_lbl)

        # ── Kategori + Kod ────────────────────────────────────────────────────
        kat_lbl = CaptionLabel(f"[{kategori}]")
        kat_lbl.setAlignment(Qt.AlignCenter)
        kat_lbl.setStyleSheet("color: #0078D4; font-weight: bold;")
        layout.addWidget(kat_lbl)

        kod_lbl = CaptionLabel(f"Kod: {urun_kodu}")
        kod_lbl.setAlignment(Qt.AlignCenter)
        kod_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        layout.addWidget(kod_lbl)

        # ── Satış Fiyatı ─────────────────────────────────────────────────────
        fiyat_str = para_formatla(satis_fiyati) if satis_fiyati > 0 else "Fiyat girilmedi"
        fiyat_lbl = CaptionLabel(fiyat_str)
        fiyat_lbl.setAlignment(Qt.AlignCenter)
        if satis_fiyati > 0:
            fiyat_lbl.setStyleSheet(
                "color: #065F46; font-weight: bold; font-size: 12px;"
            )
        else:
            fiyat_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(fiyat_lbl)

        layout.addStretch()

        # ── Alt bar: [−]  Stok etiketi  [+] ─────────────────────────────────
        stok_bg, stok_fg, stok_border, stok_text = self._stok_renk(stok_adedi)

        bottom = QHBoxLayout()
        bottom.setSpacing(6)

        self.btn_azalt = PushButton("−")
        self.btn_azalt.setFixedSize(34, 34)
        self.btn_azalt.setStyleSheet(
            "PushButton { border-radius: 8px; font-size: 16px; font-weight: bold;"
            " background-color: #FFF0F0; color: #D13438; border: 1px solid #F3D0D0; }"
            "PushButton:hover { background-color: #FFD9D9; }"
        )
        self.btn_azalt.clicked.connect(self._stok_azalt)

        self.stok_lbl = QLabel(stok_text)
        self.stok_lbl.setAlignment(Qt.AlignCenter)
        self._set_stok_style(stok_bg, stok_fg, stok_border)

        self.btn_artir = PushButton("+")
        self.btn_artir.setFixedSize(34, 34)
        self.btn_artir.setStyleSheet(
            "PushButton { border-radius: 8px; font-size: 16px; font-weight: bold;"
            " background-color: #F0FFF4; color: #107C10; border: 1px solid #C6E8C6; }"
            "PushButton:hover { background-color: #D4F5D4; }"
        )
        self.btn_artir.clicked.connect(self._stok_ekle)

        bottom.addWidget(self.btn_azalt)
        bottom.addWidget(self.stok_lbl, stretch=1)
        bottom.addWidget(self.btn_artir)
        layout.addLayout(bottom)

    # ── Yardımcı ─────────────────────────────────────────────────────────────

    def _guncelle_kart_stili(self):
        """Stok 5 ve altındaysa karta kırmızı vurgu ekler."""
        if self.stok_adedi <= 5:
            self.setStyleSheet(
                f"SimpleCardWidget {{ background-color: #FEF2F2; border: 2px solid #FCA5A5; border-radius: 12px; }}"
                "SimpleCardWidget:hover { background-color: #FEE2E2; }"
            )
        else:
            self.setStyleSheet(
                f"SimpleCardWidget {{ background-color: {CARD_BG}; border: 1px solid #E5E7EB; border-radius: 12px; }}"
                "SimpleCardWidget:hover { background-color: #F9FAFB; }"
            )

    @staticmethod
    def _stok_renk(stok: int) -> tuple[str, str, str, str]:
        """Stok miktarına göre renk ve etiket metni döndürür."""
        if stok == 0:
            return "#FEE2E2", "#991B1B", "#FECACA", "Tükendi"
        elif stok <= 5:
            return "#FEE2E2", "#7F1D1D", "#FECACA", f"Kritik: {stok}"
        elif stok <= 10:
            return "#FEF3C7", "#92400E", "#FDE68A", f"Az: {stok}"
        else:
            return "#D1FAE5", "#065F46", "#A7F3D0", f"Stok: {stok}"

    def _set_stok_style(self, bg: str, fg: str, border: str):
        self.stok_lbl.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border-radius: 6px;"
            f" border: 1px solid {border};"
            " padding: 3px 6px; font-weight: 600; font-size: 11px;"
        )

    def _stok_guncelle_ui(self):
        """Stok değerini DB'ye yazar ve etiketi yeniler."""
        self._service.stok_guncelle(self.urun_id, self.stok_adedi)
        bg, fg, border, text = self._stok_renk(self.stok_adedi)
        self.stok_lbl.setText(text)
        self._set_stok_style(bg, fg, border)
        self._guncelle_kart_stili()

    # ── Olay İşleyiciler ─────────────────────────────────────────────────────

    def _stok_ekle(self):
        self.stok_adedi += 1
        self._stok_guncelle_ui()
        InfoBar.success(
            "Stok +1", f"{self.urun_adi} → {self.stok_adedi} adet",
            duration=1200, parent=self.window()
        )

    def _stok_azalt(self):
        if self.stok_adedi <= 0:
            InfoBar.warning(
                "Uyarı", "Stok zaten 0, daha fazla düşürülemez.",
                duration=1500, parent=self.window()
            )
            return
        self.stok_adedi -= 1
        self._stok_guncelle_ui()
        InfoBar.warning(
            "Stok −1", f"{self.urun_adi} → {self.stok_adedi} adet",
            duration=1200, parent=self.window()
        )

    def _duzenle_ac(self):
        """Düzenleme diyaloğunu açar; kaydet veya sil işlemini servise iletir."""
        mevcut_kat = self._service.kategorileri_getir()

        dialog = UrunDuzenleDialog(
            mevcut_kat, self.urun_id, self.urun_adi,
            self.urun_kodu, self.kategori, self.stok_adedi,
            resim_yolu=self._resim_yolu,
            marka=self.marka,
            alis_fiyati=self.alis_fiyati,
            satis_fiyati=self.satis_fiyati,
            alt_kategori=self.alt_kategori,
            parent=self.window(),
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        if dialog._silindi:
            self._service.urun_sil(self.urun_id)
            InfoBar.warning(
                "Ürün Silindi", f"{self.urun_adi} kaldırıldı.",
                duration=2000, parent=self.window()
            )
        else:
            ad, kod, kat, stok, secilen_resim, yeni_marka, alis, satis, yeni_alt_kategori = dialog.yeni_veri
            self._service.urun_guncelle(
                self.urun_id, ad, kod, kat, stok,
                mevcut_kod=self.urun_kodu,
                secilen_resim=secilen_resim,
                marka=yeni_marka,
                alis_fiyati=alis,
                satis_fiyati=satis,
                alt_kategori=yeni_alt_kategori,
            )
            InfoBar.success(
                "Kaydedildi", f"{ad} güncellendi.",
                duration=1500, parent=self.window()
            )

        if self._on_refresh:
            self._on_refresh()
