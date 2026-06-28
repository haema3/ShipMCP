"""
ShipMCP — 조선소(선박) 용어 MCP 서버
Shipbuilding Terminology MCP Server

A comprehensive MCP server that provides shipbuilding/terminology data
to help LLMs understand specialized shipbuilding terms.

MCP Primitives provided:
  🔷 Resources  — 용어 및 카테고리 데이터 조회 (application-controlled)
  🔧 Tools      — 용어 검색, 번역, 설명 조회 (model-controlled)
  💬 Prompts    — 용어 학습, 문서 작성 도우미 (user-controlled)
"""

from __future__ import annotations

import json
import os
from typing import Any

import click
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ship_mcp.data.repository import (
    count_terms,
    get_category,
    get_repository,
    get_related_terms,
    get_term,
    get_term_by_name,
    get_terms_by_category,
    list_all_terms,
    list_categories,
    reset_repository,
    search_terms,
)

# ── MCP Server ──────────────────────────────────────────────────────────────

mcp = FastMCP("ShipMCP — 조선소 선박 용어 서버", json_response=True)
TOOL_SERVICE_NAME = "조선/선박 용어 MCP"


def _readonly_tool_annotations(title: str) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )


# ══════════════════════════════════════════════════════════════════════════════
# RESOURCES — Data that the client (LLM) can load into context
# ══════════════════════════════════════════════════════════════════════════════

@mcp.resource("shipmcp://categories")
def list_all_categories() -> str:
    """List all shipbuilding terminology categories."""
    cats = list_categories()
    lines = ["# 조선소 용어 카테고리 | Shipbuilding Categories\n"]
    for cat in cats:
        lines.append(
            f"## {cat['icon']} {cat['name_en']} ({cat['name_ko']})\n"
            f"**ID:** `{cat['id']}`  \n"
            f"**EN:** {cat['description_en']}  \n"
            f"**KO:** {cat['description_ko']}\n"
        )
    return "\n".join(lines)


@mcp.resource("shipmcp://category/{category_id}")
def get_category_resource(category_id: str) -> str:
    """Get all terms in a specific shipbuilding category.

    Args:
        category_id: The category ID (e.g. 'ship-types', 'hull-structure', 'propulsion')
    """
    cat = get_category(category_id)
    if not cat:
        categories = list_categories()
        return f"# Category not found\n\nNo category with ID '{category_id}'.\n\nAvailable IDs: {', '.join(c['id'] for c in categories)}"

    terms = get_terms_by_category(category_id)

    lines = [
        f"# {cat['icon']} {cat['name_en']} ({cat['name_ko']})",
        f"**{cat['description_en']}**",
        f"**{cat['description_ko']}**",
        "",
        f"## Terms ({len(terms)} entries)",
        "",
    ]

    for term in terms:
        abbr = f" ({term['abbreviation']})" if term["abbreviation"] else ""
        lines.append(
            f"### {term['term_en']}{abbr}",
        )
        lines.append(f"**한국어:** {term['term_ko']}")
        lines.append(f"**EN:** {term['description_en']}")
        lines.append(f"**KO:** {term['description_ko']}")
        if term["synonyms"]:
            lines.append(f"**Synonyms:** {', '.join(term['synonyms'])}")
        if term["related_terms"]:
            related_names = []
            for rid in term["related_terms"]:
                rt = get_term(rid)
                if rt:
                    related_names.append(f"[{rt['term_en']}](shipmcp://term/{rid})")
            if related_names:
                lines.append(f"**Related:** {', '.join(related_names)}")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("shipmcp://term/{term_id}")
def get_term_resource(term_id: str) -> str:
    """Get detailed information about a specific shipbuilding term.

    Args:
        term_id: The unique term ID (e.g. 'bulk-carrier', 'keel', 'propeller')
    """
    term = get_term(term_id)
    if not term:
        # Try searching by name
        term = get_term_by_name(term_id)
    if not term:
        return f"# Term not found\n\nNo term with ID or name '{term_id}' found.\nUse 'shipmcp://search/{term_id}' to find related terms."

    abbr = f" ({term['abbreviation']})" if term["abbreviation"] else ""
    cat = get_category(term["category"])
    cat_info = f"{cat['icon']} {cat['name_en']}" if cat else term["category"]

    lines = [
        f"# {term['term_en']}{abbr}",
        f"**한국어:** {term['term_ko']}",
        f"**Category:** {cat_info}",
        f"**ID:** `{term['id']}`",
        "",
        "## Description",
        f"**EN:** {term['description_en']}",
        f"**KO:** {term['description_ko']}",
        "",
    ]

    if term["synonyms"]:
        lines.append(f"**Synonyms:** {', '.join(term['synonyms'])}")
        lines.append("")

    related = get_related_terms(term)
    if related:
        lines.append("## Related Terms")
        for rt in related:
            r_abbr = f" ({rt['abbreviation']})" if rt["abbreviation"] else ""
            lines.append(f"- **{rt['term_en']}{r_abbr}** — {rt['term_ko']}")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("shipmcp://search/{query}")
