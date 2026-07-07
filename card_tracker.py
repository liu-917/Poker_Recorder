"""扑克牌收集记录 - 数据模型与持久化"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

# 四种花色
SUITS = ("spade", "heart", "diamond", "club")
SUIT_LABELS = {
    "spade": "♠ 黑桃",
    "heart": "♥ 红桃",
    "diamond": "♦ 方块",
    "club": "♣ 梅花",
}
SUIT_SYMBOLS = {
    "spade": "♠",
    "heart": "♥",
    "diamond": "♦",
    "club": "♣",
}
SUIT_COLORS = {
    "spade": "#1a1a2e",
    "heart": "#c0392b",
    "diamond": "#e74c3c",
    "club": "#1a1a2e",
}

# 点数 A-10-J-Q-K
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")

# 大小王
JOKERS = ("small", "big")
JOKER_LABELS = {
    "small": "小王",
    "big": "大王",
}

DEFAULT_SAVE_PATH = Path(__file__).parent / "collection_data.json"


@dataclass
class Card:
    suit: str | None  # None 表示王牌
    rank: str  # 普通牌为 A-K；王牌为 small/big

    @property
    def card_id(self) -> str:
        if self.suit is None:
            return f"joker_{self.rank}"
        return f"{self.suit}_{self.rank}"

    @property
    def display_name(self) -> str:
        if self.suit is None:
            return JOKER_LABELS[self.rank]
        return f"{SUIT_SYMBOLS[self.suit]}{self.rank}"

    @property
    def full_name(self) -> str:
        if self.suit is None:
            return JOKER_LABELS[self.rank]
        return f"{SUIT_LABELS[self.suit]} {self.rank}"


def all_cards() -> list[Card]:
    cards: list[Card] = []
    for suit in SUITS:
        for rank in RANKS:
            cards.append(Card(suit=suit, rank=rank))
    for joker in JOKERS:
        cards.append(Card(suit=None, rank=joker))
    return cards


STANDARD_DECK_SIZE = len(SUITS) * len(RANKS)  # 52
TOTAL_CARDS = len(all_cards())  # 54（含大小王）


@dataclass
class CardCollection:
    collected: set[str] = field(default_factory=set)

    def is_collected(self, card: Card) -> bool:
        return card.card_id in self.collected

    def add(self, card: Card) -> bool:
        """添加收集，返回 True 表示新添加，False 表示已存在。"""
        if card.card_id in self.collected:
            return False
        self.collected.add(card.card_id)
        return True

    def remove(self, card: Card) -> bool:
        """取消收集，返回 True 表示成功移除。"""
        if card.card_id not in self.collected:
            return False
        self.collected.discard(card.card_id)
        return True

    @property
    def count(self) -> int:
        return len(self.collected)

    @property
    def standard_count(self) -> int:
        return sum(
            1
            for cid in self.collected
            if not cid.startswith("joker_")
        )

    def iter_collected_cards(self) -> Iterator[Card]:
        card_map = {c.card_id: c for c in all_cards()}
        for cid in sorted(self.collected):
            if cid in card_map:
                yield card_map[cid]

    def reset(self) -> None:
        self.collected.clear()

    def to_dict(self) -> dict:
        return {"collected": sorted(self.collected)}

    @classmethod
    def from_dict(cls, data: dict) -> CardCollection:
        return cls(collected=set(data.get("collected", [])))

    def save(self, path: Path | None = None) -> None:
        path = path or DEFAULT_SAVE_PATH
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path | None = None) -> CardCollection:
        path = path or DEFAULT_SAVE_PATH
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return cls()
