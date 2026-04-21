# ================================================================
# consultation.py
# Medical Expert System — BCS 222 Programming Paradigms
# Role: Controller layer — orchestrates the consultation flow.
#       Connects UserSession (OOP state) with PrologBridge
#       (inference engine). Neither session.py nor bridge.py
#       know about each other — this class is the glue.
#
# Paradigm justification:
#   This class demonstrates OOP's strength in managing complex
#   stateful workflows. The Consultation object encapsulates
#   the entire flow: start -> ask -> answer -> diagnose -> end.
#   It uses polymorphism-ready design so the interface layer
#   (CLI or GUI) can swap without changing this controller.
# ================================================================

from __future__ import annotations
import sys
import threading
import time
from typing import Callable, Optional
from datetime import datetime
from pathlib import Path

# Ensure integration/ and src/oop/ are always on the path
# regardless of how this module is imported
_BASE = Path(__file__).resolve().parent
for _p in [_BASE, _BASE.parent, _BASE.parent.parent / 'integration',
           _BASE.parent.parent / 'src' / 'oop']:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from session import (
    UserSession, DiagnosisResult,
    SessionState, ConfidenceLevel
)
from integration.bridge import PrologBridge
try:
    from integration.lisp_connector import LispConnector
except ImportError:
    try:
        from integration.lisp_connector import LispConnector
    except ImportError:
        LispConnector = None


# ----------------------------------------------------------------
# CONSULTATION EVENTS — for the interface layer to hook into
# ----------------------------------------------------------------

class ConsultationEvent:
    """
    Event types emitted by the Consultation controller.
    The interface layer registers callbacks for these.
    """
    QUESTION_READY  = "question_ready"   # a new question is available
    ANSWER_RECORDED = "answer_recorded"  # patient answer was processed
    DIAGNOSIS_READY = "diagnosis_ready"  # final result is available
    STATUS_UPDATE   = "status_update"    # candidate count changed
    ERROR           = "error"            # something went wrong


# ----------------------------------------------------------------
# CONSULTATION CONTROLLER
# ----------------------------------------------------------------

class Consultation:
    """
    Drives a single patient consultation from start to finish.

    Responsibilities:
      - Initialise and reset the Prolog engine via bridge
      - Feed patient answers to Prolog one step at a time
      - Receive next questions and pass them to the interface
      - Detect completion and build DiagnosisResult
      - Update UserSession after every exchange
      - Run the reasoning engine on a background thread
        (fulfils the concurrency requirement)

    Usage:
        session      = UserSession("Ahmed", age=28)
        bridge       = PrologBridge(prolog_dir)
        bridge.load()
        consultation = Consultation(session, bridge)
        consultation.start()
        # interface layer then calls consultation.answer(True/False)
    """

    def __init__(self, session: UserSession, bridge: PrologBridge,
                 lisp_dir=None):
        self._session    = session
        self._bridge     = bridge
        self._lisp       = LispConnector(lisp_dir) if (lisp_dir and LispConnector) else None
        self._preloaded: list[str] = []        # symptoms confirmed by Lisp
        self._intake_candidates: int = 15       # candidates after free-text intake
        self._preloaded_denied: list[str] = []  # symptoms denied by Lisp

        # Current pending question — set by Prolog, read by interface
        self._current_symptom:  Optional[str] = None
        self._current_question: Optional[str] = None

        # Gate — reasoning thread waits until intake is complete
        self._intake_ready     = threading.Event()
        # Update candidate count after preloaded symptoms are asserted
        self._intake_candidates = len(list(
            self._bridge._prolog.query("candidate(D)")
        ))
        self._intake_ready.set()  # default: ready immediately

        # Threading — reasoning runs on background thread
        # so the UI thread stays responsive
        self._lock            = threading.Lock()
        self._answer_event    = threading.Event()
        self._question_event  = threading.Event()
        self._done_event      = threading.Event()
        self._pending_answer: Optional[bool] = None

        # Callbacks registered by the interface layer
        self._callbacks: dict[str, list[Callable]] = {
            ConsultationEvent.QUESTION_READY:  [],
            ConsultationEvent.ANSWER_RECORDED: [],
            ConsultationEvent.DIAGNOSIS_READY: [],
            ConsultationEvent.STATUS_UPDATE:   [],
            ConsultationEvent.ERROR:           [],
        }

        # Background reasoning thread
        self._reasoning_thread: Optional[threading.Thread] = None

    # ----------------------------------------------------------------
    # EVENT SYSTEM
    # ----------------------------------------------------------------

    def on(self, event: str, callback: Callable) -> None:
        """
        Register a callback for a consultation event.
        The interface layer uses this to hook into the flow.

        Example:
            consultation.on(ConsultationEvent.QUESTION_READY,
                            lambda q: print(q['question']))
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, data: dict = None) -> None:
        """Fire all callbacks registered for this event."""
        for cb in self._callbacks.get(event, []):
            try:
                cb(data or {})
            except Exception as e:
                print(f"[Consultation] Callback error on {event}: {e}")

    # ----------------------------------------------------------------
    # LIFECYCLE
    # ----------------------------------------------------------------

    def preload_symptoms(self, raw_text: str) -> dict:
        """
        Called BEFORE start() when the patient describes symptoms
        in free text. Uses the Lisp layer to extract symptom atoms,
        asserts them into Prolog, and returns what was found so the
        interface can confirm with the patient.
        """
        if not self._lisp:
            return {"found": [], "negated": [], "source": "none"}

        result   = self._lisp.extract_for_session(raw_text)
        to_assert = result.get("to_assert", [])
        to_deny   = result.get("to_deny",   [])

        # Pre-assert into Prolog engine and mark as asked
        # so next_question/1 skips them in the Q&A loop
        for s in to_assert:
            # Use bridge query — shares same Prolog engine context
            self._bridge.query(f"assert_symptom({s})")
            self._preloaded.append(s)

        for s in to_deny:
            self._bridge.query(f"deny_symptom({s})")
            self._preloaded_denied.append(s)

        # Get source from a direct process_input call for reporting
        raw_result = self._lisp.process_input("")
        return {
            "found":   to_assert,
            "negated": to_deny,
            "source":  "lisp" if self._lisp.is_available() else "fallback"
        }

    def intake_complete(self) -> None:
        """
        Called by the interface after free-text intake is done.
        Unblocks the reasoning thread to start asking questions.
        Asserts symptoms AND marks them as asked so next_question
        never re-asks them in the Q&A loop.
        """
        for s in self._preloaded:
            # Use bridge.assert_symptom which handles asked/1 internally
            self._bridge.assert_symptom(s)
            # Belt-and-suspenders: also assert via direct query
            self._bridge.query(f"assertz(asked({s}))")

        for s in self._preloaded_denied:
            self._bridge.deny_symptom(s)
            self._bridge.query(f"assertz(asked({s}))")

        self._intake_ready.set()

    def start(self) -> None:
        """
        Start the consultation.
        Resets Prolog session, transitions UserSession to ACTIVE,
        then launches the reasoning thread which fetches the
        first question and waits for answers.
        """
        self._session.start()
        self._bridge.reset_session()

        # Clear the intake gate — reasoning thread will wait
        # until preload_symptoms() has finished and re-asserted facts
        self._intake_ready.clear()
        self._preloaded.clear()
        self._preloaded_denied.clear()

        # Launch reasoning on background thread
        self._reasoning_thread = threading.Thread(
            target=self._reasoning_loop,
            name="ReasoningThread",
            daemon=True   # thread dies if main program exits
        )
        self._reasoning_thread.start()

    def answer(self, response: bool) -> None:
        """
        Called by the interface layer when patient answers yes/no.
        Thread-safe — signals the reasoning thread to continue.

        Parameters:
            response: True = yes, False = no
        """
        if not self._session.is_active:
            # Session timed out — silently ignore late answers
            return

        with self._lock:
            self._pending_answer = response

        # Signal reasoning thread that an answer is ready
        self._answer_event.set()

    def wait_for_question(self, timeout: float = 10.0) -> bool:
        """
        Block until the reasoning thread has a new question ready.
        Returns True if a question arrived, False if timed out.
        Used by synchronous CLI interface.
        """
        result = self._question_event.wait(timeout=timeout)
        self._question_event.clear()
        return result

    def wait_for_completion(self, timeout: float = 120.0) -> bool:
        """
        Block until the consultation is fully complete.
        Returns True if completed, False if timed out.
        """
        return self._done_event.wait(timeout=timeout)

    # ----------------------------------------------------------------
    # REASONING THREAD
    # ----------------------------------------------------------------

    def _reasoning_loop(self) -> None:
        """
        Runs on the background thread.
        Fetches first question, then loops: wait for answer ->
        send to Prolog -> get next action -> emit event.

        This is the concurrency architecture the assignment requires:
        - Main thread  : handles UI (input/output)
        - Reasoning thread: handles Prolog inference
        The threading.Event objects synchronize them cleanly.
        """
        try:
            # Wait until free-text intake is complete
            # (interface calls intake_complete() to unblock this)
            self._intake_ready.wait(timeout=5.0)

            # Small pause to ensure all assertz() calls from
            # intake_complete() have fully committed in Prolog
            import time as _time
            _time.sleep(0.1)

            # Get first question from Prolog, skipping preloaded ones
            action = self._get_next_skipping_preloaded()
            self._handle_action(action)

            # Main loop
            while self._session.is_active:
                # Wait for the interface layer to provide an answer
                answered = self._answer_event.wait(timeout=120.0)
                self._answer_event.clear()

                if not answered:
                    # Timeout — end session gracefully
                    self._finish_incomplete("Session timed out.")
                    break

                # Read the pending answer (thread-safe)
                with self._lock:
                    response = self._pending_answer
                    self._pending_answer = None

                if response is None:
                    continue

                # Record in session BEFORE sending to Prolog
                # so the log is always ahead of the engine
                self._session.record_answer(
                    symptom          = self._current_symptom,
                    question_text    = self._current_question,
                    answer           = response,
                    candidates_remaining = self._get_candidate_count()
                )

                self._emit(ConsultationEvent.ANSWER_RECORDED, {
                    "symptom": self._current_symptom,
                    "answer":  response
                })

                # Send answer to Prolog and get next action
                action = self._bridge.step(
                    self._current_symptom, response
                )
                # Skip any pre-loaded symptoms that slip through
                while (action.get("action") == "ask" and
                       action.get("symptom") in self._preloaded + self._preloaded_denied):
                    self._bridge.assert_symptom(action["symptom"])
                    action = self._bridge.get_first_question()
                self._handle_action(action)

        except Exception as e:
            self._emit(ConsultationEvent.ERROR, {"message": str(e)})
            self._finish_incomplete(f"Error: {e}")

    def _get_next_skipping_preloaded(self) -> dict:
        """
        Gets next question, guaranteed to skip preloaded symptoms.
        Uses direct Prolog assertz into diagnosis_rules module namespace
        so next_question/1 sees the facts correctly.
        """
        skip = set(self._preloaded + self._preloaded_denied)

        # Write directly into diagnosis_rules module namespace
        # This is the only reliable way across pyswip versions
        for s in skip:
            try:
                list(self._bridge._prolog.query(
                    f"assertz(diagnosis_rules:asked({s}))"
                ))
            except Exception:
                pass

        for s in self._preloaded:
            try:
                list(self._bridge._prolog.query(
                    f"assertz(diagnosis_rules:symptom({s}))"
                ))
            except Exception:
                pass

        for s in self._preloaded_denied:
            try:
                list(self._bridge._prolog.query(
                    f"assertz(diagnosis_rules:denied({s}))"
                ))
            except Exception:
                pass

        # Fetch next question — should skip all preloaded
        for _ in range(30):
            results = list(self._bridge._prolog.query(
                "next_question(S), symptom_question(S, Q)"
            ))
            if not results:
                return self._bridge._build_result()
            row = results[0]
            sym = str(row["S"])
            q   = row["Q"]
            if isinstance(q, bytes):
                q = q.decode("utf-8")
            if sym not in skip:
                return {"action": "ask", "symptom": sym, "question": str(q)}
            # Still a preloaded one — mark asked and retry
            try:
                list(self._bridge._prolog.query(
                    f"assertz(diagnosis_rules:asked({sym}))"
                ))
            except Exception:
                pass
        return self._bridge.get_first_question()

    def _handle_action(self, action: dict) -> None:
        """
        Route the action dict returned by bridge.step() or
        bridge.get_first_question() to the correct handler.
        """
        if action["action"] == "ask":
            self._current_symptom  = action["symptom"]
            self._current_question = action["question"]

            # Emit status update with live candidate count
            try:
                status = self._bridge.get_status()
            except Exception:
                status = {"candidates": []}
            self._emit(ConsultationEvent.STATUS_UPDATE, status)

            # Count only questions actually asked (not preloaded ones)
            asked_count = self._session.log.question_count - len(self._preloaded) - len(self._preloaded_denied)
            display_number = max(1, asked_count + 1)

            # Emit question ready — interface layer displays it
            self._emit(ConsultationEvent.QUESTION_READY, {
                "symptom":  self._current_symptom,
                "question": self._current_question,
                "number":   display_number
            })

            # Signal the interface thread a question is waiting
            self._question_event.set()

        elif action["action"] == "result":
            self._finish_with_result(action)

    # ----------------------------------------------------------------
    # FINISH HANDLERS
    # ----------------------------------------------------------------

    def _finish_with_result(self, action: dict) -> None:
        """Build DiagnosisResult and complete the session."""
        disease    = action.get("disease", "unknown")
        confidence = action.get("confidence", 0.0)
        desc       = action.get("description", "")
        tests      = action.get("tests", [])

        is_conclusive = disease not in ("inconclusive", "insufficient_data")

        result = DiagnosisResult(
            disease       = disease,
            confidence    = confidence,
            description   = desc,
            tests         = tests,
            is_conclusive = is_conclusive
        )

        self._session.complete(result)

        self._emit(ConsultationEvent.DIAGNOSIS_READY, {
            "disease":          disease,
            "confidence":       confidence,
            "confidence_level": result.confidence_level.value,
            "description":      desc,
            "tests":            tests,
            "is_conclusive":    is_conclusive,
            "summary":          self._session.summary()
        })

        self._done_event.set()

    def _finish_incomplete(self, reason: str = "") -> None:
        """End session without a diagnosis."""
        self._session.end_incomplete()
        self._emit(ConsultationEvent.DIAGNOSIS_READY, {
            "disease":       "insufficient_data",
            "confidence":    0.0,
            "is_conclusive": False,
            "reason":        reason
        })
        self._done_event.set()

    # ----------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------

    def _get_candidate_count(self) -> int:
        """How many diseases are still possible right now."""
        try:
            status = self._bridge.get_status()
            return len(status.get("candidates", []))
        except Exception:
            return 0

    # ----------------------------------------------------------------
    # PROPERTIES — read-only access for interface layer
    # ----------------------------------------------------------------

    @property
    def current_question(self) -> Optional[str]:
        return self._current_question

    @property
    def current_symptom(self) -> Optional[str]:
        return self._current_symptom

    @property
    def session(self) -> UserSession:
        return self._session

    @property
    def is_done(self) -> bool:
        return self._done_event.is_set()

    @property
    def question_number(self) -> int:
        return self._session.log.question_count + 1

    def get_progress(self) -> dict:
        """
        Returns current consultation progress.
        Used by the interface to show a progress indicator.
        """
        status = {}
        try:
            status = self._bridge.get_status()
        except Exception:
            pass

        return {
            "questions_asked":   self._session.log.question_count,
            "candidates_left":   len(status.get("candidates", [])),
            "top_candidate":     status.get("top_candidate", "none"),
            "top_confidence":    status.get("top_confidence", 0.0),
            "confirmed_count":   len(self._session.record.confirmed_symptoms),
        }


# ----------------------------------------------------------------
# CONSULTATION FACTORY — clean entry point
# ----------------------------------------------------------------

def create_consultation(patient_name: str,
                        prolog_dir,
                        patient_age: int = None,
                        lisp_dir=None) -> tuple[Consultation, UserSession]:
    """
    Factory function — creates and wires up everything needed
    for a consultation in one call.

    Returns (consultation, session) so the interface layer
    has direct access to both.
    """
    session = UserSession(patient_name, patient_age)
    bridge  = PrologBridge(prolog_dir)
    bridge.load()
    consultation = Consultation(session, bridge, lisp_dir=lisp_dir)
    return consultation, session