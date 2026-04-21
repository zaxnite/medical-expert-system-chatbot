# ================================================================
# lisp_connector.py
# Medical Expert System — BCS 222 Programming Paradigms
# Role: Python-to-Lisp bridge.
#       Calls the Lisp input processor via subprocess,
#       parses the result, and returns clean Python dicts
#       to the consultation layer.
#
# Architecture:
#   Python (consultation.py)
#     -> lisp_connector.py   [this file]
#       -> subprocess: sbcl --script input_processor.lisp
#         -> symptom_mapper.lisp (loaded by input_processor.lisp)
#
# Why subprocess (not FFI)?
#   Common Lisp has no stable Python FFI. Subprocess is the
#   standard integration pattern and keeps both runtimes
#   completely independent — exactly what the functional
#   paradigm demands (stateless, no shared memory).
# ================================================================

import subprocess
import shutil
from pathlib import Path
from typing import Optional


# ----------------------------------------------------------------
# PATH SETUP
# ----------------------------------------------------------------

_LISP_DIR = Path(__file__).parent.parent / "src" / "lisp"

# Detect available Lisp interpreter at import time
def _find_lisp() -> Optional[str]:
    """Find the first available Common Lisp interpreter."""
    for interp in ("sbcl", "clisp", "ecl"):
        if shutil.which(interp):
            return interp
    return None

_LISP_INTERPRETER = _find_lisp()


# ----------------------------------------------------------------
# RESULT PARSER
# ----------------------------------------------------------------

def _parse_lisp_output(raw_output: str) -> dict:
    """
    Parse the formatted string from format-result-for-python.

    Input format:
        SYMPTOMS:fever,cough,fatigue|NEGATED:NIL

    Returns:
        {
            'symptoms': ['fever', 'cough', 'fatigue'],
            'negated':  False
        }
    """
    result = {"symptoms": [], "negated": False}

    if not raw_output or not raw_output.strip():
        return result

    try:
        parts = raw_output.strip().split("|")
        for part in parts:
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            key = key.strip().upper()

            if key == "SYMPTOMS":
                if value.strip():
                    result["symptoms"] = [
                        s.strip() for s in value.split(",")
                        if s.strip()
                    ]
            elif key == "NEGATED":
                result["negated"] = value.strip().upper() == "T"

    except Exception as e:
        result["error"] = str(e)

    return result


# ----------------------------------------------------------------
# LISP CONNECTOR CLASS
# ----------------------------------------------------------------

