"""
タスク一覧表示ビュー
Phase 1: MVP - 表形式でのタスク表示
"""
from typing import List
from todo_cli.core.models import Task
from todo_cli.core.utils import format_date, truncate_text


def render_task_list(tasks: List[Task], show_all: bool = False) -> None:
    """
    タスク一覧を表形式で表示

    Args:
        tasks: 表示するタスクのリスト
        show_all: 完了タスクも含めて表示するか（Phase 1では未使用）
    """
    if not tasks:
        print("タスクがありません")
        return

    # ヘッダー表示
    print(f"{'ID':<4} | {'タイトル':<40} | {'期日':<8}")
    print("-" * 60)

    # タスク表示
    for task in tasks:
        title = truncate_text(task.title, max_length=40)
        due = format_date(task.due)
        status_marker = "✓" if task.is_done() else " "

        print(f"{task.id:<4} | {title:<40} | {due:<8}")

    # 統計情報表示
    pending_count = sum(1 for t in tasks if t.is_pending())
    done_count = sum(1 for t in tasks if t.is_done())

    if show_all:
        print(f"\n未完: {pending_count}件 | 完了: {done_count}件")
    else:
        print(f"\n未完: {pending_count}件")


def render_task_list_with_status(tasks: List[Task]) -> None:
    """
    タスク一覧を状態カラム付きで表示（--all オプション用）

    Args:
        tasks: 表示するタスクのリスト
    """
    if not tasks:
        print("タスクがありません")
        return

    # ヘッダー表示
    print(f"{'ID':<4} | {'タイトル':<40} | {'期日':<8} | {'状態':<4}")
    print("-" * 70)

    # タスク表示
    for task in tasks:
        title = truncate_text(task.title, max_length=40)
        due = format_date(task.due)
        status = "完了" if task.is_done() else "未完"

        print(f"{task.id:<4} | {title:<40} | {due:<8} | {status:<4}")

    # 統計情報表示
    pending_count = sum(1 for t in tasks if t.is_pending())
    done_count = sum(1 for t in tasks if t.is_done())
    print(f"\n未完: {pending_count}件 | 完了: {done_count}件")


def render_task_detail(task: Task) -> None:
    """
    タスクの詳細を表示

    Args:
        task: 表示するタスク
    """
    print(f"ID: {task.id}")
    print(f"タイトル: {task.title}")
    print(f"期日: {format_date(task.due)}")
    print(f"状態: {'完了' if task.is_done() else '未完'}")
    print(f"作成日時: {task.created_at}")
    if task.url:
        print(f"URL: {task.url}")
