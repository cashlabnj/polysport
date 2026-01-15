from __future__ import annotations

from dataclasses import dataclass
from typing import Set


@dataclass
class TelegramAuth:
    admin_ids: Set[int]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids
