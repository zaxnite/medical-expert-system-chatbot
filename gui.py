# gui.py
# Medical Expert System - BCS 222 Programming Paradigms
# Tkinter GUI for the medical expert system.
# All diagnosis logic stays in consultation.py / bridge.py / lisp_connector.py

from __future__ import annotations
import sys
import threading
import time
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# gui.py is placed at the project root alongside main.py
_BASE        = Path(__file__).resolve().parent
_OOP_DIR     = _BASE / "src" / "oop"
_INTEGRATION = _BASE / "integration"

for _p in [_BASE, _OOP_DIR, _INTEGRATION]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# colour palette (from presentation slides)
DARK_BG      = "#0d1b2a"
PANEL_BG     = "#1a2e45"
SIDEBAR_BG   = "#0f2035"
TEAL         = "#00b4d8"
TEAL_DARK    = "#0096b7"
TEAL_FAINT   = "#0a3352"
GOLD         = "#f4c842"
GREEN        = "#4ade80"
RED_SOFT     = "#f87171"
WHITE        = "#ffffff"
OFF_WHITE    = "#c8d8e8"
MUTED        = "#6b8caa"
BORDER       = "#1e3a54"
INPUT_BG     = "#0f2a40"
SCROLLBAR_BG = "#1a2e45"

# fonts
FONT_TITLE  = ("Consolas", 18, "bold")
FONT_HEAD   = ("Consolas", 13, "bold")
FONT_LABEL  = ("Consolas", 10, "bold")
FONT_BODY   = ("Consolas", 10)
FONT_SMALL  = ("Consolas", 9)
FONT_MONO   = ("Courier New", 9)


