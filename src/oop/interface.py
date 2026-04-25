# interface.py
# Medical Expert System - BCS 222 Programming Paradigms
# Terminal user interface. Handles all input/output.
# Runs on the MAIN thread. The reasoning engine runs on a background
# thread inside Consultation.
#
# Design:
#   - Zero business logic lives here
#   - All decisions are delegated to Consultation / session
#   - This file only knows how to display and collect input

from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure integration/ and src/oop/ are always on the path
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

WIDTH        = 56
BORDER       = "=" * WIDTH
THIN_BORDER  = "-" * WIDTH

CONFIDENCE_COLOURS = {
    ConfidenceLevel.HIGH:      "\033[92m",   # green
    ConfidenceLevel.MODERATE:  "\033[93m",   # yellow
    ConfidenceLevel.LOW:       "\033[91m",   # red
    ConfidenceLevel.UNCERTAIN: "\033[90m",   # grey
}
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"


def _supports_colour() -> bool:
    """Check if terminal supports ANSI colour codes."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    """Wrap text in colour code if terminal supports it."""
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

    # Map level string back to enum for colour
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

    # Symptoms you reported
    if confirmed:
        print()
        print(_c("  Symptoms you reported:", BOLD))
        for s in confirmed:
            print(_c(f"    ✓  {s.replace('_', ' ').title()}", "\033[92m"))

    # Other known symptoms of this disease the patient didn't confirm
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
    session  = consultation.session
    log      = session.log
    intake   = log._intake_count
    asked    = log.asked_question_count
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
    """Read a yes/no answer. Loops on invalid input."""
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
    """Read patient name, reject empty input."""
    while True:
        try:
            name = input("  Your name: ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        if name:
            return name
        print("  Name cannot be empty.")


def _read_age() -> Optional[int]:
    """Read optional age - Enter to skip."""
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
    """
    Terminal interface for the Medical Expert System.

    Runs on the main thread.
    Registers event callbacks on the Consultation object so
    the reasoning thread can push questions and results to it.

    Flow:
        1. Patient describes symptoms in free text (Lisp processes)
        2. System confirms extracted symptoms
        3. Yes/no question loop for remaining unknowns
        4. Diagnosis presented
    """

    def __init__(self, prolog_dir: Path, lisp_dir: Path = None):
        self._prolog_dir   = prolog_dir
        self._lisp_dir     = lisp_dir
        self._consultation: Optional[Consultation] = None
        self._last_q_data: Optional[dict] = None
        self._result_data: Optional[dict] = None
        self._candidates  = 20  # start with all 20 diseases

    # ----------------------------------------------------------------
    # ENTRY POINT
    # ----------------------------------------------------------------

    def run(self):
        """Main entry point - runs the full application loop."""
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
        """Run one full consultation for a named patient."""
        print()
        print(_c(f"  Starting consultation for {name}...", "\033[90m"))
        time.sleep(0.4)

        # Create consultation + session
        self._consultation, session = create_consultation(
            name, self._prolog_dir, age, lisp_dir=self._lisp_dir
        )

        # Register ALL callbacks BEFORE starting the reasoning thread.
        # DIAGNOSIS_READY registered here (not inside _question_loop) to eliminate
        # the race window where a fast diagnosis fires before _question_loop() has
        # a chance to register its handler.
        self._result_data = None

        def _on_result_early(data: dict):
            self._result_data = data

        self._consultation.on(
            ConsultationEvent.QUESTION_READY,
            self._on_question_ready
        )
        self._consultation.on(
            ConsultationEvent.STATUS_UPDATE,
            self._on_status_update
        )
        self._consultation.on(
            ConsultationEvent.ERROR,
            self._on_error
        )
        self._consultation.on(
            ConsultationEvent.DIAGNOSIS_READY,
            _on_result_early
        )

        # Start reasoning thread (resets Prolog session)
        self._consultation.start()

        # Free-text symptom intake AFTER start so pre-loaded symptoms survive into the Q&A loop
        self._free_text_intake()

        # Main question-answer loop on this thread
        self._question_loop()

        # Show result
        if self._result_data:
            _print_result(self._result_data)
            _print_session_summary(self._consultation)

            # Offer to save session log
            self._offer_save(session)

    def _free_text_intake(self) -> list[str]:
        """
        Ask patient to describe symptoms in natural language.
        Lisp processes the text and extracts symptom atoms.
        Patient confirms before they are asserted into Prolog.
        Returns list of pre-loaded symptom atoms.
        """
        print()
        print(_c(THIN_BORDER, CYAN))
        print(_c("  Describe Your Symptoms", BOLD))
        print(_c(THIN_BORDER, CYAN))
        print()
        print("  Please describe how you are feeling in your own words.")
        print(_c("  (or press Enter to skip to yes/no questions)", "[90m"))
        print()

        try:
            raw = input(_c("  Your symptoms: ", BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            return []

        if not raw:
            # No text entered - unblock reasoning thread immediately
            self._consultation.intake_complete()
            return []

        # Send to Lisp for processing
        print()
        print(_c("  Processing...", "[90m"))
        result = self._consultation.preload_symptoms(raw)
        found   = result.get("found",   [])
        negated = result.get("negated", [])

        if not found and not negated:
            print(_c("  No specific symptoms detected in your description.", "[93m"))
            print(  "  We will ask you yes/no questions instead.")
            print()
            self._consultation.intake_complete()  # unblock reasoning thread
            return []

        # Display what was found
        print()
        if found:
            print(_c("  Symptoms detected in your description:", BOLD))
            for s in found:
                display = s.replace("_", " ").title()
                print(_c(f"    + {display}", "[92m"))

        if negated:
            print(_c("  Symptoms you indicated you do NOT have:", BOLD))
            for s in negated:
                display = s.replace("_", " ").title()
                print(_c(f"    - {display}", "[91m"))

        print()

        # Ask patient to confirm
        try:
            confirm = input(
                _c("  Is this correct? (yes / no): ", BOLD)
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return []

        if confirm not in ("yes", "y"):
            print(_c("  No problem — we will ask you questions instead.", "[90m"))
            print()
            # Retract Prolog facts asserted by preload_symptoms() before clearing Python lists.
            # Without this, symptom/1 facts stay in Prolog and inflate confidence scores
            # even though the patient rejected the auto-detected symptoms.
            for s in self._consultation._preloaded:
                try:
                    list(self._consultation._bridge._prolog.query(
                        f"retract(diagnosis_rules:symptom({s}))"
                    ))
                    list(self._consultation._bridge._prolog.query(
                        f"retract(diagnosis_rules:asked({s}))"
                    ))
                except Exception:
                    pass
            for s in self._consultation._preloaded_denied:
                try:
                    list(self._consultation._bridge._prolog.query(
                        f"retract(diagnosis_rules:denied({s}))"
                    ))
                    list(self._consultation._bridge._prolog.query(
                        f"retract(diagnosis_rules:asked({s}))"
                    ))
                except Exception:
                    pass
            self._consultation._preloaded.clear()
            self._consultation._preloaded_denied.clear()
            self._consultation.intake_complete()
            return []

        # Record preloaded symptoms in session log, flagged as intake
        # so they appear in MedicalRecord but don't inflate question count
        for s in found:
            self._consultation._session.record_answer(
                symptom       = s,
                question_text = f"(from your description: {s.replace(chr(95),' ')})",
                answer        = True,
                candidates_remaining = self._candidates,
                from_intake   = True
            )
        for s in negated:
            self._consultation._session.record_answer(
                symptom       = s,
                question_text = f"(from your description: no {s.replace(chr(95),' ')})",
                answer        = False,
                candidates_remaining = self._candidates,
                from_intake   = True
            )

        total = len(found) + len(negated)
        print(_c(f"  Great — {total} symptom(s) recorded from your description.", "[92m"))
        print(_c("  We will now ask about any remaining symptoms.", "[90m"))
        print()
        # Update displayed candidate count to reflect pre-loaded symptoms
        try:
            cands = list(self._consultation._bridge._prolog.query("candidate(D)"))
            self._candidates = len(cands)
        except Exception:
            pass

        # Unblock reasoning thread - pre-loaded facts are now set
        self._consultation.intake_complete()
        return found

    def _question_loop(self):
        """
        Blocking loop on main thread.
        Waits for questions from reasoning thread,
        collects answers, passes them back.
        """
        self._result_data = None

        # Register result handler inside loop so we can break out when it fires
        result_received = [False]

        def on_result(data: dict):
            self._result_data = data
            result_received[0] = True

        self._consultation.on(
            ConsultationEvent.DIAGNOSIS_READY, on_result
        )

        while not result_received[0]:
            # Wait for next question from reasoning thread
            got_q = self._consultation.wait_for_question(timeout=15.0)

            if result_received[0]:
                break

            if not got_q:
                if self._consultation.is_done:
                    break
                continue

            # Display question
            _print_question(
                number     = self._last_q_data.get("number", "?"),
                question   = self._last_q_data.get("question", ""),
                candidates = self._candidates
            )

            # Collect answer on main thread (blocking)
            response = _read_yes_no()

            # Pass to reasoning thread
            self._consultation.answer(response)

        # Wait for reasoning thread to fully finish
        self._consultation.wait_for_completion(timeout=10.0)

    # ----------------------------------------------------------------
    # EVENT CALLBACKS (called from reasoning thread)
    # ----------------------------------------------------------------

    def _on_question_ready(self, data: dict):
        """Store latest question data for main thread to display."""
        self._last_q_data = data
        if "candidates" in data:
            self._candidates = data["candidates"]

    def _on_status_update(self, data: dict):
        """Update candidate count for display."""
        candidates = data.get("candidates", [])
        if candidates:
            self._candidates = len(candidates)

    def _on_error(self, data: dict):
        """Print error message."""
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
        """Ask if user wants to run another consultation."""
        print()
        try:
            raw = input(
                _c("  Start another consultation? (yes / no): ", BOLD)
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return raw in ("yes", "y")

    def _offer_save(self, session):
        """Offer to save the session log as JSON."""
        print()
        try:
            raw = input(
                _c("  Save session log? (yes / no): ", BOLD)
            ).strip().lower()
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
# STANDALONE ENTRY POINT
# ----------------------------------------------------------------

def main():
    """
    Entry point when running interface.py directly.
    Resolves the Prolog and Lisp directories relative to this file.
    """
    base = Path(__file__).parent.parent
    prolog_dir = base / "src" / "prolog"
    lisp_dir   = base / "src" / "lisp"

    if not prolog_dir.exists():
        base = Path(__file__).parent
        prolog_dir = base / "src" / "prolog"
        lisp_dir   = base / "src" / "lisp"

    if not prolog_dir.exists():
        print(f"ERROR: Prolog directory not found: {prolog_dir}")
        sys.exit(1)

    interface = MedicalInterface(prolog_dir, lisp_dir=lisp_dir)
    interface.run()


if __name__ == "__main__":
    main()