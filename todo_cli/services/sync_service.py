"""
同期サービス
Phase 2: Slack⇄ローカル同期ロジック
"""
import os
from typing import List, Optional, Tuple
from datetime import datetime
from todo_cli.core.models import Task
from todo_cli.core.storage import TaskStorage, ConfigStorage
from todo_cli.services.slack_service import SlackService, SlackBookmark, SlackAPIError


class SyncService:
    """Slackとローカルの同期を管理"""

    def __init__(self, storage: Optional[TaskStorage] = None):
        """
        初期化

        Args:
            storage: タスクストレージ（テスト用にオーバーライド可能）
        """
        self.storage = storage or TaskStorage()
        self.config_storage = ConfigStorage()
        self.slack_service: Optional[SlackService] = None

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

    def _get_channel_id(self) -> str:
        """
        設定からチャンネルIDを取得

        Returns:
            str: チャンネルID

        Raises:
            ValueError: チャンネルIDが設定されていない場合
        """
        config = self.config_storage.load()
        if not config.slack_channel_id:
            raise ValueError(
                "Slackチャンネル IDが設定されていません。\n"
                "todo setup コマンドで設定してください。"
            )
        return config.slack_channel_id

    def pull_from_slack(self) -> Tuple[int, int, int]:
        """
        Slackからブックマークを取得してローカルと同期（Pull）

        処理フロー:
        1. Slackからブックマーク一覧を取得
        2. ローカルタスクと照合
        3. 新規ブックマーク → ローカルに追加
        4. Slackで削除されたブックマーク → ローカルから削除（完了済みは保持）

        Returns:
            Tuple[int, int, int]: (追加件数, 削除件数, エラー件数)

        Raises:
            ValueError: 設定エラー
            SlackAPIError: Slack API呼び出しエラー
        """
        try:
            slack = self._get_slack_service()
            channel_id = self._get_channel_id()

            # Slackからブックマーク取得
            slack_bookmarks = slack.list_bookmarks(channel_id)
            slack_urls = {bm.link for bm in slack_bookmarks}

            # ローカルタスク取得
            local_tasks = self.storage.load_all()
            local_pending_tasks = [t for t in local_tasks if t.is_pending()]

            added_count = 0
            deleted_count = 0

            # 新規ブックマークをローカルに追加
            local_urls = {t.url for t in local_tasks if t.url}
            for bookmark in slack_bookmarks:
                if bookmark.link not in local_urls:
                    # 新規タスクとして追加
                    self.storage.add_task(
                        title=bookmark.title or "Untitled",
                        due=None,
                        url=bookmark.link
                    )
                    added_count += 1

            # Slackで削除されたブックマークをローカルから削除
            for task in local_pending_tasks:
                if task.url and task.url not in slack_urls:
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
        ローカルタスクに対応するSlackブックマークを削除（Push）

        Args:
            task_url: 削除するタスクのURL

        Returns:
            bool: 削除成功時True

        Raises:
            ValueError: 設定エラー
            SlackAPIError: Slack API呼び出しエラー
        """
        try:
            if not task_url:
                return False

            slack = self._get_slack_service()
            channel_id = self._get_channel_id()

            # Slackからブックマークを取得してURLで検索
            bookmarks = slack.list_bookmarks(channel_id)
            for bookmark in bookmarks:
                if bookmark.link == task_url:
                    # 一致するブックマークを削除
                    slack.remove_bookmark(channel_id, bookmark.id)
                    return True

            # 一致するブックマークが見つからなかった
            return False

        except (ValueError, SlackAPIError):
            raise
        except Exception as e:
            raise SlackAPIError(f"Slackブックマーク削除中にエラーが発生しました: {e}")

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
                message = f"接続成功: {user_info.get('user')} @ {user_info.get('team')}"
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
        # 環境変数チェック
        if not os.getenv("SLACK_TOKEN"):
            return False

        # チャンネルID設定チェック
        config = self.config_storage.load()
        if not config.slack_channel_id:
            return False

        return True
