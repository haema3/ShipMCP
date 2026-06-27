"""
조선소 용어 카테고리 정의
Shipbuilding Terminology Categories
"""

from typing import TypedDict


class Category(TypedDict):
    """A shipbuilding term category."""
    id: str
    name_en: str
    name_ko: str
    description_en: str
    description_ko: str
    icon: str


CATEGORIES: list[Category] = [
    {
        "id": "ship-types",
        "name_en": "Ship Types",
        "name_ko": "선종 (船種)",
        "description_en": "Classification of vessels by purpose and design",
        "description_ko": "용도와 설계에 따른 선박 분류",
        "icon": "🚢",
    },
    {
        "id": "hull-structure",
        "name_en": "Hull Structure",
        "name_ko": "선체 구조 (船體構造)",
        "description_en": "The main structural components of a ship's hull",
        "description_ko": "선체의 주요 구조 부재",
        "icon": "🏗️",
    },
    {
        "id": "propulsion",
        "name_en": "Propulsion System",
        "name_ko": "추진 시스템 (推進 system)",
        "description_en": "Systems that provide thrust and movement to the vessel",
        "description_ko": "선박에 추진력을 제공하는 시스템",
        "icon": "⚙️",
    },
    {
        "id": "navigation",
        "name_en": "Navigation & Communication",
        "name_ko": "항해 및 통신 (航海 및 通信)",
        "description_en": "Equipment and systems for navigation and onboard communication",
        "description_ko": "항해 및 선내 통신을 위한 장비와 시스템",
        "icon": "🧭",
    },
    {
        "id": "cargo",
        "name_en": "Cargo Handling",
        "name_ko": "화물 처리 (貨物處理)",
        "description_en": "Equipment and systems for loading, stowing, and discharging cargo",
        "description_ko": "화물 적재, 배치 및 하역을 위한 장비와 시스템",
        "icon": "📦",
    },
    {
        "id": "safety",
        "name_en": "Safety & Lifesaving",
        "name_ko": "안전 및 구명 (安全 및 救命)",
        "description_en": "Safety equipment, firefighting, and lifesaving appliances",
        "description_ko": "안전 장비, 소방 및 구명 설비",
        "icon": "🛟",
    },
    {
        "id": "shipbuilding-process",
        "name_en": "Shipbuilding Process",
        "name_ko": "조선 공정 (造船工程)",
        "description_en": "Stages and methods in the ship manufacturing process",
        "description_ko": "선박 제조 공정의 단계와 방법",
        "icon": "🔧",
    },
    {
        "id": "ship-dimensions",
        "name_en": "Ship Dimensions & Tonnage",
        "name_ko": "선박 치수 및 톤수 (船舶 尺寸 및 噸數)",
        "description_en": "Measurements, dimensions, and tonnage classifications of vessels",
        "description_ko": "선박의 측정, 치수 및 톤수 분류",
        "icon": "📐",
    },
    {
        "id": "design",
        "name_en": "Ship Design & Naval Architecture",
        "name_ko": "선박 설계 및 조선공학 (船舶設計 및 造船工學)",
        "description_en": "Principles and practices of naval architecture and marine engineering",
        "description_ko": "조선공학 및 선박 설계의 원리와 실제",
        "icon": "📋",
    },
    {
        "id": "marine-engineering",
        "name_en": "Marine Engineering",
        "name_ko": "선박 기관 (船舶機關)",
        "description_en": "Engine room systems, piping, electrical, and auxiliary machinery",
        "description_ko": "기관실 시스템, 배관, 전기 및 보조 기계",
        "icon": "🔩",
    },
    {
        "id": "mooring-anchoring",
        "name_en": "Mooring & Anchoring",
        "name_ko": "계류 및 정박 (繫留 및 碇泊)",
        "description_en": "Equipment and operations for securing a vessel to a dock or anchorage",
        "description_ko": "선박을 부두 또는 정박지에 고정하는 장비와 작업",
        "icon": "⚓",
    },
    {
        "id": "electrical",
        "name_en": "Electrical & Automation",
        "name_ko": "전기 및 자동화 (電氣 및 自動化)",
        "description_en": "Electrical power systems, automation, and control systems on ships",
        "description_ko": "선박 전력 시스템, 자동화 및 제어 시스템",
        "icon": "💡",
    },
    {
        "id": "classification",
        "name_en": "Classification & Regulation",
        "name_ko": "선급 및 규정 (船級 및 規定)",
        "description_en": "Classification societies, international regulations, and industry standards",
        "description_ko": "선급 협회, 국제 규정 및 산업 표준",
        "icon": "📜",
    },
    {
        "id": "welding-fabrication",
        "name_en": "Welding & Fabrication",
        "name_ko": "용접 및 가공 (鎔接 및 加工)",
        "description_en": "Welding techniques, material preparation, and fabrication methods in shipbuilding",
        "description_ko": "조선에서의 용접 기술, 재료 준비 및 가공 방법",
        "icon": "🔥",
    },
]


def get_category(category_id: str) -> Category | None:
    """Get a category by its ID."""
    for cat in CATEGORIES:
        if cat["id"] == category_id:
            return cat
    return None


def list_categories() -> list[Category]:
    """Return all categories."""
    return list(CATEGORIES)
