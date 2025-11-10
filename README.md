# Todo CLI

Slack連携Todo管理CLI - ターミナル上で動作する軽量タスク管理ツール

## 現在のステータス: Phase 2 完成 ✅

**Slackブックマークと双方向同期**に対応しました！
- Slackでブックマークした投稿 → 自動的にTodoとして追加
- CLIでタスク完了/削除 → Slackのブックマークも削除
- `todo list` 実行時に自動同期

---

## 機能

### Phase 1 MVP ✅
- ✅ タスク追加
- ✅ タスク一覧表示
- ✅ タスク完了
- ✅ タスク削除
- ✅ サマリー表示（ステータスバー用）
- ✅ 期日管理
- ✅ ID自動採番（欠番なし）

### Phase 2 Slack連携 ✅
- ✅ Slackブックマーク連携
- ✅ 自動同期機能（Pull/Push）
- ✅ 環境変数によるトークン管理
- ✅ エラーハンドリング & リトライ処理
- ✅ オフライン時のフォールバック

---

## インストール

### 必要要件
- Python 3.9以上

### インストール手順

1. リポジトリをクローン
```bash
cd ~/Projects
git clone <repository-url> todo-cli
cd todo-cli
```

2. 依存関係をインストール
```bash
pip3 install -e .
```

または、直接実行する場合:
```bash
pip3 install -r requirements.txt
```

---

## Slack連携セットアップ

### 1. Slack OAuth Tokenを取得

1. https://api.slack.com/apps にアクセス
2. "Create New App" → "From scratch"
3. App Name と Workspace を選択
4. **OAuth & Permissions** → **User Token Scopes** に以下を追加:
   - `bookmarks:read`
   - `bookmarks:write`
5. **Install App to Workspace** をクリック
6. **User OAuth Token** (xoxp-から始まる)をコピー

### 2. 環境変数を設定

```bash
# ~/.zshrc または ~/.bashrc に追加
export SLACK_TOKEN="xoxp-your-token-here"

# 設定を反映
source ~/.zshrc  # または source ~/.bashrc
```

### 3. CLIセットアップを実行

```bash
todo setup
```

対話形式でSlackチャンネルIDを入力します：
- チャンネルIDの確認方法: Slackでチャンネルを右クリック → "リンクをコピー"
- URLの末尾が `C01ABC123` のような形式

セットアップ完了後、`todo list` で自動的にSlackブックマークと同期されます。

---

## 使い方

### 基本コマンド

#### タスク追加
```bash
python3 -m todo_cli.main add "タスク名"
python3 -m todo_cli.main add "タスク名" --due 11/15
```

#### タスク一覧表示
```bash
# 未完了タスクのみ表示
python3 -m todo_cli.main list

# 完了タスクも含めて表示
python3 -m todo_cli.main list --all
```

#### タスク完了
```bash
python3 -m todo_cli.main done <id>
```

#### タスク削除
```bash
# 確認プロンプト付き
python3 -m todo_cli.main delete <id>

# 確認なし
python3 -m todo_cli.main delete <id> --force
```

#### サマリー表示
```bash
python3 -m todo_cli.main summary
```

#### バージョン確認
```bash
python3 -m todo_cli.main version
```

---

## 使用例

```bash
# タスクを追加
$ python3 -m todo_cli.main add "バグ修正: ログイン画面" --due 11/15
✓ タスクを追加しました (ID: 1)

$ python3 -m todo_cli.main add "ドキュメント更新" --due 11/20
✓ タスクを追加しました (ID: 2)

# タスク一覧を表示
$ python3 -m todo_cli.main list
ID   | タイトル                    | 期日
-----------------------------------------------------
1    | バグ修正: ログイン画面          | 11/15
2    | ドキュメント更新               | 11/20

未完: 2件

# タスクを完了
$ python3 -m todo_cli.main done 1
✓ タスク #1 を完了しました

# サマリー表示
$ python3 -m todo_cli.main summary
Todo: 1件
```

---

## データ保存場所

タスクデータは以下の場所に保存されます：
```
~/.todo-cli/tasks.json
```

---

## エイリアス設定（推奨）

毎回 `python3 -m todo_cli.main` と入力するのは大変なので、エイリアスの設定を推奨します：

### Bash/Zsh
```bash
# ~/.bashrc または ~/.zshrc に追加
alias todo="python3 -m todo_cli.main"
```

設定後:
```bash
todo add "新しいタスク"
todo list
todo done 1
```

---

## iTerm2/tmux ステータスバー連携

`summary` コマンドはステータスバー表示用に最適化されています：

### iTerm2の場合
1. Preferences → Profiles → Session
2. Status bar enabled をチェック
3. Configure Status Bar をクリック
4. "Interpolated String" を追加
5. 値に `\(user.todo_count)` を設定
6. Advanced → Triggers で以下を追加:
   - Regular Expression: `.*`
   - Action: Set User Variable
   - Variable: `todo_count`
   - Value: `$(python3 -m todo_cli.main summary)`

---

## プロジェクト構造

```
todo-cli/
├── todo_cli/
│   ├── main.py              # CLIエントリーポイント
│   ├── core/
│   │   ├── models.py        # データモデル（Task, Config）
│   │   ├── storage.py       # JSON読み書き・ID採番
│   │   └── utils.py         # ユーティリティ関数
│   ├── services/            # Phase 2
│   │   ├── slack_service.py # Slack API クライアント
│   │   └── sync_service.py  # 同期ロジック
│   └── views/
│       ├── list_view.py     # 一覧表示
│       └── summary_view.py  # サマリー表示
├── tests/                   # テストコード（Phase 3で追加）
├── requirements.txt         # 依存関係
├── pyproject.toml          # プロジェクト設定
├── todo                     # ラッパースクリプト
└── README.md               # このファイル
```

---

## 開発ロードマップ

### Phase 1: MVP ✅ (完了)
- ローカルタスク管理
- 基本的なCRUD操作
- 期日管理
- サマリー表示

### Phase 2: Slack連携 ✅ (完了)
- Slackブックマーク連携
- 自動同期（Pull/Push）
- 環境変数によるトークン管理
- エラーハンドリング & リトライ処理
- オフライン時のフォールバック

### Phase 3: テスト & 最適化 (予定)
- 単体テスト
- 統合テスト（モック使用）
- ドキュメント整備
- パフォーマンス最適化
- CI/CD構築

---

## トラブルシューティング

### データファイルが見つからない
初回実行時に自動的に `~/.todo-cli/` ディレクトリが作成されます。

### 日付形式エラー
サポートされる期日形式:
- `11/10` (月/日)
- `11-10` (月-日)
- `2025-11-10` (ISO 8601形式)

### ID再採番について
タスクを削除すると、IDは自動的に再採番されます（欠番なし）。

---

## ライセンス

MIT License

---

## 貢献

Phase 1はMVPのため、機能追加の提案は大歓迎です！
IssueまたはPull Requestをお待ちしています。

---

## 変更履歴

### v0.2.0 (2025-11-10)
- Phase 2: Slack連携機能実装
- Slack API連携（bookmarks.list/remove）
- 自動同期機能（Pull/Push）
- setupコマンド追加
- 環境変数によるトークン管理（SLACK_TOKEN）
- エラーハンドリング & リトライ処理
- --no-syncオプション追加（list コマンド）

### v0.1.0 (2025-11-10)
- Phase 1 MVP リリース
- ローカルタスク管理機能実装
- 基本的なCLIコマンド実装
