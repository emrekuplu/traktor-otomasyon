# =============================================================================
#  views/stock_screen.py
#  Sorumluluk : Ürün & Stok Yönetimi ekranı – İki kademeli yapı:
#               Sayfa 0 → Marka Vitrini
#               Sayfa 1 → Seçilen markaya göre filtrelenmiş ürün listesi
#  ÖNEMLİ     : sqlite3 veya doğrudan DB kodu BULUNMAZ.
# =============================================================================

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QDialog, QStackedWidget, QLabel
)
from qfluentwidgets import (
    SubtitleLabel, PrimaryPushButton, PushButton,
    FlowLayout, SearchLineEdit, ComboBox, InfoBar, CaptionLabel,
    IconWidget, FluentIcon, StrongBodyLabel
)
from constants import BG_COLOR, TEXT_MUTED, ANA_MARKALAR
from services.urun_service import UrunService
from views.urun_ekle_dialog import UrunEkleDialog
from views.urun_karti import UrunKarti
from views.marka_vitrini import MarkaVitrini
from views.filtre_vitrini import FiltreVitrini


def _opaque_widget(parent=None, color: str = BG_COLOR) -> QWidget:
    w = QWidget(parent)
    w.setAttribute(Qt.WA_StyledBackground, True)
    w.setStyleSheet(f"background-color: {color};")
    return w


# ── Sayfa indeksleri ──────────────────────────────────────────────────────────
SAYFA_VITRIN  = 0
SAYFA_URUNLER = 1
SAYFA_FILTRE_VITRINI = 2


