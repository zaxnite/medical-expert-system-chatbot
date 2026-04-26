# bridge.py
# Medical Expert System - BCS 222 Programming Paradigms
# Connects Python to SWI-Prolog. Loads the Prolog files and exposes

import os
import ctypes
from pathlib import Path
from pyswip import Prolog, Functor, Variable, Atom
import re

# Increase stack before the engine starts.
os.environ.setdefault("SWI_HOME_DIR", "")
os.environ["SWIPL_STACK_LIMIT"] = "256m"


_PROLOG_DIR = Path(__file__).parent.parent / "src" / "prolog"


class PrologBridge:
    # Wrapper around SWI-Prolog engine

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
        # Load all Prolog files in order
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
        # Wipe all dynamic facts and start fresh
        self._require_loaded()
        list(self._prolog.query("reset_session"))

    # ----------------------------------------------------------------
    # SYMPTOM ASSERTION
    # ----------------------------------------------------------------

    def assert_symptom(self, symptom: str) -> None:
        # Tell Prolog patient confirmed this symptom
        self._require_loaded()
        list(self._prolog.query(f"assert_symptom({symptom})"))

    def deny_symptom(self, symptom: str) -> None:
        # Tell Prolog patient denied this symptom
        self._require_loaded()
        list(self._prolog.query(f"deny_symptom({symptom})"))

    # ----------------------------------------------------------------
    # NEXT QUESTION
    # ----------------------------------------------------------------

    def get_next_question(self) -> dict | None:
        # Ask Prolog what symptom to ask about next
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
        # Process one patient answer and return next action
        self._require_loaded()

        if answer:
            self.assert_symptom(symptom)
        else:
            self.deny_symptom(symptom)
        list(self._prolog.query(f"assertz(diagnosis_rules:asked({symptom}))"))

        # Check diagnosis() first — if it fires, stop immediately
        done = list(self._prolog.query("consultation_complete(diagnosed)"))
        if done:
            return self._build_result()

        # Get next question before checking other termination conditions.
        nq = self.get_next_question()

        if nq is not None:
            # Early exit: if only 1 candidate remains with confidence >= 65%
            # and at least 3 confirmed symptoms, no need to ask further.
            candidates = list(self._prolog.query("candidate(D)"))
            if len(candidates) == 1:
                sole = str(candidates[0]["D"])
                conf_res = list(self._prolog.query(f"confidence({sole}, Pct)"))
                matched = list(self._prolog.query(
                    f"symptom_of({sole}, S), symptom(S)"
                ))
                if (conf_res and float(conf_res[0]["Pct"]) >= 65.0
                        and len(matched) >= 3):
                    return self._build_early_exit_result(sole, float(conf_res[0]["Pct"]))

            # More questions available — ask the next one
            candidates = list(self._prolog.query("candidate(D)"))
            return {"action": "ask", "candidate_count": len(candidates), **nq}

        # No more questions left — check remaining termination conditions
        done = list(self._prolog.query("consultation_complete(Reason)"))
        if done:
            return self._build_result()

        return self._build_result()

    def get_first_question(self) -> dict:
        # Get first question without processing any answer
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
        # Build result when only 1 candidate remains
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
        # Query consult_result and format output
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
        # Get confirmed and other symptoms for disease
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
        # Convert Prolog T-C pairs into Python dicts
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
        # Return snapshot of engine state
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
        # Run any Prolog query and return results
        self._require_loaded()
        return [
            {k: str(v) for k, v in row.items()}
            for row in self._prolog.query(prolog_query)
        ]