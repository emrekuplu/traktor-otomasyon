# =============================================================================
#  constants.py – Uygulama Geneli Sabitler
#  Tüm katmanlar (database, services, views) bu modülden import eder.
# =============================================================================

import os
import sys

def get_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

def para_formatla(deger: float) -> str:
    """
    Sayıyı Türk lirası formatında gösterir.
    Örnek: 1450.5  →  '1.450,50 ₺'
    """
    try:
        return f"{deger:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"
    except (ValueError, TypeError):
        return "0,00 ₺"

# ── Kimlik Doğrulama ─────────────────────────────────────────────────────────
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "admin"

# ── Veritabanı ────────────────────────────────────────────────────────────────
DB_PATH = get_path("traktor_mete_v2.db")

# ── Renk Paleti ───────────────────────────────────────────────────────────────
BG_COLOR     = "#F5F5F7"
CARD_BG      = "#FFFFFF"
TEXT_PRIMARY = "#1A1A2E"
TEXT_MUTED   = "#6B6B80"

# ── QStackedWidget Ekran İndeksleri ──────────────────────────────────────────
IDX_LOGIN   = 0
IDX_DASH    = 1
IDX_STOCK   = 2
IDX_FINANCE = 3
IDX_ORDER   = 4
IDX_CRITICAL= 5

# ── Dosya Sistemi ─────────────────────────────────────────────────────────────
RESIM_KLASORU = get_path("urun_resimleri")
LOGOLAR_KLASORU = get_path("resources/marka_logolari")
IKON_KLASORU = get_path("resources/icons")

# ── Marka Sistemi ─────────────────────────────────────────────────────────────
# Vitrin ekranındaki 9 ana marka
ANA_MARKALAR = [
    "Fiat", "Ford", "Massey Ferguson", "Steyr",
    "New Holland", "Same", "Deutz Fahr", "Erkunt", "Başak",
]
# Form dropdown'ında gösterilecek tam liste
MARKALAR_FORM = ANA_MARKALAR + ["Diğer"]

# Her marka için vitrin rengi ve emoji ikonu
MARKA_TEMA: dict[str, tuple[str, str, str]] = {
    # marka_adi : (bg_rengi, metin_rengi, emoji)
    "Fiat":             ("#FEE2E2", "#991B1B", "🔴"),
    "Ford":             ("#DBEAFE", "#1E40AF", "🔵"),
    "Massey Ferguson":  ("#FCE7F3", "#9D174D", "🟣"),
    "Steyr":            ("#D1FAE5", "#065F46", "🟢"),
    "New Holland":      ("#FEF9C3", "#854D0E", "💛"),
    "Same":             ("#FFEDD5", "#9A3412", "🟠"),
    "Deutz Fahr":       ("#DCFCE7", "#166534", "🌿"),
    "Erkunt":           ("#E0E7FF", "#3730A3", "🔷"),
    "Başak":            ("#FFF7ED", "#C2410C", "🌾"),
}
# Özel kutular
VITRIN_DIGER_RENK = ("#F3F4F6", "#374151", "📦")
VITRIN_TUM_RENK   = ("#F0F9FF", "#0369A1", "🌐")
