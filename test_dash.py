import sys
from PyQt5.QtWidgets import QApplication
from views.dashboard_screen import DashboardScreen

app = QApplication(sys.argv)
try:
    d = DashboardScreen(go_stock=lambda: None, go_finance=lambda: None, go_order=lambda: None)
    print("Dashboard basariyla olusturuldu.")
except Exception as e:
    import traceback
    traceback.print_exc()

