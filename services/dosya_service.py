# =============================================================================
#  services/dosya_service.py
#  Sorumluluk : Ürün resimlerinin dosya sisteminde yönetimi.
#               - Resim klasörünü oluşturma
#               - Seçilen resmi benzersiz adla kopyalama
#  ÖNEMLİ     : Bu modülde PyQt5 nesneleri BULUNMAZ.
# =============================================================================

import os
import shutil
from constants import RESIM_KLASORU


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
        Hedef dosya yolu (str) veya None (dosya yoksa / seçilmediyse).
        """
        if not secilen_yol or not os.path.isfile(secilen_yol):
            return None

        DosyaService.resim_klasorunu_hazirla()

        uzanti = os.path.splitext(secilen_yol)[1].lower() or ".jpg"
        # Kod içindeki özel karakterleri dosya adı için temizle
        guvenli_kod = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in kod
        )
        hedef = os.path.join(RESIM_KLASORU, f"{guvenli_kod}{uzanti}")
        shutil.copy(secilen_yol, hedef)
        return hedef
