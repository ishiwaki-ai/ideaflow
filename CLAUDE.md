# IdeaFlow — AI化アイデア出し＆フロー設計ツール

## 概要
AI化のアイデア出しから自動化フロー設計まで一気通貫でできるローカルWebアプリ。

参照元として作ったサービス:
- アイデア出し: https://gais-oneclick-259747770348.asia-northeast1.run.app/?v=agent-app
- フロー設計: https://flowforge-259747770348.asia-northeast1.run.app/

## 起動方法
```bash
cd /Users/tomohiro/my-project/ideaflow
./start.sh
```
→ ブラウザが自動で http://localhost:8100 を開く

## ファイル構成
```
ai-automation/
├── app.py            # FastAPI バックエンド（Claude API 呼び出し）
├── static/
│   └── index.html    # フロントエンド（タブ切り替え UI）
├── start.sh          # 起動スクリプト（.env 読み込み＋ブラウザ自動起動）
├── .env              # APIキー（gitignore 対象）
├── .env.example      # .env のテンプレート
└── pyproject.toml    # 依存パッケージ（uv で管理）
```

## 機能

### タブ1: アイデア生成
- 入力: 業種・部署・課題・AIレベル感
- 出力: AI活用アイデア 6〜8件（カード形式）
- 「→ フロー設計へ」ボタンでそのまま次タブに引き渡し可能

### タブ2: フロー設計
- 入力: 自動化したい業務を一言
- 出力: ステップ別フロー（種類ごとに色分け）
- チャットでフローをその場で修正
- 「Claude Codeへの実装指示を生成」でPythonコード例付き指示書を出力・コピー

## API エンドポイント
| メソッド | パス | 説明 |
|---|---|---|
| POST | /api/generate-ideas | アイデア生成（SSE ストリーミング）|
| POST | /api/generate-flow | フロー生成（SSE ストリーミング）|
| POST | /api/chat-flow | チャット修正（SSE ストリーミング）|
| POST | /api/export-instructions | 実装指示書生成（SSE ストリーミング）|

## 技術スタック
- Backend: FastAPI + uvicorn
- Frontend: Vanilla HTML / CSS / JS（フレームワークなし）
- AI: claude-sonnet-4-6（Anthropic API、SSEストリーミング）
- 依存管理: uv

## よくある修正パターン
- **プロンプトを変えたい** → `app.py` の `IDEA_USER` / `FLOW_USER` 等の定数を編集
- **UIを変えたい** → `static/index.html` を編集（サーバーは --reload 中なので即反映）
- **モデルを変えたい** → `app.py` の `sse_stream()` 内の `model=` を変更
- **ポートを変えたい** → `.env` の `PORT=` を変更

## プロジェクト一覧の管理（重要）

新しいプロジェクトが完成・着手されたときは、**必ず以下の2ファイルを更新すること**。

### 1. `projects.json`（IdeaFlow のプロジェクト一覧タブに表示される）
```json
{
  "name": "プロジェクト名",
  "description": "概要説明",
  "location": "~/パス/",
  "status": "稼働中",
  "start": "起動コマンド",
  "url": null,
  "tech": ["使用技術"],
  "note": "補足（任意）"
}
```
`status` は `稼働中` / `開発中` / `進行中` / `スクリプト` / `スキル` から選ぶ。

### 2. `~/systems.md`（全プロジェクトのマスター一覧）
同じ内容を1行で追記する。
