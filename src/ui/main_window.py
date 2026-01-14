"""
Main Application Window.
Coordinates login and chat screens.
"""

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent

from .styles import Styles
from .login_screen import LoginScreen
from .chat_screen import ChatScreen
from ..models.base import init_database
from ..models.user import User
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.
    Manages navigation between login and chat screens.
    """

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.session_token = None

        # Initialize database
        init_database()

        self.setup_ui()

    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("OBD InsightBot - Vehicle Diagnostics")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(Styles.MAIN_STYLE)

        # Stacked widget for screen navigation
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Login screen
        self.login_screen = LoginScreen()
        self.login_screen.login_successful.connect(self._on_login_success)
        self.stack.addWidget(self.login_screen)

        # Chat screen placeholder (created on login)
        self.chat_screen = None

        logger.info("Main window initialized")

    def _on_login_success(self, user: User, token: str):
        """Handle successful login."""
        logger.info(f"User logged in: {user.username}")

        self.current_user = user
        self.session_token = token

        # Create chat screen
        if self.chat_screen:
            self.stack.removeWidget(self.chat_screen)
            self.chat_screen.deleteLater()

        self.chat_screen = ChatScreen(user, token)
        self.chat_screen.logout_requested.connect(self._on_logout)
        self.stack.addWidget(self.chat_screen)

        # Switch to chat screen
        self.stack.setCurrentWidget(self.chat_screen)

    def _on_logout(self):
        """Handle logout."""
        logger.info(f"User logged out: {self.current_user.username if self.current_user else 'Unknown'}")

        self.current_user = None
        self.session_token = None

        # Reset login screen
        self.login_screen.reset()

        # Switch to login screen
        self.stack.setCurrentWidget(self.login_screen)

        # Clean up chat screen
        if self.chat_screen:
            self.stack.removeWidget(self.chat_screen)
            self.chat_screen.deleteLater()
            self.chat_screen = None

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        # Logout if user is logged in
        if self.session_token:
            from ..services.auth_service import AuthService
            AuthService.logout(self.session_token)

        logger.info("Application closing")
        event.accept()
