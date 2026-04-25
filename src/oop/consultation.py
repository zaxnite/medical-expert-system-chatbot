# consultation.py
# Medical Expert System - BCS 222 Programming Paradigms
# Controller layer - connects UserSession (OOP state) with PrologBridge (inference engine).
# This code connects session.py and bridge.py.
# (start -> ask -> answer -> diagnose -> end) needs an object that owns the full flow.
# The interface layer (CLI or GUI) can swap out without touching this controller.

from __future__ import annotations
import sys
import threading
import time
from typing import Callable, Optional
from datetime import datetime
from pathlib import Path

# Ensure integration/ and src/oop/ are always on the path
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
# CONSULTATION EVENTS
# ----------------------------------------------------------------

class ConsultationEvent:
    # Event types for consultation
    QUESTION_READY  = "question_ready"  
    ANSWER_RECORDED = "answer_recorded" 
    DIAGNOSIS_READY = "diagnosis_ready"  
    STATUS_UPDATE   = "status_update"    
    ERROR           = "error"            


# ----------------------------------------------------------------
# CONSULTATION CONTROLLER
# ----------------------------------------------------------------

class Consultation:
    # Main controller for consultation flow

    def __init__(self, session: UserSession, bridge: PrologBridge,
                 lisp_dir=None):
        self._session    = session
        self._bridge     = bridge
        self._lisp       = LispConnector(lisp_dir) if (lisp_dir and LispConnector) else None
        self._preloaded: list[str] = []        
        self._intake_candidates: int = 15       
        self._preloaded_denied: list[str] = []  

        # Current pending question - set by Prolog, read by interface
        self._current_symptom:  Optional[str] = None
        self._current_question: Optional[str] = None

        # Gate - reasoning thread waits until intake is complete
        self._intake_ready     = threading.Event()
        # Update candidate count after preloaded symptoms are asserted
        self._intake_candidates = len(list(
            self._bridge._prolog.query("candidate(D)")
        ))
        self._intake_ready.set()  # default: ready immediately

        # Reasoning runs on a background thread so the UI thread stays responsive
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
        # Register callback for event
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, data: dict = None) -> None:
        # Fire callbacks for this event
        for cb in self._callbacks.get(event, []):
            try:
                cb(data or {})
            except Exception as e:
                print(f"[Consultation] Callback error on {event}: {e}")

    # ----------------------------------------------------------------
    # LIFECYCLE
    # ----------------------------------------------------------------

    def preload_symptoms(self, raw_text: str) -> dict:
        # Extract symptoms from free text
        if not self._lisp:
            return {"found": [], "negated": [], "source": "none"}

        result   = self._lisp.extract_for_session(raw_text)
        to_assert = result.get("to_assert", [])
        to_deny   = result.get("to_deny",   [])

        # Assert symptoms into Prolog
        for s in to_assert:
            list(self._bridge._prolog.query(
                f"assertz(diagnosis_rules:symptom({s}))"
            ))
            list(self._bridge._prolog.query(
                f"assertz(diagnosis_rules:asked({s}))"
            ))
            self._preloaded.append(s)

        for s in to_deny:
            list(self._bridge._prolog.query(
                f"assertz(diagnosis_rules:denied({s}))"
            ))
            list(self._bridge._prolog.query(
                f"assertz(diagnosis_rules:asked({s}))"
            ))
            self._preloaded_denied.append(s)

        # Get source from a direct process_input call for reporting
        raw_result = self._lisp.process_input("")
        return {
            "found":   to_assert,
            "negated": to_deny,
            "source":  "lisp" if self._lisp.is_available() else "fallback"
        }

    def intake_complete(self) -> None:
        # Signal intake is done
        self._intake_ready.set()

    def start(self) -> None:
        # Start consultation and launch reasoning thread
        self._session.start()
        self._bridge.reset_session()

        # Wait for intake to complete
        self._intake_ready.clear()

        # Launch reasoning thread
        self._reasoning_thread = threading.Thread(
            target=self._reasoning_loop,
            name="ReasoningThread",
            daemon=True
        )
        self._reasoning_thread.start()

    def answer(self, response: bool) -> None:
        # Record patient answer
        if not self._session.is_active:
            # Session timed out - silently ignore late answers
            return

        with self._lock:
            self._pending_answer = response

        # Signal reasoning thread that an answer is ready
        self._answer_event.set()

    def wait_for_question(self, timeout: float = 10.0) -> bool:
        # Wait for next question
        result = self._question_event.wait(timeout=timeout)
        self._question_event.clear()
        return result

    def wait_for_completion(self, timeout: float = 120.0) -> bool:
        # Wait for consultation to finish
        return self._done_event.wait(timeout=timeout)

    # ----------------------------------------------------------------
    # REASONING THREAD
    # ----------------------------------------------------------------

    def _reasoning_loop(self) -> None:
        # Background reasoning thread
        try:
            # Wait for intake to complete
            self._intake_ready.wait(timeout=120.0)

            # Get first question
            action = self._get_next_skipping_preloaded()
            self._handle_action(action)

            # Loop until done
            while self._session.is_active:
                # Wait for patient answer
                answered = self._answer_event.wait(timeout=120.0)
                self._answer_event.clear()

                if not answered:
                    # Timeout - end session gracefully
                    self._finish_incomplete("Session timed out.")
                    break

                # Read the pending answer (thread-safe)
                with self._lock:
                    response = self._pending_answer
                    self._pending_answer = None

                if response is None:
                    continue

                # Record answer
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

                # Send to Prolog
                action = self._bridge.step(
                    self._current_symptom, response
                )
                # Skip preloaded symptoms
                while (action.get("action") == "ask" and
                       action.get("symptom") in self._preloaded + self._preloaded_denied):
                    self._bridge.assert_symptom(action["symptom"])
                    action = self._bridge.get_first_question()
                
                # Early exit if only one disease left
                if action.get("action") == "ask":
                    candidate_count = self._get_candidate_count()
                    if candidate_count == 1:
                        candidates = list(self._bridge._prolog.query("candidate(D)"))
                        sole = str(candidates[0]["D"])
                        conf_res = list(self._bridge._prolog.query(
                            f"confidence({sole}, Pct)"
                        ))
                        matched = list(self._bridge._prolog.query(
                            f"symptom_of({sole}, S), symptom(S)"
                        ))
                        pct = float(conf_res[0]["Pct"]) if conf_res else 0.0
                        if pct >= 60.0 and len(matched) >= 3:
                            action = self._bridge._build_early_exit_result(sole, pct)
                
                self._handle_action(action)

        except Exception as e:
            self._emit(ConsultationEvent.ERROR, {"message": str(e)})
            self._finish_incomplete(f"Error: {e}")

    def _get_next_skipping_preloaded(self) -> dict:
        # Get next question, skip preloaded ones
        skip = set(self._preloaded + self._preloaded_denied)

        # Mark as asked
        for s in skip:
            try:
                list(self._bridge._prolog.query(
                    f"assertz(diagnosis_rules:asked({s}))"
                ))
            except Exception:
                pass

        # Fetch next question - should skip all preloaded
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
            # Still a preloaded one - mark asked and retry
            try:
                list(self._bridge._prolog.query(
                    f"assertz(diagnosis_rules:asked({sym}))"
                ))
            except Exception:
                pass
        return self._bridge.get_first_question()

    def _handle_action(self, action: dict) -> None:
        # Handle action from Prolog
        if action["action"] == "ask":
            self._current_symptom  = action["symptom"]
            self._current_question = action["question"]

            # Emit status update with live candidate count
            try:
                status = self._bridge.get_status()
            except Exception:
                status = {"candidates": []}
            self._emit(ConsultationEvent.STATUS_UPDATE, status)

            # Use asked_question_count which already excludes intake entries
            display_number = self._session.log.asked_question_count + 1

            # Emit question ready - interface layer displays it
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
        # Complete with diagnosis result
        disease    = action.get("disease", "unknown")
        confidence = min(100.0, action.get("confidence", 0.0))
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
            "disease":             disease,
            "confidence":          confidence,
            "confidence_level":    result.confidence_level.value,
            "description":         desc,
            "tests":               tests,
            "is_conclusive":       is_conclusive,
            "confirmed_symptoms":  action.get("confirmed_symptoms", []),
            "other_symptoms":      action.get("other_symptoms", []),
            "summary":             self._session.summary()
        })

        self._done_event.set()

    def _finish_incomplete(self, reason: str = "") -> None:
        # End without diagnosis
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
        # Count possible diseases
        try:
            status = self._bridge.get_status()
            return len(status.get("candidates", []))
        except Exception:
            return 0

    # ----------------------------------------------------------------
    # PROPERTIES
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
        # Next question number
        return self._session.log.asked_question_count + 1

    def get_progress(self) -> dict:
        # Return progress info
        status = {}
        try:
            status = self._bridge.get_status()
        except Exception:
            pass

        return {
            "questions_asked":   self._session.log.asked_question_count,
            "candidates_left":   len(status.get("candidates", [])),
            "top_candidate":     status.get("top_candidate", "none"),
            "top_confidence":    min(100.0, status.get("top_confidence", 0.0)),
            "confirmed_count":   len(self._session.record.confirmed_symptoms),
        }


# ----------------------------------------------------------------
# CONSULTATION FACTORY
# ----------------------------------------------------------------

def create_consultation(patient_name: str,
                        prolog_dir,
                        patient_age: int = None,
                        lisp_dir=None) -> tuple[Consultation, UserSession]:
    # Create and set up consultation
    session = UserSession(patient_name, patient_age)
    bridge  = PrologBridge(prolog_dir)
    bridge.load()
    consultation = Consultation(session, bridge, lisp_dir=lisp_dir)
    return consultation, session