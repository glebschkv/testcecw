"""
Input validation utilities.
"""

import re
from typing import Tuple
from pathlib import Path


class Validators:
    """Collection of validation functions."""

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username format.

        Args:
            username: Username to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"

        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if len(username) > 50:
            return False, "Username must be at most 50 characters"

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"

        return True, ""

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"

        if len(password) < 6:
            return False, "Password must be at least 6 characters"

        if len(password) > 128:
            return False, "Password must be at most 128 characters"

        return True, ""

    @staticmethod
    def validate_passwords_match(password: str, confirm: str) -> Tuple[bool, str]:
        """
        Validate that passwords match.

        Args:
            password: Primary password
            confirm: Confirmation password

        Returns:
            Tuple of (is_valid, error_message)
        """
        if password != confirm:
            return False, "Passwords do not match"

        return True, ""

    @staticmethod
    def validate_file_path(file_path: str, expected_extension: str = ".csv") -> Tuple[bool, str]:
        """
        Validate a file path.

        Args:
            file_path: Path to validate
            expected_extension: Expected file extension

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "File path is required"

        path = Path(file_path)

        if not path.exists():
            return False, "File does not exist"

        if not path.is_file():
            return False, "Path is not a file"

        if expected_extension and path.suffix.lower() != expected_extension.lower():
            return False, f"File must be a {expected_extension} file"

        return True, ""

    @staticmethod
    def validate_chat_name(name: str) -> Tuple[bool, str]:
        """
        Validate chat name.

        Args:
            name: Chat name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Chat name is required"

        if len(name) > 100:
            return False, "Chat name must be at most 100 characters"

        # Check for invalid characters
        if re.search(r'[<>:"/\\|?*]', name):
            return False, "Chat name contains invalid characters"

        return True, ""

    @staticmethod
    def validate_obd_fault_code(code: str) -> Tuple[bool, str]:
        """
        Validate OBD-II fault code format.

        Args:
            code: Fault code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not code:
            return False, "Fault code is required"

        # OBD-II codes are in format: PXXXX, CXXXX, BXXXX, or UXXXX
        pattern = r'^[PCBU][0-9]{4}$'

        if not re.match(pattern, code.upper()):
            return False, "Invalid fault code format. Expected format: P0123, C0123, B0123, or U0123"

        return True, ""
