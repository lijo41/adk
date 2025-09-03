"""User and session models."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    """User model."""
    id: str
    username: str
    email: str
    role: UserRole
    created_time: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


@dataclass
class Session:
    """User session model."""
    id: str
    user_id: str
    created_time: datetime
    last_activity: datetime
    is_active: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
