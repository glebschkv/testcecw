"""
Login and Registration Screen.
Implements BR1: Account Management
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .styles import Styles
from ..services.auth_service import AuthService, AuthenticationError
from ..utils.validators import Validators


class LoginScreen(QWidget):
    """
    Login and registration screen widget.

    Implements:
    - BR1.1: User creates an account
    - BR1.2: User logs-in to their account
    """

    # Signals
    login_successful = pyqtSignal(object, str)  # (User, session_token)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI components."""
        self.setStyleSheet(Styles.LOGIN_STYLE)

        # Main layout with subtle background
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
            }
        """ + Styles.LOGIN_STYLE)

        # Container frame with refined card design
        container = QFrame()
        container.setObjectName("loginFrame")
        container.setFixedWidth(400)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(40, 40, 40, 40)

        # Logo/Icon area - refined diamond icon
        icon_label = QLabel("◆")
        icon_label.setStyleSheet("""
            font-size: 36px;
            color: #6366F1;
            padding: 8px;
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(icon_label)

        # Title
        title = QLabel("InsightBot")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Smart Vehicle Diagnostics")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(subtitle)

        container_layout.addSpacing(12)

        # Stacked widget for login/register forms
        self.stacked_widget = QStackedWidget()

        # Login form
        self.login_form = self._create_login_form()
        self.stacked_widget.addWidget(self.login_form)

        # Register form
        self.register_form = self._create_register_form()
        self.stacked_widget.addWidget(self.register_form)

        container_layout.addWidget(self.stacked_widget)

        main_layout.addWidget(container)

    def _create_login_form(self) -> QWidget:
        """Create the login form."""
        form = QWidget()
        layout = QVBoxLayout(form)
        layout.setSpacing(14)

        # Username
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Username")
        layout.addWidget(self.login_username)

        # Password
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.login_password)

        # Error label with refined styling
        self.login_error = QLabel()
        self.login_error.setObjectName("errorLabel")
        self.login_error.hide()
        layout.addWidget(self.login_error)

        layout.addSpacing(4)

        # Login button
        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("loginButton")
        login_btn.clicked.connect(self._handle_login)
        layout.addWidget(login_btn)

        # Divider with text
        divider_layout = QHBoxLayout()
        divider_left = QFrame()
        divider_left.setFrameShape(QFrame.Shape.HLine)
        divider_left.setStyleSheet("background-color: #E4E4E7;")
        divider_layout.addWidget(divider_left)
        or_label = QLabel("or")
        or_label.setStyleSheet("color: #A1A1AA; font-size: 12px; padding: 0 12px;")
        divider_layout.addWidget(or_label)
        divider_right = QFrame()
        divider_right.setFrameShape(QFrame.Shape.HLine)
        divider_right.setStyleSheet("background-color: #E4E4E7;")
        divider_layout.addWidget(divider_right)
        layout.addLayout(divider_layout)

        # Register link
        register_btn = QPushButton("Create Account")
        register_btn.setObjectName("registerButton")
        register_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(register_btn)

        # Enter key handling
        self.login_password.returnPressed.connect(self._handle_login)

        return form

    def _create_register_form(self) -> QWidget:
        """Create the registration form."""
        form = QWidget()
        layout = QVBoxLayout(form)
        layout.setSpacing(14)

        # Username
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Username")
        layout.addWidget(self.register_username)

        # Password
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Password")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.register_password)

        # Confirm password
        self.register_confirm = QLineEdit()
        self.register_confirm.setPlaceholderText("Confirm Password")
        self.register_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.register_confirm)

        # Error label with refined styling
        self.register_error = QLabel()
        self.register_error.setObjectName("errorLabel")
        self.register_error.hide()
        layout.addWidget(self.register_error)

        layout.addSpacing(4)

        # Register button
        register_btn = QPushButton("Create Account")
        register_btn.setObjectName("loginButton")
        register_btn.clicked.connect(self._handle_register)
        layout.addWidget(register_btn)

        # Back to login
        back_btn = QPushButton("Back to Sign In")
        back_btn.setObjectName("registerButton")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(back_btn)

        return form

    def _handle_login(self):
        """Handle login attempt (BR1.2)."""
        username = self.login_username.text().strip()
        password = self.login_password.text()

        # Validate
        valid, error = Validators.validate_username(username)
        if not valid:
            self._show_login_error(error)
            return

        try:
            user, token = AuthService.login(username, password)
            self.login_error.hide()
            self.login_successful.emit(user, token)
        except AuthenticationError as e:
            self._show_login_error(str(e))

    def _handle_register(self):
        """Handle registration attempt (BR1.1)."""
        username = self.register_username.text().strip()
        password = self.register_password.text()
        confirm = self.register_confirm.text()

        # Validate username
        valid, error = Validators.validate_username(username)
        if not valid:
            self._show_register_error(error)
            return

        # Validate password
        valid, error = Validators.validate_password(password)
        if not valid:
            self._show_register_error(error)
            return

        # Validate passwords match
        valid, error = Validators.validate_passwords_match(password, confirm)
        if not valid:
            self._show_register_error(error)
            return

        try:
            user = AuthService.register(username, password)
            self.register_error.hide()

            # Show success and switch to login
            QMessageBox.information(
                self,
                "Account Created",
                f"Account '{username}' created successfully!\nPlease sign in."
            )

            # Clear fields and switch to login
            self.register_username.clear()
            self.register_password.clear()
            self.register_confirm.clear()
            self.login_username.setText(username)
            self.stacked_widget.setCurrentIndex(0)

        except AuthenticationError as e:
            self._show_register_error(str(e))

    def _show_login_error(self, message: str):
        """Display login error message."""
        self.login_error.setText(message)
        self.login_error.show()

    def _show_register_error(self, message: str):
        """Display registration error message."""
        self.register_error.setText(message)
        self.register_error.show()

    def reset(self):
        """Reset the form fields."""
        self.login_username.clear()
        self.login_password.clear()
        self.login_error.hide()
        self.register_username.clear()
        self.register_password.clear()
        self.register_confirm.clear()
        self.register_error.hide()
        self.stacked_widget.setCurrentIndex(0)
