# interface.py
# Medical Expert System - BCS 222 Programming Paradigms
# Terminal UI — handles all display and input. Runs on the main thread.

from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from typing import Optional

_BASE = Path(__file__).resolve().parent
for _p in [_BASE, _BASE.parent, _BASE.parent.parent / 'integration',
           _BASE.parent.parent / 'src' / 'oop']:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from session import SessionState, ConfidenceLevel
from consultation import Consultation, ConsultationEvent, create_consultation

# ----------------------------------------------------------------
# DISPLAY CONSTANTS
# ----------------------------------------------------------------

WIDTH       = 56
BORDER      = "=" * WIDTH
THIN_BORDER = "-" * WIDTH

CONFIDENCE_COLOURS = {
    ConfidenceLevel.HIGH:      "\033[92m",  # green
    ConfidenceLevel.MODERATE:  "\033[93m",  # yellow
    ConfidenceLevel.LOW:       "\033[91m",  # red
    ConfidenceLevel.UNCERTAIN: "\033[90m",  # grey
}
RESET = "\033[0m"
BOLD  = "\033[1m"
CYAN  = "\033[96m"
WHITE = "\033[97m"


def _supports_colour() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    if _supports_colour():
        return f"{code}{text}{RESET}"
    return text


# ----------------------------------------------------------------
# PRINT HELPERS
# ----------------------------------------------------------------

def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _banner():
    print(_c(BORDER, CYAN))
    print(_c(f"{'Medical Expert System':^{WIDTH}}", BOLD + WHITE))
    print(_c(f"{'BCS 222 — Programming Paradigms':^{WIDTH}}", WHITE))
    print(_c(BORDER, CYAN))
    print()


def _section(title: str):
    print()
    print(_c(THIN_BORDER, CYAN))
    print(_c(f"  {title}", BOLD))
    print(_c(THIN_BORDER, CYAN))


def _print_question(number: int, question: str, candidates: int):
    print()
    print(_c(f"  Question {number}", BOLD))
    print(f"  {question}")
    print(_c(f"  [{candidates} condition(s) still possible]", "\033[90m"))


def _print_result(data: dict):
    disease    = data.get("disease", "unknown")
    confidence = data.get("confidence", 0.0)
    level_str  = data.get("confidence_level", "Uncertain")
    desc       = data.get("description", "")
    tests      = data.get("tests", [])
    conclusive = data.get("is_conclusive", False)
    confirmed  = data.get("confirmed_symptoms", [])
    other      = data.get("other_symptoms", [])

    print()
    print(_c(BORDER, CYAN))
    print(_c(f"{'DIAGNOSIS RESULT':^{WIDTH}}", BOLD + WHITE))
    print(_c(BORDER, CYAN))

    if not conclusive:
        print(_c(f"\n  Result: Inconclusive", "\033[91m"))
        print(  f"  Not enough information to make a confident diagnosis.")
        print(  f"  Please consult a doctor for further evaluation.")
        print()
        print(_c(BORDER, CYAN))
        return

    try:
        level_enum = ConfidenceLevel(level_str)
        colour = CONFIDENCE_COLOURS.get(level_enum, "")
    except ValueError:
        colour = ""

    disease_display = disease.replace("_", " ").title()
    print()
    print(f"  {'Condition':<14}: {_c(disease_display, BOLD)}")
    print(f"  {'Confidence':<14}: {_c(f'{confidence:.1f}%  [{level_str}]', colour)}")
    print()
    print(f"  {'About':<14}: {desc}")

    if confirmed:
        print()
        print(_c("  Symptoms you reported:", BOLD))
        for s in confirmed:
            print(_c(f"    ✓  {s.replace('_', ' ').title()}", "\033[92m"))

    if other:
        print()
        print(_c("  Other symptoms associated with this condition:", BOLD))
        for s in other:
            print(_c(f"    •  {s.replace('_', ' ').title()}", "\033[90m"))
        print(_c("  If you experience any of the above, seek medical advice.", "\033[90m"))

    if tests:
        print()
        print(_c(f"  Recommended tests:", BOLD))
        for t in tests:
            test_name = t['test'].replace("_", " ").title()
            confirms  = t['confirms'].replace("_", " ")
            print(f"    •  {test_name}")
            print(_c(f"       confirms: {confirms}", "\033[90m"))

    print()
    print(_c("  DISCLAIMER: This system is not a substitute for", "\033[90m"))
    print(_c("  professional medical advice. Please consult a", "\033[90m"))
    print(_c("  qualified doctor to confirm any diagnosis.", "\033[90m"))
    print()
    print(_c(BORDER, CYAN))


def _print_session_summary(consultation: Consultation):
    session = consultation.session
    log     = session.log
    intake  = log._intake_count
    asked   = log.asked_question_count
    _section("Consultation Summary")
    print(f"  Patient   : {session.patient_name}")
    print(f"  Session   : {session.session_id}")
    print(f"  Questions : {asked}")
    if intake > 0:
        print(f"  From desc : {intake} symptom(s) from your description")
    print(f"  Confirmed : {', '.join(session.record.confirmed_symptoms) or 'none'}")
    print(f"  Denied    : {', '.join(session.record.denied_symptoms) or 'none'}")
    print()


