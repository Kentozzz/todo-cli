"""
Slack API サービス
Phase 2: Slackブックマーク連携
"""
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time


@dataclass
class SlackBookmark:
    """Slackブックマークデータ"""
    id: str
    title: str
    link: str
    created: int  # Unix timestamp
    channel_id: str


class SlackAPIError(Exception):
    """Slack API エラー"""
    pass


class SlackService:
    """Slack API クライアント"""

    def __init__(self, token: str):
        """
        初期化

        Args:
            token: Slack OAuth Token (xoxp-* または xoxb-*)
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

    def list_bookmarks(self, channel_id: str) -> List[SlackBookmark]:
        """
        指定チャンネルのブックマーク一覧を取得

        Args:
            channel_id: チャンネルID（例: C01ABC123）

        Returns:
            List[SlackBookmark]: ブックマークのリスト

        Raises:
            SlackAPIError: API呼び出し失敗時
        """
        try:
            data = self._request(
                method="GET",
                endpoint="bookmarks.list",
                params={"channel_id": channel_id}
            )

            bookmarks = []
            for item in data.get("bookmarks", []):
                # linkタイプのブックマークのみ処理
                if item.get("type") == "link":
                    bookmark = SlackBookmark(
                        id=item["id"],
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        created=item.get("date_created", 0),
                        channel_id=channel_id
                    )
                    bookmarks.append(bookmark)

            return bookmarks

        except SlackAPIError:
            raise
        except Exception as e:
            raise SlackAPIError(f"Failed to list bookmarks: {e}")

    def remove_bookmark(self, channel_id: str, bookmark_id: str) -> bool:
        """
        ブックマークを削除

        Args:
            channel_id: チャンネルID
            bookmark_id: ブックマークID

        Returns:
            bool: 削除成功時True

        Raises:
            SlackAPIError: API呼び出し失敗時
        """
        try:
            self._request(
                method="POST",
                endpoint="bookmarks.remove",
                json_data={
                    "channel_id": channel_id,
                    "bookmark_id": bookmark_id
                }
            )
            return True

        except SlackAPIError:
            raise
        except Exception as e:
            raise SlackAPIError(f"Failed to remove bookmark: {e}")

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
