"""
File-based persistence for instance tracking state.
Stores instance records and user assignments at ~/.cr8/instance_assignments.json.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from .models import InstanceRecord, UserSession

logger = logging.getLogger(__name__)


class InstanceManagerState:
    """File-based persistence for instance-to-user assignment tracking."""

    def __init__(self):
        self.state_file = Path.home() / ".cr8" / "instance_assignments.json"
        self.instances: dict[int, InstanceRecord] = {}
        self.user_assignments: dict[str, int] = {}  # username -> vastai_id
        self._ensure_dir()
        self._load()

    def _ensure_dir(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                for id_str, rec_data in data.get("instances", {}).items():
                    self.instances[int(id_str)] = InstanceRecord.from_dict(rec_data)
                self.user_assignments = data.get("user_assignments", {})
                logger.info(
                    f"Loaded state: {len(self.instances)} instances, "
                    f"{len(self.user_assignments)} user assignments"
                )
        except Exception as e:
            logger.warning(f"Failed to load instance state: {e}")

    def save(self):
        try:
            data = {
                "instances": {str(k): v.to_dict() for k, v in self.instances.items()},
                "user_assignments": self.user_assignments,
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save instance state: {e}")

    def add_instance(self, record: InstanceRecord):
        self.instances[record.vastai_id] = record
        self.save()

    def add_user(self, instance_id: int, session: UserSession):
        if instance_id in self.instances:
            self.instances[instance_id].users[session.username] = session
            import time
            self.instances[instance_id].last_user_activity = time.time()
            self.user_assignments[session.username] = instance_id
            self.save()

    def remove_user(self, username: str) -> Optional[int]:
        instance_id = self.user_assignments.pop(username, None)
        if instance_id and instance_id in self.instances:
            self.instances[instance_id].users.pop(username, None)
            import time
            self.instances[instance_id].last_user_activity = time.time()
            self.save()
        return instance_id

    def remove_instance(self, instance_id: int):
        record = self.instances.pop(instance_id, None)
        if record:
            for username in list(record.users.keys()):
                self.user_assignments.pop(username, None)
            self.save()

    def get_user_instance(self, username: str) -> Optional[int]:
        return self.user_assignments.get(username)

    def find_available_instance(self, gpu_name: str) -> Optional[InstanceRecord]:
        """Find a running instance with the matching GPU that has capacity."""
        for record in self.instances.values():
            if record.gpu_name == gpu_name and record.status == "running" and record.has_capacity:
                return record
        return None