# ----------------------------------------------------------------
# INPUT HELPERS
# ----------------------------------------------------------------

def _read_yes_no() -> bool:
    while True:
        try:
            raw = input(_c("  Your answer (yes / no): ", BOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Consultation cancelled.")
            sys.exit(0)
        if raw in ("yes", "y"):
            return True
        if raw in ("no", "n"):
            return False
        print(_c("  Please type  yes  or  no.", "\033[91m"))


def _read_name() -> str:
    while True:
        try:
            name = input("  Your name: ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        if name:
            return name
        print("  Name cannot be empty.")


def _read_age() -> Optional[int]:
    try:
        raw = input("  Your age (press Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
    if not raw:
        return None
    try:
        age = int(raw)
        if 0 < age < 130:
            return age
    except ValueError:
        pass
    return None


# ----------------------------------------------------------------
# MAIN INTERFACE CLASS
# ----------------------------------------------------------------

class MedicalInterface:
    # runs on the main thread and delegates all logic to Consultation
    # flow: free-text intake -> confirmed symptoms -> yes/no Q&A -> diagnosis

    def __init__(self, prolog_dir: Path, lisp_dir: Path = None):
        self._prolog_dir   = prolog_dir
        self._lisp_dir     = lisp_dir
        self._consultation: Optional[Consultation] = None
        self._last_q_data:  Optional[dict]         = None
        self._result_data:  Optional[dict]         = None
        self._candidates = 20  # start with all 20 diseases

    # ----------------------------------------------------------------
    # ENTRY POINT
    # ----------------------------------------------------------------

    def run(self):
        _clear()
        _banner()
        self._show_welcome()

        while True:
            name = _read_name()
            age  = _read_age()
            self._run_consultation(name, age)
            if not self._ask_another():
                break

        self._show_goodbye()

    # ----------------------------------------------------------------
    # CONSULTATION FLOW
    # ----------------------------------------------------------------

    def _run_consultation(self, name: str, age: Optional[int]):
        print()
        print(_c(f"  Starting consultation for {name}...", "\033[90m"))
        time.sleep(0.4)

        self._consultation, session = create_consultation(
            name, self._prolog_dir, age, lisp_dir=self._lisp_dir
        )

        # register all callbacks before starting the reasoning thread to avoid
        # a race where a fast diagnosis fires before the handler is registered
        self._result_data = None

        def _on_result_early(data: dict):
            self._result_data = data

        self._consultation.on(ConsultationEvent.QUESTION_READY,  self._on_question_ready)
        self._consultation.on(ConsultationEvent.STATUS_UPDATE,   self._on_status_update)
        self._consultation.on(ConsultationEvent.ERROR,           self._on_error)
        self._consultation.on(ConsultationEvent.DIAGNOSIS_READY, _on_result_early)

        self._consultation.start()
        self._free_text_intake()
        self._question_loop()

        if self._result_data:
            _print_result(self._result_data)
            _print_session_summary(self._consultation)
            self._offer_save(session)

    def _free_text_intake(self) -> list[str]:
        # asks the patient to describe symptoms in plain text, Lisp extracts them,
        # patient confirms before they get asserted into Prolog
        print()
        print(_c(THIN_BORDER, CYAN))
        print(_c("  Describe Your Symptoms", BOLD))
        print(_c(THIN_BORDER, CYAN))
        print()
        print("  Please describe how you are feeling in your own words.")
        print(_c("  (or press Enter to skip to yes/no questions)", "\033[90m"))
        print()

        try:
            raw = input(_c("  Your symptoms: ", BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            return []

        if not raw:
            self._consultation.intake_complete()
            return []

        print()
        print(_c("  Processing...", "\033[90m"))
        result  = self._consultation.preload_symptoms(raw)
        found   = result.get("found",   [])
        negated = result.get("negated", [])

        if not found and not negated:
            print(_c("  No specific symptoms detected in your description.", "\033[93m"))
            print(  "  We will ask you yes/no questions instead.")
            print()
            self._consultation.intake_complete()
            return []

        print()
        if found:
            print(_c("  Symptoms detected in your description:", BOLD))
            for s in found:
                print(_c(f"    + {s.replace('_', ' ').title()}", "\033[92m"))

        if negated:
            print(_c("  Symptoms you indicated you do NOT have:", BOLD))
            for s in negated:
                print(_c(f"    - {s.replace('_', ' ').title()}", "\033[91m"))

        print()

        try:
            confirm = input(_c("  Is this correct? (yes / no): ", BOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return []

        if confirm not in ("yes", "y"):
            print(_c("  No problem — we will ask you questions instead.", "\033[90m"))
            print()
            # retract the Prolog facts we just asserted — without this, symptom/1 facts
            # stay in Prolog and inflate confidence even though the patient rejected them
            for s in self._consultation._preloaded:
                try:
                    list(self._consultation._bridge._prolog.query(f"retract(diagnosis_rules:symptom({s}))"))
                    list(self._consultation._bridge._prolog.query(f"retract(diagnosis_rules:asked({s}))"))
                except Exception:
                    pass
            for s in self._consultation._preloaded_denied:
                try:
                    list(self._consultation._bridge._prolog.query(f"retract(diagnosis_rules:denied({s}))"))
                    list(self._consultation._bridge._prolog.query(f"retract(diagnosis_rules:asked({s}))"))
                except Exception:
                    pass
            self._consultation._preloaded.clear()
            self._consultation._preloaded_denied.clear()
            self._consultation.intake_complete()
            return []

        # log intake symptoms in the session so they appear in MedicalRecord
        # but are flagged so they don't inflate the displayed question count
        for s in found:
            self._consultation._session.record_answer(
                symptom              = s,
                question_text        = f"(from your description: {s.replace(chr(95),' ')})",
                answer               = True,
                candidates_remaining = self._candidates,
                from_intake          = True
            )
        for s in negated:
            self._consultation._session.record_answer(
                symptom              = s,
                question_text        = f"(from your description: no {s.replace(chr(95),' ')})",
                answer               = False,
                candidates_remaining = self._candidates,
                from_intake          = True
            )

        total = len(found) + len(negated)
        print(_c(f"  Great — {total} symptom(s) recorded from your description.", "\033[92m"))
        print(_c("  We will now ask about any remaining symptoms.", "\033[90m"))
        print()

        try:
            cands = list(self._consultation._bridge._prolog.query("candidate(D)"))
            self._candidates = len(cands)
        except Exception:
            pass

        self._consultation.intake_complete()
        return found

    def _question_loop(self):
        # blocks on the main thread, waits for questions from the reasoning thread,
        # collects answers and passes them back
        self._result_data = None
        result_received   = [False]

        def on_result(data: dict):
            self._result_data    = data
            result_received[0]   = True

        self._consultation.on(ConsultationEvent.DIAGNOSIS_READY, on_result)

        while not result_received[0]:
            got_q = self._consultation.wait_for_question(timeout=15.0)

            if result_received[0]:
                break

            if not got_q:
                if self._consultation.is_done:
                    break
                continue

            _print_question(
                number     = self._last_q_data.get("number", "?"),
                question   = self._last_q_data.get("question", ""),
                candidates = self._candidates
            )

            response = _read_yes_no()
            self._consultation.answer(response)

        self._consultation.wait_for_completion(timeout=10.0)

    # ----------------------------------------------------------------
    # EVENT CALLBACKS (called from reasoning thread)
    # ----------------------------------------------------------------

    def _on_question_ready(self, data: dict):
        self._last_q_data = data
        if "candidates" in data:
            self._candidates = data["candidates"]

    def _on_status_update(self, data: dict):
        candidates = data.get("candidates", [])
        if candidates:
            self._candidates = len(candidates)

    def _on_error(self, data: dict):
        print(_c(f"\n  System error: {data.get('message', 'Unknown')}", "\033[91m"))

    # ----------------------------------------------------------------
    # AUXILIARY UI
    # ----------------------------------------------------------------

    def _show_welcome(self):
        _section("Welcome")
        print("  This system will ask you a series of yes/no")
        print("  questions about your symptoms and suggest a")
        print("  possible diagnosis.")
        print()
        print(_c("  Note: This is NOT a substitute for a real", "\033[93m"))
        print(_c("  doctor. Always seek professional advice.", "\033[93m"))
        print()
        _section("Patient Details")

    def _show_goodbye(self):
        print()
        print(_c(BORDER, CYAN))
        print(_c(f"{'Thank you for using the Medical Expert System':^{WIDTH}}", WHITE))
        print(_c(f"{'Please consult a doctor for medical advice':^{WIDTH}}", "\033[90m"))
        print(_c(BORDER, CYAN))
        print()

    def _ask_another(self) -> bool:
        print()
        try:
            raw = input(_c("  Start another consultation? (yes / no): ", BOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return raw in ("yes", "y")

    def _offer_save(self, session):
        print()
        try:
            raw = input(_c("  Save session log? (yes / no): ", BOLD)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if raw in ("yes", "y"):
            filename = f"session_{session.session_id}.json"
            try:
                session.export_json(filename)
                print(_c(f"  Saved to {filename}", "\033[92m"))
            except Exception as e:
                print(_c(f"  Could not save: {e}", "\033[91m"))


# ----------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------

def main():
    base       = Path(__file__).parent.parent
    prolog_dir = base / "src" / "prolog"
    lisp_dir   = base / "src" / "lisp"

    if not prolog_dir.exists():
        base       = Path(__file__).parent
        prolog_dir = base / "src" / "prolog"
        lisp_dir   = base / "src" / "lisp"

    if not prolog_dir.exists():
        print(f"ERROR: Prolog directory not found: {prolog_dir}")
        sys.exit(1)

    interface = MedicalInterface(prolog_dir, lisp_dir=lisp_dir)
    interface.run()


if __name__ == "__main__":
    main()