"""
Data models for instance tracking and user assignments.
"""

from dataclasses import dataclass, field, asdict


@dataclass
class UserSession:
    """Tracks a user's Blender session on an instance."""
    username: str
    blender_pid: int
    started_at: float  # timestamp

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserSession":
        return cls(**data)


@dataclass
class InstanceRecord:
    """Tracks a VastAI instance and its users."""
    vastai_id: int
    gpu_name: str
    host: str
    ssh_port: int
    status: str  # "provisioning", "running", "destroying"
    max_users: int
    created_at: float  # timestamp
    last_user_activity: float  # timestamp
    users: dict[str, UserSession] = field(default_factory=dict)

    @property
    def user_count(self) -> int:
        return len(self.users)

    @property
    def has_capacity(self) -> bool:
        return self.user_count < self.max_users

    @property
    def is_empty(self) -> bool:
        return self.user_count == 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["users"] = {
            k: v.to_dict() if isinstance(v, UserSession) else v
            for k, v in self.users.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "InstanceRecord":
        users = {}
        for k, v in data.get("users", {}).items():
            users[k] = UserSession.from_dict(v) if isinstance(v, dict) else v
        data["users"] = users
        return cls(**data)


@dataclass
class InstanceAssignment:
    """Returned to callers — represents a user's assignment to an instance."""
    instance_id: int
    host: str
    ssh_port: int
    gpu_name: str
    blender_pid: int
