# =============================================================================
#  views/login_screen.py
#  Sorumluluk : Kullanıcı giriş ekranı (Ekran 0).
# =============================================================================

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from qfluentwidgets import (
    TitleLabel, CaptionLabel, PrimaryPushButton,
    LineEdit, PasswordLineEdit, InfoBar
)
from constants import BG_COLOR, CARD_BG, TEXT_MUTED, DEMO_USERNAME, DEMO_PASSWORD


class LoginScreen(QWidget):
    def __init__(self, on_success, parent=None):
        super().__init__(parent)
        self.on_success = on_success
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        root = QVBoxLayout(self)
        root.addStretch(2)
        h_center = QHBoxLayout()
        h_center.addStretch(1)
        h_center.addWidget(self._build_card(), 0, Qt.AlignCenter)
        h_center.addStretch(1)
        root.addLayout(h_center)
        root.addStretch(3)

    def _build_card(self) -> QWidget:
        card = QWidget()
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setFixedWidth(400)
        card.setStyleSheet(f"QWidget {{ background-color: {CARD_BG}; border-radius: 18px; }}")

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(45)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(42, 48, 42, 48)
        layout.setSpacing(18)

        icon_lbl = QLabel("⚙️")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 48px; background: transparent;")
        layout.addWidget(icon_lbl)

        title = TitleLabel("Anıl Oto")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = CaptionLabel("Masaüstü Otomasyon Sistemi")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        layout.addWidget(sub)

        self.input_user = LineEdit()
        self.input_user.setPlaceholderText("Kullanıcı Adı")
        self.input_user.setFixedHeight(44)
        self.input_user.returnPressed.connect(self._attempt_login)
        layout.addWidget(self.input_user)

        self.input_pass = PasswordLineEdit()
        self.input_pass.setPlaceholderText("Şifre")
        self.input_pass.setFixedHeight(44)
        self.input_pass.returnPressed.connect(self._attempt_login)
        layout.addWidget(self.input_pass)

        self.btn_login = PrimaryPushButton("Giriş Yap")
        self.btn_login.setFixedHeight(46)
        self.btn_login.clicked.connect(self._attempt_login)
        layout.addWidget(self.btn_login)

        hint = CaptionLabel("Demo: admin / admin")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        layout.addWidget(hint)
        return card

    def _attempt_login(self):
        if (self.input_user.text().strip() == DEMO_USERNAME
                and self.input_pass.text().strip() == DEMO_PASSWORD):
            self.input_pass.clear()
            self.on_success()
        else:
            InfoBar.error(
                "Giriş Başarısız",
                "Kullanıcı adı veya şifre hatalı.",
                parent=self.window(),
            )
