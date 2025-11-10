"""
Todo CLI メインエントリーポイント
Phase 1: MVP - ローカルタスク管理CLI
"""
import typer
from typing import Optional
from todo_cli.core.storage import TaskStorage
from todo_cli.core.utils import parse_date, validate_task_id
from todo_cli.views.list_view import render_task_list, render_task_list_with_status
from todo_cli.views.summary_view import render_summary

app = typer.Typer(
    name="todo",
    help="Slack連携Todo管理CLI (Phase 1: ローカル管理)",
    add_completion=False
)

# ストレージインスタンス
storage = TaskStorage()


@app.command()
def add(
    title: str = typer.Argument(..., help="タスクのタイトル"),
    due: Optional[str] = typer.Option(None, "--due", "-d", help="期日 (例: 11/10 または 2025-11-10)")
):
    """
    新規タスクを追加
    """
    # 期日のパース
    due_date = None
    if due:
        due_date = parse_date(due)
        if not due_date:
            typer.echo(f"エラー: 期日の形式が不正です: {due}", err=True)
            typer.echo("サポートされる形式: 11/10, 11-10, 2025-11-10", err=True)
            raise typer.Exit(code=1)

    # タスク追加
    try:
        task = storage.add_task(title=title, due=due_date)
        typer.echo(f"✓ タスクを追加しました (ID: {task.id})")
    except Exception as e:
        typer.echo(f"エラー: タスクの追加に失敗しました: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_tasks(
    all: bool = typer.Option(False, "--all", "-a", help="完了タスクも含めて表示")
):
    """
    タスク一覧を表示
    """
    try:
        if all:
            tasks = storage.load_all()
            render_task_list_with_status(tasks)
        else:
            tasks = storage.load_pending()
            render_task_list(tasks, show_all=False)
    except Exception as e:
        typer.echo(f"エラー: タスクの読み込みに失敗しました: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def done(
    task_id: str = typer.Argument(..., help="完了するタスクのID")
):
    """
    タスクを完了状態にする
    """
    # IDの検証
    id_int = validate_task_id(task_id)
    if not id_int:
        typer.echo(f"エラー: 無効なタスクIDです: {task_id}", err=True)
        raise typer.Exit(code=1)

    # タスクを完了
    try:
        success = storage.mark_done(id_int)
        if success:
            typer.echo(f"✓ タスク #{id_int} を完了しました")
        else:
            typer.echo(f"エラー: タスク #{id_int} が見つかりません", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"エラー: タスクの完了に失敗しました: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def delete(
    task_id: str = typer.Argument(..., help="削除するタスクのID"),
    force: bool = typer.Option(False, "--force", "-f", help="確認なしで削除")
):
    """
    タスクを完全削除
    """
    # IDの検証
    id_int = validate_task_id(task_id)
    if not id_int:
        typer.echo(f"エラー: 無効なタスクIDです: {task_id}", err=True)
        raise typer.Exit(code=1)

    # タスクの存在確認
    task = storage.get_task_by_id(id_int)
    if not task:
        typer.echo(f"エラー: タスク #{id_int} が見つかりません", err=True)
        raise typer.Exit(code=1)

    # 確認プロンプト
    if not force:
        typer.echo(f"タスク #{id_int}: {task.title}")
        confirm = typer.confirm("本当に削除しますか？")
        if not confirm:
            typer.echo("削除をキャンセルしました")
            raise typer.Exit(code=0)

    # タスクを削除
    try:
        success = storage.delete_task(id_int)
        if success:
            typer.echo(f"✓ タスク #{id_int} を完全削除しました")
        else:
            typer.echo(f"エラー: タスク #{id_int} の削除に失敗しました", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"エラー: タスクの削除に失敗しました: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def summary():
    """
    未完了タスク件数を表示（ステータスバー用）
    """
    try:
        tasks = storage.load_all()
        render_summary(tasks)
    except Exception as e:
        typer.echo("Todo: -", err=True)
        raise typer.Exit(code=1)


@app.command()
def version():
    """
    バージョン情報を表示
    """
    typer.echo("todo-cli version 0.1.0 (Phase 1: MVP)")
    typer.echo("ローカルタスク管理のみ対応")


if __name__ == "__main__":
    app()
