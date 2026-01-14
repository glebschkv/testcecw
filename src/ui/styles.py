"""
UI Styles and Themes for OBD InsightBot.
Implements BR8: Severity color coding.
"""


class SeverityStyles:
    """Severity-based color schemes for BR8."""

    CRITICAL = {
        "background": "#FFEBEE",
        "border": "#F44336",
        "text": "#C62828",
        "icon": "🔴",
        "name": "Critical"
    }

    WARNING = {
        "background": "#FFF8E1",
        "border": "#FFC107",
        "text": "#F57F17",
        "icon": "🟡",
        "name": "Warning"
    }

    NORMAL = {
        "background": "#E8F5E9",
        "border": "#4CAF50",
        "text": "#2E7D32",
        "icon": "🟢",
        "name": "Normal"
    }

    @classmethod
    def get(cls, severity: str) -> dict:
        """Get style dict for a severity level."""
        styles = {
            "critical": cls.CRITICAL,
            "warning": cls.WARNING,
            "normal": cls.NORMAL
        }
        return styles.get(severity.lower(), cls.NORMAL)


class Styles:
    """Application-wide styles."""

    # Color Palette
    PRIMARY_COLOR = "#1976D2"
    PRIMARY_DARK = "#1565C0"
    PRIMARY_LIGHT = "#42A5F5"
    SECONDARY_COLOR = "#424242"
    BACKGROUND = "#FAFAFA"
    SURFACE = "#FFFFFF"
    ERROR = "#D32F2F"
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    DIVIDER = "#BDBDBD"

    # Main Application Style
    MAIN_STYLE = """
    QMainWindow {
        background-color: #FAFAFA;
    }

    QWidget {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
    }

    QPushButton {
        background-color: #1976D2;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #1565C0;
    }

    QPushButton:pressed {
        background-color: #0D47A1;
    }

    QPushButton:disabled {
        background-color: #BDBDBD;
        color: #757575;
    }

    QLineEdit {
        padding: 10px;
        border: 2px solid #BDBDBD;
        border-radius: 4px;
        background-color: white;
    }

    QLineEdit:focus {
        border-color: #1976D2;
    }

    QTextEdit {
        padding: 10px;
        border: 2px solid #BDBDBD;
        border-radius: 4px;
        background-color: white;
    }

    QTextEdit:focus {
        border-color: #1976D2;
    }

    QLabel {
        color: #212121;
    }

    QListWidget {
        border: 1px solid #BDBDBD;
        border-radius: 4px;
        background-color: white;
    }

    QListWidget::item {
        padding: 10px;
        border-bottom: 1px solid #EEEEEE;
    }

    QListWidget::item:selected {
        background-color: #E3F2FD;
        color: #1976D2;
    }

    QListWidget::item:hover {
        background-color: #F5F5F5;
    }

    QScrollBar:vertical {
        background-color: #F5F5F5;
        width: 12px;
        border-radius: 6px;
    }

    QScrollBar::handle:vertical {
        background-color: #BDBDBD;
        border-radius: 6px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #9E9E9E;
    }

    QMessageBox {
        background-color: white;
    }

    QDialog {
        background-color: #FAFAFA;
    }
    """

    # Login Screen Style
    LOGIN_STYLE = """
    QFrame#loginFrame {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
    }

    QLabel#titleLabel {
        font-size: 24px;
        font-weight: bold;
        color: #1976D2;
    }

    QLabel#subtitleLabel {
        font-size: 14px;
        color: #757575;
    }

    QLineEdit {
        min-height: 40px;
    }

    QPushButton#loginButton {
        min-height: 45px;
        font-size: 16px;
    }

    QPushButton#registerButton {
        background-color: transparent;
        color: #1976D2;
        border: 2px solid #1976D2;
    }

    QPushButton#registerButton:hover {
        background-color: #E3F2FD;
    }
    """

    # Chat Screen Style
    CHAT_STYLE = """
    QFrame#chatFrame {
        background-color: white;
        border-radius: 8px;
    }

    QFrame#sidebarFrame {
        background-color: #263238;
        border-radius: 0px;
    }

    QLabel#sidebarTitle {
        color: white;
        font-size: 16px;
        font-weight: bold;
    }

    QListWidget#chatList {
        background-color: transparent;
        border: none;
        color: white;
    }

    QListWidget#chatList::item {
        padding: 12px;
        border-bottom: 1px solid #37474F;
        color: #ECEFF1;
    }

    QListWidget#chatList::item:selected {
        background-color: #37474F;
        color: white;
    }

    QListWidget#chatList::item:hover {
        background-color: #455A64;
    }

    QPushButton#newChatButton {
        background-color: #1976D2;
        color: white;
        border-radius: 4px;
        padding: 12px;
    }

    QTextEdit#messageInput {
        border: 2px solid #E0E0E0;
        border-radius: 20px;
        padding: 10px 15px;
        font-size: 14px;
    }

    QTextEdit#messageInput:focus {
        border-color: #1976D2;
    }

    QPushButton#sendButton {
        background-color: #1976D2;
        border-radius: 20px;
        min-width: 40px;
        min-height: 40px;
    }

    QPushButton#micButton {
        background-color: #757575;
        border-radius: 20px;
        min-width: 40px;
        min-height: 40px;
    }

    QPushButton#micButton:hover {
        background-color: #616161;
    }
    """

    # Message Bubble Styles
    USER_MESSAGE_STYLE = """
    QFrame {
        background-color: #E3F2FD;
        border-radius: 15px;
        padding: 10px;
        margin: 5px;
    }
    """

    ASSISTANT_MESSAGE_STYLE = """
    QFrame {
        background-color: #F5F5F5;
        border-radius: 15px;
        padding: 10px;
        margin: 5px;
    }
    """

    @classmethod
    def get_message_style(cls, severity: str) -> str:
        """Get message style based on severity (BR8)."""
        colors = SeverityStyles.get(severity)
        return f"""
        QFrame {{
            background-color: {colors['background']};
            border-left: 4px solid {colors['border']};
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
        }}
        QLabel {{
            color: {colors['text']};
        }}
        """

    @classmethod
    def get_severity_indicator(cls, severity: str) -> str:
        """Get severity indicator HTML."""
        colors = SeverityStyles.get(severity)
        return f"""
        <span style="color: {colors['border']}; font-weight: bold;">
            {colors['icon']} {colors['name']}
        </span>
        """