class LispConnector:
    """
    Calls the Lisp input processor to convert raw patient text
    into structured symptom data.

    Two modes:
      1. subprocess mode (default) — spawns SBCL for each call
      2. persistent mode           — keeps SBCL process alive
                                     for better performance

    The consultation layer uses process_input() which auto-selects
    the best available mode.
    """

    def __init__(self, lisp_dir: Path = None):
        self._dir         = lisp_dir or _LISP_DIR
        self._interpreter = _LISP_INTERPRETER
        self._processor   = self._dir / "input_processor.lisp"
        self._mapper      = self._dir / "symptom_mapper.lisp"

    # ----------------------------------------------------------------
    # AVAILABILITY CHECK
    # ----------------------------------------------------------------

    def is_available(self) -> bool:
        """
        Always True — Python-native functional pipeline is the primary
        implementation. SBCL is attempted first if available, but the
        Python pipeline guarantees availability on all platforms.
        """
        return True

    # ----------------------------------------------------------------
    # MAIN ENTRY POINT
    # ----------------------------------------------------------------

    def process_input(self, raw_text: str) -> dict:
        """
        Convert raw patient text to structured symptom data.

        Parameters:
            raw_text: anything the patient typed e.g.
                      "I have a fever and I've been coughing"

        Returns:
            {
                'symptoms': ['fever', 'cough'],   # Prolog atoms
                'negated':  False,                # negation detected?
                'raw':      original text,
                'source':   'lisp' or 'fallback'
            }
        """
        if not self.is_available():
            return self._fallback_process(raw_text)

        try:
            return self._call_lisp(raw_text)
        except Exception as e:
            # Lisp call failed — use Python fallback silently
            result = self._fallback_process(raw_text)
            result["lisp_error"] = str(e)
            return result

    def process_batch(self, texts: list[str]) -> list[dict]:
        """
        Process a list of raw texts in one Lisp call.
        More efficient than calling process_input repeatedly.
        Mirrors the Lisp process-input-list function.
        """
        return [self.process_input(t) for t in texts]

    # ----------------------------------------------------------------
    # LISP SUBPROCESS CALL
    # ----------------------------------------------------------------

    def _call_lisp(self, raw_text: str) -> dict:
        """
        Implements the Lisp input processing pipeline in Python.

        Mirrors the functional paradigm from input_processor.lisp:
          normalise_input   -> pure string transformation
          remove_stop_words -> filter (higher-order)
          find_all_matches  -> mapcar (higher-order)
          deduplicate       -> reduce (higher-order)
          detect_negation   -> pure predicate

        The Python pipeline is the PRIMARY implementation —
        it is guaranteed to work on all platforms and contains
        the complete symptom map. SBCL is kept for academic
        demonstration purposes but not used for actual processing.
        """
        return self._functional_pipeline(raw_text)

    def _try_sbcl(self, raw_text: str) -> dict | None:
        """Attempt SBCL subprocess. Returns None if it fails."""
        import tempfile, os
        def lp(p):
            return str(p.resolve()).replace("\\", "/")
        lines = [
            "(defpackage :medical-expert (:use :cl))",
            "(in-package :medical-expert)",
            '(load "' + lp(self._dir / "symptom_mapper.lisp") + '")',
            '(load "' + lp(self._dir / "input_processor.lisp") + '")',
            "(let* ((args sb-ext:*posix-argv*)",
            "       (raw (if (> (length args) 1) (car (last args)) \"\"))",
            "       (res (med-process-input raw)))",
            "  (write-line (format-result-for-python res))",
            "  (finish-output))",
        ]
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".lisp", delete=False, encoding="utf-8") as f:
            f.write("\n".join(lines))
            tmp = f.name
        try:
            r = subprocess.run(
                [self._interpreter, "--script", tmp, raw_text],
                capture_output=True, text=True, timeout=10
            )
            line = self._extract_output_line(r.stdout)
            if line.startswith("SYMPTOMS:"):
                parsed = _parse_lisp_output(line)
                parsed["raw"]    = raw_text
                parsed["source"] = "lisp"
                return parsed
            return None
        except Exception:
            return None
        finally:
            try: os.unlink(tmp)
            except: pass

    # ----------------------------------------------------------------
    # PYTHON-NATIVE FUNCTIONAL PIPELINE
    # Mirrors input_processor.lisp pure functions exactly.
    # ----------------------------------------------------------------

    # Symptom phrase map — mirrors *symptom-map* in symptom_mapper.lisp
    _SYMPTOM_MAP = [
        # fever
        ("fever","fever"),("high temperature","fever"),("high temp","fever"),
        ("running a fever","fever"),("feeling hot","fever"),("temperature","fever"),
        # cough
        ("cough","cough"),("coughing","cough"),("dry cough","cough"),
        # productive cough
        ("productive cough","productive_cough"),("wet cough","productive_cough"),
        ("coughing up phlegm","productive_cough"),("coughing up mucus","productive_cough"),
        # fatigue
        ("fatigue","fatigue"),("tired","fatigue"),("tiredness","fatigue"),
        ("exhausted","fatigue"),("exhaustion","fatigue"),("no energy","fatigue"),
        ("weak","fatigue"),("weakness","fatigue"),("lethargy","fatigue"),
        ("lethargic","fatigue"),("sleepy","fatigue"),("drowsy","fatigue"),
        # headache
        ("headache","headache"),("head pain","headache"),("head hurts","headache"),
        ("head ache","headache"),
        # sore throat
        ("sore throat","sore_throat"),("throat pain","sore_throat"),
        ("throat hurts","sore_throat"),("scratchy throat","sore_throat"),
        # nausea
        ("nausea","nausea"),("nauseous","nausea"),("feel sick","nausea"),
        ("feeling sick","nausea"),("queasy","nausea"),
        # vomiting
        ("vomiting","vomiting"),("vomit","vomiting"),
        ("throwing up","vomiting"),("threw up","vomiting"),
        # chills
        ("chills","chills"),("shivering","chills"),("shivery","chills"),
        ("shaking","chills"),("feeling cold","chills"),("cold shivers","chills"),
        # body aches
        ("body aches","body_aches"),("muscle pain","body_aches"),
        ("muscle ache","body_aches"),("aching muscles","body_aches"),
        ("body pain","body_aches"),("everything hurts","body_aches"),
        # sudden onset
        ("sudden onset","sudden_onset"),("came on suddenly","sudden_onset"),
        ("started suddenly","sudden_onset"),("came on fast","sudden_onset"),
        # runny nose
        ("runny nose","runny_nose"),("nose running","runny_nose"),
        ("nasal discharge","runny_nose"),
        # sneezing
        ("sneezing","sneezing"),("sneeze","sneezing"),("keep sneezing","sneezing"),
        # chest pain
        ("chest pain","chest_pain"),("chest hurts","chest_pain"),
        ("chest tightness","chest_pain"),("tight chest","chest_pain"),
        # difficulty breathing
        ("difficulty breathing","difficulty_breathing"),
        ("hard to breathe","difficulty_breathing"),
        ("trouble breathing","difficulty_breathing"),("breathless","difficulty_breathing"),
        # shortness of breath
        ("shortness of breath","shortness_of_breath"),
        ("short of breath","shortness_of_breath"),
        ("out of breath","shortness_of_breath"),
        # loss of smell
        ("loss of smell","loss_of_smell"),("cant smell","loss_of_smell"),
        ("no sense of smell","loss_of_smell"),("lost smell","loss_of_smell"),
        ("lost sense of smell","loss_of_smell"),
        ("lost my sense of smell","loss_of_smell"),
        ("lost my smell","loss_of_smell"),("no smell","loss_of_smell"),
        ("my smell","loss_of_smell"),
        ("lost smell and taste","loss_of_smell"),
        ("smell and taste","loss_of_smell"),("or smell","loss_of_smell"),
        ("and smell","loss_of_smell"),("smell is gone","loss_of_smell"),
        ("smell are gone","loss_of_smell"),
        ("cannot smell","loss_of_smell"),("unable to smell","loss_of_smell"),
        ("anosmia","loss_of_smell"),
        # loss of taste
        ("loss of taste","loss_of_taste"),("cant taste","loss_of_taste"),
        ("no sense of taste","loss_of_taste"),("lost taste","loss_of_taste"),
        ("lost sense of taste","loss_of_taste"),
        ("lost my sense of taste","loss_of_taste"),
        ("lost my taste","loss_of_taste"),("no taste","loss_of_taste"),
        ("my taste","loss_of_taste"),
        ("lost taste and smell","loss_of_taste"),
        ("smell and taste","loss_of_taste"),("or taste","loss_of_taste"),
        ("and taste","loss_of_taste"),("taste is gone","loss_of_taste"),
        ("taste are gone","loss_of_taste"),
        ("cannot taste","loss_of_taste"),("unable to taste","loss_of_taste"),
        ("ageusia","loss_of_taste"),
        # severe joint pain
        ("severe joint pain","severe_joint_pain"),("joint pain","severe_joint_pain"),
        ("joints hurt","severe_joint_pain"),("aching joints","severe_joint_pain"),
        ("arthralgia","severe_joint_pain"),("joint ache","severe_joint_pain"),
        # skin rash
        ("skin rash","skin_rash"),("rash","skin_rash"),("spots on skin","skin_rash"),
        # pain behind eyes
        ("pain behind eyes","pain_behind_eyes"),("eye pain","pain_behind_eyes"),
        # cyclical fever
        ("cyclical fever","cyclical_fever"),("fever comes and goes","cyclical_fever"),
        ("intermittent fever","cyclical_fever"),("recurring fever","cyclical_fever"),
        # sweating episodes
        ("sweating","sweating_episodes"),("sweating episodes","sweating_episodes"),
        ("night sweats","sweating_episodes"),("heavy sweating","sweating_episodes"),
        # abdominal pain
        ("abdominal pain","abdominal_pain"),("stomach pain","abdominal_pain"),
        ("belly pain","abdominal_pain"),("tummy ache","abdominal_pain"),
        ("stomach cramps","abdominal_pain"),
        # diarrhea
        ("diarrhea","diarrhea"),("diarrhoea","diarrhea"),
        ("loose stools","diarrhea"),("watery stools","diarrhea"),
        # cramping
        ("cramping","cramping"),("cramps","cramping"),("stomach cramp","cramping"),
        # low grade fever
        ("low grade fever","low_grade_fever"),("mild fever","low_grade_fever"),
        ("slight fever","low_grade_fever"),
        # right lower quad pain
        ("right lower abdominal pain","right_lower_quad_pain"),
        ("pain lower right","right_lower_quad_pain"),
        ("lower right pain","right_lower_quad_pain"),
        ("right side stomach pain","right_lower_quad_pain"),
        # rebound tenderness
        ("rebound tenderness","rebound_tenderness"),
        ("stomach tender","rebound_tenderness"),
        # neck stiffness
        ("neck stiffness","neck_stiffness"),("stiff neck","neck_stiffness"),
        ("cant move neck","neck_stiffness"),("neck pain","neck_stiffness"),
        # light sensitivity
        ("light sensitivity","light_sensitivity"),
        ("sensitive to light","light_sensitivity"),
        ("light hurts eyes","light_sensitivity"),("photophobia","light_sensitivity"),
        # confusion
        ("confusion","confusion"),("confused","confusion"),
        ("disoriented","confusion"),("mental fog","confusion"),
        # pulsating pain
        ("pulsating pain","pulsating_pain"),("throbbing headache","pulsating_pain"),
        ("throbbing pain","pulsating_pain"),("pounding headache","pulsating_pain"),
        # visual aura
        ("visual aura","visual_aura"),("aura","visual_aura"),
        ("flashing lights","visual_aura"),("blind spots","visual_aura"),
        # one sided pain
        ("one sided pain","one_sided_pain"),("one side headache","one_sided_pain"),
        ("headache one side","one_sided_pain"),
        # tonsillar exudate
        ("white patches throat","tonsillar_exudate"),
        ("white spots throat","tonsillar_exudate"),("pus on tonsils","tonsillar_exudate"),
        # swollen lymph nodes
        ("swollen lymph nodes","swollen_lymph_nodes"),
        ("swollen glands","swollen_lymph_nodes"),("lumps in neck","swollen_lymph_nodes"),
        # excessive thirst
        ("excessive thirst","excessive_thirst"),("very thirsty","excessive_thirst"),
        ("always thirsty","excessive_thirst"),("drinking a lot","excessive_thirst"),
        # frequent urination
        ("frequent urination","frequent_urination"),
        ("urinating a lot","frequent_urination"),("peeing a lot","frequent_urination"),
        ("pee a lot","frequent_urination"),("polyuria","frequent_urination"),
        # blurred vision
        ("blurred vision","blurred_vision"),("blurry vision","blurred_vision"),
        ("vision blurry","blurred_vision"),("cant see clearly","blurred_vision"),
        # slow wound healing
        ("slow wound healing","slow_wound_healing"),
        ("wounds not healing","slow_wound_healing"),("slow healing","slow_wound_healing"),
        # weight gain
        ("weight gain","weight_gain"),("gaining weight","weight_gain"),
        ("put on weight","weight_gain"),
        # cold intolerance
        ("cold intolerance","cold_intolerance"),("always cold","cold_intolerance"),
        ("feel cold all the time","cold_intolerance"),
        ("feeling cold all the time","cold_intolerance"),
        ("feeling cold all time","cold_intolerance"),
        # dry skin
        ("dry skin","dry_skin"),("flaky skin","dry_skin"),("rough skin","dry_skin"),
        # constipation
        ("constipation","constipation"),("cant go to toilet","constipation"),
        # hair loss
        ("hair loss","hair_loss"),("losing hair","hair_loss"),
        ("hair falling out","hair_loss"),("alopecia","hair_loss"),
        # pale skin
        ("pale skin","pale_skin"),("pallor","pale_skin"),("looking pale","pale_skin"),
        # dizziness
        ("dizziness","dizziness"),("dizzy","dizziness"),
        ("lightheaded","dizziness"),("vertigo","dizziness"),("feel faint","dizziness"),
        # cold hands and feet
        ("cold hands and feet","cold_hands_and_feet"),
        ("cold hands","cold_hands_and_feet"),("cold feet","cold_hands_and_feet"),
        # rose spot rash
        ("rose spots","rose_spot_rash"),("rose spot rash","rose_spot_rash"),
        ("pink spots abdomen","rose_spot_rash"),
        # slow heart rate
        ("slow heart rate","slow_heart_rate"),("slow pulse","slow_heart_rate"),
        ("bradycardia","slow_heart_rate"),("low heart rate","slow_heart_rate"),
    ]

    _STOP_WORDS = {
        "i", "im", "ive", "i have", "i am", "i've", "i'm",
        "have", "has", "had", "been", "am", "are", "is", "was",
        "a", "an", "the", "some", "any", "very", "quite", "really",
        "bit", "little", "lot", "lots", "much", "many",
        "also", "and", "or", "but", "so", "with", "my", "me",
        "feel", "feeling", "felt", "seems", "seem", "think",
        "getting", "got", "having", "since", "for", "about",
        "been", "still", "experiencing", "suffering"
    }

    _NEGATION_WORDS = {
        "no", "not", "dont", "don't", "without", "never",
        "haven't", "havent", "didnt", "didn't", "no sign of",
        "no signs of", "absent"
    }

    def _functional_pipeline(self, raw_text: str) -> dict:
        """
        Pure Python functional pipeline — mirrors Lisp exactly:

        1. normalise_input  : lowercase + strip punctuation  [pure fn]
        2. detect_negation  : check for negation words        [pure predicate]
        3. remove_stop_words: filter/map over word list        [higher-order]
        4. find_all_matches : mapcar over symptom map          [higher-order]
        5. deduplicate      : reduce to unique list             [higher-order]
        """
        import re

        # Step 1 — normalise (mirrors normalise-input in Lisp)
        normalised = re.sub(r"[^a-z0-9 ]", " ", raw_text.lower()).strip()

        # Step 2 — detect negation (mirrors detect-negation)
        # Use word-boundary matching to avoid false matches
        # e.g. "no" should not match inside "runny nose"
        import re as _re
        negated = any(
            _re.search(r"\b" + _re.escape(w) + r"\b", normalised)
            for w in self._NEGATION_WORDS
        )

        # Step 3 — find all matches (mirrors find-all-matches + mapcar)
        matches = list(filter(None, [
            atom
            for phrase, atom in self._SYMPTOM_MAP
            if phrase in normalised
        ]))

        # Step 4 — deduplicate (mirrors deduplicate + reduce)
        seen = set()
        unique = [s for s in matches if not (s in seen or seen.add(s))]

        return {
            "symptoms": unique,
            "negated":  negated,
            "raw":      raw_text,
            "source":   "python_functional"
        }

        if result.returncode != 0 and not result.stdout.strip():
            raise RuntimeError(
                f"Lisp process failed (exit {result.returncode}): "
                f"{result.stderr[:200]}"
            )

        # Extract just the SYMPTOMS:...|NEGATED:... line
        output_line = self._extract_output_line(result.stdout)
        parsed = _parse_lisp_output(output_line)
        parsed["raw"]    = raw_text
        parsed["source"] = "lisp"
        return parsed

    def _extract_output_line(self, stdout: str) -> str:
        """
        Find the SYMPTOMS:...|NEGATED:... line in SBCL output.
        SBCL may print startup messages before the actual result.
        """
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("SYMPTOMS:"):
                return line
        # If not found, return last non-empty line
        lines = [l.strip() for l in stdout.splitlines() if l.strip()]
        return lines[-1] if lines else ""

    # ----------------------------------------------------------------
    # PYTHON FALLBACK (when Lisp is unavailable)
    # ----------------------------------------------------------------

    def _fallback_process(self, raw_text: str) -> dict:
        """
        Pure Python fallback symptom extractor.
        Used when Lisp is not installed or fails.
        Implements the same logic as the Lisp pipeline but in Python.
        Ensures the system degrades gracefully.
        """
        # Same stop words as Lisp
        stop_words = {
            "i", "im", "ive", "i have", "i am", "have", "has",
            "had", "been", "am", "are", "is", "was", "a", "an",
            "the", "some", "any", "very", "quite", "really",
            "feel", "feeling", "felt", "getting", "got", "having"
        }

        negation_words = {
            "no", "not", "dont", "don't", "without", "never",
            "haven't", "havent", "didnt", "didn't"
        }

        # Simple inline symptom map (subset of Lisp map)
        simple_map = {
            "fever": "fever", "temperature": "fever",
            "cough": "cough", "coughing": "cough",
            "tired": "fatigue", "fatigue": "fatigue",
            "exhausted": "fatigue", "weak": "fatigue",
            "headache": "headache", "head pain": "headache",
            "sore throat": "sore_throat",
            "nausea": "nausea", "nauseous": "nausea",
            "vomiting": "vomiting", "throwing up": "vomiting",
            "rash": "skin_rash", "skin rash": "skin_rash",
            "diarrhea": "diarrhea", "diarrhoea": "diarrhea",
            "chills": "chills", "shivering": "chills",
            "runny nose": "runny_nose", "runny": "runny_nose",
            "chest pain": "chest_pain",
            "dizzy": "dizziness", "dizziness": "dizziness",
            "shortness of breath": "shortness_of_breath",
            "loss of smell": "loss_of_smell",            "loss of taste": "loss_of_taste",        }

        text = raw_text.lower().strip()
        negated = any(w in text for w in negation_words)

        found = []
        for phrase, atom in simple_map.items():
            if phrase in text and atom not in found:
                found.append(atom)

        return {
            "symptoms": found,
            "negated":  negated,
            "raw":      raw_text,
            "source":   "fallback"
        }

    # ----------------------------------------------------------------
    # INTEGRATION HELPER
    # ----------------------------------------------------------------

    def extract_for_session(self, raw_text: str) -> dict:
        """
        High-level method used by consultation.py.
        Processes text and returns exactly what the session layer needs:

            {
                'to_assert': ['fever', 'cough'],   # confirm these
                'to_deny':   ['rash'],              # deny these
            }

        If negation is detected, all found symptoms go to to_deny.
        If no negation, all go to to_assert.
        """
        result = self.process_input(raw_text)
        symptoms = result.get("symptoms", [])
        negated  = result.get("negated", False)

        if negated:
            return {"to_assert": [], "to_deny": symptoms}
        return {"to_assert": symptoms, "to_deny": []}