def search_term_resource(query: str) -> str:
    """Search for terms by keyword across English names, Korean names, and descriptions.

    Args:
        query: The keyword to search for
    """
    results = search_terms(query, max_results=20)

    if not results:
        return f"# No results\n\nNo matching terms found for '{query}'."

    lines = [
        f"# Search Results: '{query}'",
        f"**{len(results)} term(s) found**",
        "",
    ]

    for term in results:
        abbr = f" ({term['abbreviation']})" if term["abbreviation"] else ""
        cat = get_category(term["category"])
        cat_icon = cat["icon"] if cat else ""
        lines.append(
            f"- **{term['term_en']}{abbr}** {cat_icon} — {term['term_ko']}"
        )
        lines.append(f"  *{term['description_en'][:120]}...*" if len(term["description_en"]) > 120 else f"  *{term['description_en']}*")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("shipmcp://glossary")
def full_glossary() -> str:
    """Get a compact glossary of all shipbuilding terms (English → Korean)."""
    lines = [
        "# 조선소 용어 전체 용어집 | Complete Shipbuilding Glossary",
        "",
        "| English Term | 한국어 | Category |",
        "|---|---|---|",
    ]

    for term in list_all_terms():
        cat = get_category(term["category"])
        cat_name = f"{cat['icon']} {cat['name_en']}" if cat else term["category"]
        abbr = f" ({term['abbreviation']})" if term["abbreviation"] else ""
        lines.append(f"| **{term['term_en']}{abbr}** | {term['term_ko']} | {cat_name} |")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# TOOLS — Functions the LLM can invoke
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    description=f"{TOOL_SERVICE_NAME}: Search shipbuilding terminology by keyword.",
    annotations=_readonly_tool_annotations("Search Ship Terms"),
)
def search_ship_terms(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search shipbuilding terminology by keyword.
    IMPORTANT: Use this for ANY shipbuilding question, including Korean terms!
    
    Searches across English terms, Korean terms (한국어), abbreviations, and descriptions.
    Example: search_ship_terms("용골") will find "Keel"
    Example: search_ship_terms("DWT") will find "Deadweight Tonnage"

    Args:
        query: The keyword or phrase to search for (English or Korean — both work!)
        max_results: Maximum number of results to return (default 10, max 50)

    Returns:
        A list of matching terms with id, English, Korean, abbreviation, and description
    """
    results = search_terms(query, max_results=min(max_results, 50))
    return [
        {
            "id": t["id"],
            "term_en": t["term_en"],
            "term_ko": t["term_ko"],
            "abbreviation": t["abbreviation"],
            "category": t["category"],
            "description_en": t["description_en"],
            "description_ko": t["description_ko"],
        }
        for t in results
    ]


@mcp.tool(
    description=f"{TOOL_SERVICE_NAME}: Get detailed information for a shipbuilding term.",
    annotations=_readonly_tool_annotations("Get Term Detail"),
)
def get_term_detail(term_id_or_name: str) -> dict[str, Any] | str:
    """Get detailed information about a specific shipbuilding term.
    IMPORTANT: Call this after search_ship_terms() to get FULL details.
    Works with Korean names too! e.g. get_term_detail("용골") returns keel details.

    Args:
        term_id_or_name: The term's unique ID (e.g. 'bulk-carrier'), English name, or Korean name (e.g. '용골', '벌크선')

    Returns:
        Detailed term information including descriptions, category, synonyms, and related terms
    """
    term = get_term(term_id_or_name)
    if not term:
        term = get_term_by_name(term_id_or_name)
    if not term:
        return f"Term '{term_id_or_name}' not found. Use search_ship_terms() to find it."

    cat = get_category(term["category"])
    related = get_related_terms(term)

    result: dict[str, Any] = {
        "id": term["id"],
        "term_en": term["term_en"],
        "term_ko": term["term_ko"],
        "abbreviation": term["abbreviation"],
        "category": {
            "id": term["category"],
            "name_en": cat["name_en"] if cat else term["category"],
            "name_ko": cat["name_ko"] if cat else "",
            "icon": cat["icon"] if cat else "",
        },
        "description_en": term["description_en"],
        "description_ko": term["description_ko"],
        "synonyms": term["synonyms"],
        "related_terms": [
            {
                "id": rt["id"],
                "term_en": rt["term_en"],
                "term_ko": rt["term_ko"],
                "abbreviation": rt["abbreviation"],
            }
            for rt in related
        ],
    }
    return result


@mcp.tool(
    description=f"{TOOL_SERVICE_NAME}: List shipbuilding terms in a category.",
    annotations=_readonly_tool_annotations("List Terms by Category"),
)
def list_terms_by_category(category_id: str) -> list[dict[str, Any]]:
    """List all shipbuilding terms in a specific category.

    Args:
        category_id: The category ID.
                    Available: ship-types, hull-structure, propulsion, navigation,
                    cargo, safety, shipbuilding-process, ship-dimensions, design,
                    marine-engineering, mooring-anchoring, electrical, classification,
                    welding-fabrication

    Returns:
        A list of terms in the category with basic info
    """
    cat = get_category(category_id)
    if not cat:
        available = [c["id"] for c in list_categories()]
        return [{"error": f"Unknown category '{category_id}'", "available_categories": available}]

    terms = get_terms_by_category(category_id)
    return [
        {
            "id": t["id"],
            "term_en": t["term_en"],
            "term_ko": t["term_ko"],
            "abbreviation": t["abbreviation"],
        }
        for t in terms
    ]


@mcp.tool(
    description=f"{TOOL_SERVICE_NAME}: List all shipbuilding terminology categories.",
    annotations=_readonly_tool_annotations("List Categories"),
)
def list_categories_tool() -> list[dict[str, Any]]:
    """List all shipbuilding terminology categories.

    Returns:
        All available categories with their IDs, names, and descriptions
    """
    return [
        {
            "id": c["id"],
            "name_en": c["name_en"],
            "name_ko": c["name_ko"],
            "description_en": c["description_en"],
            "description_ko": c["description_ko"],
            "icon": c["icon"],
            "term_count": len(get_terms_by_category(c["id"])),
        }
        for c in list_categories()
    ]


@mcp.tool(
    description=f"{TOOL_SERVICE_NAME}: Translate terms between English and Korean.",
    annotations=_readonly_tool_annotations("Translate Term"),
)
def translate_term(term: str, from_lang: str = "en", to_lang: str = "ko") -> dict[str, Any] | str:
    """Translate a shipbuilding term between English and Korean.

    Args:
        term: The term to translate (English or Korean)
        from_lang: Source language ('en' or 'ko', default 'en')
        to_lang: Target language ('en' or 'ko', default 'ko')

    Returns:
        The translated term and related information
    """
    result = get_term_by_name(term)
    if not result:
        return f"Term '{term}' not found in the shipbuilding glossary."

    if from_lang == "en" and to_lang == "ko":
        return {
            "original": result["term_en"],
            "translation": result["term_ko"],
            "abbreviation": result["abbreviation"],
            "category": result["category"],
        }
    elif from_lang == "ko" and to_lang == "en":
        return {
            "original": result["term_ko"],
            "translation": result["term_en"],
            "abbreviation": result["abbreviation"],
            "category": result["category"],
        }
    else:
        return {
            "term_en": result["term_en"],
            "term_ko": result["term_ko"],
            "abbreviation": result["abbreviation"],
        }


@mcp.tool(
    description=f"{TOOL_SERVICE_NAME}: Get glossary statistics by category.",
    annotations=_readonly_tool_annotations("Get Term Statistics"),
)
def get_term_statistics() -> dict[str, Any]:
    """Get statistics about the shipbuilding terminology database.

    Returns:
        Count of terms, categories, and category-wise distribution
    """
    categories = list_categories()
    total = count_terms()
    cat_stats = {}
    for cat in categories:
        count = len(get_terms_by_category(cat["id"]))
        if count > 0:
            cat_stats[cat["id"]] = {
                "name_en": cat["name_en"],
                "name_ko": cat["name_ko"],
                "icon": cat["icon"],
                "count": count,
            }

    return {
        "total_terms": total,
        "total_categories": len(categories),
        "categories_with_terms": len(cat_stats),
        "by_category": cat_stats,
    }


# ══════════════════════════════════════════════════════════════════════════════
# PROMPTS — Reusable templates for LLM interactions
# ══════════════════════════════════════════════════════════════════════════════

@mcp.prompt()
def learn_term(term_name: str) -> str:
    """Learn about a specific shipbuilding term in detail.

    Creates a structured learning prompt for understanding a shipbuilding term.

    Args:
        term_name: The English or Korean name of the term to learn about
    """
    return (
        f"I want to learn about the shipbuilding term '{term_name}' in detail.\n\n"
        f"Please:\n"
        f"1. Look up the term using the shipmcp tools and resources\n"
        f"2. Explain it in simple, easy-to-understand language\n"
        f"3. Provide its Korean equivalent and explain the Korean terminology\n"
        f"4. Explain how it relates to other shipbuilding concepts\n"
        f"5. Give a practical example of how this term is used in real shipbuilding\n"
        f"6. If applicable, mention any abbreviations or alternative names"
    )


@mcp.prompt()
def korean_english_glossary(category: str = "all") -> str:
    """Generate a Korean-English glossary for a shipbuilding category.

    Args:
        category: Category ID or 'all' for entire glossary
    """
    if category == "all":
        return (
            "Please generate a comprehensive Korean-English glossary of shipbuilding terms. "
            "Use the shipmcp resources and tools to get all terms. "
            "Format it as a markdown table with columns: English | Korean | Abbreviation | Brief Description. "
            "Group terms by category with appropriate headers."
        )
    else:
        return (
            f"Please generate a Korean-English glossary for the shipbuilding category '{category}'. "
            "Use the shipmcp resources to get terms in this category. "
            "Format it as a markdown table with columns: English | Korean | Abbreviation | Brief Description."
        )


@mcp.prompt()
def explain_document(text: str) -> str:
    """Explain shipbuilding-related text by identifying and defining key terms.

    Args:
        text: The text containing shipbuilding terminology to explain
    """
    return (
        f"I have the following text that contains shipbuilding terminology. "
        f"Please analyze it and explain each shipbuilding term you find:\n\n"
        f"---\n{text}\n---\n\n"
        f"For each term, please:\n"
        f"1. Identify the shipbuilding term and provide its Korean equivalent\n"
        f"2. Look up the detailed definition using shipmcp\n"
        f"3. Explain how it's used in context within the text above\n"
        f"4. Note any related terms that might be helpful to understand\n\n"
        f"Present this as a structured glossary following the text."
    )


@mcp.prompt()
def compare_terms(term1: str, term2: str) -> str:
    """Compare two shipbuilding terms and explain their differences.

    Args:
        term1: First term (English or Korean)
        term2: Second term (English or Korean)
    """
    return (
        f"Please compare the shipbuilding terms '{term1}' and '{term2}'.\n\n"
        f"Use shipmcp to look up both terms and:\n"
        f"1. Define each term clearly (English and Korean)\n"
        f"2. Explain the key differences between them\n"
        f"3. Describe when each is used and in what context\n"
        f"4. Explain how they relate to each other (if they do)\n"
        f"5. Provide examples to illustrate the difference"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ══════════════════════════════════════════════════════════════════════════════

@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
    help="Transport protocol (default: stdio)",
)
@click.option(
    "--port",
    default=8000,
    help="Port for HTTP transports (sse, streamable-http)",
    type=int,
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Bind address (use 0.0.0.0 for remote access)",
)
@click.option(
    "--db-path",
    default=None,
    help="SQLite DB file path (default: ship_mcp/data/ship_terms.db or SHIP_MCP_DB_PATH)",
)
def main(transport: str, port: int, host: str, db_path: str | None) -> None:
    """Run the ShipMCP server.

    Examples:

        # STDIO mode (default) -- for Claude Desktop
        uv run ship-mcp

        # Streamable HTTP mode -- remote access from any machine
        uv run ship-mcp --transport streamable-http --host 0.0.0.0 --port 8000

        # SSE mode -- alternative HTTP, local only
        uv run ship-mcp --transport sse --port 8000
    """
    if db_path:
        os.environ["SHIP_MCP_DB_PATH"] = db_path
        reset_repository()

    get_repository()

    # Set host/port on mcp settings for HTTP transports
    mcp.settings.host = host
    mcp.settings.port = port

    # Allow all hosts for external access (disable DNS rebinding protection)
    from mcp.server.transport_security import TransportSecuritySettings
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
        allowed_hosts=["*:*"],
        allowed_origins=["*"],
    )

    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http")
    elif transport == "sse":
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()
