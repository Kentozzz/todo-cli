"""
データモデル定義
Phase 1: MVP - ローカルタスク管理用の基本モデル
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Literal

TaskStatus = Literal["pending", "done"]


@dataclass
class Task:
    """
    タスクデータモデル

    Attributes:
        id: タスクID（連番、欠番なし）
        title: タスク名
        url: SlackのURL（Phase 2で使用、Phase 1では空文字列可）
        due: 期日（ISO 8601形式: "2025-11-10"）
        status: ステータス（"pending" | "done"）
        created_at: 作成日時（ISO 8601形式）
    """
    id: int
    title: str
    url: str
    due: Optional[str]
    status: TaskStatus
    created_at: str

    @classmethod
    def create(cls, id: int, title: str, due: Optional[str] = None, url: str = "") -> "Task":
        """
        新規タスクを作成

        Args:
            id: タスクID
            title: タスク名
            due: 期日（オプション）
            url: SlackのURL（Phase 1では不要）

        Returns:
            Task: 新規タスクインスタンス
        """
        now = datetime.now().isoformat()
        return cls(
            id=id,
            title=title,
            url=url,
            due=due,
            status="pending",
            created_at=now
        )

    def to_dict(self) -> dict:
        """タスクを辞書形式に変換"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """辞書からタスクを生成"""
        return cls(**data)

    def mark_done(self) -> None:
        """タスクを完了状態にする"""
        self.status = "done"

    def is_pending(self) -> bool:
        """未完了かどうかを判定"""
        return self.status == "pending"

    def is_done(self) -> bool:
        """完了済みかどうかを判定"""
        return self.status == "done"


@dataclass
class Config:
    """
    設定データモデル（Phase 2で使用）

    Attributes:
        slack_token: Slack OAuth Token
        slack_channel_id: Slackチャンネ ID（ブックマーク取得先）
        default_sort: デフォルトソート順（"due" | "created" | "id"）
    """
    slack_token: str = ""
    slack_channel_id: str = ""
    default_sort: Literal["due", "created", "id"] = "due"

    def to_dict(self) -> dict:
        """設定を辞書形式に変換"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """辞書から設定を生成"""
        return cls(**data)