class StockScreen(QWidget):
    """
    İki kademeli ürün & stok yönetimi ekranı.

    Sayfa 0 – MarkaVitrini: 9 ana marka + Diğer + Tüm Markalar kutularını gösterir.
    Sayfa 1 – Ürün Listesi: Seçilen markaya göre filtrelenmiş ürün kartları.
    """

    def __init__(self, go_back, parent=None):
        super().__init__(parent)
        self._go_back = go_back
        self._service = UrunService()
        self._aktif_marka: str | None = None   # "Tüm Markalar" / "Diğer" / "Fiat" vb.
        self._aktif_filtre_tipi: str | None = None
        self.kart_listesi: list[UrunKarti] = []

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        # ── Ana QStackedWidget ────────────────────────────────────────────────
        self.stack = QStackedWidget(self)
        self.stack.setAttribute(Qt.WA_StyledBackground, True)
        self.stack.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.stack)

        # ── Sayfa 0: Marka Vitrini ────────────────────────────────────────────
        self.vitrin = MarkaVitrini(
            go_back=go_back,
            on_marka_sec=self._marka_secildi,
            on_filtre_vitrini_sec=self._filtre_vitrini_secildi,
        )
        self.stack.addWidget(self.vitrin)

        # ── Sayfa 1: Ürün Listesi ─────────────────────────────────────────────
        self.stack.addWidget(self._urunler_sayfasi_olustur())
        
        # ── Sayfa 2: Filtre Vitrini ───────────────────────────────────────────
        self.filtre_vitrin_ekrani = FiltreVitrini(
            go_back=self._vitrine_don_from_filtre,
            on_filtre_sec=self._filtre_secildi
        )
        self.stack.addWidget(self.filtre_vitrin_ekrani)

        self.stack.setCurrentIndex(SAYFA_VITRIN)

    # ── Ürün Listesi Sayfası Kurulumu ──────────────────────────────────────────

    def _urunler_sayfasi_olustur(self) -> QWidget:
        """Sayfa 1'i (ürün kartları) oluşturup döndürür."""
        sayfa = QWidget()
        sayfa.setAttribute(Qt.WA_StyledBackground, True)
        sayfa.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(sayfa)
        root.setContentsMargins(24, 20, 24, 0)
        root.setSpacing(14)

        # ── Üst Bar ──────────────────────────────────────────────────────────
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.btn_vitrine_don = PushButton("⬅  Markalara Dön")
        self.btn_vitrine_don.setFixedHeight(38)
        self.btn_vitrine_don.clicked.connect(self._vitrine_don)
        top_bar.addWidget(self.btn_vitrine_don)

        self.btn_yeni = PrimaryPushButton("+ Yeni Ürün")
        self.btn_yeni.setFixedHeight(38)
        self.btn_yeni.clicked.connect(self._pencere_ac_ve_ekle)
        top_bar.addWidget(self.btn_yeni)

        self.arama = SearchLineEdit()
        self.arama.setPlaceholderText("Ürün veya kod ara…")
        self.arama.setFixedHeight(38)
        self.arama.textChanged.connect(self._filtrele)
        top_bar.addWidget(self.arama, stretch=3)

        self.kat_filtresi = ComboBox()
        self.kat_filtresi.setFixedHeight(38)
        self.kat_filtresi.currentIndexChanged.connect(self._filtrele)
        top_bar.addWidget(self.kat_filtresi, stretch=2)

        self.stok_filtresi = ComboBox()
        self.stok_filtresi.addItems([
            "Tüm Ürünler", "Stokta ( > 10 )", "Kritik Stok ( <= 10 )", "Tükenenler ( 0 )"
        ])
        self.stok_filtresi.setFixedHeight(38)
        self.stok_filtresi.currentIndexChanged.connect(self._filtrele)
        top_bar.addWidget(self.stok_filtresi, stretch=2)

        root.addLayout(top_bar)

        # Başlık (marka adı dinamik güncellenir)
        self.baslik_lbl = SubtitleLabel("📦  Ürün Listesi")
        root.addWidget(self.baslik_lbl)

        # ── Scroll + FlowLayout ───────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet(
            f"QScrollArea, #qt_scrollarea_viewport {{ border: none; background-color: {BG_COLOR}; }}"
        )
        self.tasiyici = _opaque_widget(color=BG_COLOR)
        self.flow = FlowLayout(self.tasiyici, needAni=False)
        self.flow.setContentsMargins(6, 10, 6, 30)
        self.flow.setHorizontalSpacing(18)
        self.flow.setVerticalSpacing(18)

        self.scroll.setWidget(self.tasiyici)
        root.addWidget(self.scroll)

        # ── Boş Durum (Empty State) ──────────────────────────────────────────
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        self.empty_icon = IconWidget(FluentIcon.SEARCH)
        self.empty_icon.setFixedSize(64, 64)
        empty_layout.addWidget(self.empty_icon, 0, Qt.AlignCenter)
        
        self.empty_lbl = StrongBodyLabel("Aramanızla eşleşen parça bulunamadı.")
        self.empty_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; margin-top: 10px;")
        empty_layout.addWidget(self.empty_lbl, 0, Qt.AlignCenter)
        
        self.empty_widget.setVisible(False)
        root.addWidget(self.empty_widget)

        return sayfa

    # ── Geçiş Mantığı ─────────────────────────────────────────────────────────

    def _marka_secildi(self, marka: str):
        """Vitrin'de bir markaya tıklandığında çağrılır."""
        self._aktif_marka = marka
        self._aktif_filtre_tipi = None
        self.verileri_yukle()
        self.stack.setCurrentIndex(SAYFA_URUNLER)

    def _filtre_vitrini_secildi(self):
        self.stack.setCurrentIndex(SAYFA_FILTRE_VITRINI)

    def _filtre_secildi(self, filtre_tipi: str):
        self._aktif_marka = None
        self._aktif_filtre_tipi = filtre_tipi
        self.verileri_yukle()
        self.stack.setCurrentIndex(SAYFA_URUNLER)

    def _vitrine_don_from_filtre(self):
        self.stack.setCurrentIndex(SAYFA_VITRIN)

    def _vitrine_don(self):
        """'Markalara Dön' veya 'Filtrelere Dön' butonuna basıldığında döner."""
        if self._aktif_filtre_tipi is not None:
            self.stack.setCurrentIndex(SAYFA_FILTRE_VITRINI)
        else:
            self._aktif_marka = None
            self.vitrin.yenile()           # Sayıları güncelle
            self.stack.setCurrentIndex(SAYFA_VITRIN)

    # ── Veri İşlemleri ────────────────────────────────────────────────────────

    def verileri_yukle(self):
        """Aktif markaya göre ürünleri çeker ve kartları dizer."""
        # Kartları temizle
        for kart in self.kart_listesi:
            self.flow.removeWidget(kart)
            kart.deleteLater()
        self.kart_listesi.clear()

        # Markaya veya Filtreye göre veri çek
        marka = self._aktif_marka
        filtre_tipi = self._aktif_filtre_tipi

        if filtre_tipi is not None:
            urunler = self._service.alt_kategoriye_gore_getir(filtre_tipi)
            baslik = f"⚙️  {filtre_tipi}"
        elif marka is None or marka == "Tüm Markalar":
            urunler = self._service.tum_urunleri_getir()
            baslik  = "📦  Tüm Ürünler"
        elif marka == "Diğer Markalar":
            urunler = self._service.diger_markalari_getir()
            baslik  = "📦  Diğer Markalar"
        else:
            urunler = self._service.markaya_gore_getir(marka)
            baslik  = f"📦  {marka}"

        self.baslik_lbl.setText(baslik)

        kategoriler = {"Tüm Kategoriler"}
        for u in urunler:
            kart = UrunKarti(
                u["id"], u["ad"], u["kod"], u["kategori"], u["stok"],
                resim_yolu=u.get("resim_yolu", ""),
                marka=u.get("marka", "Diğer"),
                alis_fiyati=u.get("alis_fiyati", 0.0),
                satis_fiyati=u.get("satis_fiyati", 0.0),
                alt_kategori=u.get("alt_kategori", "Yok"),
                on_refresh=self.verileri_yukle,
            )
            self.flow.addWidget(kart)
            self.kart_listesi.append(kart)
            kategoriler.add(u["kategori"])

        # Kategori filtresini güncelle
        self.kat_filtresi.blockSignals(True)
        self.kat_filtresi.clear()
        diger_kat = sorted(k for k in kategoriler if k != "Tüm Kategoriler")
        self.kat_filtresi.addItems(["Tüm Kategoriler"] + diger_kat)
        self.kat_filtresi.blockSignals(False)

        # Sorunun kalıcı çözümü: 
        # Çok sayıda ürün eklendikten sonra Qt henüz widget'ların gerçek 
        # boyutlarını hesaplamamış olabilir. Bu yüzden layout'u zorla 
        # güncelleme işlemini 50 milisaniye (çok kısa bir an) gecikmeyle, 
        # uygulama döngüsü (event loop) nefes aldıktan sonra yapıyoruz.
        QTimer.singleShot(50, self._gecikmeli_layout_guncelle)

    def _gecikmeli_layout_guncelle(self):
        """FlowLayout'un donmasını engellemek için gecikmeli tetiklenen güncelleme."""
        self._filtrele()
        if self.tasiyici.layout():
            self.tasiyici.layout().invalidate()
        self.tasiyici.adjustSize()

    def _pencere_ac_ve_ekle(self):
        """Yeni ürün ekleme diyalogunu açar."""
        # Veritabanındaki tüm benzersiz kategorileri çekiyoruz ki
        # sadece aktif markanın kategorileriyle kısıtlı kalmasın.
        mevcut_kategoriler = self._service.kategorileri_getir()
        dialog = UrunEkleDialog(mevcut_kategoriler, self.window())

        # Aktif marka varsa ComboBox'ı önceden seç
        if self._aktif_marka and self._aktif_marka not in ("Tüm Markalar", "Diğer Markalar"):
            idx = dialog.input_marka.findText(self._aktif_marka)
            if idx >= 0:
                dialog.input_marka.setCurrentIndex(idx)

        if dialog.exec_() == QDialog.Accepted:
            ad, kod, kat, stok, secilen_resim, marka, alis, satis, alt_kategori = dialog.yeni_veri
            try:
                sonuc = self._service.urun_ekle(
                    ad, kod, kat, stok, secilen_resim, marka, alis, satis, alt_kategori
                )
                InfoBar.success(
                    "Başarılı",
                    f"{sonuc['ad']} eklendi. Kod: {sonuc['kod']}",
                    parent=self.window(),
                )
                self.verileri_yukle()
            except ValueError as exc:
                InfoBar.error("Hata", str(exc), parent=self.window())

    # ── Filtreleme ────────────────────────────────────────────────────────────

    def set_filter_critical(self):
        """Dışarıdan (örneğin Dashboard) tetiklenerek sadece kritik stokları filtreler."""
        self._aktif_marka = "Tüm Markalar"
        self.verileri_yukle()
        self.stok_filtresi.setCurrentIndex(2) # 2 = Kritik Stok (<=10)

    def _filtrele(self):
        """Arama, kategori ve stok filtrelerine göre kartları göster/gizle."""
        metin       = self.arama.text().lower().strip()
        stok_idx    = self.stok_filtresi.currentIndex()
        secilen_kat = self.kat_filtresi.currentText()

        gorunen_sayisi = 0

        for kart in self.kart_listesi:
            metin_ok = (metin in kart.urun_adi.lower()) or (metin in kart.urun_kodu.lower())

            if   stok_idx == 1: stok_ok = kart.stok_adedi > 10
            elif stok_idx == 2: stok_ok = 0 < kart.stok_adedi <= 10
            elif stok_idx == 3: stok_ok = kart.stok_adedi == 0
            else:               stok_ok = True

            kat_ok = (secilen_kat == "Tüm Kategoriler") or (kart.kategori == secilen_kat)
            
            is_visible = (metin_ok and stok_ok and kat_ok)
            kart.setVisible(is_visible)
            if is_visible:
                gorunen_sayisi += 1

        if gorunen_sayisi == 0:
            if not self.kart_listesi:
                self.empty_icon.setIcon(FluentIcon.FOLDER)
                self.empty_lbl.setText("Bu markada henüz ürün bulunmuyor.")
            else:
                self.empty_icon.setIcon(FluentIcon.SEARCH)
                self.empty_lbl.setText("Aramanızla eşleşen parça yok.")
            self.empty_widget.setVisible(True)
            self.scroll.setVisible(False)
        else:
            self.empty_widget.setVisible(False)
            self.scroll.setVisible(True)
