# Todo CLI

Slack連携Todo管理CLI - ターミナル上で動作する軽量タスク管理ツール

## 現在のステータス: Phase 2 完成 ✅

**Slackリアクション（👀）と双方向同期**に対応しました！
- Slackで 👀 `:eyes:` リアクションを付けた投稿 → 自動的にTodoとして追加
- CLIでタスク完了/削除 → Slackのリアクションも自動削除
- `todo list` 実行時に自動同期
- キャッシュ機構搭載（1分以内の連続実行はAPI呼び出しなし）

✅ **公式API使用**: `reactions.list` / `reactions.remove` を使用しています。

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
- ✅ Slackリアクション連携（公式API: reactions.list / reactions.remove）
- ✅ 自動同期機能（Pull/Push）
- ✅ 環境変数によるトークン管理
- ✅ キャッシュ機構（1分間のRate limit対策）
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

2. 依存関係をインストール（推奨）
```bash
pip3 install -e .
```

これで `todo` コマンドが使えるようになります。

または、直接実行する場合:
```bash
pip3 install -r requirements.txt
# この場合は python3 -m todo_cli.main で実行
```

---

## Slack連携セットアップ

### 1. Slack OAuth Tokenを取得

1. https://api.slack.com/apps にアクセス
2. "Create New App" → "From scratch"
3. App Name と Workspace を選択
4. **OAuth & Permissions** → **User Token Scopes** に以下を追加:
   - `reactions:read` （リアクション情報の取得）
   - `reactions:write` （リアクションの削除）
   - `channels:history` （パブリックチャンネルの履歴）
   - `groups:history` （プライベートチャンネルの履歴）
   - `im:history` （DMの履歴）
   - `mpim:history` （グループDMの履歴）
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
# デフォルト絵文字（👀 :eyes:）を使用
todo setup

# または、別の絵文字を指定
todo setup --emoji memo  # 📝 :memo: を使用
```

Slack APIへの接続をテストし、設定を完了します。

### 4. 使い方

1. **Slackで 👀 `:eyes:` リアクションを付ける**
   - Todo化したいメッセージに 👀 リアクションを付ける

2. **CLIで確認**
   ```bash
   todo list  # 自動的に同期される
   ```

3. **完了したらタスクをdone**
   ```bash
   todo done 1  # Slackのリアクションも自動削除される
   ```

---

## 使い方

### 基本コマンド

#### タスク追加
```bash
todo add "タスク名"
todo add "タスク名" --due 11/15
```

#### タスク一覧表示
```bash
# 未完了タスクのみ表示
todo list

# 完了タスクも含めて表示
todo list --all
```

#### タスク完了
```bash
todo done <id>
```

#### タスク削除
```bash
# 確認プロンプト付き
todo delete <id>

# 確認なし
todo delete <id> --force
```

#### サマリー表示
```bash
todo summary
```

#### バージョン確認
```bash
todo version
```

---

## 使用例

```bash
# タスクを追加
$ todo add "バグ修正: ログイン画面" --due 11/15
✓ タスクを追加しました (ID: 1)

$ todo add "ドキュメント更新" --due 11/20
✓ タスクを追加しました (ID: 2)

# タスク一覧を表示
$ todo list
ID   | タイトル                    | 期日
-----------------------------------------------------
1    | バグ修正: ログイン画面          | 11/15
2    | ドキュメント更新               | 11/20

未完: 2件

# タスクを完了
$ todo done 1
✓ タスク #1 を完了しました

# サマリー表示
$ todo summary
Todo: 1件
```

---

## データ保存場所

タスクデータは以下の場所に保存されます：
```
~/.todo-cli/tasks.json
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
   - Value: `$(todo summary)`

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
- Slackリアクション連携（公式API使用）
- 自動同期（Pull/Push）
- 環境変数によるトークン管理
- キャッシュ機構（Rate limit対策）
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
- **Slackリアクション連携**（公式API: reactions.list / reactions.remove）
- 👀 `:eyes:` 絵文字でTodo化（カスタマイズ可能）
- 自動同期機能（Pull/Push）
- **キャッシュ機構**（1分間のRate limit対策）
- setupコマンド追加（--emojiオプション対応）
- 環境変数によるトークン管理（SLACK_TOKEN）
- エラーハンドリング & リトライ処理
- --no-syncオプション追加（list コマンド）

### v0.1.0 (2025-11-10)
- Phase 1 MVP リリース
- ローカルタスク管理機能実装
- 基本的なCLIコマンド実装
