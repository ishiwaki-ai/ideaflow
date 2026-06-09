from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import anthropic
import json
from pathlib import Path

limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
client = anthropic.Anthropic()

# ── Prompts ────────────────────────────────────────────────────────────────

IDEA_SYSTEM = (
    "あなたはAI化・業務自動化の専門コンサルタントです。"
    "JSONのみを出力してください。説明文やマークダウンコードブロック（```）は含めないこと。"
)

IDEA_USER = """以下の情報をもとに、具体的なAI活用・自動化アイデアを6〜8個生成してください。

業種: {industry}
部署・役割: {department}
課題・やりたいこと: {challenges}
AIレベル感: {level}

以下のJSON配列を出力してください:
[
  {{
    "id": 1,
    "title": "アイデアタイトル（15文字以内）",
    "description": "具体的な説明（2〜3文）",
    "benefits": "期待される効果・メリット",
    "tools": ["ツール1", "ツール2"],
    "difficulty": "easy",
    "impact": "high",
    "flow_hint": "自動化したい業務を一言で（フロー設計に渡す20〜30文字のテキスト）"
  }}
]

difficulty: easy | medium | hard
impact: low | medium | high"""

FLOW_SYSTEM = (
    "あなたは業務自動化フロー設計の専門家です。"
    "JSONのみを出力してください。説明文やマークダウンコードブロック（```）は含めないこと。"
)

FLOW_USER = """以下の業務を自動化するための詳細なフロー（4〜8ステップ）を設計してください。

業務: {description}

以下のJSONを出力してください:
{{
  "title": "フロータイトル",
  "summary": "フローの概要（1〜2文）",
  "steps": [
    {{
      "id": 1,
      "title": "ステップタイトル（10文字以内）",
      "description": "このステップで何をするか（1〜2文）",
      "type": "trigger",
      "tools": ["使用するツール"],
      "output": "このステップの出力物"
    }}
  ]
}}

type:
- trigger: 起動条件（スケジュール・webhook・メール受信など）
- ai: AI処理（Claude・要約・分類・生成など）
- action: 外部サービス操作（メール送信・DB保存・Slack通知など）
- condition: 条件分岐・承認フロー
- output: 最終出力（レポート・通知・記録）"""

CHAT_SYSTEM = (
    "あなたは業務自動化フロー設計の専門家です。"
    "更新後のJSONのみを出力してください。説明文は含めないこと。"
)

CHAT_USER = """現在のフローをユーザーの指示に従って更新してください。

現在のフロー:
{current_flow}

ユーザーの指示: {message}

同じJSON形式でフローを出力してください。"""

EXPORT_SYSTEM = "あなたはPythonエンジニアです。業務自動化フローの実装指示書をMarkdown形式で作成してください。"

EXPORT_USER = """以下の業務自動化フローをClaude Codeで実装するための指示書を作成してください。

{flow}

## 形式
# フロー実装指示書: {{タイトル}}

## 概要と目的
## 前提条件・必要な環境
（uvを使ったパッケージインストールコマンドを含めること）
## 各ステップの実装
（各ステップのPythonコード例を含めること）
## エラーハンドリング
## 実行方法"""

# ── Pydantic models ────────────────────────────────────────────────────────

class IdeaRequest(BaseModel):
    industry: str
    department: str
    challenges: str
    level: str = "intermediate"

class FlowRequest(BaseModel):
    description: str

class ChatRequest(BaseModel):
    current_flow: dict
    message: str

class ExportRequest(BaseModel):
    flow: dict

# ── Streaming helper ───────────────────────────────────────────────────────

LEVEL_MAP = {
    "nocode": "ノーコード・ローコード（プログラミング不要）",
    "intermediate": "中級（APIを使った自動化）",
    "advanced": "高度（カスタム開発・複雑なパイプライン）",
}

def sse_stream(system: str, user: str, max_tokens: int = 4096) -> StreamingResponse:
    async def generate():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'chunk': text}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# ── API routes ─────────────────────────────────────────────────────────────

PROJECTS_FILE = Path(__file__).parent / "projects.json"

@app.get("/api/projects")
async def get_projects():
    return JSONResponse(content=[])


@app.post("/api/generate-ideas")
@limiter.limit("20/hour")
async def generate_ideas(request: Request, req: IdeaRequest):
    user = IDEA_USER.format(
        industry=req.industry,
        department=req.department,
        challenges=req.challenges,
        level=LEVEL_MAP.get(req.level, req.level),
    )
    return sse_stream(IDEA_SYSTEM, user)


@app.post("/api/generate-flow")
@limiter.limit("20/hour")
async def generate_flow(request: Request, req: FlowRequest):
    return sse_stream(FLOW_SYSTEM, FLOW_USER.format(description=req.description))


@app.post("/api/chat-flow")
@limiter.limit("30/hour")
async def chat_flow(request: Request, req: ChatRequest):
    user = CHAT_USER.format(
        current_flow=json.dumps(req.current_flow, ensure_ascii=False, indent=2),
        message=req.message,
    )
    return sse_stream(CHAT_SYSTEM, user)


@app.post("/api/export-instructions")
@limiter.limit("10/hour")
async def export_instructions(request: Request, req: ExportRequest):
    user = EXPORT_USER.format(
        flow=json.dumps(req.flow, ensure_ascii=False, indent=2)
    )
    return sse_stream(EXPORT_SYSTEM, user, max_tokens=8192)


# ── Static files (must be last) ────────────────────────────────────────────

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
