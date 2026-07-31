import os
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QSplitter, QGridLayout, QSizePolicy
)
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, StrongBodyLabel, BodyLabel, CaptionLabel,
    SearchLineEdit, PushButton, PrimaryPushButton, InfoBar, FlowLayout,
    IconWidget, FluentIcon
)
from constants import BG_COLOR, TEXT_MUTED, CARD_BG, para_formatla
from services.urun_service import UrunService
from views.veresiye_dialog import VeresiyeDialog


class PosUrunKarti(QFrame):
    """
    Hızlı satış ekranı için sade ürün kartı.
    Tıklandığında `on_click(urun_dict)` tetiklenir.
    """
    def __init__(self, urun: dict, on_click, parent=None):
        super().__init__(parent)
        self.urun = urun
        self._on_click = on_click
        self.setFixedSize(160, 200)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            PosUrunKarti {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            PosUrunKarti:hover {
                border: 1px solid #9CA3AF;
                background-color: #F9FAFB;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Görsel
        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignCenter)
        resim_yolu = urun.get("resim_yolu")
        if resim_yolu and os.path.exists(resim_yolu):
            pix = QPixmap(resim_yolu).scaled(100, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_lbl.setPixmap(pix)
        else:
            img_lbl.setText("📦")
            img_lbl.setStyleSheet("font-size: 32px; background: transparent;")
        layout.addWidget(img_lbl, 0, Qt.AlignCenter)

        # Ad & Fiyat
        ad = urun.get("ad", "")
        if len(ad) > 30:
            ad = ad[:27] + "..."
        ad_lbl = StrongBodyLabel(ad)
        ad_lbl.setWordWrap(True)
        ad_lbl.setAlignment(Qt.AlignCenter)
        ad_lbl.setStyleSheet("font-size: 13px; color: #1F2937; background: transparent;")
        layout.addWidget(ad_lbl, 1, Qt.AlignCenter)

        fiyat = urun.get("satis_fiyati", 0.0)
        fiyat_lbl = SubtitleLabel(para_formatla(fiyat))
        fiyat_lbl.setStyleSheet("font-size: 14px; color: #059669; font-weight: bold; background: transparent;")
        layout.addWidget(fiyat_lbl, 0, Qt.AlignCenter)

        # Stok durumu
        stok = urun.get("stok", 0)
        stok_lbl = CaptionLabel(f"Stok: {stok}")
        color = "#DC2626" if stok <= 0 else "#6B7280"
        stok_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(stok_lbl, 0, Qt.AlignCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_click(self.urun)
        super().mousePressEvent(event)


class CartItemWidget(QFrame):
    """Sepetteki bir kalemi temsil eder."""
    def __init__(self, urun: dict, miktar: int, on_miktar_degis, on_sil, parent=None):
        super().__init__(parent)
        self.urun = urun
        self.miktar = miktar
        self.urun_id = urun["id"]
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            CartItemWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # İsim ve Kod
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        ad = urun.get("ad", "")
        if len(ad) > 25:
            ad = ad[:22] + "..."
            
        ad_lbl = StrongBodyLabel(ad)
        ad_lbl.setStyleSheet("font-size: 13px; color: #1F2937; background: transparent;")
        info_layout.addWidget(ad_lbl)
        
        kod_lbl = CaptionLabel(urun.get("kod", ""))
        kod_lbl.setStyleSheet("color: #9CA3AF; background: transparent;")
        info_layout.addWidget(kod_lbl)
        layout.addLayout(info_layout, stretch=1)

        # Miktar Ayarı (Büyük ve Belirgin Butonlar)
        btn_style = """
            PushButton {
                background-color: #E0E0E0; border: 1px solid #BDBDBD; border-radius: 4px;
                color: #1F2937; font-size: 18px; font-weight: bold; padding: 0;
            }
            PushButton:hover { background-color: #D6D6D6; }
        """
        
        btn_minus = PushButton("-")
        btn_minus.setFixedSize(34, 34)
        btn_minus.setStyleSheet(btn_style)
        btn_minus.clicked.connect(lambda: on_miktar_degis(self.urun_id, -1))
        layout.addWidget(btn_minus)

        miktar_lbl = BodyLabel(str(self.miktar))
        miktar_lbl.setAlignment(Qt.AlignCenter)
        miktar_lbl.setFixedWidth(30)
        layout.addWidget(miktar_lbl)

        btn_plus = PushButton("+")
        btn_plus.setFixedSize(34, 34)
        btn_plus.setStyleSheet(btn_style)
        btn_plus.clicked.connect(lambda: on_miktar_degis(self.urun_id, 1))
        layout.addWidget(btn_plus)

        # Ara Toplam
        ara_toplam = self.miktar * urun.get("satis_fiyati", 0.0)
        fiyat_lbl = StrongBodyLabel(para_formatla(ara_toplam))
        fiyat_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        fiyat_lbl.setFixedWidth(100)
        layout.addWidget(fiyat_lbl)

        # Sil Butonu
        btn_sil = PushButton("🗑")
        btn_sil.setFixedSize(32, 32)
        btn_sil.setStyleSheet("color: #DC2626; border: none; background: transparent;")
        btn_sil.setCursor(Qt.PointingHandCursor)
        btn_sil.clicked.connect(lambda: on_sil(self.urun_id))
        layout.addWidget(btn_sil)


class OrderScreen(QWidget):
    """
    Yeni Sipariş Oluştur (Hızlı Satış / POS) Ekranı.
    Sol Kolon: Ürün arama ve vitrin
    Sağ Kolon: Sepet (Fiş), Toplam, Ödeme Butonları
    """

    def __init__(self, go_back, go_stock, go_finance, parent=None):
        super().__init__(parent)
        self.go_back = go_back
        self._service = UrunService()
        
        # State
        self.tum_urunler = []
        self.cart = {}  # urun_id -> {'urun': dict, 'miktar': int}

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Header ──
        header = QHBoxLayout()
        btn_geri = PushButton("← Ana Menü")
        btn_geri.setFixedHeight(38)
        btn_geri.clicked.connect(self.go_back)
        header.addWidget(btn_geri)

        title = TitleLabel("Hızlı Satış (POS)")
        title.setStyleSheet("font-weight: bold; color: #111827; margin-left: 16px;")
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        # ── Main Content (Splitter) ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E5E7EB; width: 1px; }")

        # Sol Kolon (Ürünler)
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 16, 0)

        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("Ürün Ara (İsim, Kod veya Barkod)...")
        self.search_input.setFixedHeight(44)
        self.search_input.setStyleSheet("""
            SearchLineEdit {
                border: 2px solid #D1D5DB;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 15px;
                padding-left: 12px;
                color: #111827;
            }
            SearchLineEdit:focus {
                border: 2px solid #3B82F6;
            }
        """)
        self.search_input.textChanged.connect(self._filtrele)
        left_layout.addWidget(self.search_input)

        self.scroll_left = QScrollArea()
        self.scroll_left.setWidgetResizable(True)
        self.scroll_left.setFrameShape(QFrame.NoFrame)
        self.scroll_left.setStyleSheet("background: transparent;")
        
        self.flow_container = QWidget()
        self.flow_container.setStyleSheet("background: transparent;")
        self.flow_layout = FlowLayout(self.flow_container, needAni=False)
        self.flow_layout.setContentsMargins(4, 16, 4, 16)
        self.flow_layout.setHorizontalSpacing(16)
        self.flow_layout.setVerticalSpacing(16)
        
        self.scroll_left.setWidget(self.flow_container)
        left_layout.addWidget(self.scroll_left)
        splitter.addWidget(self.left_panel)

        # Sağ Kolon (Tezgah / Fiş)
        self.right_panel = QFrame()
        self.right_panel.setAttribute(Qt.WA_StyledBackground, True)
        self.right_panel.setStyleSheet("""
            QFrame {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                border-radius: 12px;
            }
        """)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        fis_baslik = SubtitleLabel("Sepetiniz")
        fis_baslik.setStyleSheet("font-weight: bold; color: #1F2937; background: transparent; border: none;")
        right_layout.addWidget(fis_baslik)

        # Cart Items
        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setFrameShape(QFrame.NoFrame)
        self.cart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cart_scroll.setStyleSheet("background: transparent; border: none;")
        
        self.cart_container = QWidget()
        self.cart_container.setStyleSheet("background: transparent;")
        self.cart_layout = QVBoxLayout(self.cart_container)
        self.cart_layout.setContentsMargins(0, 0, 0, 0)
        self.cart_layout.setSpacing(0)
        self.cart_layout.setAlignment(Qt.AlignTop)
        
        self.cart_scroll.setWidget(self.cart_container)
        right_layout.addWidget(self.cart_scroll, stretch=1)

        # Toplam Tutar
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("background: transparent; border-top: 2px dashed #D1D5DB;")
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 16, 0, 0)

        self.lbl_toplam = TitleLabel("Genel Toplam: 0,00 ₺")
        self.lbl_toplam.setAlignment(Qt.AlignRight)
        self.lbl_toplam.setStyleSheet("font-size: 32px; font-weight: bold; color: #111827; border: none;")
        bottom_layout.addWidget(self.lbl_toplam)

        # Ödeme Butonları
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(12)
        
        self.btn_nakit = PushButton("💵 Nakit")
        self.btn_nakit.setFixedHeight(60)
        self.btn_nakit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_nakit.setStyleSheet("""
            PushButton { background-color: #66BB6A; color: white; font-size: 18px; font-weight: bold; border-radius: 10px; border: none; }
            PushButton:hover { background-color: #57A65A; }
        """)
        self.btn_nakit.clicked.connect(lambda: self._odeme_yap("Nakit"))
        btns_layout.addWidget(self.btn_nakit)

        self.btn_kredi = PushButton("💳 Kredi Kartı")
        self.btn_kredi.setFixedHeight(60)
        self.btn_kredi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_kredi.setStyleSheet("""
            PushButton { background-color: #6CA0DC; color: white; font-size: 18px; font-weight: bold; border-radius: 10px; border: none; }
            PushButton:hover { background-color: #5B8CBE; }
        """)
        self.btn_kredi.clicked.connect(lambda: self._odeme_yap("Kredi Kartı"))
        btns_layout.addWidget(self.btn_kredi)

        self.btn_veresiye = PushButton("📝 Veresiye / Cari")
        self.btn_veresiye.setFixedHeight(60)
        self.btn_veresiye.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_veresiye.setStyleSheet("""
            PushButton { background-color: #E28743; color: white; font-size: 18px; font-weight: bold; border-radius: 10px; border: none; }
            PushButton:hover { background-color: #C6763A; }
        """)
        self.btn_veresiye.clicked.connect(self._veresiye_modal_ac)
        btns_layout.addWidget(self.btn_veresiye)

        bottom_layout.addLayout(btns_layout)
        right_layout.addWidget(bottom_frame)

        splitter.addWidget(self.right_panel)
        splitter.setSizes([650, 450])
        root.addWidget(splitter, stretch=1)

        self._verileri_yukle()

    def _verileri_yukle(self):
        self.tum_urunler = self._service.tum_urunleri_getir()
        self._filtrele(self.search_input.text())

    def _filtrele(self, metin: str):
        # Akıcı olması için mevcut widget'ları temizle
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget() if hasattr(item, "widget") else item
            if widget:
                widget.deleteLater()

        metin = metin.lower()
        eklenen = 0
        for u in self.tum_urunler:
            ad = (u.get("ad") or "").lower()
            kod = (u.get("kod") or "").lower()
            if not metin or metin in ad or metin in kod:
                kart = PosUrunKarti(u, on_click=self._sepete_ekle)
                self.flow_layout.addWidget(kart)
                eklenen += 1
                if eklenen > 50:  # Performans için max 50 ürün göster
                    break
                    
        # FlowLayout'un yüksekliğini güncellemesi için
        self.flow_layout.update()

    def _sepete_ekle(self, urun: dict):
        urun_id = urun["id"]
        if urun_id in self.cart:
            self.cart[urun_id]["miktar"] += 1
        else:
            self.cart[urun_id] = {"urun": urun, "miktar": 1}
        self._sepet_guncelle()

    def _sepet_miktar_degistir(self, urun_id: int, degisim: int):
        if urun_id in self.cart:
            yeni = self.cart[urun_id]["miktar"] + degisim
            if yeni <= 0:
                del self.cart[urun_id]
            else:
                self.cart[urun_id]["miktar"] = yeni
            self._sepet_guncelle()

    def _sepetten_sil(self, urun_id: int):
        if urun_id in self.cart:
            del self.cart[urun_id]
            self._sepet_guncelle()

    def _sepet_guncelle(self):
        # Arayüzü temizle
        while self.cart_layout.count():
            item = self.cart_layout.takeAt(0)
            widget = item.widget() if hasattr(item, "widget") else item
            if widget:
                widget.deleteLater()

        toplam = 0.0
        for uid, data in self.cart.items():
            urun = data["urun"]
            miktar = data["miktar"]
            ara_toplam = miktar * urun.get("satis_fiyati", 0.0)
            toplam += ara_toplam
            
            w = CartItemWidget(
                urun=urun,
                miktar=miktar,
                on_miktar_degis=self._sepet_miktar_degistir,
                on_sil=self._sepetten_sil
            )
            self.cart_layout.insertWidget(self.cart_layout.count() - 1, w)

        self.lbl_toplam.setText(f"Genel Toplam: {para_formatla(toplam)}")

    def _odeme_yap(self, odeme_tipi: str, musteri: str = None):
        if not self.cart:
            InfoBar.warning(title="Hata", content="Sepet boş!", parent=self, duration=2000)
            return

        # Stoktan düş ve satışı tamamla
        try:
            for uid, data in self.cart.items():
                eski_stok = data["urun"].get("stok", 0)
                yeni_stok = max(0, eski_stok - data["miktar"])
                
                # Stok güncellenirken (fark < 0 olduğu için) UrunService "ÇIKIŞ" logu atacaktır.
                self._service.stok_guncelle(uid, yeni_stok)
            
            mesaj = f"Satış ({odeme_tipi}) başarıyla tamamlandı!"
            if musteri:
                mesaj += f"\nMüşteri: {musteri}"
                
            InfoBar.success(title="Başarılı", content=mesaj, parent=self, duration=3000)
            
            # Reset
            self.cart.clear()
            self._sepet_guncelle()
            self._verileri_yukle() # Stoklar güncellendiği için sol paneli tazele

        except Exception as e:
            InfoBar.error(title="Hata", content=f"İşlem sırasında hata oluştu:\n{e}", parent=self, duration=4000)

    def _veresiye_modal_ac(self):
        if not self.cart:
            InfoBar.warning(title="Hata", content="Sepet boş!", parent=self, duration=2000)
            return
            
        toplam = sum(d["miktar"] * d["urun"].get("satis_fiyati", 0.0) for d in self.cart.values())
        dialog = VeresiyeDialog(tutar=toplam, parent=self)
        if dialog.exec_():
            self._odeme_yap("Veresiye/Cari", musteri=dialog.musteri_adi)
