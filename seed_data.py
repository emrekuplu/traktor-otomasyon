# =============================================================================
#  seed_data.py
#  Test verilerini (ürünler, satışlar, stok hareketleri vb.) veritabanına ekler.
# =============================================================================

import os
import random
import uuid
from datetime import datetime, timedelta
from contextlib import closing

# Proje kök dizinini sys.path'e ekleyelim ki database, constants modülleri bulunabilsin
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DbManager

def _generate_fis_no(days_ago: int = 0) -> str:
    dt = datetime.now() - timedelta(days=days_ago)
    return "Fis-" + dt.strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:6].upper()

def seed_db():
    print("Veritabanı bağlantısı başlatılıyor...")
    DbManager.baslat()
    
    with closing(DbManager.baglanti_al()) as conn, conn:
        cursor = conn.cursor()
        
        # ── 1. ÜRÜNLER (10-15 adet) ────────────────────────────────────────────────
        print("1. Traktör parçaları ekleniyor...")
        urunler_data = [
            ("Traktör Yağ Filtresi", "TRK-001", "Filtreler", 25, "New Holland", 150.0, 220.0, "Motor"),
            ("Yakıt Pompası Komple", "TRK-002", "Motor", 5, "Massey Ferguson", 1200.0, 1650.0, "Yakıt Sistemi"),
            ("Ön Far Camı", "TRK-003", "Aydınlatma", 12, "Diğer", 250.0, 380.0, "Dış Aksam"),
            ("Debriyaj Balatası", "TRK-004", "Aktarma", 8, "Diğer", 1800.0, 2400.0, "Şanzıman"),
            ("Hava Filtresi Dış", "TRK-005", "Filtreler", 40, "Fiat", 200.0, 310.0, "Motor"),
            ("Hidrolik Direksiyon Pompası", "TRK-006", "Hidrolik", 3, "New Holland", 2500.0, 3300.0, "Direksiyon"),
            ("Arka Stop Lambası", "TRK-007", "Aydınlatma", 20, "Steyr", 180.0, 275.0, "Dış Aksam"),
            ("Marş Dinamosu 12V", "TRK-008", "Elektrik", 6, "Erkunt", 1400.0, 1950.0, "Motor"),
            ("Su Pompası (Devirdaim)", "TRK-009", "Motor", 10, "Same", 650.0, 890.0, "Soğutma"),
            ("PTO (Kuyruk Mili) Keçesi", "TRK-010", "Aktarma", 50, "Başak", 80.0, 130.0, "Şanzıman"),
            ("Şanzıman Dişlisi 3. Vites", "TRK-011", "Aktarma", 4, "Deutz Fahr", 2100.0, 2850.0, "Şanzıman"),
            ("Kontak Anahtarı Seti", "TRK-012", "Elektrik", 15, "Massey Ferguson", 350.0, 520.0, "Kabin"),
            ("Silindir Kapak Contası", "TRK-013", "Motor", 18, "Ford", 420.0, 600.0, "Conta"),
            ("Radyatör Kapağı", "TRK-014", "Motor", 30, "New Holland", 90.0, 150.0, "Soğutma"),
            ("Akümülatör 105 Amper", "TRK-015", "Elektrik", 7, "Diğer", 2800.0, 3500.0, "Akü"),
        ]
        
        for d in urunler_data:
            try:
                cursor.execute(
                    "INSERT INTO urunler (ad, kod, kategori, stok, marka, alis_fiyati, satis_fiyati, alt_kategori) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    d
                )
            except Exception as e:
                print(f"Ürün eklenemedi ({d[1]}): {e}")
        print("Yeni ürünler başarıyla eklendi.")
            
        # ── 2. KASA & BANKA BAKİYELERİ ─────────────────────────────────────────────
        print("2. Kasa ve Banka bakiyeleri güncelleniyor...")
        cursor.execute("UPDATE kasalar SET bakiye = bakiye + 12500 WHERE ad = 'Merkez Kasa (Nakit)'")
        cursor.execute("UPDATE bankalar SET bakiye = bakiye + 45000 WHERE ad = 'POS / Banka Hesabı'")
        
        # Kasa ve Banka ID'lerini al
        kasa_id = cursor.execute("SELECT id FROM kasalar WHERE ad = 'Merkez Kasa (Nakit)'").fetchone()
        kasa_id = kasa_id[0] if kasa_id else None
        
        banka_id = cursor.execute("SELECT id FROM bankalar WHERE ad = 'POS / Banka Hesabı'").fetchone()
        banka_id = banka_id[0] if banka_id else None

        # ── 3. ÖRNEK SATIŞLAR (Son 1-2 Gün) ────────────────────────────────────────
        print("3. Örnek satışlar ve detayları ekleniyor...")
        
        # Son eklenen ürünlerin ID'lerini alalım
        urun_id_list = [row[0] for row in cursor.execute("SELECT id FROM urunler").fetchall()]
        if len(urun_id_list) >= 3 and kasa_id and banka_id:
            satislar_data = [
                {"musteri": "Perakende Müşteri", "gun": 1, "tip": "NAKIT", "tutar": 1330.0},
                {"musteri": "Ahmet Yılmaz", "gun": 2, "tip": "KREDI_KARTI", "tutar": 2400.0},
                {"musteri": "Mehmet Usta", "gun": 0, "tip": "VERESIYE", "tutar": 1950.0},
            ]
            
            for s in satislar_data:
                fis_no = _generate_fis_no(s["gun"])
                dt = (datetime.now() - timedelta(days=s["gun"])).strftime("%Y-%m-%d %H:%M:%S")
                
                odeme_durumu = "ODENDI" if s["tip"] != "VERESIYE" else "ODENMEDI"
                
                cursor.execute(
                    """
                    INSERT INTO satislar (fis_no, musteri_adi, toplam_tutar, net_tutar, odeme_durumu, tarih) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (fis_no, s["musteri"], s["tutar"], s["tutar"], odeme_durumu, dt)
                )
                satis_id = cursor.lastrowid
                
                # Ödeme Kaydı
                if s["tip"] == "NAKIT":
                    cursor.execute(
                        "INSERT INTO odemeler (satis_id, musteri_adi, odeme_tipi, kasa_id, tutar, tarih) VALUES (?, ?, ?, ?, ?, ?)",
                        (satis_id, s["musteri"], s["tip"], kasa_id, s["tutar"], dt)
                    )
                elif s["tip"] == "KREDI_KARTI":
                    cursor.execute(
                        "INSERT INTO odemeler (satis_id, musteri_adi, odeme_tipi, banka_id, tutar, tarih) VALUES (?, ?, ?, ?, ?, ?)",
                        (satis_id, s["musteri"], s["tip"], banka_id, s["tutar"], dt)
                    )
                else: # VERESIYE
                    cursor.execute(
                        "INSERT INTO odemeler (satis_id, musteri_adi, odeme_tipi, tutar, tarih) VALUES (?, ?, ?, ?, ?)",
                        (satis_id, s["musteri"], s["tip"], s["tutar"], dt)
                    )
                
                # Rastgele 1 veya 2 ürün seçip detay ekle
                secilenler = random.sample(urun_id_list, k=random.choice([1, 2]))
                for u_id in secilenler:
                    cursor.execute(
                        "INSERT INTO satis_detaylari (satis_id, urun_id, miktar, birim_fiyat, ara_toplam) VALUES (?, ?, ?, ?, ?)",
                        (satis_id, u_id, 1, s["tutar"]/len(secilenler), s["tutar"]/len(secilenler))
                    )
                    # Stok hareketi çıkışı
                    cursor.execute(
                        "INSERT INTO stok_hareketleri (urun_id, islem_tipi, miktar, aciklama, tarih) VALUES (?, 'ÇIKIŞ', ?, ?, ?)",
                        (u_id, 1, f"Satış: {fis_no}", dt)
                    )

        # ── 4. MANUEL STOK LOGLARI ─────────────────────────────────────────────────
        print("4. Manuel stok artırma/azaltma logları ekleniyor...")
        if len(urun_id_list) > 1:
            u_id1 = urun_id_list[0]
            u_id2 = urun_id_list[1]
            dt_log = (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute(
                "INSERT INTO stok_hareketleri (urun_id, islem_tipi, miktar, aciklama, tarih) VALUES (?, 'GİRİŞ', 5, 'Stok Artırma', ?)",
                (u_id1, dt_log)
            )
            cursor.execute(
                "INSERT INTO stok_hareketleri (urun_id, islem_tipi, miktar, aciklama, tarih) VALUES (?, 'ÇIKIŞ', 2, 'Stok Azaltma', ?)",
                (u_id2, dt_log)
            )

    print("\n✅ Tüm test verileri başarıyla eklendi! 'python main.py' komutuyla projeyi çalıştırıp görebilirsiniz.")

if __name__ == "__main__":
    seed_db()
