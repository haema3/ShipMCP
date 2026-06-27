# ShipMCP

조선소/선박 전문 용어를 LLM이 정확히 이해하도록 돕는 MCP 서버입니다.

- Korean + English shipbuilding terminology
- 실제 업무에서 자주 쓰는 조선, 선급, IMO, 설계/생산 용어 포함
- MCP 표준 Primitive인 Resources, Tools, Prompts 제공

## What This Server Provides

### 1) Resources
클라이언트가 컨텍스트로 로드할 수 있는 정적/조회형 데이터입니다.

- shipmcp://categories
- shipmcp://category/{category_id}
- shipmcp://term/{term_id}
- shipmcp://search/{query}
- shipmcp://glossary

### 2) Tools
모델이 호출할 수 있는 실행형 함수입니다.

- search_ship_terms(query, max_results=10)
- get_term_detail(term_id_or_name)
- list_terms_by_category(category_id)
- list_categories_tool()
- translate_term(term, from_lang="en", to_lang="ko")
- get_term_statistics()

### 3) Prompts
재사용 가능한 프롬프트 템플릿입니다.

- learn_term(term_name)
- korean_english_glossary(category="all")
- explain_document(text)
- compare_terms(term1, term2)

## Data Coverage

현재 데이터 기준:

- Categories: 14
- Terms: 364

카테고리 목록:

- ship-types
- hull-structure
- propulsion
- navigation
- cargo
- safety
- shipbuilding-process
- ship-dimensions
- design
- marine-engineering
- mooring-anchoring
- electrical
- classification
- welding-fabrication

## Requirements

- Python 3.10+
- uv

## Installation

```bash
git clone <your-repo-url>
cd ShipMCP
uv sync
```

## Run

기본(권장) STDIO 모드:

```bash
uv run ship-mcp
```

또는 모듈 직접 실행:

```bash
uv run python -m ship_mcp.server
```

HTTP 모드 예시:

```bash
# Streamable HTTP
uv run ship-mcp --transport streamable-http --host 0.0.0.0 --port 8000

# SSE
uv run ship-mcp --transport sse --port 8000
```

## MCP Client Setup

### Claude Desktop

claude_desktop_config.json 예시:

```json
{
  "mcpServers": {
    "shipmcp": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\path\\to\\ShipMCP", "ship-mcp"],
      "env": {}
    }
  }
}
```

### Claude Code

```bash
claude mcp add shipmcp -- uv run --directory C:\\path\\to\\ShipMCP ship-mcp
```

## Usage Examples

권장 호출 순서:

1. search_ship_terms 로 후보 검색
2. get_term_detail 로 상세 정보 조회
3. 필요 시 translate_term 으로 번역

예시 질의:

- "용골이 뭐야?"
- "DWT 뜻 알려줘"
- "Bulk Carrier와 Tanker 차이 비교"
- "이 문단의 조선 용어를 풀어서 설명해줘"

## Project Structure

```text
ShipMCP/
├─ pyproject.toml
├─ README.md
└─ ship_mcp/
   ├─ __init__.py
   ├─ server.py
   └─ data/
      ├─ __init__.py
      ├─ categories.py
      ├─ terms.py
      ├─ terms_imo.py
      └─ terms_shipyard.py
```

## Development Notes

- 엔트리포인트: pyproject.toml 의 ship-mcp = ship_mcp.server:main
- 기본 전송 프로토콜: stdio
- 지원 전송 프로토콜: stdio, sse, streamable-http

## License

MIT