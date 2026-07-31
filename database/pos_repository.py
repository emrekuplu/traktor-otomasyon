# =============================================================================
#  database/pos_repository.py
#  Sorumluluk : POS, Cari, Kasa, Banka tablolarına erişim.
# =============================================================================

import sqlite3
from contextlib import closing
from database.db_manager import DbManager


class PosRepository:
    # ── Kasalar & Bankalar ────────────────────────────────────────────────────

    def kasalari_getir(self) -> list[dict]:
        with closing(DbManager.baglanti_al()) as conn, conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kasalar")
            return [dict(row) for row in cursor.fetchall()]

    def bankalari_getir(self) -> list[dict]:
        with closing(DbManager.baglanti_al()) as conn, conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bankalar")
            return [dict(row) for row in cursor.fetchall()]

    # ── Finansal Özet (Dashboard için) ────────────────────────────────────────

    def finans_ozeti_getir(self) -> dict:
        """Kasa ve bankalardaki toplam bakiyeyi döndürür."""
        with closing(DbManager.baglanti_al()) as conn, conn:
            toplam_kasa = conn.execute("SELECT COALESCE(SUM(bakiye), 0) FROM kasalar").fetchone()[0]
            toplam_banka = conn.execute("SELECT COALESCE(SUM(bakiye), 0) FROM bankalar").fetchone()[0]

            return {
                "toplam_kasa": toplam_kasa,
                "toplam_banka": toplam_banka,
                "toplam_alacak": 0.0,
                "toplam_borc": 0.0
            }

    def son_odemeleri_getir(self, filtre_tipi: str = "Tüm İşlemler", limit: int = 50) -> list[dict]:
        """Son yapılan ödeme/tahsilat hareketlerini döndürür."""
        sorgu_odemeler = """
            SELECT 
                'ODEME' AS tip, o.id, o.odeme_tipi, o.tutar, o.tarih, o.satis_id,
                o.musteri_adi AS cari_ad, k.ad AS kasa_ad, b.ad AS banka_ad,
                s.fis_no
            FROM odemeler o
            LEFT JOIN kasalar k ON o.kasa_id = k.id
            LEFT JOIN bankalar b ON o.banka_id = b.id
            LEFT JOIN satislar s ON o.satis_id = s.id
        """
        
        sorgu_stok = """
            SELECT 
                'STOK' AS tip, sh.id, 
                CASE WHEN sh.islem_tipi = 'GİRİŞ' THEN 'STOK_ARTIS' ELSE 'STOK_AZALIS' END AS odeme_tipi,
                0.0 AS tutar, sh.tarih, NULL AS satis_id,
                sh.aciklama AS cari_ad, '-' AS kasa_ad, '-' AS banka_ad,
                '-' AS fis_no
            FROM stok_hareketleri sh
            WHERE sh.aciklama LIKE 'Stok Artırma%' OR sh.aciklama LIKE 'Stok Azaltma%'
        """

        if filtre_tipi == "Satış İşlemleri":
            sorgu = f"SELECT * FROM ({sorgu_odemeler}) AS tum_hareketler ORDER BY tarih DESC LIMIT ?"
        elif filtre_tipi == "Stok İşlemleri":
            sorgu = f"SELECT * FROM ({sorgu_stok}) AS tum_hareketler ORDER BY tarih DESC LIMIT ?"
        else: # Tüm İşlemler
            sorgu = f"SELECT * FROM ({sorgu_odemeler} UNION ALL {sorgu_stok}) AS tum_hareketler ORDER BY tarih DESC LIMIT ?"

        with closing(DbManager.baglanti_al()) as conn, conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sorgu, (limit,))
            return [dict(row) for row in cursor.fetchall()]
