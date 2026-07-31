# =============================================================================
#  services/urun_service.py
#  Sorumluluk : Ürünlerle ilgili tüm iş kurallarını yönetir.
#  ÖNEMLİ     : Bu modülde PyQt5 nesneleri BULUNMAZ.
# =============================================================================

import sqlite3
from database.urun_repository import UrunRepository
from services.dosya_service import DosyaService
from constants import ANA_MARKALAR
from core.events import event_bus


class UrunService:
    """
    Ürün iş mantığı servisi.
    View katmanı bu sınıfın metodlarını çağırır;
    doğrudan veritabanına veya dosya sistemine erişmez.
    """

    def __init__(self):
        self._repo = UrunRepository()
        self._dosya = DosyaService()

    # ── Okuma İşlemleri ────────────────────────────────────────────────────────

    def tum_urunleri_getir(self) -> list[dict]:
        """Tüm ürün kayıtlarını döndürür."""
        return self._repo.tum_urunleri_getir()

    def markaya_gore_getir(self, marka: str) -> list[dict]:
        """Belirli markaya ait ürünleri döndürür."""
        return self._repo.markaya_gore_getir(marka)

    def alt_kategoriye_gore_getir(self, alt_kategori: str) -> list[dict]:
        """Belirli alt kategoriye ait ürünleri döndürür."""
        return self._repo.alt_kategoriye_gore_getir(alt_kategori)

    def diger_markalari_getir(self) -> list[dict]:
        """Ana 9 marka listesinde bulunmayan tüm ürünleri döndürür."""
        return self._repo.diger_markalari_getir(ANA_MARKALAR)

    def kritik_urunleri_getir(self) -> list[dict]:
        """Stoğu 5 ve altında olan ürünleri döndürür."""
        return self._repo.kritik_urunleri_getir()

    def marka_sayilarini_getir(self) -> dict[str, int]:
        """Her markadaki ürün adedini {marka: adet} dict olarak döndürür."""
        return self._repo.marka_sayilarini_getir()

    def kpi_getir(self) -> dict:
        """
        Dashboard KPI verilerini döndürür.
        {toplam_urun, depo_degeri, kritik_stok}
        """
        return self._repo.kpi_getir()

    def kategorileri_getir(self) -> list[str]:
        """Veritabanındaki benzersiz kategorileri döndürür."""
        return self._repo.kategorileri_getir()

    def stok_hareketleri_getir(self, urun_id: int) -> list[dict]:
        """Ürüne ait son 10 stok hareketini döndürür."""
        return self._repo.stok_hareketleri_getir(urun_id)

    def tum_stok_hareketleri_getir(self, filtre: str | None = None) -> list[dict]:
        """
        Sistemdeki tüm stok hareketlerini ürün bilgisiyle birlikte döndürür.

        filtre=None   → tümü
        filtre='GİRİŞ' → yalnızca girişler (Gelen)
        filtre='ÇIKIŞ' → yalnızca çıkışlar (Giden)
        """
        return self._repo.tum_stok_hareketleri_getir(filtre)

    def stok_hareketi_sil(self, hareket_id: int) -> None:
        """Belirtilen ID'ye sahip stok hareketini siler."""
        self._repo.stok_hareketi_sil(hareket_id)

    def tum_stok_hareketlerini_temizle(self) -> int:
        """
        Tüm stok hareketlerini siler.
        Döndürür: Silinen kayıt sayısı.
        """
        return self._repo.tum_stok_hareketlerini_temizle()


    # ── Yazma İşlemleri ───────────────────────────────────────────────────────

    def urun_ekle(
        self,
        ad: str,
        kod: str,
        kategori: str,
        stok: int,
        secilen_resim: str = "",
        marka: str = "Diğer",
        alis_fiyati: float = 0.0,
        satis_fiyati: float = 0.0,
        alt_kategori: str = "Yok",
    ) -> dict:
        """
        Yeni ürün ekler.

        İş Kuralları
        ------------
        1. `kod` boşsa otomatik "TRK-XXXX" üretir.
        2. `secilen_resim` geçerliyse resmi kopyalar.
        3. Kod çakışmasında ValueError fırlatır.

        Döndürür: {'ad': str, 'kod': str, 'marka': str}
        """
        if not kod:
            max_id = self._repo.max_id_getir()
            kod = f"TRK-{max_id + 1000}"

        hedef_resim_yolu = self._dosya.resim_kaydet(secilen_resim, kod)

        try:
            self._repo.ekle(
                ad, kod, kategori, stok, hedef_resim_yolu,
                marka, alis_fiyati, satis_fiyati, alt_kategori
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"{kod} kodlu bir ürün zaten var!")

        event_bus.urun_degisti.emit()
        return {"ad": ad, "kod": kod, "marka": marka}

    def stok_guncelle(self, urun_id: int, yeni_stok: int) -> None:
        """Ürünün stok değerini günceller ve log atar."""
        eski_urun = self._repo.urun_getir(urun_id)
        if eski_urun:
            fark = yeni_stok - eski_urun["stok"]
            if fark != 0:
                islem_tipi = "GİRİŞ" if fark > 0 else "ÇIKIŞ"
                aciklama = f"Stok Artırma ({eski_urun['ad']})" if fark > 0 else f"Stok Azaltma ({eski_urun['ad']})"
                self._repo.stok_hareket_ekle(urun_id, islem_tipi, abs(fark), aciklama)

        self._repo.stok_guncelle(urun_id, yeni_stok)
        event_bus.urun_degisti.emit()
        event_bus.stok_degisti.emit()

    def urun_guncelle(
        self,
        urun_id: int,
        ad: str,
        kod: str,
        kategori: str,
        stok: int,
        mevcut_kod: str = "",
        secilen_resim: str = "",
        marka: str = "Diğer",
        alis_fiyati: float = 0.0,
        satis_fiyati: float = 0.0,
        alt_kategori: str = "Yok",
    ) -> None:
        """
        Ürün bilgilerini günceller.

        İş Kuralları
        ------------
        - `kod` boş bırakılırsa `mevcut_kod` korunur.
        - `secilen_resim` geçerliyse resim kopyalanıp güncellenir.
        - `secilen_resim` boşsa mevcut resim korunur.
        """
        if not kod:
            kod = mevcut_kod

        eski_urun = self._repo.urun_getir(urun_id)
        if eski_urun:
            fark = stok - eski_urun["stok"]
            if fark != 0:
                islem_tipi = "GİRİŞ" if fark > 0 else "ÇIKIŞ"
                aciklama = f"Stok Artırma ({eski_urun['ad']})" if fark > 0 else f"Stok Azaltma ({eski_urun['ad']})"
                self._repo.stok_hareket_ekle(urun_id, islem_tipi, abs(fark), aciklama)

        hedef_resim = self._dosya.resim_kaydet(secilen_resim, kod) if secilen_resim else None
        self._repo.guncelle(
            urun_id, ad, kod, kategori, stok,
            resim_yolu=hedef_resim,
            marka=marka,
            alis_fiyati=alis_fiyati,
            satis_fiyati=satis_fiyati,
            alt_kategori=alt_kategori,
        )
        event_bus.urun_degisti.emit()
        event_bus.stok_degisti.emit()

    def urun_sil(self, urun_id: int) -> None:
        """Ürünü veritabanından kalıcı olarak siler."""
        self._repo.sil(urun_id)
        event_bus.urun_degisti.emit()
