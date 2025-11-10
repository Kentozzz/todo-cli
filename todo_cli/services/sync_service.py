"""
同期サービス
Phase 2（改訂版）: Slack リアクション ⇄ ローカル同期ロジック
"""
import os
import time
from typing import List, Optional, Tuple, Dict
from datetime import datetime
from todo_cli.core.models import Task
from todo_cli.core.storage import TaskStorage, ConfigStorage
from todo_cli.services.slack_service import SlackService, SlackReactionItem, SlackAPIError


class SyncService:
    """Slackとローカルの同期を管理"""

    # キャッシュ有効期限（秒）
    CACHE_DURATION = 60  # 1分間

    def __init__(self, storage: Optional[TaskStorage] = None):
        """
        初期化

        Args:
            storage: タスクストレージ（テスト用にオーバーライド可能）
        """
        self.storage = storage or TaskStorage()
        self.config_storage = ConfigStorage()
        self.slack_service: Optional[SlackService] = None
        self._last_sync_time: float = 0
        self._last_sync_data: List[SlackReactionItem] = []

    def _get_slack_service(self) -> SlackService:
        """
        Slack APIサービスを取得

        Returns:
            SlackService: Slackサービスインスタンス

        Raises:
            ValueError: SLACK_TOKEN環境変数が設定されていない場合
        """
        if self.slack_service:
            return self.slack_service

        # 環境変数からトークンを取得
        token = os.getenv("SLACK_TOKEN")
        if not token:
            raise ValueError(
                "SLACK_TOKEN環境変数が設定されていません。\n"
                "export SLACK_TOKEN=xoxp-your-token を実行してください。"
            )

        self.slack_service = SlackService(token)
        return self.slack_service

    def _get_reaction_emoji(self) -> str:
        """
        設定から使用する絵文字を取得

        Returns:
            str: 絵文字名（デフォルト: "eyes"）
        """
        config = self.config_storage.load()
        return getattr(config, "reaction_emoji", "eyes")

    def _should_use_cache(self) -> bool:
        """
        キャッシュを使用すべきかチェック

        Returns:
            bool: キャッシュが有効な場合True
        """
        current_time = time.time()
        elapsed = current_time - self._last_sync_time
        return elapsed < self.CACHE_DURATION and len(self._last_sync_data) > 0

    def pull_from_slack(self, force: bool = False) -> Tuple[int, int, int]:
        """
        Slackのリアクション付きメッセージを取得してローカルと同期（Pull）

        処理フロー:
        1. Slackからリアクション付きメッセージを取得（キャッシュ利用可能）
        2. ローカルタスクと照合
        3. 新規アイテム → ローカルに追加
        4. Slackで削除されたアイテム → ローカルから削除（完了済みは保持）

        Args:
            force: Trueの場合、キャッシュを無視して強制的に取得

        Returns:
            Tuple[int, int, int]: (追加件数, 削除件数, エラー件数)

        Raises:
            ValueError: 設定エラー
            SlackAPIError: Slack API呼び出しエラー
        """
        try:
            slack = self._get_slack_service()
            emoji = self._get_reaction_emoji()

            # キャッシュチェック
            if not force and self._should_use_cache():
                reaction_items = self._last_sync_data
            else:
                # Slackからリアクション付きメッセージ取得
                reaction_items = slack.list_reactions(emoji=emoji, limit=50)
                # キャッシュ更新
                self._last_sync_time = time.time()
                self._last_sync_data = reaction_items

            slack_urls = {item.message_url for item in reaction_items}

            # ローカルタスク取得
            local_tasks = self.storage.load_all()
            local_pending_tasks = [t for t in local_tasks if t.is_pending()]

            added_count = 0
            deleted_count = 0

            # 新規アイテムをローカルに追加
            # ローカルのベースURLセット（メタデータを除去）
            local_base_urls = {
                t.url.split("#channel=")[0] for t in local_tasks if t.url
            }
            for item in reaction_items:
                if item.message_url not in local_base_urls:
                    # 新規タスクとして追加
                    # URLにチャンネルIDとタイムスタンプを埋め込む（削除時に使用）
                    url_with_metadata = (
                        f"{item.message_url}"
                        f"#channel={item.channel_id}"
                        f"&ts={item.message_ts}"
                        f"&emoji={emoji}"
                    )
                    self.storage.add_task(
                        title=item.title,
                        due=None,
                        url=url_with_metadata
                    )
                    added_count += 1

            # Slackで削除されたアイテムをローカルから削除
            for task in local_pending_tasks:
                if task.url:
                    # URLからベースURLを抽出
                    base_url = task.url.split("#channel=")[0]
                    if base_url and base_url not in slack_urls:
                        # 未完了タスクのみ削除（完了済みは履歴として保持）
                        self.storage.delete_task(task.id)
                        deleted_count += 1

            return (added_count, deleted_count, 0)

        except (ValueError, SlackAPIError):
            raise
        except Exception as e:
            raise SlackAPIError(f"同期処理中にエラーが発生しました: {e}")

    def push_to_slack(self, task_url: str) -> bool:
        """
        ローカルタスクに対応するSlackリアクションを削除（Push）

        Args:
            task_url: 削除するタスクのURL（メタデータ埋め込み済み）

        Returns:
            bool: 削除成功時True

        Raises:
            ValueError: 設定エラー
            SlackAPIError: Slack API呼び出しエラー
        """
        try:
            if not task_url:
                return False

            # URLからメタデータを抽出
            # 形式: {base_url}#channel={channel_id}&ts={timestamp}&emoji={emoji}
            if "#channel=" not in task_url:
                # メタデータが埋め込まれていない（古いデータ）
                return False

            parts = task_url.split("#channel=")
            if len(parts) != 2:
                return False

            metadata = parts[1]
            meta_parts = metadata.split("&")

            channel_id = None
            timestamp = None
            emoji = None

            for part in meta_parts:
                if part.startswith("ts="):
                    timestamp = part[3:]
                elif part.startswith("emoji="):
                    emoji = part[6:]
                elif "=" not in part:
                    channel_id = part
                else:
                    key, value = part.split("=", 1)
                    if key == "":
                        channel_id = value

            if not all([channel_id, timestamp, emoji]):
                return False

            slack = self._get_slack_service()

            # Slackリアクションを削除
            slack.remove_reaction(emoji=emoji, channel=channel_id, timestamp=timestamp)

            # キャッシュをクリア（次回取得時に最新データを取得）
            self._last_sync_time = 0
            self._last_sync_data = []

            return True

        except (ValueError, SlackAPIError):
            raise
        except Exception as e:
            raise SlackAPIError(f"Slackリアクション削除中にエラーが発生しました: {e}")

    def test_slack_connection(self) -> Tuple[bool, str]:
        """
        Slack接続をテスト

        Returns:
            Tuple[bool, str]: (成功/失敗, メッセージ)
        """
        try:
            slack = self._get_slack_service()
            if slack.test_connection():
                user_info = slack.get_user_info()
                emoji = self._get_reaction_emoji()
                message = f"接続成功: {user_info.get('user')} @ {user_info.get('team')}\n使用絵文字: :{emoji}:"
                return (True, message)
            else:
                return (False, "接続失敗")

        except ValueError as e:
            return (False, str(e))
        except SlackAPIError as e:
            return (False, f"API error: {e}")
        except Exception as e:
            return (False, f"予期しないエラー: {e}")

    def is_slack_configured(self) -> bool:
        """
        Slack連携が設定済みかチェック

        Returns:
            bool: 設定済みならTrue
        """
        # 環境変数チェックのみ
        return bool(os.getenv("SLACK_TOKEN"))
