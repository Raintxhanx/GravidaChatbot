from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class User:
    email: str
    role: str
    id: Optional[uuid.UUID] = None
    profile_picture: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None