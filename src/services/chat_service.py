"""
Chat management service.
Implements BR3: Chat History
"""

from typing import Optional, List
from pathlib import Path
from datetime import datetime

from ..models.base import DatabaseSession
from ..models.chat import Chat, Message
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class ChatService:
    """
    Service for managing chat sessions.

    Implements:
    - BR3.1: User views chat history
    - BR3.2: User deletes chat history
    - BR3.3: User renames chat log
    - BR3.4: User exports chat log
    """

    @staticmethod
    def create_chat(user_id: int, obd_log_path: str, parsed_data: dict, name: Optional[str] = None) -> Chat:
        """
        Create a new chat session with parsed OBD data.

        Args:
            user_id: ID of the user creating the chat
            obd_log_path: Path to the uploaded OBD-II log file
            parsed_data: Parsed OBD-II data from OBDParser
            name: Optional name for the chat

        Returns:
            Created Chat object
        """
        with DatabaseSession() as session:
            chat = Chat(
                user_id=user_id,
                name=name or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                obd_log_path=obd_log_path,
                parsed_metrics=parsed_data.get("metrics"),
                fault_codes=parsed_data.get("fault_codes")
            )
            session.add(chat)
            session.flush()

            logger.info(f"Created chat {chat.id} for user {user_id}")

            # Detach from session
            session.expunge(chat)
            return chat

    @staticmethod
    def get_user_chats(user_id: int) -> List[Chat]:
        """
        Get all chats for a user (BR3.1).

        Args:
            user_id: User's ID

        Returns:
            List of Chat objects, ordered by most recent first
        """
        with DatabaseSession() as session:
            chats = session.query(Chat).filter(
                Chat.user_id == user_id
            ).order_by(Chat.updated_at.desc()).all()

            # Detach all chats from session
            for chat in chats:
                session.expunge(chat)

            return chats

    @staticmethod
    def get_chat(chat_id: int, user_id: int) -> Optional[Chat]:
        """
        Get a specific chat by ID.

        Args:
            chat_id: Chat ID
            user_id: User ID (for authorization)

        Returns:
            Chat object if found and owned by user, None otherwise
        """
        with DatabaseSession() as session:
            chat = session.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()

            if chat:
                session.expunge(chat)

            return chat

    @staticmethod
    def get_chat_messages(chat_id: int, user_id: int) -> List[Message]:
        """
        Get all messages for a chat.

        Args:
            chat_id: Chat ID
            user_id: User ID (for authorization)

        Returns:
            List of Message objects
        """
        with DatabaseSession() as session:
            # Verify ownership
            chat = session.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()

            if not chat:
                return []

            messages = session.query(Message).filter(
                Message.chat_id == chat_id
            ).order_by(Message.created_at).all()

            for message in messages:
                session.expunge(message)

            return messages

    @staticmethod
    def add_message(chat_id: int, role: str, content: str, severity: str = "normal", metadata: dict = None) -> Message:
        """
        Add a message to a chat.

        Args:
            chat_id: Chat ID
            role: Message role ('user' or 'assistant')
            content: Message content
            severity: Severity level for BR8 ('critical', 'warning', 'normal')
            metadata: Optional metadata (e.g., source documents)

        Returns:
            Created Message object
        """
        with DatabaseSession() as session:
            message = Message(
                chat_id=chat_id,
                role=role,
                content=content,
                severity=severity,
                extra_data=metadata
            )
            session.add(message)

            # Update chat's updated_at
            chat = session.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                chat.updated_at = datetime.utcnow()

            session.flush()
            session.expunge(message)

            logger.debug(f"Added {role} message to chat {chat_id}")
            return message

    @staticmethod
    def rename_chat(chat_id: int, user_id: int, new_name: str) -> Optional[Chat]:
        """
        Rename a chat (BR3.3).

        Args:
            chat_id: Chat ID
            user_id: User ID (for authorization)
            new_name: New name for the chat

        Returns:
            Updated Chat object, or None if not found
        """
        with DatabaseSession() as session:
            chat = session.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()

            if not chat:
                return None

            old_name = chat.name
            chat.rename(new_name)
            session.flush()

            logger.info(f"Renamed chat {chat_id}: '{old_name}' -> '{new_name}'")

            session.expunge(chat)
            return chat

    @staticmethod
    def delete_chat(chat_id: int, user_id: int) -> bool:
        """
        Delete a chat and all its messages (BR3.2).

        Args:
            chat_id: Chat ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        with DatabaseSession() as session:
            chat = session.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()

            if not chat:
                return False

            session.delete(chat)
            logger.info(f"Deleted chat {chat_id}")
            return True

    @staticmethod
    def delete_multiple_chats(chat_ids: List[int], user_id: int) -> int:
        """
        Delete multiple chats (BR3.2).

        Args:
            chat_ids: List of chat IDs to delete
            user_id: User ID (for authorization)

        Returns:
            Number of chats deleted
        """
        deleted_count = 0
        with DatabaseSession() as session:
            for chat_id in chat_ids:
                chat = session.query(Chat).filter(
                    Chat.id == chat_id,
                    Chat.user_id == user_id
                ).first()

                if chat:
                    session.delete(chat)
                    deleted_count += 1

            logger.info(f"Deleted {deleted_count} chats for user {user_id}")

        return deleted_count

    @staticmethod
    def export_chat(chat_id: int, user_id: int, export_format: str = "txt") -> Optional[str]:
        """
        Export a chat to a file (BR3.4).

        Args:
            chat_id: Chat ID
            user_id: User ID (for authorization)
            export_format: Export format ('txt' supported)

        Returns:
            Exported content as string, or None if not found
        """
        with DatabaseSession() as session:
            chat = session.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()

            if not chat:
                return None

            # Load messages
            messages = session.query(Message).filter(
                Message.chat_id == chat_id
            ).order_by(Message.created_at).all()

            if export_format.lower() == "txt":
                return ChatService._export_to_txt(chat, messages)
            else:
                logger.warning(f"Unsupported export format: {export_format}")
                return None

    @staticmethod
    def _export_to_txt(chat: Chat, messages: List[Message]) -> str:
        """Export chat to plain text format."""
        lines = [
            "=" * 60,
            f"OBD InsightBot - Chat Export",
            "=" * 60,
            f"Chat Name: {chat.name}",
            f"Created: {chat.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Last Updated: {chat.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 60,
            ""
        ]

        # Add parsed data summary if available
        if chat.parsed_metrics:
            lines.append("VEHICLE METRICS SUMMARY:")
            for metric in chat.parsed_metrics:
                status_icon = {"critical": "[!]", "warning": "[*]", "normal": "[+]"}.get(metric.get("status"), "[ ]")
                lines.append(f"  {status_icon} {metric.get('name', 'Unknown')}: {metric.get('value', 'N/A')} {metric.get('unit', '')}")
            lines.append("")

        if chat.fault_codes:
            lines.append("FAULT CODES:")
            for code in chat.fault_codes:
                lines.append(f"  - {code.get('code', 'Unknown')}: {code.get('description', 'No description')}")
            lines.append("")

        lines.append("-" * 60)
        lines.append("CONVERSATION:")
        lines.append("-" * 60)
        lines.append("")

        for message in messages:
            role_label = "You" if message.role == "user" else "InsightBot"
            timestamp = message.created_at.strftime("%H:%M:%S")
            severity_marker = ""
            if message.severity == "critical":
                severity_marker = " [CRITICAL]"
            elif message.severity == "warning":
                severity_marker = " [WARNING]"

            lines.append(f"[{timestamp}] {role_label}{severity_marker}:")
            lines.append(message.content)
            lines.append("")

        lines.append("=" * 60)
        lines.append("End of Export")
        lines.append("=" * 60)

        return "\n".join(lines)

    @staticmethod
    def get_chats_by_date(user_id: int, date: datetime) -> List[Chat]:
        """
        Get chats for a specific date (BR3.1).

        Args:
            user_id: User's ID
            date: Date to filter by

        Returns:
            List of chats created on the specified date
        """
        with DatabaseSession() as session:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

            chats = session.query(Chat).filter(
                Chat.user_id == user_id,
                Chat.created_at >= start_of_day,
                Chat.created_at <= end_of_day
            ).order_by(Chat.created_at.desc()).all()

            for chat in chats:
                session.expunge(chat)

            return chats

    @staticmethod
    def search_chats(user_id: int, query: str) -> List[Chat]:
        """
        Search chats by name or content.

        Args:
            user_id: User's ID
            query: Search query

        Returns:
            List of matching chats
        """
        with DatabaseSession() as session:
            chats = session.query(Chat).filter(
                Chat.user_id == user_id,
                Chat.name.ilike(f"%{query}%")
            ).order_by(Chat.updated_at.desc()).all()

            for chat in chats:
                session.expunge(chat)

            return chats
