"""
UI Styles and Themes for OBD InsightBot.
Clean, minimalistic design with excellent contrast and visibility.
Implements BR8: Severity color coding.
"""


class SeverityStyles:
    """Severity-based color schemes for BR8 - Refined, muted colors."""

    CRITICAL = {
        "background": "#FEF2F2",
        "border": "#F87171",
        "text": "#B91C1C",
        "badge_bg": "#DC2626",
        "badge_text": "#FFFFFF",
        "name": "Critical"
    }

    WARNING = {
        "background": "#FFFBEB",
        "border": "#FBBF24",
        "text": "#B45309",
        "badge_bg": "#D97706",
        "badge_text": "#FFFFFF",
        "name": "Warning"
    }

    NORMAL = {
        "background": "#F0FDF4",
        "border": "#4ADE80",
        "text": "#15803D",
        "badge_bg": "#16A34A",
        "badge_text": "#FFFFFF",
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
    """Application-wide styles - Clean Minimalist Design System."""

    # ═══════════════════════════════════════════════════════════════
    # COLOR PALETTE
    # ═══════════════════════════════════════════════════════════════

    # Primary Accent (Indigo)
    ACCENT = "#6366F1"
    ACCENT_DARK = "#4F46E5"
    ACCENT_DARKER = "#4338CA"
    ACCENT_LIGHT = "#818CF8"
    ACCENT_SUBTLE = "#EEF2FF"

    # Neutral Colors (Zinc-based)
    BG_PRIMARY = "#FAFAFA"
    BG_SECONDARY = "#F4F4F5"
    SURFACE = "#FFFFFF"
    SURFACE_MUTED = "#F4F4F5"

    # Text Colors
    TEXT_PRIMARY = "#18181B"
    TEXT_SECONDARY = "#52525B"
    TEXT_MUTED = "#A1A1AA"
    TEXT_DISABLED = "#D4D4D8"

    # Border Colors
    BORDER = "#E4E4E7"
    BORDER_LIGHT = "#F4F4F5"
    BORDER_FOCUS = "#6366F1"

    # Sidebar Colors
    SIDEBAR_BG = "#18181B"
    SIDEBAR_BG_DARK = "#09090B"
    SIDEBAR_TEXT = "#FAFAFA"
    SIDEBAR_TEXT_MUTED = "#A1A1AA"
    SIDEBAR_HOVER = "rgba(255, 255, 255, 0.08)"
    SIDEBAR_SELECTED = "rgba(99, 102, 241, 0.2)"

    # Status Colors
    ERROR = "#EF4444"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"

    # ═══════════════════════════════════════════════════════════════
    # MAIN APPLICATION STYLE
    # ═══════════════════════════════════════════════════════════════

    MAIN_STYLE = """
    /* ─────────────────────────────────────────────────────────────
       BASE STYLES
       ───────────────────────────────────────────────────────────── */

    QMainWindow {
        background-color: #FAFAFA;
    }

    QWidget {
        font-family: 'Inter', 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-size: 14px;
        color: #18181B;
    }

    /* ─────────────────────────────────────────────────────────────
       BUTTONS - Clean, visible defaults
       ───────────────────────────────────────────────────────────── */

    QPushButton {
        background-color: #6366F1;
        color: #FFFFFF;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
    }

    QPushButton:hover {
        background-color: #4F46E5;
    }

    QPushButton:pressed {
        background-color: #4338CA;
    }

    QPushButton:disabled {
        background-color: #E4E4E7;
        color: #A1A1AA;
    }

    /* ─────────────────────────────────────────────────────────────
       TEXT INPUTS - Clean, subtle borders
       ───────────────────────────────────────────────────────────── */

    QLineEdit {
        padding: 12px 16px;
        border: 1.5px solid #E4E4E7;
        border-radius: 10px;
        background-color: #FFFFFF;
        color: #18181B;
        font-size: 14px;
        selection-background-color: #6366F1;
        selection-color: white;
    }

    QLineEdit:hover {
        border-color: #D4D4D8;
    }

    QLineEdit:focus {
        border-color: #6366F1;
        border-width: 2px;
        padding: 11px 15px;
    }

    QLineEdit::placeholder {
        color: #A1A1AA;
    }

    QTextEdit {
        padding: 12px 16px;
        border: 1.5px solid #E4E4E7;
        border-radius: 10px;
        background-color: #FFFFFF;
        color: #18181B;
        font-size: 14px;
        selection-background-color: #6366F1;
        selection-color: white;
    }

    QTextEdit:hover {
        border-color: #D4D4D8;
    }

    QTextEdit:focus {
        border-color: #6366F1;
        border-width: 2px;
        padding: 11px 15px;
    }

    /* ─────────────────────────────────────────────────────────────
       LABELS
       ───────────────────────────────────────────────────────────── */

    QLabel {
        color: #18181B;
        background-color: transparent;
    }

    /* ─────────────────────────────────────────────────────────────
       LIST WIDGETS
       ───────────────────────────────────────────────────────────── */

    QListWidget {
        border: 1px solid #E4E4E7;
        border-radius: 8px;
        background-color: #FFFFFF;
        color: #18181B;
        outline: none;
        padding: 4px;
    }

    QListWidget::item {
        padding: 12px 16px;
        border-radius: 6px;
        margin: 2px 4px;
        color: #18181B;
        background-color: transparent;
    }

    QListWidget::item:selected {
        background-color: #EEF2FF;
        color: #4F46E5;
    }

    QListWidget::item:hover:!selected {
        background-color: #F4F4F5;
        color: #18181B;
    }

    /* ─────────────────────────────────────────────────────────────
       SCROLL AREAS & SCROLLBARS - Minimal
       ───────────────────────────────────────────────────────────── */

    QScrollArea {
        border: none;
        background-color: transparent;
    }

    QScrollBar:vertical {
        background-color: transparent;
        width: 6px;
        border-radius: 3px;
        margin: 4px 2px;
    }

    QScrollBar::handle:vertical {
        background-color: #D4D4D8;
        border-radius: 3px;
        min-height: 40px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #A1A1AA;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        background-color: transparent;
        height: 6px;
        border-radius: 3px;
        margin: 2px 4px;
    }

    QScrollBar::handle:horizontal {
        background-color: #D4D4D8;
        border-radius: 3px;
        min-width: 40px;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #A1A1AA;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* ─────────────────────────────────────────────────────────────
       MESSAGE BOXES & DIALOGS
       ───────────────────────────────────────────────────────────── */

    QMessageBox {
        background-color: #FFFFFF;
    }

    QMessageBox QLabel {
        color: #18181B;
        font-size: 14px;
    }

    QMessageBox QPushButton {
        min-width: 90px;
        padding: 8px 20px;
        border-radius: 8px;
    }

    QDialog {
        background-color: #FAFAFA;
    }

    /* ─────────────────────────────────────────────────────────────
       MENUS - Clean dropdowns
       ───────────────────────────────────────────────────────────── */

    QMenu {
        background-color: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 10px;
        padding: 6px;
    }

    QMenu::item {
        padding: 10px 20px;
        border-radius: 6px;
        color: #18181B;
        background-color: transparent;
        margin: 2px;
        font-size: 13px;
    }

    QMenu::item:selected {
        background-color: #F4F4F5;
        color: #18181B;
    }

    QMenu::separator {
        height: 1px;
        background-color: #E4E4E7;
        margin: 6px 12px;
    }

    QInputDialog {
        background-color: #FFFFFF;
    }

    QInputDialog QLineEdit {
        min-width: 300px;
    }

    /* ─────────────────────────────────────────────────────────────
       TOOLTIPS
       ───────────────────────────────────────────────────────────── */

    QToolTip {
        background-color: #18181B;
        color: #FAFAFA;
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
    }
    """

    # ═══════════════════════════════════════════════════════════════
    # LOGIN SCREEN STYLE
    # ═══════════════════════════════════════════════════════════════

    LOGIN_STYLE = """
    QFrame#loginFrame {
        background-color: transparent;
        border: none;
    }

    QLabel#titleLabel {
        font-size: 28px;
        font-weight: 600;
        color: #18181B;
        letter-spacing: -0.5px;
        background: transparent;
    }

    QLabel#subtitleLabel {
        font-size: 15px;
        color: #71717A;
        font-weight: 400;
        background: transparent;
    }

    QLabel#errorLabel {
        color: #DC2626;
        font-size: 13px;
        font-weight: 500;
        padding: 10px 14px;
        background-color: #FEF2F2;
        border-radius: 8px;
        border: 1px solid #FECACA;
    }

    QLineEdit {
        min-height: 48px;
        font-size: 14px;
        border-radius: 10px;
        border: 1.5px solid #E4E4E7;
        padding: 0 16px;
        background-color: #FFFFFF;
    }

    QLineEdit:hover {
        border-color: #D4D4D8;
    }

    QLineEdit:focus {
        border: 2px solid #6366F1;
        padding: 0 15px;
        background-color: #FFFFFF;
    }

    QPushButton#loginButton {
        min-height: 48px;
        font-size: 14px;
        font-weight: 600;
        border-radius: 10px;
        background-color: #6366F1;
        color: #FFFFFF;
        border: none;
    }

    QPushButton#loginButton:hover {
        background-color: #4F46E5;
    }

    QPushButton#loginButton:pressed {
        background-color: #4338CA;
    }

    QPushButton#loginButton:disabled {
        background-color: #C7D2FE;
        color: #FFFFFF;
    }

    QPushButton#registerButton {
        background-color: transparent;
        color: #52525B;
        border: 1.5px solid #E4E4E7;
        min-height: 48px;
        font-size: 14px;
        font-weight: 500;
        border-radius: 10px;
    }

    QPushButton#registerButton:hover {
        background-color: #F4F4F5;
        border-color: #D4D4D8;
        color: #18181B;
    }

    QPushButton#registerButton:pressed {
        background-color: #E4E4E7;
    }
    """

    # ═══════════════════════════════════════════════════════════════
    # CHAT SCREEN STYLE
    # ═══════════════════════════════════════════════════════════════

    CHAT_STYLE = """
    /* ─────────────────────────────────────────────────────────────
       MAIN CHAT FRAME
       ───────────────────────────────────────────────────────────── */

    QFrame#chatFrame {
        background-color: #FAFAFA;
        border: none;
    }

    /* ─────────────────────────────────────────────────────────────
       SIDEBAR - Dark, clean
       ───────────────────────────────────────────────────────────── */

    QFrame#sidebarFrame {
        background-color: #18181B;
        border-radius: 0px;
    }

    QLabel#sidebarTitle {
        color: #FAFAFA;
        font-size: 18px;
        font-weight: 600;
        letter-spacing: -0.3px;
    }

    QLabel#usernameLabel {
        color: #A1A1AA;
        font-size: 13px;
        font-weight: 400;
    }

    QLabel#historyLabel {
        color: #71717A;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* ─────────────────────────────────────────────────────────────
       CHAT LIST
       ───────────────────────────────────────────────────────────── */

    QListWidget#chatList {
        background-color: transparent;
        border: none;
        outline: none;
        padding: 0px;
    }

    QListWidget#chatList::item {
        padding: 12px 14px;
        border-radius: 8px;
        color: #A1A1AA;
        background-color: transparent;
        margin: 2px 4px;
        font-size: 13px;
        border-left: 3px solid transparent;
    }

    QListWidget#chatList::item:selected {
        background-color: rgba(99, 102, 241, 0.15);
        color: #FFFFFF;
        border-left: 3px solid #6366F1;
    }

    QListWidget#chatList::item:hover:!selected {
        background-color: rgba(255, 255, 255, 0.08);
        color: #E4E4E7;
    }

    /* ─────────────────────────────────────────────────────────────
       NEW CHAT BUTTON - Solid, prominent
       ───────────────────────────────────────────────────────────── */

    QPushButton#newChatButton {
        background-color: #6366F1;
        color: #FFFFFF;
        border-radius: 10px;
        padding: 14px 16px;
        font-size: 14px;
        font-weight: 600;
        border: none;
    }

    QPushButton#newChatButton:hover {
        background-color: #4F46E5;
    }

    QPushButton#newChatButton:pressed {
        background-color: #4338CA;
    }

    /* ─────────────────────────────────────────────────────────────
       SETTINGS/LOGOUT BUTTON - Clearly visible on dark sidebar
       ───────────────────────────────────────────────────────────── */

    QPushButton#logoutButton {
        background-color: rgba(255, 255, 255, 0.1);
        color: #E4E4E7;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        padding: 6px;
        font-size: 15px;
        font-weight: 500;
    }

    QPushButton#logoutButton:hover {
        background-color: rgba(255, 255, 255, 0.18);
        color: #FFFFFF;
        border-color: rgba(255, 255, 255, 0.25);
    }

    QPushButton#logoutButton:pressed {
        background-color: rgba(255, 255, 255, 0.08);
        color: #FAFAFA;
    }

    /* ─────────────────────────────────────────────────────────────
       CHAT HEADER
       ───────────────────────────────────────────────────────────── */

    QLabel#chatHeader {
        color: #18181B;
        font-size: 18px;
        font-weight: 600;
        letter-spacing: -0.3px;
    }

    /* ─────────────────────────────────────────────────────────────
       MESSAGE INPUT - Clean, borderless inside input frame
       ───────────────────────────────────────────────────────────── */

    QTextEdit#messageInput {
        border: none;
        border-radius: 0px;
        padding: 8px 4px;
        font-size: 14px;
        background-color: transparent;
        color: #18181B;
        selection-background-color: #6366F1;
        selection-color: white;
    }

    QTextEdit#messageInput:hover {
        border: none;
    }

    QTextEdit#messageInput:focus {
        border: none;
        padding: 8px 4px;
    }

    QTextEdit#messageInput:disabled {
        background-color: transparent;
        color: #A1A1AA;
        border: none;
    }

    /* ─────────────────────────────────────────────────────────────
       SEND BUTTON - Always clearly visible
       ───────────────────────────────────────────────────────────── */

    QPushButton#sendButton {
        background-color: #6366F1;
        border-radius: 12px;
        min-width: 44px;
        max-width: 44px;
        min-height: 44px;
        max-height: 44px;
        font-size: 18px;
        border: none;
        color: #FFFFFF;
        font-weight: bold;
    }

    QPushButton#sendButton:hover {
        background-color: #4F46E5;
    }

    QPushButton#sendButton:pressed {
        background-color: #4338CA;
    }

    QPushButton#sendButton:disabled {
        background-color: #E4E4E7;
        color: #A1A1AA;
    }

    /* ─────────────────────────────────────────────────────────────
       SIDEBAR SCROLLBAR - Dark theme variant
       ───────────────────────────────────────────────────────────── */

    QListWidget#chatList QScrollBar:vertical {
        background-color: transparent;
        width: 6px;
        border-radius: 3px;
        margin: 4px 2px;
    }

    QListWidget#chatList QScrollBar::handle:vertical {
        background-color: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
        min-height: 40px;
    }

    QListWidget#chatList QScrollBar::handle:vertical:hover {
        background-color: rgba(255, 255, 255, 0.3);
    }

    QListWidget#chatList QScrollBar::add-line:vertical,
    QListWidget#chatList QScrollBar::sub-line:vertical {
        height: 0px;
    }

    /* ─────────────────────────────────────────────────────────────
       MIC BUTTON
       ───────────────────────────────────────────────────────────── */

    QPushButton#micButton {
        background-color: #F4F4F5;
        color: #52525B;
        border-radius: 10px;
        min-width: 40px;
        max-width: 40px;
        min-height: 40px;
        max-height: 40px;
        font-size: 16px;
        border: 1px solid #E4E4E7;
    }

    QPushButton#micButton:hover {
        background-color: #E4E4E7;
        color: #18181B;
        border-color: #D4D4D8;
    }

    QPushButton#micButton:pressed {
        background-color: #D4D4D8;
    }

    /* ─────────────────────────────────────────────────────────────
       UPLOAD BUTTON
       ───────────────────────────────────────────────────────────── */

    QPushButton#uploadButton {
        background-color: transparent;
        color: #52525B;
        border: 1.5px solid #E4E4E7;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }

    QPushButton#uploadButton:hover {
        background-color: #F4F4F5;
        border-color: #D4D4D8;
        color: #18181B;
    }

    QPushButton#uploadButton:pressed {
        background-color: #E4E4E7;
    }

    /* ─────────────────────────────────────────────────────────────
       DELETE BUTTON - Danger action in context menus
       ───────────────────────────────────────────────────────────── */

    QPushButton#deleteButton {
        background-color: transparent;
        color: #DC2626;
        border: 1.5px solid #FECACA;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }

    QPushButton#deleteButton:hover {
        background-color: #FEF2F2;
        border-color: #F87171;
        color: #B91C1C;
    }

    QPushButton#deleteButton:pressed {
        background-color: #FEE2E2;
    }
    """

    # ═══════════════════════════════════════════════════════════════
    # MESSAGE BUBBLE STYLES
    # ═══════════════════════════════════════════════════════════════

    USER_MESSAGE_STYLE = """
    QFrame {
        background-color: #EEF2FF;
        border-radius: 12px;
        border: none;
        padding: 0px;
        margin: 0px;
    }
    QLabel {
        color: #18181B;
        background-color: transparent;
    }
    """

    ASSISTANT_MESSAGE_STYLE = """
    QFrame {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E4E4E7;
        padding: 0px;
        margin: 0px;
    }
    QLabel {
        color: #18181B;
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
            border-left: 3px solid {colors['border']};
            border-radius: 12px;
            padding: 0px;
            margin: 0px;
        }}
        QLabel {{
            color: #18181B;
            background-color: transparent;
        }}
        """

    @classmethod
    def get_severity_badge_style(cls, severity: str) -> str:
        """Get severity badge style (pill-shaped badge)."""
        colors = SeverityStyles.get(severity)
        return f"""
        QLabel {{
            background-color: {colors['badge_bg']};
            color: {colors['badge_text']};
            border-radius: 10px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        }}
        """

    @classmethod
    def get_severity_indicator(cls, severity: str) -> str:
        """Get severity indicator HTML."""
        colors = SeverityStyles.get(severity)
        return f"""
        <span style="
            background-color: {colors['badge_bg']};
            color: {colors['badge_text']};
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
        ">{colors['name']}</span>
        """
