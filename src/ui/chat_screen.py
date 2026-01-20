"""
Main Chat Screen.
Implements BR2, BR3, BR4, BR5, BR8
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QScrollArea, QSplitter,
    QMenu, QInputDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QEvent
from PyQt6.QtGui import QFont, QAction, QTextCursor, QKeyEvent

from .styles import Styles, SeverityStyles
from ..models.user import User
from ..models.chat import Chat, Message
from ..services.chat_service import ChatService
from ..services.obd_parser import OBDParser, OBDParseError
from ..services.granite_client import GraniteClient
from ..services.rag_pipeline import RAGPipeline
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class ThinkingIndicator(QFrame):
    """Animated thinking indicator shown when AI is processing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dots = 0
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        """Set up the thinking indicator UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # AI avatar/icon
        avatar = QLabel("◆")
        avatar.setStyleSheet("""
            color: #6366F1;
            font-size: 16px;
            font-weight: bold;
        """)
        avatar.setFixedWidth(20)
        layout.addWidget(avatar)

        # Thinking text with animated dots
        self.thinking_label = QLabel("InsightBot is thinking")
        self.thinking_label.setStyleSheet("""
            color: #52525B;
            font-size: 14px;
            font-weight: 500;
        """)
        layout.addWidget(self.thinking_label)
        layout.addStretch()

        # Style the frame
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E4E4E7;
                border-left: 3px solid #6366F1;
                border-radius: 12px;
            }
        """)

    def setup_animation(self):
        """Set up the dot animation timer."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_dots)
        self.timer.start(500)  # Update every 500ms

    def _animate_dots(self):
        """Animate the thinking dots."""
        self.dots = (self.dots + 1) % 4
        dots_text = "." * self.dots
        self.thinking_label.setText(f"InsightBot is thinking{dots_text}")

    def stop(self):
        """Stop the animation."""
        self.timer.stop()


class MessageWidget(QFrame):
    """Widget for displaying a single message with severity styling (BR8)."""

    def __init__(self, message: dict, parent=None):
        super().__init__(parent)
        self.message = message
        self.setup_ui()

    def setup_ui(self):
        """Set up the message widget UI."""
        role = self.message.get("role", "assistant")
        content = self.message.get("content", "")
        severity = self.message.get("severity", "normal")

        # Main horizontal layout with avatar
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Avatar
        avatar = QLabel("◆" if role == "assistant" else "●")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if role == "assistant":
            avatar.setStyleSheet("""
                background-color: #EEF2FF;
                color: #6366F1;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            """)
        else:
            avatar.setStyleSheet("""
                background-color: #18181B;
                color: #FFFFFF;
                border-radius: 16px;
                font-size: 10px;
            """)
        main_layout.addWidget(avatar)

        # Content container
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        # Header row with name and severity badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Role name
        role_name = "InsightBot" if role == "assistant" else "You"
        name_label = QLabel(role_name)
        name_label.setStyleSheet("""
            font-weight: 600;
            color: #18181B;
            font-size: 13px;
            background-color: transparent;
        """)
        header_layout.addWidget(name_label)

        # Severity badge for assistant messages (non-normal)
        if role == "assistant" and severity and severity.lower() != "normal":
            style = SeverityStyles.get(severity)
            severity_badge = QLabel(style['name'])
            severity_badge.setStyleSheet(f"""
                background-color: {style['badge_bg']};
                color: {style['badge_text']};
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
            severity_badge.setFixedHeight(20)
            header_layout.addWidget(severity_badge)

        header_layout.addStretch()
        content_layout.addLayout(header_layout)

        # Message content bubble
        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(14, 12, 14, 12)
        bubble_layout.setSpacing(0)

        # Apply styling based on role and severity
        if role == "assistant":
            style = SeverityStyles.get(severity)
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {style['background']};
                    border-left: 3px solid {style['border']};
                    border-radius: 12px;
                }}
            """)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #EEF2FF;
                    border-radius: 12px;
                }
            """)

        # Content text
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_label.setStyleSheet("""
            color: #18181B;
            background-color: transparent;
            font-size: 14px;
            line-height: 1.6;
        """)
        bubble_layout.addWidget(content_label)

        content_layout.addWidget(bubble)
        main_layout.addWidget(content_frame, stretch=1)

        # Transparent frame background
        self.setStyleSheet("QFrame { background-color: transparent; }")


class ChatWorker(QThread):
    """Worker thread for processing chat queries."""

    response_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, rag_pipeline: RAGPipeline, query: str, chat_id: int, context: dict):
        super().__init__()
        self.rag_pipeline = rag_pipeline
        self.query = query
        self.chat_id = chat_id
        self.context = context

    def run(self):
        """Process the query in background."""
        try:
            response = self.rag_pipeline.query(
                self.query,
                self.chat_id,
                self.context
            )
            self.response_ready.emit({
                "response": response.response,
                "severity": response.severity
            })
        except Exception as e:
            logger.error(f"Chat worker error: {e}")
            self.error_occurred.emit(str(e))


class ChatScreen(QWidget):
    """
    Main chat interface.

    Implements:
    - BR2: File upload and chat creation
    - BR3: Chat history management
    - BR4: Vehicle status queries
    - BR5: Fault code explanation
    - BR8: Severity color coding
    """

    logout_requested = pyqtSignal()

    def __init__(self, user: User, session_token: str, parent=None):
        super().__init__(parent)
        self.user = user
        self.session_token = session_token
        self.current_chat: Optional[Chat] = None
        self.current_context: dict = {}

        # Initialize services
        self.obd_parser = OBDParser()
        self.granite_client = GraniteClient()
        self.rag_pipeline = RAGPipeline(self.granite_client)

        self.setup_ui()
        self.load_chat_history()

    def setup_ui(self):
        """Set up the chat screen UI."""
        self.setStyleSheet(Styles.CHAT_STYLE)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Main chat area
        chat_area = self._create_chat_area()
        main_layout.addWidget(chat_area, stretch=1)

    def _create_sidebar(self) -> QFrame:
        """Create the sidebar with chat history."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(280)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)

        # Header with user info
        header = QHBoxLayout()
        header.setSpacing(12)

        # App icon/logo placeholder
        logo_label = QLabel("◆")
        logo_label.setStyleSheet("""
            color: #6366F1;
            font-size: 20px;
            font-weight: bold;
        """)
        header.addWidget(logo_label)

        title = QLabel("InsightBot")
        title.setObjectName("sidebarTitle")
        header.addWidget(title)
        header.addStretch()

        # Settings/Logout button - subtle icon style
        logout_btn = QPushButton("⚙")
        logout_btn.setObjectName("logoutButton")
        logout_btn.setFixedSize(32, 32)
        logout_btn.setToolTip("Settings")
        logout_btn.clicked.connect(self._show_settings_menu)
        header.addWidget(logout_btn)
        layout.addLayout(header)

        # User label with subtle styling
        user_label = QLabel(f"@{self.user.username}")
        user_label.setObjectName("usernameLabel")
        layout.addWidget(user_label)

        # Spacer
        layout.addSpacing(8)

        # New chat button
        new_chat_btn = QPushButton("＋  New Chat")
        new_chat_btn.setObjectName("newChatButton")
        new_chat_btn.clicked.connect(self._create_new_chat)
        layout.addWidget(new_chat_btn)

        # Spacer
        layout.addSpacing(8)

        # Chat history section header
        history_label = QLabel("RECENT CHATS")
        history_label.setObjectName("historyLabel")
        layout.addWidget(history_label)

        # Chat history list
        self.chat_list = QListWidget()
        self.chat_list.setObjectName("chatList")
        self.chat_list.itemClicked.connect(self._on_chat_selected)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self._show_chat_context_menu)
        layout.addWidget(self.chat_list, stretch=1)

        return sidebar

    def _create_chat_area(self) -> QFrame:
        """Create the main chat area."""
        chat_frame = QFrame()
        chat_frame.setObjectName("chatFrame")
        layout = QVBoxLayout(chat_frame)
        layout.setContentsMargins(32, 24, 32, 20)
        layout.setSpacing(16)

        # Chat header with refined styling
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: transparent; border: none;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(12)

        self.chat_header = QLabel("Welcome to InsightBot")
        self.chat_header.setObjectName("chatHeader")
        header_layout.addWidget(self.chat_header)

        header_layout.addStretch()
        layout.addWidget(header_frame)

        # Messages scroll area with clean styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FAFAFA;
            }
        """)

        self.messages_container = QWidget()
        self.messages_container.setStyleSheet("background-color: #FAFAFA;")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(4, 12, 4, 12)
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # Welcome message
        self._show_welcome_message()

        # Input area with refined design
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_frame.setStyleSheet("""
            QFrame#inputFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E4E4E7;
            }
            QFrame#inputFrame:focus-within {
                border: 2px solid #6366F1;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 8, 8)
        input_layout.setSpacing(8)
        input_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        # Text input with auto-resize
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("Ask about your vehicle...")
        self.message_input.setMinimumHeight(36)
        self.message_input.setMaximumHeight(120)
        self.message_input.setEnabled(False)
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                padding: 6px 4px;
                font-size: 14px;
                color: #18181B;
            }
            QTextEdit:disabled {
                background-color: transparent;
                color: #A1A1AA;
            }
        """)
        self.message_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.message_input.textChanged.connect(self._adjust_input_height)
        self.message_input.installEventFilter(self)
        input_layout.addWidget(self.message_input, stretch=1)

        # Send button
        self.send_btn = QPushButton("➤")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._send_message)
        self.send_btn.setEnabled(False)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_frame)

        # Keyboard hint
        hint_label = QLabel("Press Enter to send • Shift+Enter for new line")
        hint_label.setStyleSheet("""
            color: #A1A1AA;
            font-size: 11px;
            background-color: transparent;
            padding-left: 4px;
        """)
        layout.addWidget(hint_label)

        return chat_frame

    def _show_welcome_message(self):
        """Show initial welcome message with improved design."""
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E4E4E7;
            }
        """)
        welcome_layout = QVBoxLayout(welcome_frame)
        welcome_layout.setContentsMargins(48, 48, 48, 48)
        welcome_layout.setSpacing(8)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        logo = QLabel("◆")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("""
            color: #6366F1;
            font-size: 40px;
            font-weight: bold;
            background-color: transparent;
        """)
        welcome_layout.addWidget(logo)

        welcome_layout.addSpacing(8)

        # Title
        title = QLabel("Welcome to InsightBot")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #18181B;
            font-size: 26px;
            font-weight: 600;
            letter-spacing: -0.5px;
            background-color: transparent;
        """)
        welcome_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Your intelligent vehicle diagnostics assistant")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            color: #52525B;
            font-size: 15px;
            background-color: transparent;
        """)
        welcome_layout.addWidget(subtitle)

        welcome_layout.addSpacing(32)

        # Steps container
        steps_frame = QFrame()
        steps_frame.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border-radius: 12px;
                border: none;
            }
        """)
        steps_layout = QVBoxLayout(steps_frame)
        steps_layout.setContentsMargins(24, 20, 24, 20)
        steps_layout.setSpacing(16)

        # Steps header
        steps_header = QLabel("GET STARTED")
        steps_header.setStyleSheet("""
            color: #71717A;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            background-color: transparent;
        """)
        steps_layout.addWidget(steps_header)

        # Steps
        steps = [
            ("1", "Click \"+ New Chat\" in the sidebar"),
            ("2", "Upload your OBD-II log file (.csv)"),
            ("3", "Ask anything about your vehicle")
        ]
        for num, text in steps:
            step_layout = QHBoxLayout()
            step_layout.setSpacing(12)

            num_label = QLabel(num)
            num_label.setFixedSize(24, 24)
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet("""
                background-color: #6366F1;
                color: white;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
            """)
            step_layout.addWidget(num_label)

            text_label = QLabel(text)
            text_label.setStyleSheet("""
                color: #3F3F46;
                font-size: 14px;
                background-color: transparent;
            """)
            step_layout.addWidget(text_label)
            step_layout.addStretch()
            steps_layout.addLayout(step_layout)

        welcome_layout.addWidget(steps_frame)

        welcome_layout.addSpacing(24)

        # Footer
        footer = QLabel("Powered by IBM Granite AI")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("""
            color: #A1A1AA;
            font-size: 12px;
            background-color: transparent;
        """)
        welcome_layout.addWidget(footer)

        self.messages_layout.addWidget(welcome_frame)

    def load_chat_history(self):
        """Load user's chat history (BR3.1)."""
        self.chat_list.clear()
        chats = ChatService.get_user_chats(self.user.id)

        for chat in chats:
            # Truncate long names for sidebar
            display_name = chat.name
            if len(display_name) > 28:
                display_name = display_name[:25] + "..."
            item = QListWidgetItem(f"○  {display_name}")
            item.setData(Qt.ItemDataRole.UserRole, chat.id)
            item.setToolTip(chat.name)  # Show full name on hover
            self.chat_list.addItem(item)

    def _create_new_chat(self):
        """Create a new chat with file upload (BR2)."""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OBD-II Log File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        # Validate and parse file
        try:
            is_valid, message = self.obd_parser.validate_file(file_path)

            if not is_valid:
                QMessageBox.warning(self, "Invalid File", message)
                return

            # Parse the file
            parsed_data = self.obd_parser.parse_csv(file_path)

            # Create chat
            chat = ChatService.create_chat(
                user_id=self.user.id,
                obd_log_path=file_path,
                parsed_data=parsed_data,
                name=f"Vehicle Diagnostic - {file_path.split('/')[-1]}"
            )

            # Index data for RAG
            self.rag_pipeline.index_obd_data(parsed_data, chat.id)

            # Refresh chat list and open new chat
            self.load_chat_history()
            self._load_chat(chat.id)

            # Show initial summary
            self._generate_initial_summary(parsed_data)

        except OBDParseError as e:
            QMessageBox.critical(self, "Parse Error", str(e))
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create chat: {str(e)}")

    def _on_chat_selected(self, item: QListWidgetItem):
        """Handle chat selection from list."""
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        self._load_chat(chat_id)

    def _load_chat(self, chat_id: int):
        """Load a chat and display its messages."""
        try:
            chat = ChatService.get_chat(chat_id, self.user.id)
            if not chat:
                logger.warning(f"Chat {chat_id} not found or access denied")
                QMessageBox.warning(self, "Error", "Could not load the selected chat.")
                return

            self.current_chat = chat
            self.current_context = {
                "metrics": chat.parsed_metrics or [],
                "fault_codes": chat.fault_codes or []
            }

            # Update header
            self.chat_header.setText(chat.name)

            # Clear messages
            self._clear_messages()

            # Load messages with error handling
            try:
                messages = ChatService.get_chat_messages(chat_id, self.user.id)
                for msg in messages:
                    try:
                        self._add_message_widget(msg.to_dict())
                    except Exception as e:
                        logger.error(f"Error displaying message {msg.id}: {e}")
            except Exception as e:
                logger.error(f"Error loading messages for chat {chat_id}: {e}")

            # Enable input
            self.message_input.setEnabled(True)
            self.send_btn.setEnabled(True)

            # Re-index data for RAG if needed (with error handling)
            try:
                if chat.parsed_metrics:
                    self.rag_pipeline.index_obd_data({
                        "metrics": chat.parsed_metrics,
                        "fault_codes": chat.fault_codes or [],
                        "statistics": {}
                    }, chat_id)
            except Exception as e:
                logger.error(f"Error indexing RAG data for chat {chat_id}: {e}")

        except Exception as e:
            logger.error(f"Error loading chat {chat_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load chat: {str(e)}")

    def _clear_messages(self):
        """Clear all messages from the display."""
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_message_widget(self, message: dict):
        """Add a message widget to the display."""
        widget = MessageWidget(message)
        self.messages_layout.addWidget(widget)

        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """Scroll messages to bottom."""
        try:
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            logger.debug(f"Could not scroll to bottom: {e}")

    def _adjust_input_height(self):
        """Adjust input height based on content."""
        doc_height = self.message_input.document().size().height()
        new_height = min(max(36, int(doc_height) + 12), 120)
        self.message_input.setFixedHeight(new_height)

    def eventFilter(self, obj, event):
        """Handle Enter key to send message (Shift+Enter for new line)."""
        if obj == self.message_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if event.modifiers() != Qt.KeyboardModifier.ShiftModifier:
                    self._send_message()
                    return True
        return super().eventFilter(obj, event)

    def _send_message(self):
        """Send a message and get response (BR4, BR5)."""
        if not self.current_chat:
            return

        text = self.message_input.toPlainText().strip()
        if not text:
            return

        # Clear input
        self.message_input.clear()

        try:
            # Add user message
            user_msg = ChatService.add_message(
                self.current_chat.id,
                "user",
                text
            )
            self._add_message_widget(user_msg.to_dict())

            # Show loading indicator
            self._show_loading()

            # Process query in background
            self.worker = ChatWorker(
                self.rag_pipeline,
                text,
                self.current_chat.id,
                self.current_context
            )
            self.worker.response_ready.connect(self._on_response_ready)
            self.worker.error_occurred.connect(self._on_response_error)
            self.worker.start()

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._hide_loading()
            self._add_message_widget({
                "role": "assistant",
                "content": f"Sorry, there was an error processing your message. Please try again.",
                "severity": "warning"
            })

    def _show_loading(self):
        """Show loading indicator with thinking animation."""
        self.send_btn.setEnabled(False)
        self.message_input.setEnabled(False)

        # Add thinking indicator
        self.thinking_indicator = ThinkingIndicator()
        self.messages_layout.addWidget(self.thinking_indicator)
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _hide_loading(self):
        """Hide loading indicator."""
        self.send_btn.setEnabled(True)
        self.message_input.setEnabled(True)

        # Remove thinking indicator
        if hasattr(self, 'thinking_indicator') and self.thinking_indicator:
            self.thinking_indicator.stop()
            self.thinking_indicator.deleteLater()
            self.thinking_indicator = None

    def _on_response_ready(self, response: dict):
        """Handle response from worker."""
        self._hide_loading()

        # Guard against chat being deleted while waiting for response
        if not self.current_chat:
            return

        # Add assistant message
        msg = ChatService.add_message(
            self.current_chat.id,
            "assistant",
            response["response"],
            severity=response["severity"]
        )
        self._add_message_widget(msg.to_dict())

    def _on_response_error(self, error: str):
        """Handle error from worker."""
        self._hide_loading()

        # Add error message
        self._add_message_widget({
            "role": "assistant",
            "content": f"I'm sorry, I encountered an error processing your request: {error}\n\nPlease try again.",
            "severity": "warning"
        })

    def _generate_initial_summary(self, parsed_data: dict):
        """Generate initial vehicle summary after upload."""
        # Add system message about the upload
        metrics_count = len(parsed_data.get("metrics", []))
        fault_count = len(parsed_data.get("fault_codes", []))
        has_issues = parsed_data.get("has_issues", False)

        summary = f"I've analyzed your OBD-II log file and found:\n\n"
        summary += f"• **{metrics_count}** vehicle metrics\n"
        summary += f"• **{fault_count}** fault codes\n\n"

        if has_issues:
            summary += "⚠️ Some readings need your attention. Ask me for a detailed summary!"
        else:
            summary += "✅ Your vehicle appears to be in good condition!"

        self._add_message_widget({
            "role": "assistant",
            "content": summary,
            "severity": "warning" if has_issues else "normal"
        })

    def _show_chat_context_menu(self, position):
        """Show context menu for chat list (BR3.2, BR3.3, BR3.4)."""
        item = self.chat_list.itemAt(position)
        if not item:
            return

        chat_id = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        # Rename action (BR3.3)
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self._rename_chat(chat_id, item))

        # Export action (BR3.4)
        export_action = menu.addAction("Export to .txt")
        export_action.triggered.connect(lambda: self._export_chat(chat_id))

        menu.addSeparator()

        # Delete action (BR3.2)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._delete_chat(chat_id))

        menu.exec(self.chat_list.mapToGlobal(position))

    def _rename_chat(self, chat_id: int, item: QListWidgetItem):
        """Rename a chat (BR3.3)."""
        new_name, ok = QInputDialog.getText(
            self, "Rename Chat", "Enter new name:",
            text=item.text().replace("○  ", "")
        )

        if ok and new_name:
            ChatService.rename_chat(chat_id, self.user.id, new_name)
            item.setText(f"○  {new_name}")

            if self.current_chat and self.current_chat.id == chat_id:
                self.chat_header.setText(new_name)

    def _export_chat(self, chat_id: int):
        """Export chat to file (BR3.4)."""
        content = ChatService.export_chat(chat_id, self.user.id, "txt")

        if not content:
            QMessageBox.warning(self, "Export Failed", "Could not export chat.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Chat", "chat_export.txt", "Text Files (*.txt)"
        )

        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Export Complete", f"Chat exported to {file_path}")

    def _delete_chat(self, chat_id: int):
        """Delete a chat (BR3.2)."""
        reply = QMessageBox.question(
            self, "Delete Chat",
            "Are you sure you want to delete this chat?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            ChatService.delete_chat(chat_id, self.user.id)
            self.load_chat_history()

            if self.current_chat and self.current_chat.id == chat_id:
                self.current_chat = None
                self._clear_messages()
                self._show_welcome_message()
                self.chat_header.setText("Welcome to OBD InsightBot")
                self.message_input.setEnabled(False)
                self.send_btn.setEnabled(False)

    def _show_settings_menu(self):
        """Show settings/logout menu."""
        menu = QMenu(self)

        logout_action = menu.addAction("Logout")
        logout_action.triggered.connect(self._logout)

        # Get button position
        btn = self.sender()
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _logout(self):
        """Handle logout (BR1.3)."""
        from ..services.auth_service import AuthService
        AuthService.logout(self.session_token)
        self.logout_requested.emit()
