"""扑克牌收集记录器 - 主界面"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from card_tracker import (
    TOTAL_CARDS,
    STANDARD_DECK_SIZE,
    SUITS,
    RANKS,
    JOKERS,
    SUIT_LABELS,
    SUIT_COLORS,
    JOKER_LABELS,
    Card,
    CardCollection,
    all_cards,
)

# ── 颜色主题 ──────────────────────────────────────────────
BG = "#f0f4f8"
PANEL_BG = "#ffffff"
HEADER_BG = "#2c3e50"
HEADER_FG = "#ecf0f1"
COLLECTED_BG = "#27ae60"
COLLECTED_FG = "#ffffff"
UNCOLLECTED_BG = "#ecf0f1"
HOVER_BG = "#3498db"
ACCENT = "#2980b9"
PROGRESS_BG = "#bdc3c7"
PROGRESS_FG = "#27ae60"


class CardButton(tk.Label):
    """单张扑克牌按钮（用 Label 实现，支持样式切换）"""

    def __init__(self, parent, card: Card, on_click, on_right_click, **kw):
        self.card = card
        self.on_click = on_click
        self.on_right_click = on_right_click
        super().__init__(
            parent,
            text=card.display_name,
            width=4,
            relief="raised",
            borderwidth=2,
            cursor="hand2",
            font=("Segoe UI", 11, "bold"),
            **kw,
        )
        self.bind("<Button-1>", self._handle_click)
        self.bind("<Button-3>", self._handle_right_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._collected = False

    def _handle_click(self, _event):
        self.on_click(self.card)

    def _handle_right_click(self, _event):
        self.on_right_click(self.card)

    def _on_enter(self, _event):
        if not self._collected:
            self.configure(bg=HOVER_BG, fg="#ffffff")

    def _on_leave(self, _event):
        self.refresh(self._collected)

    def refresh(self, collected: bool):
        self._collected = collected
        if collected:
            self.configure(
                bg=COLLECTED_BG, fg=COLLECTED_FG, relief="sunken",
            )
        else:
            color = SUIT_COLORS.get(self.card.suit, "#8e44ad")
            self.configure(
                bg=UNCOLLECTED_BG,
                fg=color if self.card.suit else "#8e44ad",
                relief="raised",
            )


class CardTrackerApp(tk.Tk):
    """主应用窗口"""

    def __init__(self):
        super().__init__()
        self.title("扑克牌收集记录器")
        self.configure(bg=BG)
        self.geometry("900x620")
        self.minsize(800, 560)

        self.collection = CardCollection.load()
        self._card_buttons: dict[str, CardButton] = {}
        self._history: list[tuple[str, Card]] = []

        self._build_ui()
        self._refresh_all()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI 构建 ──────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_toolbar()
        self._build_card_grid()
        self._build_jokers()
        self._build_status_bar()

    def _build_header(self):
        header = tk.Frame(self, bg=HEADER_BG, padx=20, pady=14)
        header.pack(fill="x")

        tk.Label(
            header, text="🃏 扑克牌收集记录器",
            bg=HEADER_BG, fg=HEADER_FG,
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(side="left")

        self.count_label = tk.Label(
            header, text="",
            bg=HEADER_BG, fg="#f1c40f",
            font=("Microsoft YaHei UI", 14, "bold"),
        )
        self.count_label.pack(side="right")

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg=BG, padx=16, pady=8)
        toolbar.pack(fill="x")

        style = ttk.Style()
        style.configure("Tool.TButton", font=("Microsoft YaHei UI", 9), padding=4)

        ttk.Button(toolbar, text="↩ 撤销上一张", style="Tool.TButton", command=self._undo_last).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄 重置全部", style="Tool.TButton", command=self._reset_all).pack(side="left", padx=4)

        tk.Label(
            toolbar,
            text="左键：标记收集  |  右键：取消收集  |  绿色=已收集  灰色=未收集",
            bg=BG, fg="#888",
            font=("Microsoft YaHei UI", 9),
        ).pack(side="right", padx=8)

    def _build_card_grid(self):
        outer = tk.Frame(self, bg=BG, padx=16, pady=4)
        outer.pack(fill="both", expand=True)

        panel = tk.LabelFrame(
            outer, text="  标准牌（52张）  ",
            bg=PANEL_BG, fg=HEADER_BG,
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=10, pady=8,
        )
        panel.pack(fill="both", expand=True)

        grid = tk.Frame(panel, bg=PANEL_BG)
        grid.pack()

        # 列标题
        tk.Label(grid, text="", width=8, bg=PANEL_BG).grid(row=0, column=0)
        for col, rank in enumerate(RANKS):
            tk.Label(
                grid, text=rank, width=4, bg=PANEL_BG,
                font=("Segoe UI", 9, "bold"), fg="#666",
            ).grid(row=0, column=col + 1, padx=1, pady=2)

        for row, suit in enumerate(SUITS, start=1):
            tk.Label(
                grid, text=SUIT_LABELS[suit], width=8,
                bg=PANEL_BG, fg=SUIT_COLORS[suit],
                font=("Microsoft YaHei UI", 10, "bold"),
            ).grid(row=row, column=0, padx=4, pady=3, sticky="e")

            for col, rank in enumerate(RANKS):
                card = Card(suit=suit, rank=rank)
                btn = CardButton(
                    grid, card,
                    on_click=self._on_add_card,
                    on_right_click=self._on_remove_card,
                )
                btn.grid(row=row, column=col + 1, padx=1, pady=3)
                self._card_buttons[card.card_id] = btn

    def _build_jokers(self):
        frame = tk.Frame(self, bg=BG, padx=16, pady=4)
        frame.pack(fill="x")

        panel = tk.LabelFrame(
            frame, text="  王牌  ",
            bg=PANEL_BG, fg="#8e44ad",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=12, pady=8,
        )
        panel.pack()

        for joker in JOKERS:
            card = Card(suit=None, rank=joker)
            btn = CardButton(
                panel, card,
                on_click=self._on_add_card,
                on_right_click=self._on_remove_card,
            )
            btn.configure(text=JOKER_LABELS[joker], width=8, font=("Microsoft YaHei UI", 11, "bold"))
            btn.pack(side="left", padx=12, pady=4)
            self._card_buttons[card.card_id] = btn

    def _build_status_bar(self):
        bar = tk.Frame(self, bg=PANEL_BG, padx=16, pady=10)
        bar.pack(fill="x", side="bottom")

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            bar, variable=self.progress_var,
            maximum=TOTAL_CARDS, length=300,
            style="green.Horizontal.TProgressbar",
        )
        style = ttk.Style()
        style.configure(
            "green.Horizontal.TProgressbar",
            troughcolor=PROGRESS_BG,
            background=PROGRESS_FG,
        )
        self.progress_bar.pack(side="left", padx=(0, 12))

        self.status_label = tk.Label(
            bar, text="", bg=PANEL_BG,
            font=("Microsoft YaHei UI", 10),
            fg="#333",
        )
        self.status_label.pack(side="left")

        self.deck_status_label = tk.Label(
            bar, text="", bg=PANEL_BG,
            font=("Microsoft YaHei UI", 10),
            fg="#666",
        )
        self.deck_status_label.pack(side="right")

    # ── 事件处理 ──────────────────────────────────────────

    def _on_add_card(self, card: Card):
        if self.collection.is_collected(card):
            messagebox.showinfo(
                "已收集",
                f"{card.full_name} 已经收集过了！\n\n如需取消收集，请右键点击该牌。",
                parent=self,
            )
            return
        self.collection.add(card)
        self._history.append(("add", card))
        self._refresh_card(card)
        self._refresh_status()
        self.collection.save()

    def _on_remove_card(self, card: Card):
        if not self.collection.is_collected(card):
            messagebox.showinfo(
                "未收集",
                f"{card.full_name} 尚未收集，无需取消。",
                parent=self,
            )
            return
        self.collection.remove(card)
        self._history.append(("remove", card))
        self._refresh_card(card)
        self._refresh_status()
        self.collection.save()

    def _undo_last(self):
        if not self._history:
            messagebox.showinfo("提示", "没有可撤销的操作。", parent=self)
            return
        action, card = self._history.pop()
        if action == "add":
            self.collection.remove(card)
        else:
            self.collection.add(card)
        self._refresh_card(card)
        self._refresh_status()
        self.collection.save()

    def _reset_all(self):
        if not self.collection.collected:
            messagebox.showinfo("提示", "当前没有任何收集记录。", parent=self)
            return
        if messagebox.askyesno(
            "确认重置",
            "确定要清空所有收集记录吗？此操作可撤销（撤销上一张）。",
            parent=self,
        ):
            self.collection.reset()
            self._history.clear()
            self._refresh_all()
            self.collection.save()

    def _on_close(self):
        self.collection.save()
        self.destroy()

    # ── 刷新 ──────────────────────────────────────────────

    def _refresh_card(self, card: Card):
        btn = self._card_buttons.get(card.card_id)
        if btn:
            btn.refresh(self.collection.is_collected(card))

    def _refresh_all(self):
        for card in all_cards():
            self._refresh_card(card)
        self._refresh_status()

    def _refresh_status(self):
        count = self.collection.count
        std_count = self.collection.standard_count

        self.count_label.configure(text=f"{count} / {TOTAL_CARDS}")
        self.progress_var.set(count)

        if count == TOTAL_CARDS:
            status = "🎉 恭喜！所有牌（含大小王）已全部收集完毕！"
            color = COLLECTED_BG
        elif std_count == STANDARD_DECK_SIZE:
            status = "✅ 标准 52 张已全部收集！还差大小王。"
            color = ACCENT
        else:
            status = f"已收集 {count} 张，还差 {TOTAL_CARDS - count} 张"
            color = "#333"

        self.status_label.configure(text=status, fg=color)
        self.deck_status_label.configure(
            text=f"标准牌：{std_count} / {STANDARD_DECK_SIZE}  |  含王牌：{count} / {TOTAL_CARDS}"
        )


def main():
    app = CardTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
