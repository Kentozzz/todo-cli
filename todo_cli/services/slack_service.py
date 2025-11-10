"""
Slack API サービス
Phase 2（改訂版）: Slack リアクション連携
公式API使用: reactions.list
"""
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time


@dataclass
class SlackReactionItem:
    """Slackリアクション付きアイテムデータ"""
    message_url: str      # メッセージのURL
    title: str            # メッセージテキスト
    timestamp: float      # Unix timestamp
    channel_id: str       # チャンネルID
    message_ts: str       # メッセージタイムスタンプ


class SlackAPIError(Exception):
    """Slack API エラー"""
    pass


class SlackService:
    """Slack API クライアント"""

    def __init__(self, token: str):
        """
        初期化

        Args:
            token: Slack OAuth Token (xoxp-*)
        """
        self.token = token
        self.base_url = "https://slack.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Slack APIリクエストを実行

        Args:
            method: HTTPメソッド（GET, POST, DELETE など）
            endpoint: APIエンドポイント
            params: クエリパラメータ
            json_data: JSONボディ
            max_retries: 最大リトライ回数

        Returns:
            Dict[str, Any]: APIレスポンス

        Raises:
            SlackAPIError: API呼び出し失敗時
        """
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()

                # Slack API のエラーチェック
                if not data.get("ok"):
                    error = data.get("error", "unknown_error")
                    raise SlackAPIError(f"Slack API error: {error}")

                return data

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    # リトライ前に待機（exponential backoff）
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise SlackAPIError(f"Request failed: {e}")

        raise SlackAPIError("Max retries exceeded")

    def list_reactions(self, emoji: str = "eyes", limit: int = 50) -> List[SlackReactionItem]:
        """
        特定の絵文字リアクションを付けたアイテムを取得

        Args:
            emoji: 絵文字名（例：eyes, memo, white_check_mark）
            limit: 取得件数（デフォルト50）

        Returns:
            List[SlackReactionItem]: リアクション付きアイテムのリスト

        Raises:
            SlackAPIError: API呼び出し失敗時
        """
        try:
            data = self._request(
                method="GET",
                endpoint="reactions.list",
                params={"limit": limit, "full": "true"}
            )

            reaction_items = []
            for item in data.get("items", []):
                # メッセージタイプのアイテムのみ処理
                if item.get("type") != "message":
                    continue

                message = item.get("message", {})
                reactions = message.get("reactions", [])

                # 指定された絵文字のリアクションがあるかチェック
                has_target_emoji = any(
                    r.get("name") == emoji and self._is_user_reacted(r)
                    for r in reactions
                )

                if not has_target_emoji:
                    continue

                # メッセージテキストを取得
                title = message.get("text", "")
                if not title:
                    title = "Untitled"

                # チャンネル情報を取得
                channel_id = item.get("channel", "")
                message_ts = message.get("ts", "")

                # パーマリンクを構築
                permalink = message.get("permalink")
                if not permalink and channel_id and message_ts:
                    # パーマリンクがない場合は構築
                    ts_for_url = message_ts.replace(".", "")
                    permalink = f"https://slack.com/archives/{channel_id}/p{ts_for_url}"

                if not permalink:
                    continue

                reaction_item = SlackReactionItem(
                    message_url=permalink,
                    title=title[:100],  # タイトルを100文字に制限
                    timestamp=float(message_ts) if message_ts else 0.0,
                    channel_id=channel_id,
                    message_ts=message_ts
                )
                reaction_items.append(reaction_item)

            return reaction_items

        except SlackAPIError:
            raise
        except Exception as e:
            raise SlackAPIError(f"Failed to list reactions: {e}")

    def _is_user_reacted(self, reaction: Dict[str, Any]) -> bool:
        """
        認証ユーザーがリアクションしているかチェック

        Args:
            reaction: リアクションオブジェクト

        Returns:
            bool: ユーザーがリアクションしている場合True
        """
        # reactions.listは認証ユーザーのリアクションのみ返すため、
        # usersリストに自分が含まれているかチェック
        users = reaction.get("users", [])
        return len(users) > 0

    def remove_reaction(self, emoji: str, channel: str, timestamp: str) -> bool:
        """
        リアクションを削除

        Args:
            emoji: 絵文字名
            channel: チャンネルID
            timestamp: メッセージタイムスタンプ

        Returns:
            bool: 削除成功時True

        Raises:
            SlackAPIError: API呼び出し失敗時
        """
        try:
            self._request(
                method="POST",
                endpoint="reactions.remove",
                json_data={
                    "name": emoji,
                    "channel": channel,
                    "timestamp": timestamp
                }
            )
            return True

        except SlackAPIError:
            raise
        except Exception as e:
            raise SlackAPIError(f"Failed to remove reaction: {e}")

    def test_connection(self) -> bool:
        """
        Slack API接続テスト

        Returns:
            bool: 接続成功時True

        Raises:
            SlackAPIError: 接続失敗時
        """
        try:
            data = self._request(method="GET", endpoint="auth.test")
            return data.get("ok", False)
        except SlackAPIError:
            raise
        except Exception as e:
            raise SlackAPIError(f"Connection test failed: {e}")

    def get_user_info(self) -> Dict[str, Any]:
        """
        認証ユーザーの情報を取得

        Returns:
            Dict[str, Any]: ユーザー情報

        Raises:
            SlackAPIError: API呼び出し失敗時
        """
        try:
            data = self._request(method="GET", endpoint="auth.test")
            return {
                "user": data.get("user"),
                "user_id": data.get("user_id"),
                "team": data.get("team"),
                "team_id": data.get("team_id")
            }
        except SlackAPIError:
            raise
        except Exception as e:
            raise SlackAPIError(f"Failed to get user info: {e}")
