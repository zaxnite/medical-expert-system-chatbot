# ================================================================
# bridge.py
# Medical Expert System — BCS 222 Programming Paradigms
# Role: Low-level interface between Python and SWI-Prolog.
#       Loads the Prolog files, exposes clean Python functions
#       that the OOP layer calls. No business logic lives here.
# ================================================================

import os
import ctypes
from pathlib import Path
from pyswip import Prolog, Functor, Variable, Atom

# Increase SWI-Prolog stack limits before the engine initialises.
# The default stack is too small for our 20-disease knowledge base
# and causes an assertion failure in pl-fli.c on some systems.
os.environ.setdefault("SWI_HOME_DIR", "")  # let pyswip find SWI
os.environ["SWIPL_STACK_LIMIT"] = "256m"

# ----------------------------------------------------------------
# PATH SETUP
# ----------------------------------------------------------------

# Resolve absolute path to the prolog directory so the bridge
# works regardless of where Python is invoked from.
_PROLOG_DIR = Path(__file__).parent.parent / "src" / "prolog"


class PrologBridge:
    """
    Singleton-style wrapper around the SWI-Prolog engine.
    One instance is created per consultation session.

    Responsibilities:
      - Load all three .pl files in the correct order
      - Expose assert_symptom / deny_symptom / reset
      - Expose next_question and consult_result
      - Expose engine_status for the OOP monitoring thread
    """

    def __init__(self, prolog_dir: Path = None):
        # Pass stack/heap limits directly to SWI-Prolog at startup.
        # Prevents assertion crash in pl-fli.c on Windows + pyswip.
        self._prolog = Prolog()
        try:
            list(self._prolog.query("set_prolog_flag(stack_limit, 256_000_000)"))
        except Exception:
            pass  # older SWI versions use different flag names
        self._dir = prolog_dir or _PROLOG_DIR
        self._loaded = False

    # ----------------------------------------------------------------
    # LOADING
    # ----------------------------------------------------------------

    def load(self) -> None:
        """
        Load all Prolog source files into the engine.
        Must be called once before any queries are made.
        Order matters: knowledge_base -> diagnosis_rules -> inference_engine
        """
        if self._loaded:
            return

        files = [
            self._dir / "knowledge_base.pl",
            self._dir / "diagnosis_rules.pl",
            self._dir / "inference_engine.pl",
        ]

        for pl_file in files:
            if not pl_file.exists():
                raise FileNotFoundError(
                    f"Prolog file not found: {pl_file}\n"
                    f"Check that PROLOG_DIR is correct: {self._dir}"
                )
            # Use consult/1 — standard Prolog file loader
            path_str = str(pl_file).replace("\\", "/")  # Windows path fix
            list(self._prolog.query(f"consult('{path_str}')"))

        self._loaded = True

    def _require_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError(
                "PrologBridge.load() must be called before querying."
            )

    # ----------------------------------------------------------------
    # SESSION CONTROL
    # ----------------------------------------------------------------

    def reset_session(self) -> None:
        """Wipe all dynamic facts — starts a fresh consultation."""
        self._require_loaded()
        list(self._prolog.query("reset_session"))

    # ----------------------------------------------------------------
    # SYMPTOM ASSERTION
    # ----------------------------------------------------------------

    def assert_symptom(self, symptom: str) -> None:
        """
        Tell Prolog the patient confirmed this symptom.
        symptom: Prolog atom string e.g. 'fever', 'cough'
        """
        self._require_loaded()
        list(self._prolog.query(f"assert_symptom({symptom})"))

    def deny_symptom(self, symptom: str) -> None:
        """
        Tell Prolog the patient denied this symptom.
        symptom: Prolog atom string e.g. 'fever', 'cough'
        """
        self._require_loaded()
        list(self._prolog.query(f"deny_symptom({symptom})"))

    # ----------------------------------------------------------------
    # NEXT QUESTION
    # ----------------------------------------------------------------

    def get_next_question(self) -> dict | None:
        """
        Ask Prolog what the best next symptom to ask about is.

        Returns:
            {
                'symptom': 'fever',
                'question': 'Do you have a fever or feel unusually hot?'
            }
            or None if no more questions are needed.
        """
        self._require_loaded()

        results = list(self._prolog.query(
            "next_question(S), symptom_question(S, Q)"
        ))

        if not results:
            return None

        row = results[0]
        question = row["Q"]
        if isinstance(question, bytes):
            question = question.decode("utf-8")
        return {
            "symptom":  str(row["S"]),
            "question": str(question)
        }

    # ----------------------------------------------------------------
    # CONSULTATION STEP (used by threaded OOP layer)
    # ----------------------------------------------------------------

    def step(self, symptom: str, answer: bool) -> dict:
        """
        Process one patient answer and return the next action.

        Parameters:
            symptom: the symptom atom that was just answered
            answer:  True = yes, False = no

        Returns one of three dict shapes:
            {'action': 'ask',    'symptom': ..., 'question': ...}
            {'action': 'result', 'disease': ..., 'confidence': ..., 'tests': [...]}
            {'action': 'result', 'disease': 'inconclusive', 'confidence': 0, 'tests': [...]}
        """
        self._require_loaded()

        # 1. Record patient answer (assert_symptom/deny_symptom
        #    already marks symptom as asked internally)
        if answer:
            self.assert_symptom(symptom)
        else:
            self.deny_symptom(symptom)
        # Ensure asked/1 is set so next_question skips this symptom
        list(self._prolog.query(f"assertz(asked({symptom}))"))

        # 2. Check if consultation is complete
        done = list(self._prolog.query("consultation_complete(Reason)"))
        if done:
            return self._build_result()

        # 3. Get next question — candidates already updated by step above
        nq = self.get_next_question()
        if nq is None:
            return self._build_result()

        # Attach live candidate count to the response
        candidates = list(self._prolog.query("candidate(D)"))
        return {"action": "ask", "candidate_count": len(candidates), **nq}

    def get_first_question(self) -> dict:
        """
        Called at the very start of a consultation to get
        the first question without processing any answer first.
        """
        self._require_loaded()
        nq = self.get_next_question()
        if nq:
            return {"action": "ask", **nq}
        return {"action": "result", "disease": "insufficient_data",
                "confidence": 0, "tests": []}

    # ----------------------------------------------------------------
    # RESULT RETRIEVAL
    # ----------------------------------------------------------------

    def _build_result(self) -> dict:
        """
        Internal — queries consult_result/3 and formats the output.
        """
        results = list(self._prolog.query(
            "consult_result(Disease, Confidence, Tests)"
        ))

        if not results:
            return {
                "action": "result",
                "disease": "insufficient_data",
                "confidence": 0,
                "tests": []
            }

        row = results[0]
        disease    = str(row["Disease"])
        confidence = float(row["Confidence"])
        raw_tests  = row["Tests"]

        # Parse Tests — Prolog returns list of T-C compound terms
        tests = self._parse_tests(raw_tests)

        # Also fetch human-readable description
        desc_results = list(self._prolog.query(
            f"disease_description({disease}, Desc)"
        ))
        if desc_results:
            desc = desc_results[0]["Desc"]
            description = desc.decode("utf-8") if isinstance(desc, bytes) else str(desc)
        else:
            description = ""

        return {
            "action":      "result",
            "disease":     disease,
            "confidence":  confidence,
            "description": description,
            "tests":       tests
        }

    def _parse_tests(self, raw) -> list[dict]:
        """
        Convert Prolog T-C pairs into Python dicts.
        pyswip returns these as strings: "-(rapid_flu_test, confirms_viral_strain)"
        """
        import re
        parsed = []
        if not raw:
            return parsed

        for item in raw:
            s = str(item).strip()
            # Match: -(test_atom, confirms_atom)
            m = re.match(r"-\(([^,]+),\s*([^)]+)\)", s)
            if m:
                parsed.append({
                    "test":     m.group(1).strip(),
                    "confirms": m.group(2).strip()
                })
            else:
                parsed.append({"test": s, "confirms": "unknown"})

        return parsed

    # ----------------------------------------------------------------
    # ENGINE STATUS (for monitoring thread)
    # ----------------------------------------------------------------

    def get_status(self) -> dict:
        """
        Snapshot of current engine state.
        Called by the OOP ConsultationLog to update session metadata.

        Returns:
            {
                'candidates':      [...],
                'confirmed':       [...],
                'denied':          [...],
                'questions_asked': int,
                'top_candidate':   str,
                'top_confidence':  float
            }
        """
        self._require_loaded()

        # Query candidates
        candidates = [
            str(r["D"])
            for r in self._prolog.query("candidate(D)")
        ]

        # Query confirmed symptoms
        confirmed = [
            str(r["S"])
            for r in self._prolog.query("symptom(S)")
        ]

        # Query denied symptoms
        denied = [
            str(r["S"])
            for r in self._prolog.query("denied(S)")
        ]

        # Question count
        qcount_res = list(self._prolog.query("question_count(N)"))
        questions_asked = int(qcount_res[0]["N"]) if qcount_res else 0

        # Top candidate
        top_res = list(self._prolog.query(
            "top_diagnoses([Pct-D|_])"
        ))
        if top_res:
            top_candidate  = str(top_res[0]["D"])
            top_confidence = float(top_res[0]["Pct"])
        else:
            top_candidate  = "none"
            top_confidence = 0.0

        return {
            "candidates":      candidates,
            "confirmed":       confirmed,
            "denied":          denied,
            "questions_asked": questions_asked,
            "top_candidate":   top_candidate,
            "top_confidence":  top_confidence
        }

    # ----------------------------------------------------------------
    # DIRECT QUERY (escape hatch for advanced use)
    # ----------------------------------------------------------------

    def query(self, prolog_query: str) -> list[dict]:
        """
        Run any arbitrary Prolog query and return results as
        a list of dicts. Used for testing and for predicates
        not yet wrapped above.

        Example:
            bridge.query("symptom_of(influenza, S)")
            -> [{'S': 'fever'}, {'S': 'cough'}, ...]
        """
        self._require_loaded()
        return [
            {k: str(v) for k, v in row.items()}
            for row in self._prolog.query(prolog_query)
        ]