import sys
from PyQt5.QtWidgets import QApplication
from views.urun_ekle_dialog import UrunEkleDialog, UrunDuzenleDialog

app = QApplication(sys.argv)
try:
    d1 = UrunEkleDialog(kategoriler=["Test"])
    print("UrunEkleDialog basariyla olusturuldu.")
    d2 = UrunDuzenleDialog(kategoriler=["Test"], urun_id=1, ad="Test", kod="123", kategori="Test", stok=5)
    print("UrunDuzenleDialog basariyla olusturuldu.")
except Exception as e:
    import traceback
    traceback.print_exc()

