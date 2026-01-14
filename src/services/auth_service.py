"""
Authentication service for user management.
Implements BR1: Account Management
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import secrets
import hashlib
from datetime import datetime, timedelta

from ..models.base import get_session, DatabaseSession
from ..models.user import User
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthService:
    """
    Service for user authentication and account management.

    Implements:
    - BR1.1: User creates an account
    - BR1.2: User logs-in to their account
    - BR1.3: User logs-out of their account
    - BR1.4: User deletes their account
    """

    # Active sessions: {session_token: user_id}
    _sessions: dict[str, Tuple[int, datetime]] = {}

    # Session expiry time (24 hours)
    SESSION_EXPIRY_HOURS = 24

    @classmethod
    def register(cls, username: str, password: str) -> User:
        """
        Register a new user account (BR1.1).

        Args:
            username: Unique username (3-50 characters)
            password: Password (minimum 6 characters)

        Returns:
            Created User object

        Raises:
            AuthenticationError: If registration fails
        """
        # Validate input
        cls._validate_username(username)
        cls._validate_password(password)

        with DatabaseSession() as session:
            # Check if username already exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                raise AuthenticationError(f"Username '{username}' is already taken")

            # Create new user
            user = User.create(username=username, password=password)
            session.add(user)
            session.flush()  # Get the user ID

            logger.info(f"New user registered: {username} (ID: {user.id})")
            return user

    @classmethod
    def login(cls, username: str, password: str) -> Tuple[User, str]:
        """
        Authenticate user and create session (BR1.2).

        Args:
            username: User's username
            password: User's password

        Returns:
            Tuple of (User object, session token)

        Raises:
            AuthenticationError: If login fails
        """
        with DatabaseSession() as session:
            # Find user
            user = session.query(User).filter(User.username == username).first()

            if not user:
                logger.warning(f"Login failed: User '{username}' not found")
                raise AuthenticationError("Invalid username or password")

            if not user.is_active:
                logger.warning(f"Login failed: User '{username}' is deactivated")
                raise AuthenticationError("Account is deactivated")

            # Verify password
            if not user.check_password(password):
                logger.warning(f"Login failed: Invalid password for '{username}'")
                raise AuthenticationError("Invalid username or password")

            # Update last login
            user.update_last_login()

            # Create session token
            session_token = cls._create_session(user.id)

            logger.info(f"User logged in: {username} (ID: {user.id})")

            # Detach user from session for return
            session.expunge(user)
            return user, session_token

    @classmethod
    def logout(cls, session_token: str) -> bool:
        """
        End user session (BR1.3).

        Args:
            session_token: Active session token

        Returns:
            True if logout successful
        """
        if session_token in cls._sessions:
            user_id = cls._sessions[session_token][0]
            del cls._sessions[session_token]
            logger.info(f"User logged out (ID: {user_id})")
            return True

        logger.warning("Logout attempted with invalid session token")
        return False

    @classmethod
    def delete_account(cls, user_id: int, password: str) -> bool:
        """
        Delete user account and all associated data (BR1.4).

        Args:
            user_id: ID of user to delete
            password: User's password for confirmation

        Returns:
            True if deletion successful

        Raises:
            AuthenticationError: If deletion fails
        """
        with DatabaseSession() as session:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                raise AuthenticationError("User not found")

            # Verify password for security
            if not user.check_password(password):
                raise AuthenticationError("Invalid password")

            username = user.username

            # Delete user (cascades to chats and messages)
            session.delete(user)

            # Remove any active sessions for this user
            cls._remove_user_sessions(user_id)

            logger.info(f"Account deleted: {username} (ID: {user_id})")
            return True

    @classmethod
    def validate_session(cls, session_token: str) -> Optional[User]:
        """
        Validate a session token and return the associated user.

        Args:
            session_token: Session token to validate

        Returns:
            User object if valid, None otherwise
        """
        if session_token not in cls._sessions:
            return None

        user_id, created_at = cls._sessions[session_token]

        # Check session expiry
        if datetime.utcnow() - created_at > timedelta(hours=cls.SESSION_EXPIRY_HOURS):
            del cls._sessions[session_token]
            logger.info(f"Session expired for user ID: {user_id}")
            return None

        # Get user from database
        with DatabaseSession() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.expunge(user)
            return user

    @classmethod
    def get_current_user(cls, session_token: str) -> Optional[User]:
        """Alias for validate_session."""
        return cls.validate_session(session_token)

    @classmethod
    def change_password(cls, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user's password.

        Args:
            user_id: User's ID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            AuthenticationError: If change fails
        """
        cls._validate_password(new_password)

        with DatabaseSession() as session:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                raise AuthenticationError("User not found")

            if not user.check_password(old_password):
                raise AuthenticationError("Current password is incorrect")

            user.set_password(new_password)
            logger.info(f"Password changed for user ID: {user_id}")
            return True

    # Private helper methods

    @classmethod
    def _validate_username(cls, username: str) -> None:
        """Validate username format."""
        if not username or len(username) < 3:
            raise AuthenticationError("Username must be at least 3 characters")
        if len(username) > 50:
            raise AuthenticationError("Username must be at most 50 characters")
        if not username.isalnum() and "_" not in username:
            raise AuthenticationError("Username can only contain letters, numbers, and underscores")

    @classmethod
    def _validate_password(cls, password: str) -> None:
        """Validate password strength."""
        if not password or len(password) < 6:
            raise AuthenticationError("Password must be at least 6 characters")
        if len(password) > 128:
            raise AuthenticationError("Password must be at most 128 characters")

    @classmethod
    def _create_session(cls, user_id: int) -> str:
        """Create a new session token for a user."""
        # Remove any existing sessions for this user (single session policy)
        cls._remove_user_sessions(user_id)

        # Generate secure token
        token = secrets.token_urlsafe(32)
        cls._sessions[token] = (user_id, datetime.utcnow())
        return token

    @classmethod
    def _remove_user_sessions(cls, user_id: int) -> None:
        """Remove all sessions for a specific user."""
        tokens_to_remove = [
            token for token, (uid, _) in cls._sessions.items()
            if uid == user_id
        ]
        for token in tokens_to_remove:
            del cls._sessions[token]
