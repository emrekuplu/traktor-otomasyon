# =============================================================================
#  database/db_manager.py
#  Sorumluluk : SQLite veritabanı bağlantısını yönetmek, tabloları oluşturmak
#               ve gerektiğinde örnek veri eklemek.
#  ÖNEMLİ     : Bu modülde PyQt5 veya iş mantığı kodu BULUNMAZ.
# =============================================================================

import sqlite3
from contextlib import closing
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
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        # WAL Mode ve Timeout ayarları ile kilitlenme koruması ve performans
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

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

        with closing(cls.baglanti_al()) as conn, conn:
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

            # Cariler tablosunu siliyoruz/pasife alıyoruz (artık düz metin tutacağız)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kasalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    bakiye REAL NOT NULL DEFAULT 0.0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bankalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    bakiye REAL NOT NULL DEFAULT 0.0,
                    komisyon_orani REAL DEFAULT 0.0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satislar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fis_no TEXT UNIQUE NOT NULL,
                    musteri_adi TEXT,
                    toplam_tutar REAL NOT NULL,
                    indirim REAL DEFAULT 0.0,
                    net_tutar REAL NOT NULL,
                    odeme_durumu TEXT NOT NULL, -- 'ODENDI', 'KISMEN', 'ODENMEDI'
                    tarih DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satis_detaylari (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    satis_id INTEGER NOT NULL,
                    urun_id INTEGER NOT NULL,
                    miktar INTEGER NOT NULL,
                    birim_fiyat REAL NOT NULL,
                    ara_toplam REAL NOT NULL,
                    FOREIGN KEY(satis_id) REFERENCES satislar(id),
                    FOREIGN KEY(urun_id) REFERENCES urunler(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS odemeler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    satis_id INTEGER,
                    musteri_adi TEXT,
                    odeme_tipi TEXT NOT NULL, -- 'NAKIT', 'KREDI_KARTI', 'VERESIYE'
                    kasa_id INTEGER,
                    banka_id INTEGER,
                    tutar REAL NOT NULL,
                    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(satis_id) REFERENCES satislar(id),
                    FOREIGN KEY(kasa_id) REFERENCES kasalar(id),
                    FOREIGN KEY(banka_id) REFERENCES bankalar(id)
                )
            """)

            # ── Sütun Migrasyonları (Tablolar önceden yaratıldıysa kolon ekleme) ─
            mevcut_sutunlar = [row[1] for row in cursor.execute("PRAGMA table_info(urunler)").fetchall()]
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

            # satislar tablosunda musteri_adi kontrolü
            satislar_cols = [row[1] for row in cursor.execute("PRAGMA table_info(satislar)").fetchall()]
            if "musteri_adi" not in satislar_cols:
                cursor.execute("ALTER TABLE satislar ADD COLUMN musteri_adi TEXT DEFAULT 'Perakende Müşteri'")
                
            # odemeler tablosunda musteri_adi kontrolü
            odemeler_cols = [row[1] for row in cursor.execute("PRAGMA table_info(odemeler)").fetchall()]
            if "musteri_adi" not in odemeler_cols:
                cursor.execute("ALTER TABLE odemeler ADD COLUMN musteri_adi TEXT DEFAULT 'Perakende Müşteri'")
                
            # stok_hareketleri tablosunda aciklama kontrolü
            stok_hareketleri_cols = [row[1] for row in cursor.execute("PRAGMA table_info(stok_hareketleri)").fetchall()]
            if "aciklama" not in stok_hareketleri_cols:
                cursor.execute("ALTER TABLE stok_hareketleri ADD COLUMN aciklama TEXT DEFAULT ''")

            # ── Eski kayıtların düzeltilmesi (Migration) ───────────────────────
            cursor.execute("UPDATE urunler SET marka = 'Diğer' WHERE marka IS NULL OR marka = ''")

            # Mevcut mutlak resim yollarını sadece dosya adı kalacak şekilde güncelle
            cursor.execute("SELECT id, resim_yolu FROM urunler WHERE resim_yolu IS NOT NULL AND resim_yolu != ''")
            for uid, resim_yolu in cursor.fetchall():
                if os.path.isabs(resim_yolu):
                    dosya_adi = os.path.basename(resim_yolu)
                    cursor.execute("UPDATE urunler SET resim_yolu = ? WHERE id = ?", (dosya_adi, uid))

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

            # ── Varsayılan Kasa ve Banka ───────────────────────────────────────
            cursor.execute("SELECT COUNT(*) FROM kasalar")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO kasalar (ad, bakiye) VALUES ('Merkez Kasa (Nakit)', 0.0)")

            cursor.execute("SELECT COUNT(*) FROM bankalar")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO bankalar (ad, bakiye, komisyon_orani) VALUES ('POS / Banka Hesabı', 0.0, 0.0)")

            conn.commit()
