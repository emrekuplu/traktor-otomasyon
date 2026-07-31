# =============================================================================
#  database/urun_repository.py
#  Sorumluluk : `urunler` tablosuyla ilgili TÜM SQL sorgularını kapsar.
#  ÖNEMLİ     : Bu modülde PyQt5 veya iş mantığı kodu BULUNMAZ.
#               Yalnızca ham veri (liste, dict, tuple) döndürür.
# =============================================================================

import sqlite3
from datetime import datetime
from database.db_manager import DbManager


class UrunRepository:
    """
    `urunler` tablosu için veri erişim nesnesi (Data Access Object).
    Tüm SQL sorguları buradadır; üst katmanlar ham SQL yazmaz.
    """

    _ORTAK_SUTUNLAR = (
        "id, ad, kod, kategori, stok, resim_yolu, marka, "
        "alis_fiyati, satis_fiyati, alt_kategori"
    )

    # ── Okuma İşlemleri ────────────────────────────────────────────────────────

    def tum_urunleri_getir(self) -> list[dict]:
        """Tüm ürünleri en yeni eklenenden başlayarak döndürür."""
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {self._ORTAK_SUTUNLAR} FROM urunler ORDER BY id DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def markaya_gore_getir(self, marka: str) -> list[dict]:
        """Belirli markaya ait ürünleri döndürür."""
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {self._ORTAK_SUTUNLAR} FROM urunler "
                "WHERE marka = ? ORDER BY id DESC",
                (marka,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def alt_kategoriye_gore_getir(self, alt_kategori: str) -> list[dict]:
        """Belirli alt kategoriye ait ürünleri döndürür."""
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {self._ORTAK_SUTUNLAR} FROM urunler "
                "WHERE alt_kategori = ? ORDER BY id DESC",
                (alt_kategori,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def diger_markalari_getir(self, ana_markalar: list[str]) -> list[dict]:
        """Ana markalar listesinde BULUNMAYAN veya 'Diğer' olan ürünleri döndürür."""
        yer_tutucu = ", ".join("?" * len(ana_markalar))
        sorgu = (
            f"SELECT {self._ORTAK_SUTUNLAR} FROM urunler "
            f"WHERE marka NOT IN ({yer_tutucu}) OR marka IS NULL OR marka = '' "
            "ORDER BY id DESC"
        )
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sorgu, ana_markalar)
            return [dict(row) for row in cursor.fetchall()]

    def kritik_urunleri_getir(self) -> list[dict]:
        """Stoğu 5 ve altında olan ürünleri stok miktarına göre artan sırayla döndürür."""
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {self._ORTAK_SUTUNLAR} FROM urunler WHERE stok <= 5 ORDER BY stok ASC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def marka_sayilarini_getir(self) -> dict[str, int]:
        """Her markadaki ürün adedini {marka: adet} dict olarak döndürür."""
        with DbManager.baglanti_al() as conn:
            rows = conn.execute(
                "SELECT COALESCE(marka, 'Diğer'), COUNT(*) FROM urunler GROUP BY marka"
            ).fetchall()
            return {row[0]: row[1] for row in rows}

    def kpi_getir(self) -> dict:
        """
        Dashboard için tek sorguda 3 KPI döndürür:
          - toplam_urun   : Toplam ürün çeşidi
          - depo_degeri   : SUM(alis_fiyati × stok)
          - kritik_stok   : Stoğu 5 ve altındaki ürün sayısı
        """
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT
                    COUNT(*)                                     AS toplam_urun,
                    COALESCE(SUM(alis_fiyati * stok), 0)        AS depo_degeri,
                    COUNT(CASE WHEN stok <= 5 THEN 1 END)        AS kritik_stok
                FROM urunler
            """).fetchone()
            return dict(row)

    def kategorileri_getir(self) -> list[str]:
        """Veritabanındaki benzersiz kategorileri alfabetik sırayla döndürür."""
        with DbManager.baglanti_al() as conn:
            rows = conn.execute(
                "SELECT DISTINCT kategori FROM urunler ORDER BY kategori"
            ).fetchall()
            return [row[0] for row in rows]

    def max_id_getir(self) -> int:
        """MAX(id) değerini döndürür; tablo boşsa 0 döndürür."""
        with DbManager.baglanti_al() as conn:
            row = conn.execute("SELECT MAX(id) FROM urunler").fetchone()
            return row[0] if row[0] is not None else 0

    def kod_var_mi(self, kod: str) -> bool:
        """Verilen kodun tabloda kayıtlı olup olmadığını kontrol eder."""
        with DbManager.baglanti_al() as conn:
            row = conn.execute(
                "SELECT 1 FROM urunler WHERE kod = ?", (kod,)
            ).fetchone()
            return row is not None

    def urun_getir(self, urun_id: int) -> dict | None:
        """Belirtilen ID'ye sahip ürünü döndürür."""
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                f"SELECT {self._ORTAK_SUTUNLAR} FROM urunler WHERE id = ?",
                (urun_id,)
            ).fetchone()
            return dict(row) if row else None

    # ── Yazma İşlemleri ───────────────────────────────────────────────────────

    def ekle(self, ad: str, kod: str, kategori: str, stok: int,
             resim_yolu: str | None, marka: str = "Diğer",
             alis_fiyati: float = 0.0, satis_fiyati: float = 0.0,
             alt_kategori: str = "Yok") -> None:
        """
        Yeni ürün kaydı ekler.
        Raises: sqlite3.IntegrityError – kod zaten varsa.
        """
        with DbManager.baglanti_al() as conn:
            conn.execute(
                "INSERT INTO urunler "
                "(ad, kod, kategori, stok, resim_yolu, marka, alis_fiyati, satis_fiyati, alt_kategori) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ad, kod, kategori, stok, resim_yolu, marka, alis_fiyati, satis_fiyati, alt_kategori),
            )

    def stok_guncelle(self, urun_id: int, yeni_stok: int) -> None:
        """Ürünün stok değerini günceller."""
        with DbManager.baglanti_al() as conn:
            conn.execute(
                "UPDATE urunler SET stok = ? WHERE id = ?",
                (yeni_stok, urun_id),
            )

    def guncelle(self, urun_id: int, ad: str, kod: str,
                 kategori: str, stok: int,
                 resim_yolu: str | None = None,
                 marka: str = "Diğer",
                 alis_fiyati: float = 0.0,
                 satis_fiyati: float = 0.0,
                 alt_kategori: str = "Yok") -> None:
        """
        Ürünün alanlarını günceller.
        `resim_yolu` None geçilirse mevcut değer korunur.
        """
        with DbManager.baglanti_al() as conn:
            if resim_yolu is None:
                conn.execute(
                    "UPDATE urunler "
                    "SET ad=?, kod=?, kategori=?, stok=?, marka=?, "
                    "alis_fiyati=?, satis_fiyati=?, alt_kategori=? WHERE id=?",
                    (ad, kod, kategori, stok, marka, alis_fiyati, satis_fiyati, alt_kategori, urun_id),
                )
            else:
                conn.execute(
                    "UPDATE urunler "
                    "SET ad=?, kod=?, kategori=?, stok=?, resim_yolu=?, marka=?, "
                    "alis_fiyati=?, satis_fiyati=?, alt_kategori=? WHERE id=?",
                    (ad, kod, kategori, stok, resim_yolu, marka, alis_fiyati, satis_fiyati, alt_kategori, urun_id),
                )

    def sil(self, urun_id: int) -> None:
        """Ürünü veritabanından kalıcı olarak siler."""
        with DbManager.baglanti_al() as conn:
            conn.execute("DELETE FROM urunler WHERE id = ?", (urun_id,))
            conn.execute("DELETE FROM stok_hareketleri WHERE urun_id = ?", (urun_id,))

    # ── Stok Hareketleri İşlemleri ───────────────────────────────────────────

    def stok_hareket_ekle(self, urun_id: int, islem_tipi: str, miktar: int) -> None:
        """Stok hareket logunu kaydeder."""
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with DbManager.baglanti_al() as conn:
            conn.execute(
                "INSERT INTO stok_hareketleri (urun_id, islem_tipi, miktar, tarih) VALUES (?, ?, ?, ?)",
                (urun_id, islem_tipi, miktar, simdi)
            )

    def stok_hareketleri_getir(self, urun_id: int, limit: int = 10) -> list[dict]:
        """Belirtilen ürünün en son hareketlerini getirir."""
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, islem_tipi, miktar, tarih FROM stok_hareketleri "
                "WHERE urun_id = ? ORDER BY id DESC LIMIT ?",
                (urun_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def tum_stok_hareketleri_getir(self, filtre: str | None = None) -> list[dict]:
        """
        Tüm stok hareketlerini ürün adı ve koduyla birlikte döndürür.

        Parametreler
        ------------
        filtre : None   → tüm hareketler
                 'GİRİŞ' → yalnızca stok girişleri
                 'ÇIKIŞ' → yalnızca stok çıkışları
        """
        with DbManager.baglanti_al() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if filtre:
                cursor.execute(
                    "SELECT sh.id, sh.islem_tipi, sh.miktar, sh.tarih, "
                    "u.ad AS urun_ad, u.kod AS urun_kod "
                    "FROM stok_hareketleri sh "
                    "JOIN urunler u ON sh.urun_id = u.id "
                    "WHERE sh.islem_tipi = ? "
                    "ORDER BY sh.id DESC",
                    (filtre,)
                )
            else:
                cursor.execute(
                    "SELECT sh.id, sh.islem_tipi, sh.miktar, sh.tarih, "
                    "u.ad AS urun_ad, u.kod AS urun_kod "
                    "FROM stok_hareketleri sh "
                    "JOIN urunler u ON sh.urun_id = u.id "
                    "ORDER BY sh.id DESC"
                )
            return [dict(row) for row in cursor.fetchall()]

    def stok_hareketi_sil(self, hareket_id: int) -> None:
        """Belirtilen ID'ye sahip stok hareketini siler."""
        with DbManager.baglanti_al() as conn:
            conn.execute(
                "DELETE FROM stok_hareketleri WHERE id = ?",
                (hareket_id,)
            )

    def tum_stok_hareketlerini_temizle(self) -> int:
        """
        Tüm stok hareketlerini siler.
        Döndürür: Silinen satır sayısı.
        """
        with DbManager.baglanti_al() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stok_hareketleri")
            return cursor.rowcount

