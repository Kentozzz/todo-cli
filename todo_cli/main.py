"""
Todo CLI メインエントリーポイント
Phase 2: Slack連携Todo管理CLI
"""
import typer
import os
from typing import Optional
from todo_cli.core.storage import TaskStorage, ConfigStorage
from todo_cli.core.utils import parse_date, validate_task_id
from todo_cli.views.list_view import render_task_list, render_task_list_with_status
from todo_cli.views.summary_view import render_summary
from todo_cli.services.sync_service import SyncService
from todo_cli.services.slack_service import SlackAPIError

app = typer.Typer(
    name="todo",
    help="Slack連携Todo管理CLI (Phase 2: リアクション連携対応)",
    add_completion=False
)

# ストレージインスタンス
storage = TaskStorage()
config_storage = ConfigStorage()
sync_service = SyncService(storage)


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
    all: bool = typer.Option(False, "--all", "-a", help="完了タスクも含めて表示"),
    no_sync: bool = typer.Option(False, "--no-sync", help="Slack同期をスキップ")
):
    """
    タスク一覧を表示（Slack連携時は自動同期）
    """
    try:
        # Slack同期（設定済みの場合のみ）
        if not no_sync and sync_service.is_slack_configured():
            try:
                added, deleted, errors = sync_service.pull_from_slack()
                if added > 0 or deleted > 0:
                    typer.echo(f"Slack同期: +{added}件 -{deleted}件")
            except (ValueError, SlackAPIError) as e:
                typer.echo(f"警告: Slack同期失敗（ローカルデータを表示）: {e}", err=True)

        # タスク一覧表示
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
    タスクを完了状態にする（Slack連携時はブックマークも削除）
    """
    # IDの検証
    id_int = validate_task_id(task_id)
    if not id_int:
        typer.echo(f"エラー: 無効なタスクIDです: {task_id}", err=True)
        raise typer.Exit(code=1)

    # タスク情報を取得
    task = storage.get_task_by_id(id_int)
    if not task:
        typer.echo(f"エラー: タスク #{id_int} が見つかりません", err=True)
        raise typer.Exit(code=1)

    # Slackリアクション削除（設定済みの場合のみ）
    if sync_service.is_slack_configured() and task.url:
        try:
            if sync_service.push_to_slack(task.url):
                typer.echo("Slackリアクションを削除しました")
        except (ValueError, SlackAPIError) as e:
            typer.echo(f"警告: Slackリアクション削除失敗: {e}", err=True)

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
    タスクを完全削除（Slack連携時はブックマークも削除）
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

    # Slackリアクション削除（設定済みの場合のみ）
    if sync_service.is_slack_configured() and task.url:
        try:
            if sync_service.push_to_slack(task.url):
                typer.echo("Slackリアクションを削除しました")
        except (ValueError, SlackAPIError) as e:
            typer.echo(f"警告: Slackリアクション削除失敗: {e}", err=True)

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
def setup(
    emoji: Optional[str] = typer.Option(None, "--emoji", "-e", help="使用する絵文字名（デフォルト: eyes）")
):
    """
    Slack連携の初期設定
    """
    typer.echo("=== Slack リアクション連携 初期設定 ===\n")

    # SLACK_TOKEN環境変数のチェック
    if not os.getenv("SLACK_TOKEN"):
        typer.echo("エラー: SLACK_TOKEN環境変数が設定されていません", err=True)
        typer.echo("\n以下のコマンドでトークンを設定してください:")
        typer.echo("  export SLACK_TOKEN=xoxp-your-token-here")
        typer.echo("\nSlack OAuth Tokenの取得方法:")
        typer.echo("  1. https://api.slack.com/apps にアクセス")
        typer.echo("  2. アプリを作成（または既存のアプリを選択）")
        typer.echo("  3. OAuth & Permissions → User Token Scopes に以下を追加:")
        typer.echo("     - reactions:read")
        typer.echo("     - reactions:write")
        typer.echo("     - channels:history")
        typer.echo("     - groups:history")
        typer.echo("     - im:history")
        typer.echo("     - mpim:history")
        typer.echo("  4. Install App to Workspace → User OAuth Token をコピー")
        raise typer.Exit(code=1)

    # 絵文字設定
    if emoji:
        config = config_storage.load()
        config.reaction_emoji = emoji
        config_storage.save(config)
        typer.echo(f"✓ 使用絵文字を :{emoji}: に設定しました\n")

    # 接続テスト
    typer.echo("Slack接続テスト中...")
    success, message = sync_service.test_slack_connection()
    if not success:
        typer.echo(f"エラー: {message}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"✓ {message}\n")
    typer.echo("✓ Slack リアクション連携の設定が完了しました")
    typer.echo("\n使い方:")
    current_emoji = emoji or config_storage.load().reaction_emoji
    typer.echo(f"  1. Slackで :{current_emoji}: リアクションを付ける")
    typer.echo("  2. 'todo list' でTodoとして表示される")
    typer.echo("  3. 'todo done <id>' で完了 → Slackのリアクションも自動削除")


@app.command()
def version():
    """
    バージョン情報を表示
    """
    typer.echo("todo-cli version 0.2.0 (Phase 2: Slack連携)")
    typer.echo("Slackリアクション（👀）との双方向同期対応")


if __name__ == "__main__":
    app()
