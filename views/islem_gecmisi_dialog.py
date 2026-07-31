# =============================================================================
#  views/islem_gecmisi_dialog.py
#  Sorumluluk : Sistemdeki tüm stok hareketlerini filtreli listeleyen modal.
#               Tekil/çoklu seçim silme ve tüm geçmişi temizleme destekler.
#  ÖNEMLİ     : Bu modülde sqlite3 veya iş mantığı kodu BULUNMAZ.
# =============================================================================

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox
)
from qfluentwidgets import (
    StrongBodyLabel, CaptionLabel, PushButton,
    CardWidget, InfoBar, InfoBarPosition
)
from constants import CARD_BG, BG_COLOR, TEXT_MUTED, TEXT_PRIMARY
from services.urun_service import UrunService


# ─── Filtre Sabitleri ──────────────────────────────────────────────────────────
FILTRE_TUMÜ  = "Tümü"
FILTRE_GELEN = "Gelen"   # → GİRİŞ
FILTRE_GIDEN = "Giden"   # → ÇIKIŞ

_FILTRE_DB = {
    FILTRE_TUMÜ:  None,
    FILTRE_GELEN: "GİRİŞ",
    FILTRE_GIDEN: "ÇIKIŞ",
}

# Tablo sütun indeksleri
COL_CHK   = 0
COL_TARIH = 1
COL_ISLEM = 2
COL_AD    = 3
COL_KOD   = 4
COL_MIK   = 5


