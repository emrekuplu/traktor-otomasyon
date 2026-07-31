# =============================================================================
#  services/dosya_service.py
#  Sorumluluk : Ürün resimlerinin dosya sisteminde yönetimi.
#               - Resim klasörünü oluşturma
#               - Seçilen resmi benzersiz adla kopyalama
#               - Veritabanı yedekleme
#  ÖNEMLİ     : Bu modülde PyQt5 nesneleri BULUNMAZ.
# =============================================================================

import os
import shutil
from constants import RESIM_KLASORU, DB_PATH


class DosyaService:
    """
    Dosya sistemi işlemlerini kapsülleyen servis sınıfı.
    """

    @staticmethod
    def resim_klasorunu_hazirla() -> None:
        """Resim klasörü yoksa oluşturur."""
        os.makedirs(RESIM_KLASORU, exist_ok=True)

    @staticmethod
    def resim_kaydet(secilen_yol: str, kod: str) -> str | None:
        """
        Seçilen resim dosyasını `urun_resimleri/` klasörüne kopyalar.

        Parametreler
        ------------
        secilen_yol : Kullanıcının seçtiği orijinal dosya yolu.
        kod         : Ürün kodu (dosya adı oluşturmak için kullanılır).

        Döndürür
        --------
        Dosya adı (str) veya None (dosya yoksa / seçilmediyse).
        """
        if not secilen_yol or not os.path.isfile(secilen_yol):
            return None

        DosyaService.resim_klasorunu_hazirla()

        uzanti = os.path.splitext(secilen_yol)[1].lower() or ".jpg"
        # Kod içindeki özel karakterleri dosya adı için temizle
        guvenli_kod = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in kod
        )
        dosya_adi = f"{guvenli_kod}{uzanti}"
        hedef = os.path.join(RESIM_KLASORU, dosya_adi)
        shutil.copy(secilen_yol, hedef)
        
        # Sadece dosya adını döndür (mutlak yol kaydedilmesin)
        return dosya_adi

    @staticmethod
    def backup_database(target_path: str) -> bool:
        """
        Aktif SQLite veritabanı dosyasını belirtilen hedef konuma kopyalar.
        
        Parametreler
        ------------
        target_path : Kopyalanacak hedef dosya yolu.
        
        Döndürür
        --------
        Başarılı olursa True döndürür, aksi takdirde Exception fırlatır.
        """
        try:
            shutil.copy2(DB_PATH, target_path)
            return True
        except Exception as e:
            raise Exception(f"Veritabanı yedeklenirken hata oluştu: {e}")
