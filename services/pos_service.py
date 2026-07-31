# =============================================================================
#  services/pos_service.py
#  Sorumluluk : POS, Satış ve Muhasebe İşlemleri için İş Mantığı
# =============================================================================

import uuid
from datetime import datetime
from database.db_manager import DbManager
from database.pos_repository import PosRepository
from database.urun_repository import UrunRepository
from contextlib import closing
from core.events import event_bus


class PosService:
    def __init__(self):
        self._pos_repo = PosRepository()
        self._urun_repo = UrunRepository()

    def _generate_fis_no(self) -> str:
        """Benzersiz bir fiş/fatura numarası üretir."""
        return "Fis-" + datetime.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:6].upper()
        
    def kasalari_getir(self) -> list[dict]:
        return self._pos_repo.kasalari_getir()
        
    def bankalari_getir(self) -> list[dict]:
        return self._pos_repo.bankalari_getir()

    def finans_ozeti_getir(self) -> dict:
        return self._pos_repo.finans_ozeti_getir()
        
    def son_odemeleri_getir(self, filtre_tipi: str = "Tüm İşlemler", limit: int = 50) -> list[dict]:
        return self._pos_repo.son_odemeleri_getir(filtre_tipi, limit)

    def satis_yap(self, sepet_items: list[dict], odemeler: list[dict], indirim: float = 0.0, musteri_adi: str = "Perakende Müşteri") -> int:
        """
        Sepetteki ürünlerin satışını yapar ve ödemeyi muhasebeleştirir.
        
        Parametreler:
        - sepet_items: [{'urun_id': int, 'miktar': int, 'birim_fiyat': float}]
        - odemeler: [{'odeme_tipi': 'NAKIT'|'KREDI_KARTI'|'VERESIYE', 'tutar': float, 'kasa_id': int|None, 'banka_id': int|None}]
        - indirim: Toplam üzerinden yapılan indirim.
        - musteri_adi: Satışın kime yapıldığı.
        
        Döndürür:
        - satis_id
        """
        # Toplam ve net hesaplamaları
        toplam_tutar = sum(item['miktar'] * item['birim_fiyat'] for item in sepet_items)
        net_tutar = toplam_tutar - indirim
        
        # Tüm ödemelerin toplamını bul (Veresiye hariç gerçek tahsilatlar)
        toplam_tahsilat = sum(p['tutar'] for p in odemeler if p['odeme_tipi'] != 'VERESIYE')
        
        # Ödeme durumunu belirle
        if toplam_tahsilat >= net_tutar:
            odeme_durumu = 'ODENDI'
        elif toplam_tahsilat > 0:
            odeme_durumu = 'KISMEN'
        else:
            odeme_durumu = 'ODENMEDI'

        # Eğer eksik tahsilat varsa (Veresiye) kontrol yapılabilir
        eksik_tutar = net_tutar - toplam_tahsilat
        if eksik_tutar > 0 and musteri_adi == "Perakende Müşteri":
            raise ValueError("Eksik ödeme (Veresiye) işlemi için lütfen bir Müşteri Adı giriniz!")

        fis_no = self._generate_fis_no()

        with closing(DbManager.baglanti_al()) as conn, conn:
            cursor = conn.cursor()
            
            # 1. Satış Başlığı (satislar)
            cursor.execute(
                """
                INSERT INTO satislar (fis_no, musteri_adi, toplam_tutar, indirim, net_tutar, odeme_durumu) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (fis_no, musteri_adi, toplam_tutar, indirim, net_tutar, odeme_durumu)
            )
            satis_id = cursor.lastrowid
            
            # 2. Satış Detayları (satis_detaylari) ve Stok Düşme
            for item in sepet_items:
                urun_id = item['urun_id']
                miktar = item['miktar']
                birim_fiyat = item['birim_fiyat']
                ara_toplam = miktar * birim_fiyat
                
                # Ürün mevcut mu ve stok yeterli mi?
                urun = cursor.execute("SELECT ad, stok FROM urunler WHERE id = ?", (urun_id,)).fetchone()
                if not urun:
                    raise ValueError(f"Hata: {urun_id} ID'li ürün bulunamadı.")
                
                # Stok kontrolü (Eksiye düşmeyi önlemek için, ancak şu anlık uyarı da verilebilir)
                if urun[1] < miktar:
                    raise ValueError(f"Yetersiz stok! Ürün: {urun[0]} (Mevcut: {urun[1]})")
                
                # Stok düşüşü
                cursor.execute("UPDATE urunler SET stok = stok - ? WHERE id = ?", (miktar, urun_id))
                
                # Stok hareketi (ÇIKIŞ - SATIŞ)
                cursor.execute(
                    "INSERT INTO stok_hareketleri (urun_id, islem_tipi, miktar, aciklama) VALUES (?, 'ÇIKIŞ', ?, ?)",
                    (urun_id, miktar, f"Satış: {fis_no}")
                )
                
                # Satış detayı ekle
                cursor.execute(
                    """
                    INSERT INTO satis_detaylari (satis_id, urun_id, miktar, birim_fiyat, ara_toplam)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (satis_id, urun_id, miktar, birim_fiyat, ara_toplam)
                )
                
            # 3. Tahsilatlar (odemeler) ve Kasa/Banka bakiye güncellemesi
            for p in odemeler:
                odeme_tipi = p['odeme_tipi']
                tutar = p['tutar']
                kasa_id = p.get('kasa_id')
                banka_id = p.get('banka_id')
                
                if odeme_tipi == 'NAKIT':
                    if not kasa_id:
                        raise ValueError("Nakit ödeme için Kasa seçmelisiniz!")
                    cursor.execute("UPDATE kasalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, kasa_id))
                    
                elif odeme_tipi == 'KREDI_KARTI':
                    if not banka_id:
                        raise ValueError("Kredi Kartı ödemesi için Banka/POS seçmelisiniz!")
                    # Komisyon varsa net bakiye eklenebilir, şimdilik brüt
                    cursor.execute("UPDATE bankalar SET bakiye = bakiye + ? WHERE id = ?", (tutar, banka_id))
                
                # Veresiye hareketlerini eklemeye gerek yok, onlar carinin toplam bakiyesinde toplanacak.
                # Ya da 'VERESIYE' adında bir ödeme kaydı tutulabilir
                cursor.execute(
                    """
                    INSERT INTO odemeler (satis_id, musteri_adi, odeme_tipi, kasa_id, banka_id, tutar)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (satis_id, musteri_adi, odeme_tipi, kasa_id, banka_id, tutar)
                )
                
            # 4. Cari Bakiye Güncelleme (Borçlandırma) kaldırıldı.
            if eksik_tutar > 0:
                # Ekstra veresiye kaydı log için eklenebilir
                cursor.execute(
                    """
                    INSERT INTO odemeler (satis_id, musteri_adi, odeme_tipi, tutar)
                    VALUES (?, ?, 'VERESIYE', ?)
                    """,
                    (satis_id, musteri_adi, eksik_tutar)
                )
                
            # `with closing` blok sonunda otomatik COMMIT, hata varsa otomatik ROLLBACK çalışır.
            
        # İşlem bittiğinde sinyal yay
        event_bus.satis_yapildi.emit()
        event_bus.stok_degisti.emit()
        
        return satis_id

    def satis_sil(self, satis_id: int):
        """Satış ve ilgili ödemeleri siler, stokları ve bakiye artışlarını geri alır."""
        with closing(DbManager.baglanti_al()) as conn, conn:
            cursor = conn.cursor()
            
            # 1. Ödemeleri (Kasaya / Bankaya giren tutarları) geri al (Rollback)
            odemeler = cursor.execute("SELECT odeme_tipi, tutar, kasa_id, banka_id FROM odemeler WHERE satis_id = ?", (satis_id,)).fetchall()
            for odeme in odemeler:
                tip, tutar, k_id, b_id = odeme
                if tip == 'NAKIT' and k_id:
                    cursor.execute("UPDATE kasalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, k_id))
                elif tip == 'KREDI_KARTI' and b_id:
                    cursor.execute("UPDATE bankalar SET bakiye = bakiye - ? WHERE id = ?", (tutar, b_id))
            
            # 2. Stokları iade et (Rollback)
            detaylar = cursor.execute("SELECT urun_id, miktar FROM satis_detaylari WHERE satis_id = ?", (satis_id,)).fetchall()
            for d in detaylar:
                urun_id, miktar = d
                # Stok artır
                cursor.execute("UPDATE urunler SET stok = stok + ? WHERE id = ?", (miktar, urun_id))
                # Stok hareketi iadesi
                cursor.execute(
                    "INSERT INTO stok_hareketleri (urun_id, islem_tipi, miktar, aciklama) VALUES (?, 'GİRİŞ', ?, 'Satış İptali')",
                    (urun_id, miktar)
                )
                
            # 3. Tablolardan satırları sil
            cursor.execute("DELETE FROM odemeler WHERE satis_id = ?", (satis_id,))
            cursor.execute("DELETE FROM satis_detaylari WHERE satis_id = ?", (satis_id,))
            cursor.execute("DELETE FROM satislar WHERE id = ?", (satis_id,))
            
        # Sinyalleri tetikle
        event_bus.islem_silindi.emit()
        event_bus.stok_degisti.emit()
