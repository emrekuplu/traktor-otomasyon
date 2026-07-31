# =============================================================================
#  views/finance_screen.py
#  Sorumluluk : Kasa ve Banka bakiyelerini ve son ödemeleri gösterme.
# =============================================================================

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, PushButton, PrimaryPushButton, ComboBox, TableWidget
)
from constants import BG_COLOR, TEXT_MUTED, CARD_BG, para_formatla
from services.pos_service import PosService
from core.events import event_bus
from PyQt5.QtWidgets import QMenu, QMessageBox


class FinanceScreen(QWidget):
    def __init__(self, go_back, go_stock, go_order, parent=None):
        super().__init__(parent)
        self.go_back = go_back
        self._service = PosService()

        # EventBus abonelikleri
        event_bus.satis_yapildi.connect(self.verileri_yukle)
        event_bus.islem_silindi.connect(self.verileri_yukle)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 20, 30, 30)
        root.setSpacing(16)

        # ── Navigasyon Bar ────────────────────────────────────────────────────
        nav = QHBoxLayout()
        btn_geri = PushButton("← Ana Menü")
        btn_geri.setFixedHeight(38)
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

        title = TitleLabel("Gelir & Gider Yönetimi (Kasa / Banka)")
        title.setStyleSheet("font-weight: bold; color: #111827;")
        root.addWidget(title)

        # ── KPI Kartları (Dashboard) ──
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)

        # Kasa Kartı
        self.card_kasa = self._create_kpi_card("Nakit Kasa (Toplam)", "0,00 ₺", "#059669")
        kpi_layout.addWidget(self.card_kasa)

        # Banka Kartı
        self.card_banka = self._create_kpi_card("Banka & POS (Toplam)", "0,00 ₺", "#2563EB")
        kpi_layout.addWidget(self.card_banka)

        root.addLayout(kpi_layout)

        # ── Son İşlemler (Tablo) ──
        table_header_layout = QHBoxLayout()
        
        lbl_gecmis = SubtitleLabel("Son Ödeme ve Tahsilat Hareketleri")
        lbl_gecmis.setStyleSheet("font-weight: bold; margin-top: 10px;")
        table_header_layout.addWidget(lbl_gecmis)
        table_header_layout.addStretch()
        
        lbl_filtre = BodyLabel("İşlem Türü:")
        table_header_layout.addWidget(lbl_filtre)
        
        self.combo_filtre = ComboBox()
        self.combo_filtre.addItems(["Tüm İşlemler", "Satış İşlemleri", "Stok İşlemleri"])
        self.combo_filtre.setFixedWidth(180)
        self.combo_filtre.currentIndexChanged.connect(self.verileri_yukle)
        table_header_layout.addWidget(self.combo_filtre)
        
        root.addLayout(table_header_layout)
        
        self.table = TableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Tarih", "Ödeme Tipi", "Kasa/Banka", "Cari/Müşteri", "Satış Fişi", "Tutar"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._tablo_sag_tik)
        root.addWidget(self.table, stretch=1)

        self.verileri_yukle()

    def _tablo_sag_tik(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        satis_id_item = self.table.item(row, 0)
        satis_id = satis_id_item.data(Qt.UserRole)
        
        if not satis_id:
            return

        menu = QMenu(self)
        sil_aksiyon = menu.addAction("❌ Bu İşlemi Geri Al (Sil)")
        secilen = menu.exec_(self.table.viewport().mapToGlobal(pos))
        
        if secilen == sil_aksiyon:
            cevap = QMessageBox.question(
                self, "Emin Misiniz?", 
                "Bu işlem tamamen silinecek.\nBağlı olan kasa tahsilatı geri alınacak ve stoklar iade edilecektir. Onaylıyor musunuz?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if cevap == QMessageBox.Yes:
                self._service.satis_sil(satis_id)

    def _create_kpi_card(self, title_text, value_text, color) -> QFrame:
        card = QFrame()
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 12px;
                border: 1px solid #E5E7EB;
                border-left: 5px solid {color};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = BodyLabel(title_text)
        title.setStyleSheet("color: #6B7280; font-size: 14px;")
        layout.addWidget(title)
        
        value = TitleLabel(value_text)
        value.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold; margin-top: 5px;")
        layout.addWidget(value)
        
        # Obje içinden erişebilmek için property ekliyoruz
        card.lbl_value = value
        return card

    def verileri_yukle(self):
        # Özet Verileri
        ozet = self._service.finans_ozeti_getir()
        self.card_kasa.lbl_value.setText(para_formatla(ozet.get("toplam_kasa", 0.0)))
        self.card_banka.lbl_value.setText(para_formatla(ozet.get("toplam_banka", 0.0)))

        # Tablo Verileri
        filtre_tipi = self.combo_filtre.currentText() if hasattr(self, 'combo_filtre') else "Tüm İşlemler"
        hareketler = self._service.son_odemeleri_getir(filtre_tipi, 100)
        self.table.setRowCount(len(hareketler))
        for i, h in enumerate(hareketler):
            tarih_item = QTableWidgetItem(h.get("tarih", "")[:16])
            tarih_item.setData(Qt.UserRole, h.get("satis_id"))
            self.table.setItem(i, 0, tarih_item)
            
            self.table.setItem(i, 1, QTableWidgetItem(h.get("odeme_tipi", "")))
            
            kb = h.get("kasa_ad") or h.get("banka_ad") or "-"
            self.table.setItem(i, 2, QTableWidgetItem(kb))
            
            self.table.setItem(i, 3, QTableWidgetItem(h.get("cari_ad", "-")))
            self.table.setItem(i, 4, QTableWidgetItem(h.get("fis_no", "-")))
            
            tutar_item = QTableWidgetItem(para_formatla(h.get("tutar", 0.0)))
            tutar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 5, tutar_item)
