# =============================================================================
#  views/urun_ekle_dialog.py
#  Sorumluluk : Yeni ürün ekleme ve mevcut ürünü düzenleme diyalogları.
#               Yalnızca UI bileşenleri ve form verisi toplama.
#  ÖNEMLİ     : Bu modülde sqlite3 veya iş mantığı kodu BULUNMAZ.
# =============================================================================

import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QFileDialog
)
from qfluentwidgets import (
    StrongBodyLabel, PrimaryPushButton, PushButton,
    LineEdit, SpinBox, ComboBox, InfoBar, DoubleSpinBox, BodyLabel
)
from constants import CARD_BG, TEXT_MUTED, MARKALAR_FORM
from services.urun_service import UrunService


class UrunDuzenleDialog(QDialog):
    """Mevcut ürünü düzenleme diyalogu – yalnızca arayüz."""

    def __init__(self, kategoriler, urun_id, ad, kod, kategori, stok,
                 resim_yolu: str = "", marka: str = "Diğer",
                 alis_fiyati: float = 0.0, satis_fiyati: float = 0.0,
                 alt_kategori: str = "Yok",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ürünü Düzeyle")
        self.setFixedSize(440, 540)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"QDialog {{ background-color: {CARD_BG}; }}")
        self._secilen_resim_yolu = ""
        self._service = UrunService()
        self._urun_id = urun_id
        self._silindi = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = StrongBodyLabel("✏️  Ürünü Düzeyle")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1A1A2E;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.input_ad = LineEdit()
        self.input_ad.setText(ad)
        form_layout.addRow(BodyLabel("Ürün Adı:"), self.input_ad)

        self.input_kod = LineEdit()
        self.input_kod.setText(kod)
        self.input_kod.setPlaceholderText("Boş bırakılırsa mevcut kod korunur")
        form_layout.addRow(BodyLabel("Ürün Kodu:"), self.input_kod)

        self.input_kategori = ComboBox()
        kat_listesi = [k for k in kategoriler if k != "Tüm Kategoriler"]
        self.input_kategori.addItems(kat_listesi)
        if kategori in kat_listesi:
            self.input_kategori.setCurrentText(kategori)
        form_layout.addRow(BodyLabel("Kategori:"), self.input_kategori)

        self.input_alt_kategori = ComboBox()
        self.input_alt_kategori.addItems(["Yok", "Hava Filtresi", "Yağ Filtresi", "Mazot Filtresi", "Hidrolik Filtresi", "Diğer"])
        if alt_kategori in ["Yok", "Hava Filtresi", "Yağ Filtresi", "Mazot Filtresi", "Hidrolik Filtresi", "Diğer"]:
            self.input_alt_kategori.setCurrentText(alt_kategori)
        self.lbl_alt_kategori = BodyLabel("Filtre Tipi:")
        form_layout.addRow(self.lbl_alt_kategori, self.input_alt_kategori)

        # Dinamik gösterim
        self.input_kategori.currentTextChanged.connect(self._kategori_degisti)
        self._kategori_degisti(kategori)

        self.input_marka = ComboBox()
        self.input_marka.addItems(MARKALAR_FORM)
        if marka in MARKALAR_FORM:
            self.input_marka.setCurrentText(marka)
        form_layout.addRow(BodyLabel("Marka:"), self.input_marka)

        self.input_stok = SpinBox()
        self.input_stok.setRange(0, 99999)
        self.input_stok.setValue(stok)
        form_layout.addRow(BodyLabel("Stok Adedi:"), self.input_stok)

        # ── Fiyat Alanları ────────────────────────────────────────────────────
        self.input_alis = DoubleSpinBox()
        self.input_alis.setRange(0.0, 9_999_999.99)
        self.input_alis.setDecimals(2)
        self.input_alis.setSuffix(" ₺")
        self.input_alis.setSingleStep(10.0)
        self.input_alis.setValue(alis_fiyati)
        form_layout.addRow(BodyLabel("Alış Fiyatı:"), self.input_alis)

        self.input_satis = DoubleSpinBox()
        self.input_satis.setRange(0.0, 9_999_999.99)
        self.input_satis.setDecimals(2)
        self.input_satis.setSuffix(" ₺")
        self.input_satis.setSingleStep(10.0)
        self.input_satis.setValue(satis_fiyati)
        form_layout.addRow(BodyLabel("Satış Fiyatı:"), self.input_satis)
        # ─────────────────────────────────────────────────────────────────────

        # ── Fotoğraf ─────────────────────────────────────────────────────────
        foto_satir = QHBoxLayout()
        foto_satir.setSpacing(8)
        self.btn_foto = PushButton("📷 Fotoğraf Seç")
        self.btn_foto.setFixedHeight(34)
        self.btn_foto.clicked.connect(self._fotograf_sec)
        mevcut_ad = os.path.basename(resim_yolu) if resim_yolu else "Seçilmedi"
        self.lbl_foto = QLabel(mevcut_ad)
        if resim_yolu:
            self.lbl_foto.setStyleSheet("color: #107C10; font-size: 11px; font-weight: 600;")
        else:
            self.lbl_foto.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.lbl_foto.setWordWrap(True)
        foto_satir.addWidget(self.btn_foto)
        foto_satir.addWidget(self.lbl_foto, stretch=1)
        form_layout.addRow(BodyLabel("Ürün Fotoğrafı:"), foto_satir)
        # ─────────────────────────────────────────────────────────────────────

        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_sil = PushButton("🗑️ Sil")
        btn_sil.setStyleSheet(
            "PushButton { color: #991B1B; border: 1px solid #FECACA;"
            " background: #FEE2E2; border-radius: 6px; padding: 4px 12px; }"
            "PushButton:hover { background: #FECACA; }"
        )
        btn_sil.clicked.connect(self._sil_onayla)

        btn_iptal = PushButton("İptal")
        btn_iptal.clicked.connect(self.reject)

        btn_kaydet = PrimaryPushButton("Kaydet")
        btn_kaydet.clicked.connect(self._kaydet)

        btn_layout.addWidget(btn_sil)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_iptal)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)

    def _kategori_degisti(self, text: str):
        if text == "Filtre Grubu":
            self.input_alt_kategori.show()
            self.lbl_alt_kategori.show()
        else:
            self.input_alt_kategori.hide()
            self.lbl_alt_kategori.hide()
            self.input_alt_kategori.setCurrentText("Yok")

    def _fotograf_sec(self):
        dosya_yolu, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if dosya_yolu:
            self._secilen_resim_yolu = dosya_yolu
            self.lbl_foto.setText(os.path.basename(dosya_yolu))
            self.lbl_foto.setStyleSheet("color: #107C10; font-size: 11px; font-weight: 600;")

    def _kaydet(self):
        ad    = self.input_ad.text().strip()
        kod   = self.input_kod.text().strip()
        kat   = self.input_kategori.currentText().strip()
        marka = self.input_marka.currentText().strip()
        if not ad or not kat:
            InfoBar.error(
                "Eksik Bilgi",
                "Lütfen Ürün Adı ve Kategori alanlarını doldurun.",
                parent=self,
            )
            return
        # yeni_veri: (ad, kod, kategori, stok, secilen_resim, marka, alis, satis, alt_kategori)
        self.yeni_veri = (
            ad, kod, kat,
            self.input_stok.value(),
            self._secilen_resim_yolu,
            marka,
            self.input_alis.value(),
            self.input_satis.value(),
            self.input_alt_kategori.currentText(),
        )
        self.accept()

    def _sil_onayla(self):
        self._silindi = True
        self.accept()


class UrunEkleDialog(QDialog):
    """Yeni ürün ekleme diyalogu – yalnızca arayüz ve form verisi toplama."""

    def __init__(self, kategoriler, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Ürün Ekle")
        self.setFixedSize(440, 530)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"QDialog {{ background-color: {CARD_BG}; }}")
        self._secilen_resim_yolu = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = StrongBodyLabel("Yeni Stok Kartı Oluştur")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.input_ad = LineEdit()
        self.input_ad.setPlaceholderText("Örn: Lityum Batarya")
        form_layout.addRow(BodyLabel("Ürün Adı:"), self.input_ad)

        self.input_kod = LineEdit()
        self.input_kod.setPlaceholderText("Boş bırakılırsa otomatik atanır (TRK-XXXX)")
        form_layout.addRow(BodyLabel("Ürün Kodu:"), self.input_kod)

        self.input_kategori = ComboBox()
        self.input_kategori.addItems([k for k in kategoriler if k != "Tüm Kategoriler"])
        form_layout.addRow(BodyLabel("Kategori:"), self.input_kategori)

        self.input_alt_kategori = ComboBox()
        self.input_alt_kategori.addItems(["Yok", "Hava Filtresi", "Yağ Filtresi", "Mazot Filtresi", "Hidrolik Filtresi", "Diğer"])
        self.lbl_alt_kategori = BodyLabel("Filtre Tipi:")
        form_layout.addRow(self.lbl_alt_kategori, self.input_alt_kategori)

        self.input_kategori.currentTextChanged.connect(self._kategori_degisti)
        self._kategori_degisti(self.input_kategori.currentText())

        self.input_marka = ComboBox()
        self.input_marka.addItems(MARKALAR_FORM)
        form_layout.addRow(BodyLabel("Marka:"), self.input_marka)

        self.input_stok = SpinBox()
        self.input_stok.setRange(0, 99999)
        self.input_stok.setValue(1)
        form_layout.addRow(BodyLabel("Başlangıç Stoku:"), self.input_stok)

        # ── Fiyat Alanları ────────────────────────────────────────────────────
        self.input_alis = DoubleSpinBox()
        self.input_alis.setRange(0.0, 9_999_999.99)
        self.input_alis.setDecimals(2)
        self.input_alis.setSuffix(" ₺")
        self.input_alis.setSingleStep(10.0)
        form_layout.addRow(BodyLabel("Alış Fiyatı:"), self.input_alis)

        self.input_satis = DoubleSpinBox()
        self.input_satis.setRange(0.0, 9_999_999.99)
        self.input_satis.setDecimals(2)
        self.input_satis.setSuffix(" ₺")
        self.input_satis.setSingleStep(10.0)
        form_layout.addRow(BodyLabel("Satış Fiyatı:"), self.input_satis)
        # ─────────────────────────────────────────────────────────────────────

        # ── Fotoğraf ─────────────────────────────────────────────────────────
        foto_satir = QHBoxLayout()
        foto_satir.setSpacing(8)
        self.btn_foto = PushButton("📷 Fotoğraf Seç")
        self.btn_foto.setFixedHeight(34)
        self.btn_foto.clicked.connect(self._fotograf_sec)
        self.lbl_foto = QLabel("Seçilmedi")
        self.lbl_foto.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.lbl_foto.setWordWrap(True)
        foto_satir.addWidget(self.btn_foto)
        foto_satir.addWidget(self.lbl_foto, stretch=1)
        form_layout.addRow(BodyLabel("Ürün Fotoğrafı:"), foto_satir)
        # ─────────────────────────────────────────────────────────────────────

        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_iptal = PushButton("İptal")
        btn_iptal.clicked.connect(self.reject)

        btn_kaydet = PrimaryPushButton("Kaydet")
        btn_kaydet.clicked.connect(self._verileri_kontrol_et)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_iptal)
        btn_layout.addWidget(btn_kaydet)
        layout.addLayout(btn_layout)

    def _kategori_degisti(self, text: str):
        if text == "Filtre Grubu":
            self.input_alt_kategori.show()
            self.lbl_alt_kategori.show()
        else:
            self.input_alt_kategori.hide()
            self.lbl_alt_kategori.hide()
            self.input_alt_kategori.setCurrentText("Yok")

    def _fotograf_sec(self):
        dosya_yolu, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if dosya_yolu:
            self._secilen_resim_yolu = dosya_yolu
            self.lbl_foto.setText(os.path.basename(dosya_yolu))
            self.lbl_foto.setStyleSheet("color: #107C10; font-size: 11px; font-weight: 600;")

    def _verileri_kontrol_et(self):
        ad    = self.input_ad.text().strip()
        kod   = self.input_kod.text().strip()
        kat   = self.input_kategori.currentText().strip()
        marka = self.input_marka.currentText().strip()

        if not ad or not kat:
            InfoBar.error(
                "Eksik Bilgi",
                "Lütfen Ürün Adı ve Kategori alanlarını doldurun.",
                parent=self,
            )
            return

        # yeni_veri: (ad, kod, kategori, stok, secilen_resim, marka, alis, satis, alt_kategori)
        self.yeni_veri = (
            ad, kod, kat,
            self.input_stok.value(),
            self._secilen_resim_yolu,
            marka,
            self.input_alis.value(),
            self.input_satis.value(),
            self.input_alt_kategori.currentText(),
        )
        self.accept()
