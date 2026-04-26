# Medical Expert System
### BCS 222 - Programming Paradigms

> A multi-paradigm diagnostic chatbot that integrates **Object-Oriented Python**, **Functional Lisp**, and **Logic Prolog** into a single cohesive system. The patient describes their symptoms in plain English, the system asks targeted yes/no questions, and narrows down a diagnosis from a knowledge base of 20 diseases across 5 medical groups.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![SWI-Prolog](https://img.shields.io/badge/SWI--Prolog-9.x-orange)](https://www.swi-prolog.org/)
[![SBCL](https://img.shields.io/badge/SBCL-2.x-lightgrey)](https://www.sbcl.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Repository Structure](#repository-structure)
4. [File-by-File Overview](#file-by-file-overview)
5. [How Each Paradigm Is Used](#how-each-paradigm-is-used)
6. [Disease Knowledge Base](#disease-knowledge-base)
7. [Scoring System](#scoring-system)
8. [Installation](#installation)
9. [Running the System](#running-the-system)
10. [Test Scenarios](#test-scenarios)
11. [Edge Cases](#edge-cases)

---

## Project Overview

The system conducts a medical consultation in three stages:

1. **Free-text intake** - the patient types a description of their symptoms in plain English (e.g., *"I have body aches and it came on suddenly"*). SBCL/Lisp parses this into structured symptom atoms.
2. **Confirmation** - the patient confirms or rejects the detected symptoms.
3. **Yes/No questioning** - Prolog's inference engine selects the most informative question at each step, progressively eliminating diseases until a confident diagnosis is reached.

The UI runs on the **main thread**. The Prolog reasoning engine runs on a **background thread**. A thread-safe event system connects them, so the interface never blocks the inference engine and vice versa.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     MAIN THREAD                         │
│                  interface.py (CLI)                     │
│   Patient input  ──►  free-text  ──►  yes/no answers   │
└───────────────────────┬────────────────────┬────────────┘
                        │ events             │ answers
                        ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                  consultation.py                        │
│         (Controller / Event Bus / Thread Gate)          │
│   threading.Event gates    ──     callback registry     │
└──────────┬──────────────────────────────────┬───────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────┐                ┌──────────────────────┐
│   bridge.py     │                │  lisp_connector.py   │
│  (PrologBridge) │                │  (LispConnector)     │
│                 │                │                      │
│  pyswip ──►     │                │  SBCL subprocess ──► │
│  SWI-Prolog     │                │  input_processor     │
│  engine         │                │  .lisp               │
└──────┬──────────┘                └──────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│           SWI-Prolog Engine          │
│                                      │
│  knowledge_base.pl   (facts)         │
│  diagnosis_rules.pl  (inference)     │
│  inference_engine.pl (loop control)  │
└──────────────────────────────────────┘

   session.py  ◄──  UserSession / MedicalRecord / ConsultationLog
                    (OOP state - lives on main thread)
```

---

## Repository Structure

```
medical-expert-system-chatbot/
│
├── main.py                         # Entry point - wires all three layers together
│
├── src/
│   ├── prolog/
│   │   ├── knowledge_base.pl       # Disease facts, symptoms, tests, questions
│   │   ├── diagnosis_rules.pl      # Inference engine, scoring, hard rules
│   │   └── inference_engine.pl     # Consultation loop and step-mode interface
│   │
│   ├── lisp/
│   │   ├── input_processor.lisp    # Stateless NLP pipeline (normalize → map → deduplicate)
│   │   ├── symptom_mapper.lisp     # 400+ phrase-to-atom mapping table
│   │   └── runner.lsp              # Subprocess entry point for SBCL
│   │
│   └── oop/
│       ├── session.py              # UserSession, MedicalRecord, ConsultationLog
│       ├── consultation.py         # Controller - connects session, bridge, and Lisp
│       └── interface.py            # Terminal UI (main thread only)
│
├── integration/
│   ├── bridge.py                   # Python ↔ SWI-Prolog bridge (pyswip wrapper)
│   └── lisp_connector.py           # Python ↔ SBCL bridge (subprocess)
│
├── tests/
│   └── test.txt                    # All 20 diseases + 14 edge cases - full test guide
│
└── README.md
```

---

## File-by-File Overview

### Entry Point

#### `main.py`
The application entry point. Resolves absolute paths to `src/prolog/`, `src/lisp/`, and `src/oop/` relative to its own location, then runs two checks before launching:

1. **Prolog check** - verifies that `knowledge_base.pl`, `diagnosis_rules.pl`, and `inference_engine.pl` all exist in `src/prolog/`. Exits with an error if any are missing.
2. **Lisp check** - instantiates `LispConnector` and calls `is_available()` to confirm SBCL is on `PATH` and the `.lisp` files are present. Exits with an install hint if not.

If both checks pass, it prints the startup banner showing the status of all three paradigm layers and launches `MedicalInterface`. The system always runs in interactive consultation mode - there are no command-line flags.

---

### Logic Layer (Prolog)

#### `src/prolog/knowledge_base.pl`
Pure declarative facts - no inference logic. Defines:
- `symptom_of(Disease, Symptom)` - which symptoms belong to which disease (110+ facts across 20 diseases)
- `disease_group(Disease, Group)` - groups diseases into 5 medical categories
- `symptom_question(Symptom, Text)` - the patient-facing question for each symptom atom
- `disease_description(Disease, Text)` - one-line plain-English description of each disease
- `test_required(Disease, Test)` and `test_confirms(Disease, Test, Confirms)` - recommended confirmatory tests

This file is loaded first. Nothing here changes at runtime.

#### `src/prolog/diagnosis_rules.pl`
The core inference engine. Contains 7 logical sections:

| Section | What it does |
|---|---|
| Session control | `assert_symptom/1`, `deny_symptom/1`, `reset_session/0` - manage dynamic facts |
| Hard rules | `hard_rule(Disease, not(Symptom))` - if a patient has a symptom that is impossible for a disease, that disease is immediately eliminated. 60+ rules. |
| Hallmark rules | `hallmark_symptom(Disease, Symptom)` - if a patient denies a hallmark, the disease is eliminated. Also used for early confirmation. |
| Candidate filter | `candidate(Disease)` - a disease remains a candidate only if no hard rules have fired and no hallmarks have been denied |
| **Scoring** | `confidence(Disease, Pct)` - IDF-weighted confidence: `Σ(idf_weight of matched symptoms) / Σ(idf_weight of active symptoms) × 100`. Denied symptoms are excluded from the denominator so a single NO answer cannot permanently cap a score. |
| Diagnosis | `diagnosis(Disease)` - fires when confidence ≥ 65%, at least 3 symptoms confirmed, and this disease is the top candidate |
| Question selection | `next_question(Symptom)` - picks the symptom that maximises coverage across remaining candidates, with bonuses for symptoms that cover all candidates or are unique to one |

#### `src/prolog/inference_engine.pl`
Drives the consultation loop. Provides:
- `run_consultation/0` - full interactive loop (used when running Prolog standalone)
- `run_consultation_step/3` - single-step interface called by `bridge.py` once per patient answer
- `present_result/0` - formats and prints the final diagnosis
- `engine_status/1` - snapshot of current engine state (candidates, confirmed, denied, top confidence) used by the monitoring thread

---

### Functional Layer (Lisp / SBCL)

#### `src/lisp/symptom_mapper.lisp`
A pure declarative mapping table (`*symptom-map*`) with 400+ entries. Maps natural language phrases to Prolog symptom atoms. Examples:

```lisp
("throbbing headache"    . pulsating_pain)
("flashing lights"       . visual_aura)
("night sweats"          . night_sweats)
("coughing up blood"     . haemoptysis)
("always feel cold"      . cold_intolerance)
```

No functions - just data. Loaded by `input_processor.lisp`.

#### `src/lisp/input_processor.lisp`
A stateless NLP pipeline. Takes a raw patient string and returns a structured result. The pipeline stages are:

1. **Normalise** - lowercase, strip punctuation, trim whitespace
2. **Detect negation** - look for words like *"no"*, *"not"*, *"don't have"*, *"without"* and flag the result
3. **Tokenise** - split on spaces and delimiters
4. **Phrase matching** - scan `*symptom-map*` for longest-match phrases in the token list
5. **Deduplicate** - `remove-duplicates` to prevent the same atom appearing twice
6. **Subsume** - remove generic atoms if a more specific one was already found (e.g. remove `fever` if `low_grade_fever` is present)
7. **Format** - output `SYMPTOMS:atom1,atom2|NEGATED:NIL` for Python to parse

Exported functions: `med-process-input`, `format-result-for-python`.

#### `src/lisp/runner.lsp`
Thin entry point used when SBCL is invoked as a subprocess. Loads `input_processor.lisp`, reads patient text from a temp file, calls the pipeline, and writes the formatted result to stdout before quitting.

---

### OOP Layer (Python)

#### `src/oop/session.py`
All mutable state for a patient consultation. Contains four classes:

| Class | Responsibility |
|---|---|
| `SessionState` | Enum: `PENDING → ACTIVE → COMPLETE / INCOMPLETE` |
| `ConfidenceLevel` | Enum: `HIGH / MODERATE / LOW / UNCERTAIN` with `from_pct()` |
| `QAEntry` | Dataclass: one question-answer exchange (symptom, text, answer, timestamp, candidates remaining) |
| `DiagnosisResult` | Dataclass: final diagnosis (disease, confidence, description, tests, conclusive flag) |
| `MedicalRecord` | Tracks confirmed and denied symptoms. Provides `record_yes()`, `record_no()`, `has_symptom()` |
| `ConsultationLog` | Ordered list of `QAEntry` objects. Tracks `asked_question_count` separately from intake entries. `to_dict()` for JSON export. |
| `UserSession` | Root object. Owns `MedicalRecord` + `ConsultationLog`. Lifecycle methods: `start()`, `complete()`, `end_incomplete()`. Full JSON export via `export_json()`. |

#### `src/oop/consultation.py`
The controller that connects all three layers. Key design decisions:

- **Reasoning runs on a background thread** (`_reasoning_loop`). The UI thread never blocks the inference engine.
- **Thread synchronisation** uses three `threading.Event` objects: `_answer_event` (main→background), `_question_event` (background→main), `_done_event` (signals completion).
- **Event system** - `on(event, callback)` / `_emit(event, data)` - the interface registers callbacks before `start()` is called, eliminating race conditions.
- **Intake gate** - `_intake_ready` event pauses the reasoning thread until free-text intake is complete and pre-loaded symptoms are asserted into Prolog.
- **Preloaded symptom skipping** - after Lisp detects symptoms from free text, they are asserted into Prolog and recorded in `_preloaded`. The question selector then skips them to avoid asking the patient twice.

#### `src/oop/interface.py`
The terminal UI. Runs entirely on the main thread. Contains zero business logic - all decisions are delegated to `Consultation`. Responsibilities:
- Display the welcome banner, patient details prompt, and symptom intake
- Register event callbacks on the `Consultation` object
- Block in `_question_loop()` waiting for questions from the reasoning thread
- Display the diagnosis result, session summary, and offer to save a JSON log
- Handle `KeyboardInterrupt` and `EOFError` gracefully at every input point

---

### Integration Layer

#### `integration/bridge.py`
Python ↔ SWI-Prolog bridge using `pyswip`. One instance per consultation. Key methods:

| Method | What it does |
|---|---|
| `load()` | Loads `knowledge_base.pl` → `diagnosis_rules.pl` → `inference_engine.pl` in order |
| `reset_session()` | Retracts all dynamic facts to start a fresh consultation |
| `assert_symptom(s)` | Calls `assert_symptom/1` in Prolog |
| `deny_symptom(s)` | Calls `deny_symptom/1` in Prolog |
| `get_next_question()` | Queries `next_question(S), symptom_question(S, Q)` |
| `step(symptom, answer)` | Records one patient answer, checks for early exit, returns `{'action': 'ask', ...}` or `{'action': 'result', ...}` |
| `get_status()` | Returns snapshot: candidates, confirmed/denied lists, question count, top confidence |
| `_build_result()` | Queries `consult_result/3` and formats the final diagnosis dict |
| `query(str)` | Escape hatch - run any Prolog query and return results as Python dicts |

Sets `SWIPL_STACK_LIMIT=256m` at startup to prevent stack overflow with 20 diseases.

#### `integration/lisp_connector.py`
Python ↔ SBCL bridge using `subprocess`. Key behaviour:
- Detects SBCL via `shutil.which("sbcl")`
- Writes patient text to a temp file (avoids all shell-escaping issues on Windows)
- Builds a `--eval` chain: load → read file → call pipeline → write result → quit
- Parses the `SYMPTOMS:...|NEGATED:...` output line from stdout
- `extract_for_session(text)` returns `{'to_assert': [...], 'to_deny': [...]}` ready for `bridge.py`

---

### Test Files

#### `tests/test.txt`
The single test file covering all 20 diseases and 14 edge cases, structured in two parts:

**Part 1 - Disease tests (Tests 1-20):** one test per disease, grouped by the five medical categories. Each entry provides the exact free-text phrase to type at the symptom prompt, which symptom atoms Lisp will detect, the exact yes/no answers for each question, and the expected diagnosis with IDF confidence percentage.

**Part 2 - Edge cases (Edges 1-14):** disambiguation scenarios and inconclusive cases. Covers disease pairs sharing three or more symptoms (Dengue vs Malaria, Meningitis vs Tension Headache, etc.), both-direction tests for each pair, the TB-with-haemoptysis-denied scenario that validates the denominator-exclusion fix, and three Inconclusive scenarios with different root causes. An IDF weight reference table is included at the end.
---

## How Each Paradigm Is Used

### Object-Oriented (Python)
OOP is used where **identity and mutable state** matter most. A `UserSession` has identity (who is this patient?), state (what has been asked?), and behaviour (log an answer, export a report). Inheritance and encapsulation keep the three sub-objects (`MedicalRecord`, `ConsultationLog`, `DiagnosisResult`) independently testable. Polymorphism through `ConfidenceLevel.from_pct()` keeps display logic out of the data layer.

### Functional (Lisp / SBCL)
Lisp is used for **stateless data transformation**. `input_processor.lisp` takes a string and returns a structured result with no side effects - calling it twice with the same input always returns the same output. Higher-order functions (`mapcar`, `remove-if`, `remove-duplicates`) process the symptom list in a declarative pipeline. This makes the input processor easy to test in isolation and safe to call from a subprocess without shared state concerns.

### Logic (SWI-Prolog)
Prolog is used for **inference and constraint satisfaction**. Hard rules are declared as facts (`hard_rule(disease, not(symptom))`), and Prolog's backtracking evaluates them automatically across all 20 diseases on every step. The `next_question/1` predicate uses Prolog's `findall/3` and `sort/2` to rank symptoms by information gain without any explicit loop. `\+` (negation-as-failure) implements the closed-world assumption cleanly.

---

## Disease Knowledge Base

| Group | Diseases |
|---|---|
| **Respiratory** | Influenza, Common Cold, Pneumonia, Tuberculosis |
| **Viral / Infectious** | COVID-19, Dengue Fever, Malaria, Chickenpox |
| **Gastrointestinal** | Gastroenteritis, Appendicitis, Peptic Ulcer Disease, Irritable Bowel Syndrome |
| **Neurological / ENT** | Meningitis, Migraine, Strep Throat, Tension Headache |
| **Metabolic / Systemic** | Diabetes Type 2, Hypothyroidism, Anemia, Typhoid Fever |

**60 unique symptoms** across all 20 diseases. Each symptom has a patient-facing question in `knowledge_base.pl`.

---

## Scoring System

Confidence uses **IDF (Inverse Document Frequency) weighting**:

```
confidence(Disease) = Σ idf_weight(confirmed_symptoms ∩ disease_symptoms)
                    / Σ idf_weight(disease_symptoms not denied)   ×  100
```

Where `idf_weight(symptom) = log(20 / number_of_diseases_with_this_symptom)`.

| Symptom | Appears in N diseases | IDF Weight |
|---|---|---|
| `body_aches` | 1 | 3.00 (highly specific) |
| `loss_of_smell` | 1 | 3.00 |
| `sudden_onset` | 2 | 2.30 |
| `fever` | 10 | 0.69 (generic) |
| `fatigue` | 13 | 0.43 (very generic) |

**Key properties:**
- All 20 diseases reach exactly 100% when all their symptoms are confirmed
- Denied symptoms are **excluded from the denominator** - a NO answer never permanently caps a disease's maximum score
- Diagnosis threshold: **65%** with a minimum of **3 confirmed symptoms**
- Early exit: if only 1 candidate remains with ≥ 65% confidence and ≥ 3 confirmed symptoms, questioning stops immediately

---

## Installation

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | OOP layer + integration |
| SWI-Prolog | 9.x | Logic layer |
| SBCL | 2.x | Functional layer |
| pyswip | 0.2.10+ | Python ↔ Prolog bridge |

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/zaxnite/medical-expert-system-chatbot.git
cd medical-expert-system-chatbot

# 2. Install Python dependency
pip install pyswip

# 3. Install SWI-Prolog
#    Windows: https://www.swi-prolog.org/download/stable
#    Ubuntu:  sudo apt install swi-prolog
#    macOS:   brew install swi-prolog

# 4. Install SBCL
#    Windows: https://www.sbcl.org/platform-table.html
#    Ubuntu:  sudo apt install sbcl
#    macOS:   brew install sbcl
```

---

## Running the System

```bash
python main.py
```

That is the only command needed. The system always launches in interactive consultation mode.

### What to expect

```
========================================================
             Medical Expert System
        BCS 222 - Programming Paradigms
========================================================
  Paradigm           Status       Role
  ----------------   ----------   ------------------
  OOP  (Python)      OK           Session & state
  Logic (Prolog)     OK           Diagnosis engine
  Functional (Lisp)  OK           Input processing
```

If Prolog or SBCL are missing, the startup banner will show which layer is unavailable and why. The system requires all three layers to run.

---

## Testing

The `tests/test.txt` file is the single test reference for the entire system. Open it alongside the running application and follow each entry exactly.

### Running a disease test

Each of the 20 disease tests follows this structure. Here is Test 1 as an example:

```
Free text:  I have body aches and muscle pain and it came on suddenly
Detected:   body_aches, sudden_onset

Say YES to: fever, cough, fatigue, headache, chills
Say NO to:  (nothing required)

Expected:   Influenza - 100.0% confidence
```

Type the free text exactly as shown at the symptom prompt. The phrase is taken directly from `symptom_mapper.lisp` so detection is guaranteed. Then answer each yes/no question as listed.

### Running an edge case

Edge cases test pairs of diseases that share three or more symptoms. The file includes both directions for each pair. Example:

```
Edge 6A - Dengue vs Malaria (dengue symptoms)
Free text:  I have severe joint pain and I have a rash
Say YES to: fever, headache, fatigue, pain_behind_eyes
Say NO to:  cyclical_fever, chills
Expected:   Dengue Fever - 100.0% confidence

Edge 6B - Dengue vs Malaria (malaria symptoms)
Free text:  My fever comes and goes and I have heavy sweating
Say YES to: fever, chills, headache, fatigue, nausea
Say NO to:  severe_joint_pain, skin_rash
Expected:   Malaria - 100.0% confidence
```

The file also includes three Inconclusive scenarios and the TB-with-haemoptysis-denied case that validates the denominator-exclusion fix in `diagnosis_rules.pl`.

---

## Notes

- Session logs can be saved as JSON at the end of each consultation.
- The system asks at most 20 questions before returning a result.
- All Prolog state is reset between consultations - no cross-session leakage.
- The system includes a medical disclaimer and is intended for educational demonstration only.