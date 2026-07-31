import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFrame
from qfluentwidgets import (
    TitleLabel, BodyLabel, LineEdit, PrimaryPushButton, PushButton, InfoBar
)


class VeresiyeDialog(QDialog):
    """
    Veresiye/Cari satışlarda müşteri seçmek için kullanılan basit dialog.
    """

    def __init__(self, tutar: float, parent=None):
        super().__init__(parent)
        self.tutar = tutar
        self.musteri_adi = ""

        self.setWindowTitle("Müşteri Seç")
        self.setFixedSize(400, 250)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        title = TitleLabel("Veresiye / Cari İşlem")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1A1A2E;")
        layout.addWidget(title)

        desc = BodyLabel(f"Toplam Tutar: {tutar:,.2f} ₺\nLütfen müşteri adını giriniz.")
        desc.setStyleSheet("color: #6B7280; font-size: 14px;")
        layout.addWidget(desc)

        # Müşteri Input
        self.input_musteri = LineEdit()
        self.input_musteri.setPlaceholderText("Müşteri Adı Soyadı...")
        self.input_musteri.setClearButtonEnabled(True)
        self.input_musteri.setFixedHeight(40)
        layout.addWidget(self.input_musteri)

        layout.addStretch()

        # Alt Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_iptal = PushButton("İptal")
        self.btn_iptal.setFixedHeight(38)
        self.btn_iptal.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_iptal)

        self.btn_onayla = PrimaryPushButton("Veresiyeyi Onayla")
        self.btn_onayla.setFixedHeight(38)
        self.btn_onayla.clicked.connect(self._onayla)
        btn_layout.addWidget(self.btn_onayla)

        layout.addLayout(btn_layout)

    def _onayla(self):
        ad = self.input_musteri.text().strip()
        if not ad:
            InfoBar.error(
                title="Hata",
                content="Lütfen bir müşteri adı giriniz.",
                parent=self,
                duration=2000
            )
            return
        self.musteri_adi = ad
        self.accept()
