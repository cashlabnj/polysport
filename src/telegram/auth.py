from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TelegramAuth:
    admin_ids: set[int]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids
