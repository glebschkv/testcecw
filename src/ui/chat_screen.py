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
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QAction, QTextCursor

from .styles import Styles, SeverityStyles
from ..models.user import User
from ..models.chat import Chat, Message
from ..services.chat_service import ChatService
from ..services.obd_parser import OBDParser, OBDParseError
from ..services.granite_client import GraniteClient
from ..services.rag_pipeline import RAGPipeline
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class MessageWidget(QFrame):
    """Widget for displaying a single message with severity styling (BR8)."""

    def __init__(self, message: dict, parent=None):
        super().__init__(parent)
        self.message = message
        self.setup_ui()

    def setup_ui(self):
        """Set up the message widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        role = self.message.get("role", "assistant")
        content = self.message.get("content", "")
        severity = self.message.get("severity", "normal")

        # Apply severity styling for assistant messages (BR8)
        if role == "assistant":
            style = SeverityStyles.get(severity)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {style['background']};
                    border-left: 4px solid {style['border']};
                    border-radius: 8px;
                }}
            """)

            # Severity indicator
            if severity != "normal":
                severity_label = QLabel(f"{style['icon']} {style['name']}")
                severity_label.setStyleSheet(f"color: {style['text']}; font-weight: bold;")
                layout.addWidget(severity_label)
        else:
            # User message styling
            self.setStyleSheet("""
                QFrame {
                    background-color: #E3F2FD;
                    border-radius: 8px;
                }
            """)

        # Role label
        role_label = QLabel("You" if role == "user" else "InsightBot")
        role_label.setStyleSheet("font-weight: bold; color: #424242;")
        layout.addWidget(role_label)

        # Content
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_label.setStyleSheet("color: #212121;")
        layout.addWidget(content_label)


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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Header with user info
        header = QHBoxLayout()
        title = QLabel("OBD InsightBot")
        title.setObjectName("sidebarTitle")
        header.addWidget(title)

        # Settings/Logout button
        logout_btn = QPushButton("⚙")
        logout_btn.setFixedSize(30, 30)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #37474F;
                border-radius: 15px;
            }
        """)
        logout_btn.clicked.connect(self._show_settings_menu)
        header.addWidget(logout_btn)
        layout.addLayout(header)

        # User label
        user_label = QLabel(f"👤 {self.user.username}")
        user_label.setStyleSheet("color: #B0BEC5; font-size: 12px;")
        layout.addWidget(user_label)

        # New chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setObjectName("newChatButton")
        new_chat_btn.clicked.connect(self._create_new_chat)
        layout.addWidget(new_chat_btn)

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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Chat header
        self.chat_header = QLabel("Welcome to OBD InsightBot")
        self.chat_header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1976D2;")
        layout.addWidget(self.chat_header)

        # Messages scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: #FAFAFA;")

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(10)
        scroll.setWidget(self.messages_container)
        layout.addWidget(scroll, stretch=1)

        # Welcome message
        self._show_welcome_message()

        # Input area
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)

        # Microphone button (BR6)
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setObjectName("micButton")
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.setToolTip("Voice input (coming soon)")
        input_layout.addWidget(self.mic_btn)

        # Text input
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("Type your question about your vehicle...")
        self.message_input.setFixedHeight(50)
        self.message_input.setEnabled(False)
        input_layout.addWidget(self.message_input, stretch=1)

        # Send button
        self.send_btn = QPushButton("➤")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.clicked.connect(self._send_message)
        self.send_btn.setEnabled(False)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_frame)

        return chat_frame

    def _show_welcome_message(self):
        """Show initial welcome message."""
        welcome = QLabel("""
            <h2>Welcome to OBD InsightBot!</h2>
            <p>I'm your vehicle diagnostics assistant powered by IBM Granite.</p>
            <p><b>To get started:</b></p>
            <ol>
                <li>Click <b>"+ New Chat"</b> in the sidebar</li>
                <li>Upload your OBD-II log file (.csv format)</li>
                <li>Ask me anything about your vehicle's health!</li>
            </ol>
            <p style="color: #757575;">I can help you understand fault codes, analyze metrics, and provide maintenance recommendations.</p>
        """)
        welcome.setWordWrap(True)
        welcome.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                color: #424242;
            }
        """)
        self.messages_layout.addWidget(welcome)

    def load_chat_history(self):
        """Load user's chat history (BR3.1)."""
        self.chat_list.clear()
        chats = ChatService.get_user_chats(self.user.id)

        for chat in chats:
            item = QListWidgetItem(f"📁 {chat.name}")
            item.setData(Qt.ItemDataRole.UserRole, chat.id)
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
        chat = ChatService.get_chat(chat_id, self.user.id)
        if not chat:
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

        # Load messages
        messages = ChatService.get_chat_messages(chat_id, self.user.id)
        for msg in messages:
            self._add_message_widget(msg.to_dict())

        # Enable input
        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(True)

        # Re-index data for RAG if needed
        if chat.parsed_metrics:
            self.rag_pipeline.index_obd_data({
                "metrics": chat.parsed_metrics,
                "fault_codes": chat.fault_codes or [],
                "statistics": {}
            }, chat_id)

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
        scrollbar = self.messages_container.parentWidget().verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _send_message(self):
        """Send a message and get response (BR4, BR5)."""
        if not self.current_chat:
            return

        text = self.message_input.toPlainText().strip()
        if not text:
            return

        # Clear input
        self.message_input.clear()

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

    def _show_loading(self):
        """Show loading indicator."""
        self.send_btn.setEnabled(False)
        self.message_input.setEnabled(False)

    def _hide_loading(self):
        """Hide loading indicator."""
        self.send_btn.setEnabled(True)
        self.message_input.setEnabled(True)

    def _on_response_ready(self, response: dict):
        """Handle response from worker."""
        self._hide_loading()

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
            text=item.text().replace("📁 ", "")
        )

        if ok and new_name:
            ChatService.rename_chat(chat_id, self.user.id, new_name)
            item.setText(f"📁 {new_name}")

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
