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
    BACKGROUND = "#F5F7FA"
    SURFACE = "#FFFFFF"
    ERROR = "#D32F2F"
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    DIVIDER = "#E0E0E0"

    # Main Application Style
    MAIN_STYLE = """
    QMainWindow {
        background-color: #F5F7FA;
    }

    QWidget {
        font-family: 'Segoe UI', 'SF Pro Display', -apple-system, Arial, sans-serif;
        font-size: 14px;
        color: #212121;
    }

    QPushButton {
        background-color: #1976D2;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
    }

    QPushButton:hover {
        background-color: #1565C0;
    }

    QPushButton:pressed {
        background-color: #0D47A1;
    }

    QPushButton:disabled {
        background-color: #E0E0E0;
        color: #9E9E9E;
    }

    QLineEdit {
        padding: 12px 14px;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        background-color: #FFFFFF;
        color: #212121;
        selection-background-color: #1976D2;
        selection-color: white;
    }

    QLineEdit:hover {
        border-color: #BDBDBD;
    }

    QLineEdit:focus {
        border-color: #1976D2;
        background-color: #FFFFFF;
    }

    QLineEdit::placeholder {
        color: #9E9E9E;
    }

    QTextEdit {
        padding: 12px;
        border: 2px solid #E0E0E0;
        border-radius: 8px;
        background-color: #FFFFFF;
        color: #212121;
        selection-background-color: #1976D2;
        selection-color: white;
    }

    QTextEdit:hover {
        border-color: #BDBDBD;
    }

    QTextEdit:focus {
        border-color: #1976D2;
        background-color: #FFFFFF;
    }

    QLabel {
        color: #212121;
        background-color: transparent;
    }

    QListWidget {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        background-color: #FFFFFF;
        color: #212121;
        outline: none;
    }

    QListWidget::item {
        padding: 12px 14px;
        border-bottom: 1px solid #F0F0F0;
        color: #212121;
        background-color: #FFFFFF;
    }

    QListWidget::item:selected {
        background-color: #E3F2FD;
        color: #1565C0;
        border-left: 3px solid #1976D2;
    }

    QListWidget::item:hover:!selected {
        background-color: #F5F5F5;
        color: #212121;
    }

    QScrollArea {
        border: none;
        background-color: transparent;
    }

    QScrollBar:vertical {
        background-color: #F5F5F5;
        width: 10px;
        border-radius: 5px;
        margin: 2px;
    }

    QScrollBar::handle:vertical {
        background-color: #BDBDBD;
        border-radius: 5px;
        min-height: 30px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #9E9E9E;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        background-color: #F5F5F5;
        height: 10px;
        border-radius: 5px;
        margin: 2px;
    }

    QScrollBar::handle:horizontal {
        background-color: #BDBDBD;
        border-radius: 5px;
        min-width: 30px;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #9E9E9E;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    QMessageBox {
        background-color: #FFFFFF;
    }

    QMessageBox QLabel {
        color: #212121;
    }

    QDialog {
        background-color: #F5F7FA;
    }

    QMenu {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 6px 0px;
    }

    QMenu::item {
        padding: 10px 20px;
        color: #212121;
        background-color: transparent;
    }

    QMenu::item:selected {
        background-color: #E3F2FD;
        color: #1565C0;
    }

    QMenu::separator {
        height: 1px;
        background-color: #E0E0E0;
        margin: 6px 12px;
    }

    QInputDialog {
        background-color: #FFFFFF;
    }

    QInputDialog QLineEdit {
        min-width: 300px;
    }

    QToolTip {
        background-color: #424242;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 13px;
    }
    """

    # Login Screen Style
    LOGIN_STYLE = """
    QFrame#loginFrame {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E0E0E0;
    }

    QLabel#titleLabel {
        font-size: 28px;
        font-weight: bold;
        color: #1976D2;
    }

    QLabel#subtitleLabel {
        font-size: 14px;
        color: #757575;
    }

    QLabel#errorLabel {
        color: #D32F2F;
        font-size: 13px;
    }

    QLineEdit {
        min-height: 44px;
        font-size: 15px;
    }

    QPushButton#loginButton {
        min-height: 48px;
        font-size: 16px;
        border-radius: 8px;
    }

    QPushButton#registerButton {
        background-color: transparent;
        color: #1976D2;
        border: 2px solid #1976D2;
        min-height: 48px;
        font-size: 16px;
        border-radius: 8px;
    }

    QPushButton#registerButton:hover {
        background-color: #E3F2FD;
    }

    QPushButton#registerButton:pressed {
        background-color: #BBDEFB;
    }
    """

    # Chat Screen Style
    CHAT_STYLE = """
    QFrame#chatFrame {
        background-color: #FFFFFF;
        border-radius: 0px;
    }

    QFrame#sidebarFrame {
        background-color: #1E2A38;
        border-radius: 0px;
    }

    QLabel#sidebarTitle {
        color: #FFFFFF;
        font-size: 18px;
        font-weight: bold;
    }

    QListWidget#chatList {
        background-color: transparent;
        border: none;
        outline: none;
    }

    QListWidget#chatList::item {
        padding: 14px 12px;
        border-bottom: 1px solid #2D3E50;
        color: #B8C5D3;
        background-color: transparent;
        border-radius: 0px;
        border-left: none;
    }

    QListWidget#chatList::item:selected {
        background-color: #2D3E50;
        color: #FFFFFF;
        border-left: 3px solid #1976D2;
    }

    QListWidget#chatList::item:hover:!selected {
        background-color: #273849;
        color: #FFFFFF;
    }

    QPushButton#newChatButton {
        background-color: #1976D2;
        color: white;
        border-radius: 8px;
        padding: 14px;
        font-size: 15px;
        font-weight: 600;
    }

    QPushButton#newChatButton:hover {
        background-color: #1565C0;
    }

    QPushButton#newChatButton:pressed {
        background-color: #0D47A1;
    }

    QTextEdit#messageInput {
        border: 2px solid #E0E0E0;
        border-radius: 24px;
        padding: 12px 18px;
        font-size: 15px;
        background-color: #FFFFFF;
        color: #212121;
        selection-background-color: #1976D2;
        selection-color: white;
    }

    QTextEdit#messageInput:hover {
        border-color: #BDBDBD;
    }

    QTextEdit#messageInput:focus {
        border-color: #1976D2;
    }

    QTextEdit#messageInput:disabled {
        background-color: #F5F5F5;
        color: #9E9E9E;
        border-color: #E0E0E0;
    }

    QPushButton#sendButton {
        background-color: #1976D2;
        border-radius: 20px;
        min-width: 44px;
        min-height: 44px;
        font-size: 18px;
    }

    QPushButton#sendButton:hover {
        background-color: #1565C0;
    }

    QPushButton#sendButton:pressed {
        background-color: #0D47A1;
    }

    QPushButton#sendButton:disabled {
        background-color: #E0E0E0;
    }

    QPushButton#micButton {
        background-color: #546E7A;
        border-radius: 20px;
        min-width: 44px;
        min-height: 44px;
        font-size: 18px;
    }

    QPushButton#micButton:hover {
        background-color: #455A64;
    }

    QPushButton#micButton:pressed {
        background-color: #37474F;
    }
    """

    # Message Bubble Styles
    USER_MESSAGE_STYLE = """
    QFrame {
        background-color: #E3F2FD;
        border-radius: 16px;
        padding: 12px;
        margin: 4px 0px;
    }
    QLabel {
        color: #212121;
        background-color: transparent;
    }
    """

    ASSISTANT_MESSAGE_STYLE = """
    QFrame {
        background-color: #F5F5F5;
        border-radius: 16px;
        padding: 12px;
        margin: 4px 0px;
    }
    QLabel {
        color: #212121;
        background-color: transparent;
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
            border-radius: 12px;
            padding: 12px;
            margin: 4px 0px;
        }}
        QLabel {{
            color: #212121;
            background-color: transparent;
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
