"""
サマリー表示ビュー
Phase 1: MVP - ステータスバー用1行出力
"""
from typing import List
from todo_cli.core.models import Task


def render_summary(tasks: List[Task]) -> None:
    """
    未完了タスク件数を1行で出力（iTerm2/tmuxステータスバー用）

    Args:
        tasks: タスクのリスト
    """
    pending_count = sum(1 for task in tasks if task.is_pending())
    print(f"Todo: {pending_count}件")


def render_summary_detailed(tasks: List[Task]) -> None:
    """
    詳細なサマリーを1行で出力

    Args:
        tasks: タスクのリスト
    """
    pending_count = sum(1 for task in tasks if task.is_pending())
    done_count = sum(1 for task in tasks if task.is_done())
    total_count = len(tasks)

    print(f"Todo: {pending_count}件 | 完了: {done_count}件 | 合計: {total_count}件")


def get_summary_string(tasks: List[Task]) -> str:
    """
    サマリー文字列を取得（プログラムから利用可能）

    Args:
        tasks: タスクのリスト

    Returns:
        str: サマリー文字列
    """
    pending_count = sum(1 for task in tasks if task.is_pending())
    return f"Todo: {pending_count}件"
