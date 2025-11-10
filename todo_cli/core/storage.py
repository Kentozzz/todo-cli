"""
ストレージ管理
Phase 1: MVP - ローカルタスク管理用のJSON読み書き、ID採番、ソート
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Literal
from todo_cli.core.models import Task, Config

# データディレクトリのパス
DATA_DIR = Path.home() / ".todo-cli"
TASKS_FILE = DATA_DIR / "tasks.json"
CONFIG_FILE = DATA_DIR / "config.json"


class TaskStorage:
    """タスクストレージ管理クラス"""

    def __init__(self, tasks_file: Path = TASKS_FILE):
        """
        初期化

        Args:
            tasks_file: タスクファイルのパス（テスト用にオーバーライド可能）
        """
        self.tasks_file = tasks_file
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """データディレクトリが存在しない場合は作成"""
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.tasks_file.exists():
            self._save_tasks([])

    def _save_tasks(self, tasks: List[Task]) -> None:
        """
        タスクをJSONファイルに保存

        Args:
            tasks: 保存するタスクのリスト
        """
        task_dicts = [task.to_dict() for task in tasks]
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(task_dicts, f, ensure_ascii=False, indent=2)

    def load_all(self) -> List[Task]:
        """
        すべてのタスクを読み込む

        Returns:
            List[Task]: タスクのリスト
        """
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                task_dicts = json.load(f)
                return [Task.from_dict(d) for d in task_dicts]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def load_pending(self) -> List[Task]:
        """
        未完了タスクのみ読み込む

        Returns:
            List[Task]: 未完了タスクのリスト
        """
        all_tasks = self.load_all()
        return [task for task in all_tasks if task.is_pending()]

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        指定したIDのタスクを取得

        Args:
            task_id: タスクID

        Returns:
            Optional[Task]: タスク、存在しない場合はNone
        """
        tasks = self.load_all()
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    def add_task(self, title: str, due: Optional[str] = None, url: str = "") -> Task:
        """
        新規タスクを追加

        Args:
            title: タスク名
            due: 期日（オプション）
            url: SlackのURL（Phase 1では不要）

        Returns:
            Task: 追加されたタスク
        """
        tasks = self.load_all()
        new_id = self._get_next_id(tasks)
        new_task = Task.create(id=new_id, title=title, due=due, url=url)
        tasks.append(new_task)
        sorted_tasks = self._sort_tasks(tasks)
        self._save_tasks(sorted_tasks)
        return new_task

    def update_task(self, task: Task) -> None:
        """
        タスクを更新

        Args:
            task: 更新するタスク
        """
        tasks = self.load_all()
        for i, t in enumerate(tasks):
            if t.id == task.id:
                tasks[i] = task
                break
        sorted_tasks = self._sort_tasks(tasks)
        self._save_tasks(sorted_tasks)

    def delete_task(self, task_id: int) -> bool:
        """
        タスクを削除（完全削除）し、ID再採番

        Args:
            task_id: 削除するタスクのID

        Returns:
            bool: 削除成功時True
        """
        tasks = self.load_all()
        original_count = len(tasks)
        tasks = [task for task in tasks if task.id != task_id]

        if len(tasks) == original_count:
            return False  # タスクが見つからなかった

        # ID再採番（欠番なし）
        renumbered_tasks = self._renumber_tasks(tasks)
        sorted_tasks = self._sort_tasks(renumbered_tasks)
        self._save_tasks(sorted_tasks)
        return True

    def mark_done(self, task_id: int) -> bool:
        """
        タスクを完了状態にする

        Args:
            task_id: 完了するタスクのID

        Returns:
            bool: 完了成功時True
        """
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        task.mark_done()
        self.update_task(task)
        return True

    def _get_next_id(self, tasks: List[Task]) -> int:
        """
        次のタスクIDを取得

        Args:
            tasks: 既存タスクのリスト

        Returns:
            int: 次のID（1から始まる連番）
        """
        if not tasks:
            return 1
        return max(task.id for task in tasks) + 1

    def _renumber_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        タスクIDを再採番（欠番なし）

        Args:
            tasks: タスクのリスト

        Returns:
            List[Task]: 再採番されたタスクのリスト
        """
        for i, task in enumerate(tasks, start=1):
            task.id = i
        return tasks

    def _sort_tasks(
        self,
        tasks: List[Task],
        sort_by: Literal["due", "created", "id"] = "due"
    ) -> List[Task]:
        """
        タスクをソート

        Args:
            tasks: タスクのリスト
            sort_by: ソート基準（"due" | "created" | "id"）

        Returns:
            List[Task]: ソートされたタスクのリスト
        """
        if sort_by == "due":
            # 期日順（期日なしは最後）
            return sorted(
                tasks,
                key=lambda t: (t.due is None, t.due or "", t.created_at)
            )
        elif sort_by == "created":
            return sorted(tasks, key=lambda t: t.created_at)
        else:  # "id"
            return sorted(tasks, key=lambda t: t.id)


class ConfigStorage:
    """設定ストレージ管理クラス（Phase 2で使用）"""

    def __init__(self, config_file: Path = CONFIG_FILE):
        """
        初期化

        Args:
            config_file: 設定ファイルのパス
        """
        self.config_file = config_file
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """データディレクトリが存在しない場合は作成"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Config:
        """
        設定を読み込む

        Returns:
            Config: 設定オブジェクト
        """
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
                return Config.from_dict(config_dict)
        except (FileNotFoundError, json.JSONDecodeError):
            return Config()

    def save(self, config: Config) -> None:
        """
        設定を保存

        Args:
            config: 保存する設定オブジェクト
        """
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)

        # セキュリティ: ファイルパーミッションを600に設定
        os.chmod(self.config_file, 0o600)
