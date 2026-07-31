# =============================================================================
#  views/kritik_urunler.py
#  Sorumluluk : Kritik stok seviyesindeki ürünlerin listelendiği ekran.
# =============================================================================

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QAbstractItemView, QDialog
from qfluentwidgets import (
    TableWidget, TitleLabel, BodyLabel, PushButton, InfoBar, PrimaryPushButton
)
from constants import BG_COLOR, TEXT_MUTED, para_formatla
from services.urun_service import UrunService
from views.urun_ekle_dialog import UrunDuzenleDialog

class KritikUrunlerScreen(QWidget):
    """
    Stoku 5 ve altındaki ürünleri listeleyen ekran.
    """
    def __init__(self, go_back, parent=None):
        super().__init__(parent)
        self._go_back = go_back
        self._service = UrunService()

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(20)

        # ── Üst Bar (Geri Butonu ve Başlık) ────────────────────────────────────
        top_bar = QHBoxLayout()
        top_bar.setSpacing(15)

        btn_geri = PushButton("⬅ Geri Dön")
        btn_geri.setFixedHeight(38)
        btn_geri.clicked.connect(self._go_back)
        top_bar.addWidget(btn_geri)

        baslik = TitleLabel("Kritik Stok Alarmı")
        baslik.setStyleSheet("color: #991B1B; font-weight: bold;")
        top_bar.addWidget(baslik)
        top_bar.addStretch()

        root.addLayout(top_bar)

        aciklama = BodyLabel("Aşağıdaki parçaların stok seviyesi kritik sınırın (5 adet ve altı) altına düşmüştür. Lütfen tedarik planlaması yapınız.")
        aciklama.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px;")
        aciklama.setWordWrap(True)
        root.addWidget(aciklama)

        # ── Tablo ─────────────────────────────────────────────────────────────
        self.tablo = TableWidget(self)
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setColumnCount(5)
        self.tablo.setHorizontalHeaderLabels(["Marka", "Ürün Kodu/Adı", "Güncel Stok", "Satış Fiyatı", "İşlem"])
        
        # Sütun genişlikleri
        header = self.tablo.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        root.addWidget(self.tablo)

        self.verileri_yukle()

    def verileri_yukle(self):
        self.tablo.clearContents()
        urunler = self._service.kritik_urunleri_getir()
        self.tablo.setRowCount(len(urunler))

        for row, u in enumerate(urunler):
            marka = u.get("marka") or "Diğer"
            ad_kod = f"[{u.get('kod')}] {u.get('ad')}"
            stok = u.get("stok", 0)
            fiyat = para_formatla(u.get("satis_fiyati", 0.0))

            # TableWidgetItem oluşturma yerine doğrudan setItem
            # qfluentwidgets TableWidget, QTableWidget'dan miras alır
            from PyQt5.QtWidgets import QTableWidgetItem

            item_marka = QTableWidgetItem(marka)
            item_marka.setTextAlignment(Qt.AlignCenter)
            
            item_ad = QTableWidgetItem(ad_kod)
            item_ad.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            item_stok = QTableWidgetItem(f"{stok} Adet")
            item_stok.setTextAlignment(Qt.AlignCenter)
            # Kırmızı/vurgulu metin
            if stok == 0:
                item_stok.setForeground(Qt.white)
                item_stok.setBackground(Qt.darkRed)
            else:
                from PyQt5.QtGui import QColor
                item_stok.setForeground(QColor("#991B1B"))
                item_stok.setFont(self._bold_font(item_stok.font()))

            item_fiyat = QTableWidgetItem(fiyat)
            item_fiyat.setTextAlignment(Qt.AlignCenter)

            self.tablo.setItem(row, 0, item_marka)
            self.tablo.setItem(row, 1, item_ad)
            self.tablo.setItem(row, 2, item_stok)
            self.tablo.setItem(row, 3, item_fiyat)

            # İşlem Butonu
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(8)

            btn_ekle = PrimaryPushButton("Stok Ekle (+1)")
            btn_ekle.setFixedSize(110, 28)
            btn_ekle.clicked.connect(lambda _, urun_id=u["id"], urun_ad=u["ad"], stok_adedi=stok: self._stok_ekle(urun_id, urun_ad, stok_adedi))
            
            btn_detay = PushButton("Detay")
            btn_detay.setFixedSize(70, 28)
            btn_detay.clicked.connect(lambda _, urun=u: self._duzenle_ac(urun))

            btn_layout.addWidget(btn_ekle)
            btn_layout.addWidget(btn_detay)
            btn_layout.addStretch()

            self.tablo.setCellWidget(row, 4, btn_container)

    def _bold_font(self, font):
        font.setBold(True)
        return font

    def _stok_ekle(self, urun_id: int, urun_adi: str, stok_adedi: int):
        yeni_stok = stok_adedi + 1
        self._service.stok_guncelle(urun_id, yeni_stok)
        InfoBar.success(
            "Stok +1", f"{urun_adi} stoku {yeni_stok} adet oldu.",
            duration=1500, parent=self.window()
        )
        self.verileri_yukle()

    def _duzenle_ac(self, u: dict):
        mevcut_kat = self._service.kategorileri_getir()
        dialog = UrunDuzenleDialog(
            mevcut_kat, u["id"], u["ad"], u["kod"], u["kategori"], u["stok"],
            resim_yolu=u.get("resim_yolu", ""),
            marka=u.get("marka", "Diğer"),
            alis_fiyati=u.get("alis_fiyati", 0.0),
            satis_fiyati=u.get("satis_fiyati", 0.0),
            alt_kategori=u.get("alt_kategori", "Yok"),
            parent=self.window(),
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        if dialog._silindi:
            self._service.urun_sil(u["id"])
            InfoBar.warning(
                "Ürün Silindi", f"{u['ad']} kaldırıldı.",
                duration=2000, parent=self.window()
            )
        else:
            ad, kod, kat, stok, secilen_resim, yeni_marka, alis, satis, yeni_alt_kategori = dialog.yeni_veri
            self._service.urun_guncelle(
                u["id"], ad, kod, kat, stok,
                mevcut_kod=u["kod"],
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
        
        self.verileri_yukle()
