#!/bin/bash
set -e

cd "$(dirname "$0")"

# .env があれば読み込む
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# APIキー確認
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌  ANTHROPIC_API_KEY が設定されていません"
  echo "    .env.example をコピーして .env を作り、APIキーを記載してください"
  echo "    cp .env.example .env"
  exit 1
fi

PORT=${PORT:-8100}
echo "✅  IdeaFlow を起動します → http://localhost:$PORT"

# Mac の場合はブラウザを自動で開く
if [[ "$OSTYPE" == "darwin"* ]]; then
  (sleep 1.5 && open "http://localhost:$PORT") &
fi

uv run uvicorn app:app --port "$PORT" --reload
