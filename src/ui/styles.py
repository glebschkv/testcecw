"""
UI Styles and Themes for OBD InsightBot.
Modern, clean design with Material Design 3 influences.
Implements BR8: Severity color coding.
"""


class SeverityStyles:
    """Severity-based color schemes for BR8."""

    CRITICAL = {
        "background": "#FEE2E2",
        "border": "#EF4444",
        "text": "#DC2626",
        "icon": "",
        "name": "Critical"
    }

    WARNING = {
        "background": "#FEF3C7",
        "border": "#F59E0B",
        "text": "#D97706",
        "icon": "",
        "name": "Warning"
    }

    NORMAL = {
        "background": "#D1FAE5",
        "border": "#10B981",
        "text": "#059669",
        "icon": "",
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
        if not severity:
            return cls.NORMAL
        return styles.get(severity.lower(), cls.NORMAL)


class Styles:
    """Application-wide styles - Modern Design System."""

    # Modern Color Palette
    PRIMARY_COLOR = "#3B82F6"      # Vibrant blue
    PRIMARY_DARK = "#2563EB"
    PRIMARY_LIGHT = "#60A5FA"
    SECONDARY_COLOR = "#6366F1"    # Indigo accent
    BACKGROUND = "#F8FAFC"         # Soft gray background
    SURFACE = "#FFFFFF"
    SURFACE_VARIANT = "#F1F5F9"
    ERROR = "#EF4444"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    TEXT_MUTED = "#94A3B8"
    BORDER = "#E2E8F0"
    BORDER_LIGHT = "#F1F5F9"

    # Main Application Style
    MAIN_STYLE = """
    QMainWindow {
        background-color: #F8FAFC;
    }

    QWidget {
        font-family: 'Inter', 'SF Pro Display', 'Segoe UI', -apple-system, system-ui, sans-serif;
        font-size: 14px;
        color: #1E293B;
    }

    QPushButton {
        background-color: #3B82F6;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 14px;
    }

    QPushButton:hover {
        background-color: #2563EB;
    }

    QPushButton:pressed {
        background-color: #1D4ED8;
    }

    QPushButton:disabled {
        background-color: #E2E8F0;
        color: #94A3B8;
    }

    QLineEdit {
        padding: 14px 16px;
        border: 2px solid #E2E8F0;
        border-radius: 12px;
        background-color: #FFFFFF;
        color: #1E293B;
        font-size: 15px;
        selection-background-color: #3B82F6;
        selection-color: white;
    }

    QLineEdit:hover {
        border-color: #CBD5E1;
    }

    QLineEdit:focus {
        border-color: #3B82F6;
        background-color: #FFFFFF;
    }

    QLineEdit::placeholder {
        color: #94A3B8;
    }

    QTextEdit {
        padding: 14px 16px;
        border: 2px solid #E2E8F0;
        border-radius: 12px;
        background-color: #FFFFFF;
        color: #1E293B;
        font-size: 15px;
        selection-background-color: #3B82F6;
        selection-color: white;
    }

    QTextEdit:hover {
        border-color: #CBD5E1;
    }

    QTextEdit:focus {
        border-color: #3B82F6;
        background-color: #FFFFFF;
    }

    QLabel {
        color: #1E293B;
        background-color: transparent;
    }

    QListWidget {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        background-color: #FFFFFF;
        color: #1E293B;
        outline: none;
        padding: 4px;
    }

    QListWidget::item {
        padding: 14px 16px;
        border-radius: 8px;
        margin: 2px 4px;
        color: #1E293B;
        background-color: transparent;
    }

    QListWidget::item:selected {
        background-color: #EFF6FF;
        color: #1D4ED8;
    }

    QListWidget::item:hover:!selected {
        background-color: #F8FAFC;
        color: #1E293B;
    }

    QScrollArea {
        border: none;
        background-color: transparent;
    }

    QScrollBar:vertical {
        background-color: transparent;
        width: 8px;
        border-radius: 4px;
        margin: 4px 2px;
    }

    QScrollBar::handle:vertical {
        background-color: #CBD5E1;
        border-radius: 4px;
        min-height: 40px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #94A3B8;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        background-color: transparent;
        height: 8px;
        border-radius: 4px;
        margin: 2px 4px;
    }

    QScrollBar::handle:horizontal {
        background-color: #CBD5E1;
        border-radius: 4px;
        min-width: 40px;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #94A3B8;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    QMessageBox {
        background-color: #FFFFFF;
    }

    QMessageBox QLabel {
        color: #1E293B;
        font-size: 14px;
    }

    QMessageBox QPushButton {
        min-width: 80px;
        padding: 10px 20px;
    }

    QDialog {
        background-color: #F8FAFC;
    }

    QMenu {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 8px;
    }

    QMenu::item {
        padding: 12px 20px;
        border-radius: 8px;
        color: #1E293B;
        background-color: transparent;
        margin: 2px 4px;
    }

    QMenu::item:selected {
        background-color: #EFF6FF;
        color: #1D4ED8;
    }

    QMenu::separator {
        height: 1px;
        background-color: #E2E8F0;
        margin: 8px 16px;
    }

    QInputDialog {
        background-color: #FFFFFF;
    }

    QInputDialog QLineEdit {
        min-width: 320px;
    }

    QToolTip {
        background-color: #1E293B;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
    }
    """

    # Login Screen Style - Modern Card Design
    LOGIN_STYLE = """
    QFrame#loginFrame {
        background-color: #FFFFFF;
        border-radius: 24px;
        border: 1px solid #E2E8F0;
    }

    QLabel#titleLabel {
        font-size: 32px;
        font-weight: 700;
        color: #1E293B;
    }

    QLabel#subtitleLabel {
        font-size: 15px;
        color: #64748B;
        font-weight: 400;
    }

    QLabel#errorLabel {
        color: #EF4444;
        font-size: 13px;
        font-weight: 500;
    }

    QLineEdit {
        min-height: 48px;
        font-size: 15px;
        border-radius: 12px;
    }

    QPushButton#loginButton {
        min-height: 52px;
        font-size: 16px;
        font-weight: 600;
        border-radius: 12px;
        background-color: #3B82F6;
    }

    QPushButton#loginButton:hover {
        background-color: #2563EB;
    }

    QPushButton#loginButton:pressed {
        background-color: #1D4ED8;
    }

    QPushButton#registerButton {
        background-color: transparent;
        color: #3B82F6;
        border: 2px solid #3B82F6;
        min-height: 52px;
        font-size: 16px;
        font-weight: 600;
        border-radius: 12px;
    }

    QPushButton#registerButton:hover {
        background-color: #EFF6FF;
        border-color: #2563EB;
        color: #2563EB;
    }

    QPushButton#registerButton:pressed {
        background-color: #DBEAFE;
        border-color: #1D4ED8;
        color: #1D4ED8;
    }
    """

    # Chat Screen Style - Modern Sidebar and Chat Design
    CHAT_STYLE = """
    QFrame#chatFrame {
        background-color: #FFFFFF;
        border-radius: 0px;
    }

    QFrame#sidebarFrame {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1E293B, stop:1 #0F172A);
        border-radius: 0px;
    }

    QLabel#sidebarTitle {
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    QListWidget#chatList {
        background-color: transparent;
        border: none;
        outline: none;
        padding: 4px;
    }

    QListWidget#chatList::item {
        padding: 14px 16px;
        border-radius: 10px;
        color: #94A3B8;
        background-color: transparent;
        margin: 2px 0px;
        font-size: 14px;
    }

    QListWidget#chatList::item:selected {
        background-color: rgba(59, 130, 246, 0.15);
        color: #FFFFFF;
    }

    QListWidget#chatList::item:hover:!selected {
        background-color: rgba(255, 255, 255, 0.05);
        color: #E2E8F0;
    }

    QPushButton#newChatButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #3B82F6, stop:1 #6366F1);
        color: white;
        border-radius: 12px;
        padding: 16px;
        font-size: 15px;
        font-weight: 600;
        border: none;
    }

    QPushButton#newChatButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #2563EB, stop:1 #4F46E5);
    }

    QPushButton#newChatButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1D4ED8, stop:1 #4338CA);
    }

    QTextEdit#messageInput {
        border: 2px solid #E2E8F0;
        border-radius: 24px;
        padding: 14px 20px;
        font-size: 15px;
        background-color: #FFFFFF;
        color: #1E293B;
        selection-background-color: #3B82F6;
        selection-color: white;
    }

    QTextEdit#messageInput:hover {
        border-color: #CBD5E1;
    }

    QTextEdit#messageInput:focus {
        border-color: #3B82F6;
    }

    QTextEdit#messageInput:disabled {
        background-color: #F8FAFC;
        color: #94A3B8;
        border-color: #E2E8F0;
    }

    QPushButton#sendButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #3B82F6, stop:1 #6366F1);
        border-radius: 22px;
        min-width: 48px;
        min-height: 48px;
        font-size: 18px;
        border: none;
    }

    QPushButton#sendButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #2563EB, stop:1 #4F46E5);
    }

    QPushButton#sendButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #1D4ED8, stop:1 #4338CA);
    }

    QPushButton#sendButton:disabled {
        background-color: #E2E8F0;
    }

    QPushButton#micButton {
        background-color: #64748B;
        border-radius: 22px;
        min-width: 48px;
        min-height: 48px;
        font-size: 18px;
        border: none;
    }

    QPushButton#micButton:hover {
        background-color: #475569;
    }

    QPushButton#micButton:pressed {
        background-color: #334155;
    }
    """

    # Message Bubble Styles
    USER_MESSAGE_STYLE = """
    QFrame {
        background-color: #EFF6FF;
        border-radius: 18px;
        padding: 16px;
        margin: 4px 0px;
    }
    QLabel {
        color: #1E293B;
        background-color: transparent;
    }
    """

    ASSISTANT_MESSAGE_STYLE = """
    QFrame {
        background-color: #F8FAFC;
        border-radius: 18px;
        padding: 16px;
        margin: 4px 0px;
    }
    QLabel {
        color: #1E293B;
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
            border-radius: 16px;
            padding: 16px;
            margin: 4px 0px;
        }}
        QLabel {{
            color: #1E293B;
            background-color: transparent;
        }}
        """

    @classmethod
    def get_severity_indicator(cls, severity: str) -> str:
        """Get severity indicator HTML."""
        colors = SeverityStyles.get(severity)
        return f"""
        <span style="color: {colors['border']}; font-weight: 600;">
            {colors['icon']} {colors['name']}
        </span>
        """
