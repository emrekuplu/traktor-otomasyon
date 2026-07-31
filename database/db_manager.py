# =============================================================================
#  database/db_manager.py
#  Sorumluluk : SQLite veritabanı bağlantısını yönetmek, tabloları oluşturmak
#               ve gerektiğinde örnek veri eklemek.
#  ÖNEMLİ     : Bu modülde PyQt5 veya iş mantığı kodu BULUNMAZ.
# =============================================================================

import sqlite3
from constants import DB_PATH, RESIM_KLASORU
import os


class DbManager:
    """
    Veritabanı bağlantısını ve şema yönetimini üstlenen sınıf.
    Diğer modüller doğrudan sqlite3 bağlantısı açmak yerine
    `DbManager.baglanti_al()` üzerinden bağlantı kullanmalıdır.
    """

    @staticmethod
    def baglanti_al() -> sqlite3.Connection:
        """
        Yeni bir SQLite bağlantısı döndürür.
        Çağıran taraf bağlantıyı context manager ile yönetmelidir:
            with DbManager.baglanti_al() as conn: ...
        """
        return sqlite3.connect(DB_PATH)

    @classmethod
    def baslat(cls) -> None:
        """
        Uygulamanın ilk açılışında çağrılır.
        - Resim klasörünü oluşturur.
        - Tabloları oluşturur (yoksa).
        - Sütun migrasyonu yapar (resim_yolu).
        - Tablo boşsa gerçekçi örnek veriler ekler.
        """
        # ── Resim klasörü ──────────────────────────────────────────────────────
        os.makedirs(RESIM_KLASORU, exist_ok=True)

        with cls.baglanti_al() as conn:
            cursor = conn.cursor()

            # ── Tablo oluşturma ────────────────────────────────────────────────
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS urunler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    kod TEXT UNIQUE NOT NULL,
                    kategori TEXT NOT NULL,
                    stok INTEGER NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stok_hareketleri (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    urun_id INTEGER NOT NULL,
                    islem_tipi TEXT NOT NULL,
                    miktar INTEGER NOT NULL,
                    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(urun_id) REFERENCES urunler(id)
                )
            """)

            # ── Güvenli sütun migrasyonu ───────────────────────────────────────
            mevcut_sutunlar = [
                row[1]
                for row in cursor.execute("PRAGMA table_info(urunler)").fetchall()
            ]
            if "resim_yolu" not in mevcut_sutunlar:
                cursor.execute("ALTER TABLE urunler ADD COLUMN resim_yolu TEXT")
            if "marka" not in mevcut_sutunlar:
                cursor.execute("ALTER TABLE urunler ADD COLUMN marka TEXT DEFAULT 'Diğer'")
            if "alis_fiyati" not in mevcut_sutunlar:
                cursor.execute("ALTER TABLE urunler ADD COLUMN alis_fiyati REAL DEFAULT 0.0")
            if "satis_fiyati" not in mevcut_sutunlar:
                cursor.execute("ALTER TABLE urunler ADD COLUMN satis_fiyati REAL DEFAULT 0.0")
            if "alt_kategori" not in mevcut_sutunlar:
                cursor.execute("ALTER TABLE urunler ADD COLUMN alt_kategori TEXT DEFAULT 'Yok'")

            # ── Eski kayıtların düzeltilmesi (Migration) ───────────────────────
            cursor.execute("UPDATE urunler SET marka = 'Diğer' WHERE marka IS NULL OR marka = ''")

            # ── Örnek veri (sadece tablo boşsa) ───────────────────────────────
            cursor.execute("SELECT COUNT(*) FROM urunler")
            if cursor.fetchone()[0] == 0:
                ornekler = [
                    # ── Filtre Grubu ──────────────────────────────────────────
                    ("MF 240 Yağ Filtresi (Orijinal)",       "MF-240-YF",   "Filtre Grubu",           45, None),
                    ("Fiat 480 Mazot Filtresi",               "FT-480-MF",   "Filtre Grubu",           30, None),
                    ("New Holland TD65 Hava Filtresi",        "NH-TD65-HF",  "Filtre Grubu",           22, None),
                    # ── Motor & Yakıt Sistemi ─────────────────────────────────
                    ("Fiat 640 Piston Gömlek Seti",           "FT-640-PG",   "Motor & Yakıt Sistemi",   4, None),
                    ("Fiat 480 Devirdaim Pompası",            "FT-480-DP",   "Motor & Yakıt Sistemi",   0, None),
                    ("MF 285 Mazot Pompası (Yüksek Basınç)", "MF-285-MP",   "Motor & Yakıt Sistemi",   7, None),
                    # ── Debriyaj & Şanzıman ───────────────────────────────────
                    ("New Holland TT65 Debriyaj Balatası",   "NH-TT65-DB",  "Debriyaj & Şanzıman",    8, None),
                    ("MF 285 Kuyruk Mili Dişlisi",           "MF-285-KM",   "Debriyaj & Şanzıman",    3, None),
                    # ── Hidrolik & Kaporta ────────────────────────────────────
                    ("Steyr 8073 Hidrolik Pompa",             "ST-8073-HP",  "Hidrolik & Kaporta",      5, None),
                    ("Tümosan 8095 Hidrolik Salmastra Seti", "TM-8095-HS",  "Hidrolik & Kaporta",     14, None),
                    # ── Ön Düzen & Fren ───────────────────────────────────────
                    ("Massey Ferguson 285 Rot Başı",          "MF-285-RB",   "Ön Düzen & Fren",        14, None),
                    ("Tümosan 8095 Fren Balatası",            "TM-8095-FB",  "Ön Düzen & Fren",        20, None),
                    # ── Elektrik & Aydınlatma ─────────────────────────────────
                    ("John Deere 5075E Marş Motoru",          "JD-5075-MM",  "Elektrik & Aydınlatma",   6, None),
                    ("MF 240 Tepe Lambası (LED)",             "MF-240-TL",   "Elektrik & Aydınlatma",  18, None),
                    ("New Holland TD100 Çamurluk Sinyali",   "NH-TD100-CS", "Elektrik & Aydınlatma",  12, None),
                ]
                cursor.executemany(
                    "INSERT INTO urunler (ad, kod, kategori, stok, resim_yolu) VALUES (?, ?, ?, ?, ?)",
                    ornekler,
                )
            conn.commit()