def _style_root(root: tk.Tk):
    root.configure(bg=DARK_BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame",       background=DARK_BG)
    style.configure("Panel.TFrame", background=PANEL_BG)
    style.configure("Side.TFrame",  background=SIDEBAR_BG)

    style.configure("TLabel",
                    background=DARK_BG, foreground=OFF_WHITE,
                    font=FONT_BODY)
    style.configure("Head.TLabel",
                    background=PANEL_BG, foreground=GOLD,
                    font=FONT_HEAD)
    style.configure("Title.TLabel",
                    background=DARK_BG, foreground=WHITE,
                    font=FONT_TITLE)
    style.configure("Muted.TLabel",
                    background=PANEL_BG, foreground=MUTED,
                    font=FONT_SMALL)
    style.configure("Side.TLabel",
                    background=SIDEBAR_BG, foreground=OFF_WHITE,
                    font=FONT_BODY)

    style.configure("TButton",
                    background=TEAL, foreground=DARK_BG,
                    font=FONT_LABEL, relief="flat",
                    borderwidth=0, padding=(12, 6))
    style.map("TButton",
              background=[("active", TEAL_DARK), ("disabled", BORDER)],
              foreground=[("disabled", MUTED)])

    style.configure("Yes.TButton",
                    background=GREEN, foreground=DARK_BG,
                    font=FONT_LABEL, padding=(20, 8))
    style.map("Yes.TButton",
              background=[("active", "#22c55e")])

    style.configure("No.TButton",
                    background=RED_SOFT, foreground=DARK_BG,
                    font=FONT_LABEL, padding=(20, 8))
    style.map("No.TButton",
              background=[("active", "#ef4444")])

    style.configure("TEntry",
                    fieldbackground=INPUT_BG, foreground=WHITE,
                    insertcolor=TEAL, font=FONT_BODY,
                    borderwidth=1, relief="flat")

    style.configure("TScrollbar",
                    background=SCROLLBAR_BG, troughcolor=DARK_BG,
                    arrowcolor=MUTED, borderwidth=0)

    style.configure("Horizontal.TProgressbar",
                    troughcolor=BORDER, background=TEAL,
                    borderwidth=0, thickness=4)


def _card(parent, **kwargs) -> tk.Frame:
    f = tk.Frame(parent, bg=PANEL_BG,
                 highlightbackground=BORDER,
                 highlightthickness=1,
                 **kwargs)
    return f


def _tag_label(parent, text: str, color: str = TEAL) -> tk.Label:
    return tk.Label(parent, text=text, bg=color, fg=DARK_BG,
                    font=FONT_LABEL, padx=6, pady=2)


class _DotsAnim:
    # animated loading dots shown while waiting for Prolog to respond
    def __init__(self, label: tk.Label):
        self._lbl  = label
        self._dots = 0
        self._running = False

    def start(self):
        self._running = True
        self._tick()

    def stop(self):
        self._running = False
        self._lbl.config(text="")

    def _tick(self):
        if not self._running:
            return
        self._dots = (self._dots + 1) % 4
        self._lbl.config(text="●" * self._dots + "○" * (3 - self._dots))
        self._lbl.after(400, self._tick)


class WelcomePage(tk.Frame):
    def __init__(self, master, on_start):
        super().__init__(master, bg=DARK_BG)
        self._on_start = on_start
        self._build()

    def _build(self):
        badge_row = tk.Frame(self, bg=DARK_BG)
        badge_row.pack(pady=(30, 0))
        for text, col in [("Functional · Lisp", GOLD),
                          ("Logic · Prolog", TEAL),
                          ("OOP · Python", GREEN)]:
            _tag_label(badge_row, text, col).pack(side="left", padx=5)

        hero = _card(self)
        hero.pack(padx=60, pady=20, fill="x")

        tk.Label(hero, text="Medical Expert System",
                 bg=PANEL_BG, fg=WHITE,
                 font=("Consolas", 26, "bold")).pack(pady=(28, 4))
        tk.Label(hero, text="BCS 222 — Programming Paradigms",
                 bg=PANEL_BG, fg=MUTED, font=FONT_SMALL).pack()

        sep = tk.Frame(hero, bg=TEAL, height=2)
        sep.pack(fill="x", padx=40, pady=14)

        tk.Label(hero,
                 text=(
                     "A terminal-style diagnostic assistant covering 20 diseases\n"
                     "across 5 medical groups. Answer yes/no questions about your\n"
                     "symptoms to receive a confidence-ranked diagnosis."
                 ),
                 bg=PANEL_BG, fg=OFF_WHITE,
                 font=FONT_BODY, justify="center").pack(padx=30, pady=(0, 20))

        steps_row = tk.Frame(self, bg=DARK_BG)
        steps_row.pack(pady=4)
        steps = [
            ("1", "Describe symptoms\nin plain text", GOLD),
            ("2", "Confirm & answer\nyes / no questions", TEAL),
            ("3", "Receive confidence-\nbased diagnosis", GREEN),
        ]
        for num, desc, col in steps:
            col_frame = tk.Frame(steps_row, bg=DARK_BG)
            col_frame.pack(side="left", padx=18)
            circle = tk.Label(col_frame, text=num,
                              bg=col, fg=DARK_BG,
                              font=("Consolas", 16, "bold"),
                              width=3, height=1)
            circle.pack()
            tk.Label(col_frame, text=desc, bg=DARK_BG, fg=OFF_WHITE,
                     font=FONT_SMALL, justify="center").pack(pady=4)

        details = _card(self)
        details.pack(padx=80, pady=20, fill="x")
        tk.Label(details, text="Patient Details",
                 bg=PANEL_BG, fg=GOLD, font=FONT_HEAD).pack(pady=(16, 8))

        row1 = tk.Frame(details, bg=PANEL_BG)
        row1.pack(fill="x", padx=24, pady=4)
        tk.Label(row1, text="Name:", bg=PANEL_BG, fg=MUTED,
                 font=FONT_LABEL, width=8, anchor="w").pack(side="left")
        self._name_var = tk.StringVar()
        self._name_entry = tk.Entry(row1, textvariable=self._name_var,
                                    bg=INPUT_BG, fg=WHITE,
                                    insertbackground=TEAL,
                                    font=FONT_BODY, relief="flat",
                                    highlightbackground=BORDER,
                                    highlightthickness=1)
        self._name_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self._name_entry.focus_set()

        row2 = tk.Frame(details, bg=PANEL_BG)
        row2.pack(fill="x", padx=24, pady=4)
        tk.Label(row2, text="Age:", bg=PANEL_BG, fg=MUTED,
                 font=FONT_LABEL, width=8, anchor="w").pack(side="left")
        self._age_var = tk.StringVar()
        tk.Entry(row2, textvariable=self._age_var,
                 bg=INPUT_BG, fg=WHITE,
                 insertbackground=TEAL,
                 font=FONT_BODY, relief="flat",
                 highlightbackground=BORDER,
                 highlightthickness=1,
                 width=10).pack(side="left", ipady=5)
        tk.Label(row2, text="(optional)", bg=PANEL_BG, fg=MUTED,
                 font=FONT_SMALL).pack(side="left", padx=8)

        self._err_lbl = tk.Label(details, text="",
                                  bg=PANEL_BG, fg=RED_SOFT, font=FONT_SMALL)
        self._err_lbl.pack(pady=(2, 0))

        btn = tk.Button(details, text="Begin Consultation →",
                        bg=TEAL, fg=DARK_BG, font=FONT_HEAD,
                        relief="flat", cursor="hand2",
                        activebackground=TEAL_DARK,
                        activeforeground=DARK_BG,
                        padx=20, pady=8,
                        command=self._submit)
        btn.pack(pady=(12, 20))

        self._name_entry.bind("<Return>", lambda _: self._submit())

        tk.Label(self, text="⚠  This system is not a substitute for professional medical advice.",
                 bg=DARK_BG, fg=MUTED, font=FONT_SMALL).pack(pady=(0, 20))

    def _submit(self):
        name = self._name_var.get().strip()
        if not name:
            self._err_lbl.config(text="Please enter your name to continue.")
            return
        age_raw = self._age_var.get().strip()
        age = None
        if age_raw:
            try:
                age = int(age_raw)
                if not (0 < age < 130):
                    raise ValueError
            except ValueError:
                self._err_lbl.config(text="Age must be a number between 1 and 129.")
                return
        self._err_lbl.config(text="")
        self._on_start(name, age)


class IntakePage(tk.Frame):
    def __init__(self, master, patient_name: str, on_done, on_skip):
        super().__init__(master, bg=DARK_BG)
        self._on_done = on_done
        self._on_skip = on_skip
        self._build(patient_name)

    def _build(self, name: str):
        hdr = tk.Frame(self, bg=DARK_BG)
        hdr.pack(fill="x", padx=30, pady=(20, 8))
        tk.Label(hdr, text=f"Hello, {name}",
                 bg=DARK_BG, fg=WHITE, font=FONT_TITLE).pack(side="left")

        card = _card(self)
        card.pack(padx=40, pady=10, fill="x")

        tk.Label(card, text="Describe Your Symptoms",
                 bg=PANEL_BG, fg=GOLD, font=FONT_HEAD).pack(pady=(16, 4))
        tk.Label(card,
                 text=(
                     "Tell us how you are feeling in your own words.\n"
                     "The Lisp processor will extract symptoms automatically."
                 ),
                 bg=PANEL_BG, fg=OFF_WHITE, font=FONT_BODY,
                 justify="center").pack(pady=(0, 12))

        self._text = tk.Text(card, height=5, width=60,
                             bg=INPUT_BG, fg=WHITE,
                             insertbackground=TEAL,
                             font=FONT_BODY, relief="flat",
                             highlightbackground=BORDER,
                             highlightthickness=1,
                             wrap="word",
                             padx=10, pady=8)
        self._text.pack(padx=20, pady=(0, 8), fill="x")
        self._text.insert("1.0",
                          "e.g. I have a fever, cough, and I lost my sense of smell…")
        self._text.config(fg=MUTED)

        def _clear_placeholder(e):
            if self._text.get("1.0", "end-1c") == \
               "e.g. I have a fever, cough, and I lost my sense of smell…":
                self._text.delete("1.0", "end")
                self._text.config(fg=WHITE)
        self._text.bind("<FocusIn>", _clear_placeholder)

        proc_row = tk.Frame(card, bg=PANEL_BG)
        proc_row.pack(pady=(0, 4))
        self._dots_lbl = tk.Label(proc_row, text="",
                                   bg=PANEL_BG, fg=TEAL, font=FONT_BODY)
        self._dots_lbl.pack(side="left", padx=6)
        self._proc_lbl = tk.Label(proc_row, text="",
                                   bg=PANEL_BG, fg=MUTED, font=FONT_SMALL)
        self._proc_lbl.pack(side="left")
        self._dots_anim = _DotsAnim(self._dots_lbl)

        btn_row = tk.Frame(card, bg=PANEL_BG)
        btn_row.pack(pady=(4, 18))
        self._process_btn = tk.Button(btn_row, text="Process Symptoms →",
                                       bg=TEAL, fg=DARK_BG, font=FONT_LABEL,
                                       relief="flat", cursor="hand2",
                                       activebackground=TEAL_DARK,
                                       activeforeground=DARK_BG,
                                       padx=16, pady=7,
                                       command=self._submit)
        self._process_btn.pack(side="left", padx=6)

        tk.Button(btn_row, text="Skip → Yes/No Questions",
                  bg=PANEL_BG, fg=MUTED, font=FONT_SMALL,
                  relief="flat", cursor="hand2",
                  activebackground=BORDER,
                  activeforeground=OFF_WHITE,
                  padx=10, pady=7,
                  command=self._on_skip).pack(side="left", padx=6)

        self._text.bind("<Control-Return>", lambda _: self._submit())

    def _submit(self):
        raw = self._text.get("1.0", "end-1c").strip()
        if raw == "e.g. I have a fever, cough, and I lost my sense of smell…":
            raw = ""
        self._proc_lbl.config(text="Sending to Lisp processor…")
        self._dots_anim.start()
        self._process_btn.config(state="disabled")
        self._on_done(raw)

    def finish_processing(self, found: list, denied: list):
        self._dots_anim.stop()
        self._proc_lbl.config(text=f"Done — {len(found)+len(denied)} symptom(s) detected.")


class ConfirmPage(tk.Frame):
    def __init__(self, master, found: list, denied: list, on_accept, on_reject):
        super().__init__(master, bg=DARK_BG)
        self._on_accept = on_accept
        self._on_reject = on_reject
        self._build(found, denied)

    def _build(self, found: list, denied: list):
        tk.Label(self, text="Detected Symptoms",
                 bg=DARK_BG, fg=GOLD, font=FONT_TITLE).pack(pady=(24, 4))
        tk.Label(self, text="Please confirm the symptoms identified from your description.",
                 bg=DARK_BG, fg=MUTED, font=FONT_SMALL).pack()

        card = _card(self)
        card.pack(padx=60, pady=14, fill="x")

        if found:
            tk.Label(card, text="✓  Symptoms you have:",
                     bg=PANEL_BG, fg=GREEN, font=FONT_LABEL).pack(
                         anchor="w", padx=20, pady=(14, 4))
            for s in found:
                tk.Label(card,
                         text=f"   • {s.replace('_', ' ').title()}",
                         bg=PANEL_BG, fg=OFF_WHITE, font=FONT_BODY).pack(
                             anchor="w", padx=30)

        if denied:
            tk.Label(card, text="✗  Symptoms you do NOT have:",
                     bg=PANEL_BG, fg=RED_SOFT, font=FONT_LABEL).pack(
                         anchor="w", padx=20, pady=(10, 4))
            for s in denied:
                tk.Label(card,
                         text=f"   • {s.replace('_', ' ').title()}",
                         bg=PANEL_BG, fg=OFF_WHITE, font=FONT_BODY).pack(
                             anchor="w", padx=30)

        sep = tk.Frame(card, bg=BORDER, height=1)
        sep.pack(fill="x", padx=20, pady=12)

        tk.Label(card, text="Is this correct?",
                 bg=PANEL_BG, fg=OFF_WHITE, font=FONT_LABEL).pack(pady=(0, 10))

        btn_row = tk.Frame(card, bg=PANEL_BG)
        btn_row.pack(pady=(0, 20))

        tk.Button(btn_row, text="✓  Yes, looks correct",
                  bg=GREEN, fg=DARK_BG, font=FONT_LABEL,
                  relief="flat", cursor="hand2",
                  activebackground="#22c55e",
                  activeforeground=DARK_BG,
                  padx=16, pady=8,
                  command=self._on_accept).pack(side="left", padx=8)

        tk.Button(btn_row, text="✗  No, ask me questions instead",
                  bg=PANEL_BG, fg=RED_SOFT, font=FONT_SMALL,
                  relief="flat", cursor="hand2",
                  highlightbackground=RED_SOFT,
                  highlightthickness=1,
                  padx=12, pady=8,
                  command=self._on_reject).pack(side="left", padx=8)


class QAPage(tk.Frame):
    def __init__(self, master, on_answer):
        super().__init__(master, bg=DARK_BG)
        self._on_answer = on_answer
        self._total_candidates = 20
        self._asked = 0
        self._build()

    def _build(self):
        status_bar = tk.Frame(self, bg=SIDEBAR_BG, height=36)
        status_bar.pack(fill="x")
        status_bar.pack_propagate(False)

        self._cand_lbl = tk.Label(status_bar,
                                   text="20 conditions still possible",
                                   bg=SIDEBAR_BG, fg=TEAL, font=FONT_SMALL)
        self._cand_lbl.pack(side="left", padx=16)

        self._q_lbl = tk.Label(status_bar,
                                text="Q 0",
                                bg=SIDEBAR_BG, fg=MUTED, font=FONT_SMALL)
        self._q_lbl.pack(side="right", padx=16)

        self._progress = ttk.Progressbar(self, orient="horizontal",
                                          mode="determinate",
                                          style="Horizontal.TProgressbar")
        self._progress.pack(fill="x")
        self._progress["maximum"] = 20
        self._progress["value"]   = 0

        chat_outer = tk.Frame(self, bg=DARK_BG)
        chat_outer.pack(fill="both", expand=True, padx=20, pady=12)

        scrollbar = tk.Scrollbar(chat_outer, bg=SCROLLBAR_BG,
                                  troughcolor=DARK_BG,
                                  activebackground=TEAL,
                                  width=10, relief="flat",
                                  borderwidth=0)
        scrollbar.pack(side="right", fill="y")

        self._chat = tk.Canvas(chat_outer, bg=DARK_BG,
                                highlightthickness=0,
                                yscrollcommand=scrollbar.set)
        self._chat.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._chat.yview)

        self._chat_inner = tk.Frame(self._chat, bg=DARK_BG)
        self._chat_win   = self._chat.create_window(
            (0, 0), window=self._chat_inner, anchor="nw"
        )

        self._chat_inner.bind("<Configure>", self._on_chat_resize)
        self._chat.bind("<Configure>", self._on_canvas_resize)

        self._q_card = _card(self)
        self._q_card.pack(padx=20, pady=(0, 8), fill="x")

        self._wait_lbl = tk.Label(self._q_card, text="",
                                   bg=PANEL_BG, fg=TEAL, font=FONT_SMALL)
        self._wait_lbl.pack(pady=(10, 4))
        self._wait_dots = _DotsAnim(self._wait_lbl)

        self._question_lbl = tk.Label(
            self._q_card,
            text="Waiting for first question…",
            bg=PANEL_BG, fg=WHITE,
            font=("Consolas", 13, "bold"),
            wraplength=500,
            justify="center"
        )
        self._question_lbl.pack(padx=20, pady=(6, 14))

        ans_row = tk.Frame(self, bg=DARK_BG)
        ans_row.pack(pady=(0, 18))

        self._yes_btn = tk.Button(
            ans_row, text="✓  YES",
            bg=GREEN, fg=DARK_BG,
            font=("Consolas", 12, "bold"),
            relief="flat", cursor="hand2",
            activebackground="#22c55e",
            activeforeground=DARK_BG,
            padx=36, pady=10,
            command=lambda: self._answer(True)
        )
        self._yes_btn.pack(side="left", padx=16)

        self._no_btn = tk.Button(
            ans_row, text="✗  NO",
            bg=RED_SOFT, fg=DARK_BG,
            font=("Consolas", 12, "bold"),
            relief="flat", cursor="hand2",
            activebackground="#ef4444",
            activeforeground=DARK_BG,
            padx=36, pady=10,
            command=lambda: self._answer(False)
        )
        self._no_btn.pack(side="left", padx=16)

        self._set_buttons_enabled(False)

        # y and n as keyboard shortcuts for yes/no
        self.bind_all("y", lambda _: self._answer(True)  if self._yes_btn["state"] != "disabled" else None)
        self.bind_all("n", lambda _: self._answer(False) if self._no_btn["state"] != "disabled" else None)

    def show_question(self, number: int, question: str, candidates: int):
        self._asked = number
        self._total_candidates = candidates
        self._q_lbl.config(text=f"Q {number}")
        self._cand_lbl.config(
            text=f"{candidates} condition{'s' if candidates != 1 else ''} still possible"
        )
        self._progress["value"] = min(20, number)
        self._wait_dots.stop()
        self._question_lbl.config(text=question, fg=WHITE)
        self._set_buttons_enabled(True)

    def record_answer(self, question: str, answer: bool):
        row = tk.Frame(self._chat_inner, bg=DARK_BG)
        row.pack(fill="x", pady=3, padx=8)

        q_lbl = tk.Label(row,
                          text=f"Q{self._asked}: {question}",
                          bg=TEAL_FAINT, fg=OFF_WHITE,
                          font=FONT_SMALL, anchor="w",
                          wraplength=440, justify="left",
                          padx=10, pady=6)
        q_lbl.pack(fill="x")

        ans_text = "✓  Yes" if answer else "✗  No"
        ans_col  = GREEN   if answer else RED_SOFT
        a_lbl = tk.Label(row,
                          text=ans_text,
                          bg=PANEL_BG, fg=ans_col,
                          font=FONT_LABEL, anchor="e",
                          padx=10, pady=4)
        a_lbl.pack(fill="x")

        self._chat.update_idletasks()
        self._chat.yview_moveto(1.0)

    def set_waiting(self):
        self._set_buttons_enabled(False)
        self._question_lbl.config(text="Processing answer…", fg=MUTED)
        self._wait_dots.start()

    def _answer(self, val: bool):
        self._set_buttons_enabled(False)
        self._on_answer(val)

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._yes_btn.config(state=state)
        self._no_btn.config(state=state)

    def _on_chat_resize(self, event):
        self._chat.configure(scrollregion=self._chat.bbox("all"))

    def _on_canvas_resize(self, event):
        self._chat.itemconfig(self._chat_win, width=event.width)


