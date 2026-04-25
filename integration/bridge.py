# bridge.py
# Medical Expert System - BCS 222 Programming Paradigms
# Connects Python to SWI-Prolog. Loads the Prolog files and exposes
# clean functions the OOP layer calls. No business logic lives here.

import os
import ctypes
from pathlib import Path
from pyswip import Prolog, Functor, Variable, Atom

# Increase stack before the engine starts.
# Default stack is too small for 20 diseases and causes crashes on some systems.
os.environ.setdefault("SWI_HOME_DIR", "")
os.environ["SWIPL_STACK_LIMIT"] = "256m"

# Resolve path to prolog/ so this works regardless of where Python is run from.
_PROLOG_DIR = Path(__file__).parent.parent / "src" / "prolog"


class PrologBridge:
    """
    Wrapper around the SWI-Prolog engine.
    One instance per consultation session.

    Handles:
      - Loading all three .pl files in the right order
      - assert_symptom / deny_symptom / reset
      - next_question and consult_result
      - engine_status for the OOP monitoring thread
    """

    def __init__(self, prolog_dir: Path = None):
        # Set stack limit directly at startup to prevent crashes on Windows + pyswip.
        self._prolog = Prolog()
        try:
            list(self._prolog.query("set_prolog_flag(stack_limit, 256_000_000)"))
        except Exception:
            pass  # older SWI versions use a different flag name
        self._dir = prolog_dir or _PROLOG_DIR
        self._loaded = False

    # ----------------------------------------------------------------
    # LOADING
    # ----------------------------------------------------------------

    def load(self) -> None:
        """
        Load all Prolog files into the engine.
        Must be called once before any queries.
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
            # Use consult/1 - standard Prolog file loader
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
        """Wipe all dynamic facts and start fresh."""
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
        Ask Prolog what symptom to ask about next.

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

        # Record patient answer (assert_symptom/deny_symptom marks symptom as asked internally)
        if answer:
            self.assert_symptom(symptom)
        else:
            self.deny_symptom(symptom)
        # Mark as asked so next_question skips this symptom
        list(self._prolog.query(f"assertz(diagnosis_rules:asked({symptom}))"))

        # Early exit: if only 1 candidate remains with confidence >= 60%
        # and at least 3 matching symptoms, stop asking to avoid unnecessary questions.
        candidates = list(self._prolog.query("candidate(D)"))
        if len(candidates) == 1:
            sole = str(candidates[0]["D"])
            conf_res = list(self._prolog.query(f"confidence({sole}, Pct)"))
            # Count how many confirmed symptoms belong to this disease
            matched = list(self._prolog.query(
                f"symptom_of({sole}, S), symptom(S)"
            ))
            if (conf_res and float(conf_res[0]["Pct"]) >= 60.0
                    and len(matched) >= 3):
                return self._build_early_exit_result(sole, float(conf_res[0]["Pct"]))

        # Check if consultation is done by normal criteria
        done = list(self._prolog.query("consultation_complete(Reason)"))
        if done:
            return self._build_result()

        # 3. Get next question
        nq = self.get_next_question()
        if nq is None:
            return self._build_result()

        # Attach live candidate count to the response
        candidates = list(self._prolog.query("candidate(D)"))
        return {"action": "ask", "candidate_count": len(candidates), **nq}

    def get_first_question(self) -> dict:
        """
        Called at the start of a consultation to get the first question
        without processing any answer first.
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

    def _build_early_exit_result(self, disease: str, confidence: float) -> dict:
        """
        Build result when only 1 candidate remains.
        Uses actual confidence (floored at 65%) rather than 100%,
        since being the only candidate doesn't mean every symptom matched.
        """
        tests_raw = list(self._prolog.query(f"needs_tests({disease}, Tests)"))
        tests = self._parse_tests(tests_raw[0]["Tests"]) if tests_raw else []

        desc_res = list(self._prolog.query(f"disease_description({disease}, Desc)"))
        if desc_res:
            desc = desc_res[0]["Desc"]
            description = desc.decode("utf-8") if isinstance(desc, bytes) else str(desc)
        else:
            description = ""

        confirmed, other = self._get_symptom_summary(disease)

        # Floor at 65% - sole remaining candidate justifies a minimum confidence boost
        display_confidence = max(65.0, confidence)

        return {
            "action":             "result",
            "disease":            disease,
            "confidence":         display_confidence,
            "description":        description,
            "tests":              tests,
            "confirmed_symptoms": confirmed,
            "other_symptoms":     other
        }

    def _build_result(self) -> dict:
        """Query consult_result/3 and format the output."""
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

        tests = self._parse_tests(raw_tests)

        desc_results = list(self._prolog.query(f"disease_description({disease}, Desc)"))
        if desc_results:
            desc = desc_results[0]["Desc"]
            description = desc.decode("utf-8") if isinstance(desc, bytes) else str(desc)
        else:
            description = ""

        confirmed, other = self._get_symptom_summary(disease)

        return {
            "action":             "result",
            "disease":            disease,
            "confidence":         confidence,
            "description":        description,
            "tests":              tests,
            "confirmed_symptoms": confirmed,
            "other_symptoms":     other
        }

    def _get_symptom_summary(self, disease: str) -> tuple[list[str], list[str]]:
        """
        Returns two lists for the diagnosed disease:
          confirmed - symptoms the patient reported
          other     - symptoms of the disease the patient did NOT confirm
        """
        all_symptoms = [
            str(r["S"])
            for r in self._prolog.query(f"symptom_of({disease}, S)")
        ]
        confirmed_set = {
            str(r["S"])
            for r in self._prolog.query("symptom(S)")
        }
        confirmed = [s for s in all_symptoms if s in confirmed_set]
        other     = [s for s in all_symptoms if s not in confirmed_set]
        return confirmed, other

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
        Called by ConsultationLog to update session metadata.

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
        Run any Prolog query and return results as a list of dicts.
        Used for testing and predicates not yet wrapped above.

        Example:
            bridge.query("symptom_of(influenza, S)")
            -> [{'S': 'fever'}, {'S': 'cough'}, ...]
        """
        self._require_loaded()
        return [
            {k: str(v) for k, v in row.items()}
            for row in self._prolog.query(prolog_query)
        ]