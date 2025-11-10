"""
ユーティリティ関数
Phase 1: MVP - 日時変換、フォーマット処理など
"""
from datetime import datetime
from typing import Optional


def format_date(date_str: Optional[str]) -> str:
    """
    ISO 8601形式の日付を表示用にフォーマット

    Args:
        date_str: ISO 8601形式の日付文字列（例: "2025-11-10"）

    Returns:
        str: フォーマットされた日付（例: "11/10"）、Noneの場合は "-"
    """
    if not date_str:
        return "-"

    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%m/%d")
    except (ValueError, TypeError):
        return "-"


def parse_date(date_input: str) -> Optional[str]:
    """
    ユーザー入力の日付をISO 8601形式に変換

    サポートする形式:
    - "2025-11-10" (ISO 8601)
    - "11/10" (月/日)
    - "11-10" (月-日)

    Args:
        date_input: ユーザー入力の日付文字列

    Returns:
        Optional[str]: ISO 8601形式の日付、パース失敗時はNone
    """
    if not date_input:
        return None

    # ISO 8601形式の場合はそのまま返す
    try:
        datetime.fromisoformat(date_input)
        return date_input
    except ValueError:
        pass

    # "月/日" または "月-日" 形式を試す
    current_year = datetime.now().year
    for separator in ["/", "-"]:
        if separator in date_input:
            try:
                parts = date_input.split(separator)
                if len(parts) == 2:
                    month, day = int(parts[0]), int(parts[1])
                    dt = datetime(current_year, month, day)
                    return dt.date().isoformat()
            except (ValueError, IndexError):
                pass

    return None


def format_datetime(dt_str: str) -> str:
    """
    ISO 8601形式の日時を表示用にフォーマット

    Args:
        dt_str: ISO 8601形式の日時文字列

    Returns:
        str: フォーマットされた日時（例: "2025-11-10 14:30"）
    """
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return dt_str


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    テキストを指定文字数で切り詰める

    Args:
        text: 切り詰め対象のテキスト
        max_length: 最大文字数（デフォルト: 50）

    Returns:
        str: 切り詰められたテキスト（超過時は"..."を追加）
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def validate_task_id(task_id: str) -> Optional[int]:
    """
    タスクIDの妥当性を検証

    Args:
        task_id: タスクIDの文字列

    Returns:
        Optional[int]: 有効な場合は整数のID、無効な場合はNone
    """
    try:
        id_int = int(task_id)
        if id_int > 0:
            return id_int
        return None
    except (ValueError, TypeError):
        return None