class ResultPage(tk.Frame):
    def __init__(self, master, data: dict, on_new, on_save):
        super().__init__(master, bg=DARK_BG)
        self._on_new  = on_new
        self._on_save = on_save
        self._build(data)

    def _build(self, data: dict):
        disease    = data.get("disease", "unknown")
        confidence = min(100.0, data.get("confidence", 0.0))
        level      = data.get("confidence_level", "Uncertain")
        desc       = data.get("description", "")
        tests      = data.get("tests", [])
        conclusive = data.get("is_conclusive", False)
        confirmed  = data.get("confirmed_symptoms", [])
        other_syms = data.get("other_symptoms", [])

        tk.Label(self, text="Diagnosis Result",
                 bg=DARK_BG, fg=GOLD, font=FONT_TITLE).pack(pady=(22, 4))

        if not conclusive:
            self._build_inconclusive()
            return

        main_card = _card(self)
        main_card.pack(padx=40, pady=8, fill="x")

        name_row = tk.Frame(main_card, bg=PANEL_BG)
        name_row.pack(fill="x", padx=20, pady=(18, 4))

        tk.Label(name_row, text="Condition:",
                 bg=PANEL_BG, fg=MUTED, font=FONT_LABEL,
                 width=12, anchor="w").pack(side="left")
        tk.Label(name_row,
                 text=disease.replace("_", " ").title(),
                 bg=PANEL_BG, fg=WHITE,
                 font=("Consolas", 16, "bold")).pack(side="left")

        conf_row = tk.Frame(main_card, bg=PANEL_BG)
        conf_row.pack(fill="x", padx=20, pady=4)
        tk.Label(conf_row, text="Confidence:",
                 bg=PANEL_BG, fg=MUTED, font=FONT_LABEL,
                 width=12, anchor="w").pack(side="left")

        bar_frame = tk.Frame(conf_row, bg=BORDER, height=14, width=260)
        bar_frame.pack(side="left")
        bar_frame.pack_propagate(False)

        bar_col = GREEN if confidence >= 75 else (GOLD if confidence >= 50 else RED_SOFT)
        fill_w  = int(260 * confidence / 100)
        bar_fill = tk.Frame(bar_frame, bg=bar_col, height=14, width=fill_w)
        bar_fill.place(x=0, y=0)

        tk.Label(conf_row,
                 text=f"  {confidence:.1f}%  [{level}]",
                 bg=PANEL_BG, fg=bar_col, font=FONT_LABEL).pack(side="left")

        if desc:
            sep = tk.Frame(main_card, bg=BORDER, height=1)
            sep.pack(fill="x", padx=20, pady=10)
            tk.Label(main_card, text=desc,
                     bg=PANEL_BG, fg=OFF_WHITE, font=FONT_BODY,
                     wraplength=500, justify="left",
                     padx=20).pack(anchor="w", pady=(0, 12))

        lower = tk.Frame(self, bg=DARK_BG)
        lower.pack(padx=40, pady=4, fill="x")

        if confirmed:
            left_card = _card(lower)
            left_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
            tk.Label(left_card, text="✓  Your Matched Symptoms",
                     bg=PANEL_BG, fg=GREEN, font=FONT_LABEL).pack(
                         anchor="w", padx=14, pady=(12, 4))
            for s in confirmed:
                tk.Label(left_card,
                         text=f"  • {s.replace('_', ' ').title()}",
                         bg=PANEL_BG, fg=OFF_WHITE, font=FONT_BODY).pack(
                             anchor="w", padx=14)
            tk.Frame(left_card, bg=PANEL_BG, height=12).pack()

        if tests:
            right_card = _card(lower)
            right_card.pack(side="left", fill="both", expand=True, padx=(6, 0))
            tk.Label(right_card, text="⬡  Recommended Tests",
                     bg=PANEL_BG, fg=TEAL, font=FONT_LABEL).pack(
                         anchor="w", padx=14, pady=(12, 4))
            for t in tests:
                tname = t["test"].replace("_", " ").title()
                conf  = t["confirms"].replace("_", " ")
                tk.Label(right_card, text=f"  • {tname}",
                         bg=PANEL_BG, fg=OFF_WHITE, font=FONT_BODY).pack(
                             anchor="w", padx=14)
                tk.Label(right_card, text=f"    ↳ {conf}",
                         bg=PANEL_BG, fg=MUTED, font=FONT_MONO).pack(
                             anchor="w", padx=14)
            tk.Frame(right_card, bg=PANEL_BG, height=12).pack()

        if other_syms:
            other_card = _card(self)
            other_card.pack(padx=40, pady=4, fill="x")
            tk.Label(other_card,
                     text="○  Other symptoms associated with this condition:",
                     bg=PANEL_BG, fg=MUTED, font=FONT_LABEL).pack(
                         anchor="w", padx=14, pady=(10, 4))
            txt = ",  ".join(s.replace("_", " ").title() for s in other_syms)
            tk.Label(other_card, text=txt,
                     bg=PANEL_BG, fg=MUTED, font=FONT_SMALL,
                     wraplength=500, justify="left",
                     padx=14).pack(anchor="w", pady=(0, 10))

        disc = _card(self)
        disc.pack(padx=40, pady=8, fill="x")
        tk.Label(disc,
                 text="⚠  DISCLAIMER: This is not a substitute for professional "
                      "medical advice.\n   Please consult a qualified doctor to "
                      "confirm any diagnosis.",
                 bg=PANEL_BG, fg=MUTED, font=FONT_SMALL,
                 justify="left", padx=14).pack(pady=10)

        btn_row = tk.Frame(self, bg=DARK_BG)
        btn_row.pack(pady=16)

        tk.Button(btn_row, text="⟳  New Consultation",
                  bg=TEAL, fg=DARK_BG, font=FONT_LABEL,
                  relief="flat", cursor="hand2",
                  activebackground=TEAL_DARK,
                  activeforeground=DARK_BG,
                  padx=18, pady=8,
                  command=self._on_new).pack(side="left", padx=10)

        tk.Button(btn_row, text="↓  Save Session Log",
                  bg=PANEL_BG, fg=TEAL, font=FONT_LABEL,
                  relief="flat", cursor="hand2",
                  highlightbackground=TEAL,
                  highlightthickness=1,
                  padx=18, pady=8,
                  command=self._on_save).pack(side="left", padx=10)

    def _build_inconclusive(self):
        card = _card(self)
        card.pack(padx=60, pady=30, fill="x")
        tk.Label(card, text="Inconclusive",
                 bg=PANEL_BG, fg=RED_SOFT,
                 font=("Consolas", 20, "bold")).pack(pady=(20, 8))
        tk.Label(card,
                 text=(
                     "Not enough information to reach a confident diagnosis.\n"
                     "Please consult a doctor for further evaluation."
                 ),
                 bg=PANEL_BG, fg=OFF_WHITE, font=FONT_BODY,
                 justify="center").pack(padx=30, pady=(0, 20))
        tk.Button(self, text="⟳  Start Over",
                  bg=TEAL, fg=DARK_BG, font=FONT_LABEL,
                  relief="flat", cursor="hand2",
                  activebackground=TEAL_DARK,
                  padx=18, pady=8,
                  command=self._on_new).pack(pady=14)