class IslemGecmisiDialog(QDialog):
    """
    Tüm işlem geçmişini gösteren, filtrelenebilir modal dialog.

    Özellikler
    ----------
    - Filtre butonu grubu: Tümü / Gelen / Giden
    - Checkbox ile tekil/çoklu satır seçimi
    - "Seçilenleri Sil" – onay penceresiyle seçili kayıtları siler
    - "Geçmişi Temizle" – onay penceresiyle tüm geçmişi sıfırlar
    - GİRİŞ → yeşil, ÇIKIŞ → kırmızı renk kodlaması
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("İşlem Geçmişi")
        self.setMinimumSize(920, 600)
        self.resize(1000, 660)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"QDialog {{ background-color: {BG_COLOR}; }}")

        self._service = UrunService()
        self._aktif_filtre = FILTRE_TUMÜ

        self._ui_olustur()
        self._tabloyu_guncelle()

    # ── UI Kurulum ────────────────────────────────────────────────────────────

    def _ui_olustur(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        # ── Başlık Satırı ─────────────────────────────────────────────────────
        baslik_satir = QHBoxLayout()

        ikon_lbl = QLabel("📋")
        ikon_lbl.setStyleSheet("font-size: 26px;")
        baslik_satir.addWidget(ikon_lbl)

        baslik_col = QVBoxLayout()
        baslik_col.setSpacing(2)
        baslik = StrongBodyLabel("İşlem Geçmişi")
        baslik.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {TEXT_PRIMARY};")
        baslik_col.addWidget(baslik)
        alt_baslik = CaptionLabel("Tüm stok giriş ve çıkış hareketleri")
        alt_baslik.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        baslik_col.addWidget(alt_baslik)
        baslik_satir.addLayout(baslik_col)
        baslik_satir.addStretch()

        # Kapat butonu
        btn_kapat = PushButton("✕  Kapat")
        btn_kapat.setFixedHeight(34)
        btn_kapat.clicked.connect(self.reject)
        baslik_satir.addWidget(btn_kapat)

        root.addLayout(baslik_satir)

        # ── Ayırıcı çizgi ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E5E7EB;")
        root.addWidget(sep)

        # ── Araç Çubuğu (Filtreler + Silme Butonları) ─────────────────────────
        araç_kart = CardWidget()
        araç_kart.setAttribute(Qt.WA_StyledBackground, True)
        araç_kart.setStyleSheet(
            f"CardWidget {{ background-color: {CARD_BG}; border-radius: 10px; }}"
        )

        araç_ic = QHBoxLayout(araç_kart)
        araç_ic.setContentsMargins(16, 10, 16, 10)
        araç_ic.setSpacing(8)

        # Filtre etiketi
        filtre_lbl = CaptionLabel("Filtrele:")
        filtre_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        araç_ic.addWidget(filtre_lbl)

        # Filtre butonları
        self._filtre_butonlar: dict[str, PushButton] = {}
        for etiket in (FILTRE_TUMÜ, FILTRE_GELEN, FILTRE_GIDEN):
            btn = PushButton(etiket)
            btn.setFixedHeight(32)
            btn.setMinimumWidth(76)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, e=etiket: self._filtre_degisti(e))
            self._filtre_butonlar[etiket] = btn
            araç_ic.addWidget(btn)

        # Dikey ayırıcı
        v_sep = QFrame()
        v_sep.setFrameShape(QFrame.VLine)
        v_sep.setStyleSheet("color: #D1D5DB;")
        v_sep.setFixedWidth(1)
        araç_ic.addWidget(v_sep)

        # Seçilenleri Sil butonu
        self.btn_secilenleri_sil = PushButton("🗑  Seçilenleri Sil")
        self.btn_secilenleri_sil.setFixedHeight(32)
        self.btn_secilenleri_sil.setMinimumWidth(130)
        self.btn_secilenleri_sil.setCursor(Qt.PointingHandCursor)
        self.btn_secilenleri_sil.setEnabled(False)   # Başta devre dışı
        self.btn_secilenleri_sil.setStyleSheet(
            "PushButton { color: #991B1B; border: 1px solid #FECACA;"
            " background: #FEF2F2; border-radius: 7px; padding: 4px 12px; }"
            "PushButton:hover { background: #FEE2E2; }"
            "PushButton:disabled { color: #9CA3AF; border-color: #E5E7EB;"
            " background: #F9FAFB; }"
        )
        self.btn_secilenleri_sil.clicked.connect(self._secilenleri_sil)
        araç_ic.addWidget(self.btn_secilenleri_sil)

        # Geçmişi Temizle butonu
        btn_temizle = PushButton("🧹  Geçmişi Temizle")
        btn_temizle.setFixedHeight(32)
        btn_temizle.setMinimumWidth(140)
        btn_temizle.setCursor(Qt.PointingHandCursor)
        btn_temizle.setStyleSheet(
            "PushButton { color: #7C2D12; border: 1px solid #FDBA74;"
            " background: #FFF7ED; border-radius: 7px; padding: 4px 12px; }"
            "PushButton:hover { background: #FFEDD5; }"
        )
        btn_temizle.clicked.connect(self._gecmisi_temizle)
        araç_ic.addWidget(btn_temizle)

        araç_ic.addStretch()

        # Kayıt sayısı
        self._kayit_lbl = CaptionLabel("— kayıt")
        self._kayit_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        araç_ic.addWidget(self._kayit_lbl)

        root.addWidget(araç_kart)

        # ── Seçim Durum Çubuğu ────────────────────────────────────────────────
        self._secim_lbl = CaptionLabel("")
        self._secim_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; margin-left: 4px;")
        root.addWidget(self._secim_lbl)

        # ── Tablo ─────────────────────────────────────────────────────────────
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(6)
        self.tablo.setHorizontalHeaderLabels([
            "", "Tarih", "İşlem Tipi", "Ürün Adı", "Ürün Kodu", "Miktar"
        ])

        hdr = self.tablo.horizontalHeader()
        hdr.setSectionResizeMode(COL_CHK,   QHeaderView.Fixed)
        hdr.setSectionResizeMode(COL_TARIH, QHeaderView.Fixed)
        hdr.setSectionResizeMode(COL_ISLEM, QHeaderView.Fixed)
        hdr.setSectionResizeMode(COL_AD,    QHeaderView.Stretch)
        hdr.setSectionResizeMode(COL_KOD,   QHeaderView.Fixed)
        hdr.setSectionResizeMode(COL_MIK,   QHeaderView.Fixed)

        self.tablo.setColumnWidth(COL_CHK,   36)
        self.tablo.setColumnWidth(COL_TARIH, 145)
        self.tablo.setColumnWidth(COL_ISLEM, 110)
        self.tablo.setColumnWidth(COL_KOD,   120)
        self.tablo.setColumnWidth(COL_MIK,   80)

        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionMode(QTableWidget.NoSelection)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setAlternatingRowColors(False)
        self.tablo.setShowGrid(True)
        self.tablo.verticalHeader().setDefaultSectionSize(36)
        self.tablo.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                font-size: 12px;
                outline: none;
                gridline-color: #F0F0F0;
            }
            QTableWidget::item {
                background-color: #FFFFFF;
                color: #1F2937;
                padding: 2px 6px;
            }
            QHeaderView::section {
                background-color: #F9FAFB;
                color: #374151;
                font-weight: bold;
                font-size: 11px;
                border: none;
                border-bottom: 2px solid #E5E7EB;
                border-right: 1px solid #E5E7EB;
                padding: 8px;
            }

            /* ── Checkbox görünürlüğü ───────────────────────────── */
            QTableWidget::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
            }
            QTableWidget::indicator:unchecked {
                border: 2px solid #9CA3AF;
                background-color: #FFFFFF;
                border-radius: 4px;
            }
            QTableWidget::indicator:unchecked:hover {
                border: 2px solid #3B82F6;
                background-color: #EFF6FF;
                border-radius: 4px;
            }
            QTableWidget::indicator:checked {
                border: 2px solid #2563EB;
                background-color: #2563EB;
                border-radius: 4px;
                image: url(none);
            }
        """)


        # Checkbox değişince seçim durumu güncelle
        self.tablo.itemChanged.connect(self._secim_guncelle)

        root.addWidget(self.tablo)

        # Başlangıçta "Tümü" aktif
        self._filtre_stili_guncelle(FILTRE_TUMÜ)

    # ── Filtre Mantığı ────────────────────────────────────────────────────────

    def _filtre_degisti(self, etiket: str):
        if etiket == self._aktif_filtre:
            return
        self._aktif_filtre = etiket
        self._filtre_stili_guncelle(etiket)
        self._tabloyu_guncelle()

    def _filtre_stili_guncelle(self, aktif_etiket: str):
        for etiket, btn in self._filtre_butonlar.items():
            if etiket == aktif_etiket:
                if etiket == FILTRE_GELEN:
                    btn.setStyleSheet(
                        "PushButton { background: #D1FAE5; color: #065F46; border: 1.5px solid #6EE7B7;"
                        " border-radius: 7px; font-weight: bold; padding: 4px 14px; }"
                    )
                elif etiket == FILTRE_GIDEN:
                    btn.setStyleSheet(
                        "PushButton { background: #FEE2E2; color: #991B1B; border: 1.5px solid #FCA5A5;"
                        " border-radius: 7px; font-weight: bold; padding: 4px 14px; }"
                    )
                else:
                    btn.setStyleSheet(
                        "PushButton { background: #EFF6FF; color: #1D4ED8; border: 1.5px solid #93C5FD;"
                        " border-radius: 7px; font-weight: bold; padding: 4px 14px; }"
                    )
            else:
                btn.setStyleSheet(
                    "PushButton { background: #F9FAFB; color: #374151; border: 1px solid #D1D5DB;"
                    " border-radius: 7px; padding: 4px 14px; }"
                    "PushButton:hover { background: #F3F4F6; }"
                )

    # ── Seçim Yönetimi ────────────────────────────────────────────────────────

    def _secim_guncelle(self, item: QTableWidgetItem):
        """Checkbox durumu değiştiğinde seçim etiketini ve sil butonunu günceller."""
        if item.column() != COL_CHK:
            return
        secili_sayisi = self._secili_id_listesi().__len__()
        if secili_sayisi > 0:
            self._secim_lbl.setText(f"✔  {secili_sayisi} kayıt seçildi")
            self.btn_secilenleri_sil.setEnabled(True)
        else:
            self._secim_lbl.setText("")
            self.btn_secilenleri_sil.setEnabled(False)

    def _secili_id_listesi(self) -> list[int]:
        """İşaretli checkbox'lara ait hareket ID'lerini döndürür."""
        secili = []
        for row in range(self.tablo.rowCount()):
            chk = self.tablo.item(row, COL_CHK)
            if chk and chk.checkState() == Qt.Checked:
                hareket_id = chk.data(Qt.UserRole)
                if hareket_id is not None:
                    secili.append(hareket_id)
        return secili

    # ── Silme İşlemleri ───────────────────────────────────────────────────────

    def _secilenleri_sil(self):
        """Seçili kayıtları onay alarak siler."""
        id_listesi = self._secili_id_listesi()
        if not id_listesi:
            return

        sayi = len(id_listesi)
        cevap = QMessageBox.question(
            self,
            "Silme Onayı",
            f"Seçili <b>{sayi} işlem kaydı</b> kalıcı olarak silinecek.<br>"
            "Bu işlem geri alınamaz.<br><br>Devam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if cevap != QMessageBox.Yes:
            return

        hatali = 0
        for hid in id_listesi:
            try:
                self._service.stok_hareketi_sil(hid)
            except Exception:
                hatali += 1

        self._tabloyu_guncelle()

        if hatali == 0:
            InfoBar.success(
                title="Silindi",
                content=f"{sayi} işlem kaydı başarıyla silindi.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2500,
            )
        else:
            InfoBar.warning(
                title="Kısmi Hata",
                content=f"{sayi - hatali} kayıt silindi, {hatali} kayıtta hata oluştu.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )

    def _gecmisi_temizle(self):
        """Tüm işlem geçmişini onay alarak siler."""
        toplam = self.tablo.rowCount()
        if toplam == 0:
            InfoBar.info(
                title="Boş Geçmiş",
                content="Silinecek işlem kaydı bulunmuyor.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000,
            )
            return

        cevap = QMessageBox.question(
            self,
            "Geçmişi Temizle",
            f"<b>Tüm {toplam} işlem kaydı</b> kalıcı olarak silinecek.<br>"
            "Bu işlem geri alınamaz.<br><br>"
            "<b>Tüm geçmişi temizlemek istediğinize emin misiniz?</b>",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if cevap != QMessageBox.Yes:
            return

        try:
            silinen = self._service.tum_stok_hareketlerini_temizle()
            self._tabloyu_guncelle()
            InfoBar.success(
                title="Geçmiş Temizlendi",
                content=f"{silinen} işlem kaydı silindi.",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2500,
            )
        except Exception as e:
            InfoBar.error(
                title="Hata",
                content=f"Geçmiş temizlenirken hata oluştu: {e}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3500,
            )

    # ── Tablo Güncelleme ──────────────────────────────────────────────────────

    def _tabloyu_guncelle(self):
        """Aktif filtreye göre veritabanından veri çekip tabloyu render eder."""
        # itemChanged sinyalini geçici olarak kapat (gereksiz tetiklenmesin)
        self.tablo.itemChanged.disconnect(self._secim_guncelle)

        db_filtre = _FILTRE_DB[self._aktif_filtre]
        try:
            hareketler = self._service.tum_stok_hareketleri_getir(db_filtre)
        except Exception:
            hareketler = []

        self.tablo.setRowCount(len(hareketler))

        bold_font = QFont()
        bold_font.setBold(True)

        for row, h in enumerate(hareketler):
            islem_tipi = h.get("islem_tipi", "")
            is_giris   = islem_tipi == "GİRİŞ"

            # ── Checkbox (col 0) ───────────────────────────────────────────────
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            chk.setData(Qt.UserRole, h.get("id"))   # hareket_id sakla
            chk.setBackground(QColor("#FFFFFF"))
            self.tablo.setItem(row, COL_CHK, chk)

            # ── Tarih ─────────────────────────────────────────────────────────
            tarih_str = (h.get("tarih") or "")[:16]
            self._hucre_ekle(row, COL_TARIH, tarih_str, Qt.AlignCenter)

            # ── İşlem Tipi ────────────────────────────────────────────────────
            islem_item = QTableWidgetItem("↑ GİRİŞ" if is_giris else "↓ ÇIKIŞ")
            islem_item.setTextAlignment(Qt.AlignCenter)
            islem_item.setFont(bold_font)
            if is_giris:
                islem_item.setForeground(QColor("#065F46"))
                islem_item.setBackground(QColor("#D1FAE5"))
            else:
                islem_item.setForeground(QColor("#991B1B"))
                islem_item.setBackground(QColor("#FEE2E2"))
            self.tablo.setItem(row, COL_ISLEM, islem_item)

            # ── Ürün Adı ──────────────────────────────────────────────────────
            self._hucre_ekle(row, COL_AD, h.get("urun_ad", "—"), Qt.AlignLeft | Qt.AlignVCenter)

            # ── Ürün Kodu ─────────────────────────────────────────────────────
            self._hucre_ekle(row, COL_KOD, h.get("urun_kod", "—"), Qt.AlignCenter)

            # ── Miktar ────────────────────────────────────────────────────────
            mik = self._hucre_ekle(row, COL_MIK, str(h.get("miktar", "")), Qt.AlignCenter)
            mik.setFont(bold_font)
            mik.setForeground(QColor("#065F46") if is_giris else QColor("#991B1B"))
            mik.setBackground(QColor("#FFFFFF"))

        # Seçim durumunu sıfırla
        self._secim_lbl.setText("")
        self.btn_secilenleri_sil.setEnabled(False)
        self._kayit_lbl.setText(f"{len(hareketler)} kayıt")

        # Sinyali yeniden bağla
        self.tablo.itemChanged.connect(self._secim_guncelle)

    def _hucre_ekle(self, row: int, col: int, text: str,
                    alignment: int = Qt.AlignCenter) -> QTableWidgetItem:
        """
        Tabloya bir hücre ekler.
        Açıkça beyaz arka plan (#FFFFFF) ve koyu metin (#1F2937) atar
        böylece qfluentwidgets / sistem teması rengi geçersiz kılamaz.
        """
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        item.setBackground(QColor("#FFFFFF"))
        item.setForeground(QColor("#1F2937"))
        self.tablo.setItem(row, col, item)
        return item