class HeaderBar(tk.Frame):
    # top bar shown on every page
    def __init__(self, master):
        super().__init__(master, bg=SIDEBAR_BG, height=44)
        self.pack_propagate(False)
        self._build()

    def _build(self):
        tk.Label(self, text=" ⬡ Medical Expert System",
                 bg=SIDEBAR_BG, fg=WHITE,
                 font=("Consolas", 12, "bold")).pack(side="left", padx=16)

        badge_row = tk.Frame(self, bg=SIDEBAR_BG)
        badge_row.pack(side="right", padx=16)
        for text, col in [("Python", GREEN), ("Prolog", TEAL), ("Lisp", GOLD)]:
            tk.Label(badge_row, text=text, bg=col, fg=DARK_BG,
                     font=("Consolas", 8, "bold"),
                     padx=5, pady=1).pack(side="left", padx=3)


class MedicalApp(tk.Tk):
    # main app controller - manages pages and wires GUI to consultation logic

    def __init__(self, prolog_dir: Path, lisp_dir: Path = None):
        super().__init__()
        self._prolog_dir = prolog_dir
        self._lisp_dir   = lisp_dir

        self.title("Medical Expert System — BCS 222")
        self.geometry("700x720")
        self.minsize(620, 580)
        self.configure(bg=DARK_BG)
        _style_root(self)

        self._header = HeaderBar(self)
        self._header.pack(fill="x")

        self._container = tk.Frame(self, bg=DARK_BG)
        self._container.pack(fill="both", expand=True)

        self._consultation = None
        self._session      = None
        self._current_page = None
        self._qa_page      = None
        self._patient_name = ""

        self._show_welcome()

    def _clear(self):
        if self._current_page:
            self._current_page.destroy()
        self._current_page = None

    def _show_page(self, page: tk.Frame):
        self._clear()
        self._current_page = page
        page.pack(fill="both", expand=True)

    def _show_welcome(self):
        self._show_page(WelcomePage(self._container, self._start_consultation))

    def _start_consultation(self, name: str, age: Optional[int]):
        self._patient_name = name
        try:
            from consultation import create_consultation  # type: ignore
        except ImportError as e:
            messagebox.showerror("Import Error",
                                  f"Could not load consultation module:\n{e}")
            return

        try:
            self._consultation, self._session = create_consultation(
                name, self._prolog_dir, age, lisp_dir=self._lisp_dir
            )
        except Exception as e:
            messagebox.showerror("Startup Error",
                                  f"Failed to initialise Prolog engine:\n{e}")
            return

        # register all callbacks before start() is called so no events are missed
        from consultation import ConsultationEvent  # type: ignore
        self._consultation.on(ConsultationEvent.QUESTION_READY,
                               self._on_question_ready)
        self._consultation.on(ConsultationEvent.STATUS_UPDATE,
                               self._on_status_update)
        self._consultation.on(ConsultationEvent.DIAGNOSIS_READY,
                               self._on_result)
        self._consultation.on(ConsultationEvent.ERROR, self._on_error)

        self._show_intake(name)

    def _show_intake(self, name: str):
        page = IntakePage(self._container, name,
                          on_done=self._process_intake,
                          on_skip=self._skip_intake)
        self._intake_page = page
        self._show_page(page)

    def _process_intake(self, raw_text: str):
        def _worker():
            if not raw_text:
                self.after(0, self._skip_intake)
                return
            result  = self._consultation.preload_symptoms(raw_text)
            found   = result.get("found", [])
            denied  = result.get("negated", [])
            self.after(0, lambda: self._intake_done(found, denied))

        self._consultation.start()
        threading.Thread(target=_worker, daemon=True).start()

    def _intake_done(self, found: list, denied: list):
        if not found and not denied:
            self._consultation.intake_complete()
            self._start_qa()
            return
        page = ConfirmPage(self._container, found, denied,
                            on_accept=lambda: self._accept_intake(found, denied),
                            on_reject=self._reject_intake)
        self._show_page(page)

    def _accept_intake(self, found: list, denied: list):
        for s in found:
            self._session.record_answer(
                symptom=s,
                question_text=f"(from description: {s.replace('_',' ')})",
                answer=True, candidates_remaining=20, from_intake=True
            )
        for s in denied:
            self._session.record_answer(
                symptom=s,
                question_text=f"(from description: no {s.replace('_',' ')})",
                answer=False, candidates_remaining=20, from_intake=True
            )
        self._consultation.intake_complete()
        self._start_qa()

    def _reject_intake(self):
        # undo the Prolog facts that were asserted during intake
        for s in self._consultation._preloaded:
            try:
                list(self._consultation._bridge._prolog.query(
                    f"retract(diagnosis_rules:symptom({s}))"))
                list(self._consultation._bridge._prolog.query(
                    f"retract(diagnosis_rules:asked({s}))"))
            except Exception:
                pass
        for s in self._consultation._preloaded_denied:
            try:
                list(self._consultation._bridge._prolog.query(
                    f"retract(diagnosis_rules:denied({s}))"))
                list(self._consultation._bridge._prolog.query(
                    f"retract(diagnosis_rules:asked({s}))"))
            except Exception:
                pass
        self._consultation._preloaded.clear()
        self._consultation._preloaded_denied.clear()
        self._consultation.intake_complete()
        self._start_qa()

    def _skip_intake(self):
        if not self._consultation._session.is_active:
            self._consultation.start()
        self._consultation.intake_complete()
        self._start_qa()

    def _start_qa(self):
        qa_page = QAPage(self._container, on_answer=self._submit_answer)
        self._qa_page = qa_page
        self._show_page(qa_page)
        qa_page.set_waiting()

    def _on_question_ready(self, data: dict):
        # called from the reasoning thread, so schedule on main thread
        # buffer the data in case the QA page isn't rendered yet
        self._pending_question = data
        self.after(0, self._flush_pending_question)

    def _flush_pending_question(self):
        data = getattr(self, "_pending_question", None)
        if data is None:
            return
        if self._qa_page and self._qa_page.winfo_exists():
            self._pending_question = None
            self._display_question(data)
        else:
            self.after(50, self._flush_pending_question)

    def _on_status_update(self, data: dict):
        candidates = data.get("candidates", [])
        if candidates and self._qa_page and self._qa_page.winfo_exists():
            self.after(0, lambda: self._qa_page._cand_lbl.config(
                text=f"{len(candidates)} condition{'s' if len(candidates)!=1 else ''} still possible"
            ))

    def _display_question(self, data: dict):
        if self._qa_page and self._qa_page.winfo_exists():
            cc = data.get("candidate_count")
            cands = cc if cc is not None else self._qa_page._total_candidates
            self._qa_page.show_question(
                number     = data.get("number", 1),
                question   = data.get("question", ""),
                candidates = cands if isinstance(cands, int) else len(cands)
            )

    def _submit_answer(self, response: bool):
        if self._qa_page:
            q_text = self._qa_page._question_lbl.cget("text")
            self._qa_page.record_answer(q_text, response)
            self._qa_page.set_waiting()
        self._consultation.answer(response)

    def _on_result(self, data: dict):
        self.after(0, lambda: self._show_result(data))

    def _show_result(self, data: dict):
        page = ResultPage(self._container, data,
                           on_new=self._new_consultation,
                           on_save=lambda: self._save_session())
        self._show_page(page)

    def _on_error(self, data: dict):
        msg = data.get("message", "Unknown error")
        self.after(0, lambda: messagebox.showerror("System Error", msg))

    def _new_consultation(self):
        self._consultation = None
        self._session      = None
        self._qa_page      = None
        self._show_welcome()

    def _save_session(self):
        if not self._session:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"session_{self._session.session_id}.json"
        )
        if path:
            try:
                self._session.export_json(path)
                messagebox.showinfo("Saved", f"Session saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))


def main():
    base       = Path(__file__).resolve().parent
    prolog_dir = base / "src" / "prolog"
    lisp_dir   = base / "src" / "lisp"

    if not prolog_dir.exists():
        import tkinter.messagebox as mb
        mb.showerror(
            "Missing Files",
            f"Prolog directory not found:\n{prolog_dir}\n\n"
            "Make sure gui.py is in the project root alongside main.py."
        )
        return

    lisp_dir = lisp_dir if lisp_dir.exists() else None
    app = MedicalApp(prolog_dir=prolog_dir, lisp_dir=lisp_dir)
    app.mainloop()


if __name__ == "__main__":
    main()