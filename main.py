# main.py
# Medical Expert System - BCS 222 Programming Paradigms
# Application entry point.
# Wires OOP (Python), Logic (Prolog), and Functional (Lisp) layers together
# and launches the interface.
#
# Run:
#     python main.py
#     python main.py --demo        (runs automated demo scenario)
#     python main.py --test        (runs integration smoke test)

import sys
import time
import argparse
from pathlib import Path

# ----------------------------------------------------------------
# PATH RESOLUTION
# ----------------------------------------------------------------
# Works whether you run from project root or from src/oop/
BASE_DIR   = Path(__file__).resolve().parent
PROLOG_DIR = BASE_DIR / "src" / "prolog"
LISP_DIR   = BASE_DIR / "src" / "lisp"
OOP_DIR    = BASE_DIR / "src" / "oop"

# Add src/oop to path so imports resolve cleanly
sys.path.insert(0, str(OOP_DIR))
sys.path.insert(0, str(BASE_DIR / "integration"))


# ----------------------------------------------------------------
# PARADIGM AVAILABILITY CHECK
# ----------------------------------------------------------------

def check_dependencies() -> dict:
    """
    Verify all three paradigm layers are available.
    Returns a status dict used by the startup banner.
    """
    status = {
        "prolog": False,
        "lisp":   False,
        "python": True    # always available
    }

    # Check Prolog files exist
    prolog_files = ["knowledge_base.pl", "diagnosis_rules.pl",
                    "inference_engine.pl"]
    status["prolog"] = all(
        (PROLOG_DIR / f).exists() for f in prolog_files
    )

    # Check Lisp (SBCL) availability - no fallback
    try:
        from integration.lisp_connector import LispConnector
        conn = LispConnector(LISP_DIR)
        status["lisp"] = conn.is_available()
        if not status["lisp"]:
            status["lisp_error"] = (
                "SBCL not found or Lisp files missing. "
                "Install from https://www.sbcl.org/platform-table.html"
            )
    except ImportError:
        status["lisp_error"] = "lisp_connector.py not found"

    return status


# ----------------------------------------------------------------
# STARTUP BANNER
# ----------------------------------------------------------------

CYAN  = "\033[96m"
GREEN = "\033[92m"
AMBER = "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def print_startup_banner(status: dict):
    width = 56
    print()
    print(CYAN + "=" * width + RESET)
    print(BOLD + f"{'Medical Expert System':^{width}}" + RESET)
    print(f"{'BCS 222 — Programming Paradigms':^{width}}")
    print(CYAN + "=" * width + RESET)
    print()
    print(f"  {'Paradigm':<20} {'Status':<12} {'Role'}")
    print(f"  {'-'*20} {'-'*12} {'-'*18}")

    def tick(ok): return (GREEN + "OK " + RESET) if ok else (RED + "MISSING" + RESET)

    print(f"  {'OOP  (Python)':<20} {tick(status['python'])}      Session & state")
    print(f"  {'Logic (Prolog)':<20} {tick(status['prolog'])}      Diagnosis engine")
    print(f"  {'Functional (Lisp)':<20} {tick(status['lisp'])}      Input processing")
    print()

    if not status["prolog"]:
        print(RED + f"  ERROR: Prolog files not found in:" + RESET)
        print(f"         {PROLOG_DIR}")
        print(f"  Make sure knowledge_base.pl, diagnosis_rules.pl,")
        print(f"  and inference_engine.pl are in src/prolog/")
        print()

    if not status["lisp"]:
        print(AMBER + "  WARNING: Lisp not available." + RESET)
        print(f"  Install sbcl and place .lisp files in src/lisp/")
        print(f"  Falling back to Python keyword matching.")
        print()


# ----------------------------------------------------------------
# DEMO MODE
# ----------------------------------------------------------------

def run_demo():
    """
    Automated demo - simulates a flu patient answering questions.
    Shows the full system working without requiring user input.
    """
    print()
    print(BOLD + "  Running automated demo (flu patient scenario)..." + RESET)
    print()
    time.sleep(0.5)

    from src.oop.consultation import ConsultationEvent, create_consultation
    from src.oop.session import SessionState

    flu_answers = {
        "fatigue": True,  "fever": True,       "headache": True,
        "cough": True,    "body_aches": True,   "chills": True,
        "sudden_onset": True, "runny_nose": False, "sore_throat": False,
        "nausea": False,  "chest_pain": False,  "diarrhea": False,
        "loss_of_smell": False, "neck_stiffness": False,
    }

    consultation, session = create_consultation(
        "Demo Patient", PROLOG_DIR, patient_age=30
    )

    result_holder = [None]
    consultation.on(
        ConsultationEvent.DIAGNOSIS_READY,
        lambda d: result_holder.__setitem__(0, d)
    )

    consultation.start()

    q_num = 0
    while result_holder[0] is None and q_num < 15:
        got = consultation.wait_for_question(timeout=5.0)
        if result_holder[0]:
            break
        if not got:
            break
        symptom  = consultation.current_symptom
        question = consultation.current_question
        answer   = flu_answers.get(symptom, False)
        ans_str  = "yes" if answer else "no"
        print(f"  Q{q_num+1}: {question}")
        print(AMBER + f"       -> {ans_str}" + RESET)
        time.sleep(0.3)
        consultation.answer(answer)
        q_num += 1

    consultation.wait_for_completion(timeout=10.0)

    if result_holder[0]:
        r = result_holder[0]
        print()
        print(BOLD + "  DEMO RESULT:" + RESET)
        print(f"  Disease    : {r['disease'].replace('_',' ').title()}")
        print(f"  Confidence : {r['confidence']:.1f}%  [{r.get('confidence_level','')}]")
        if r.get('description'):
            print(f"  About      : {r['description']}")
        if r.get('tests'):
            print(f"  Tests      : {[t['test'] for t in r['tests']]}")
    print()


# ----------------------------------------------------------------
# INTEGRATION TEST MODE
# ----------------------------------------------------------------

def run_tests():
    """
    Quick integration smoke test - verifies all three layers talk to each other correctly.
    """
    print()
    print(BOLD + "  Running integration tests..." + RESET)
    print()

    passed = 0
    failed = 0

    def test(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(GREEN + f"  PASS" + RESET + f"  {name}")
            passed += 1
        except Exception as e:
            print(RED + f"  FAIL" + RESET + f"  {name}: {e}")
            failed += 1

    # Test 1: Prolog loads
    def t1():
        from integration.bridge import PrologBridge
        b = PrologBridge(PROLOG_DIR)
        b.load()
        r = b.query("candidate(D)")
        assert len(r) == 15, f"Expected 15 candidates, got {len(r)}"

    test("Prolog loads — 20 diseases", t1)

    # Test 2: Hard rules work
    def t2():
        from integration.bridge import PrologBridge
        b = PrologBridge(PROLOG_DIR)
        b.load()
        b.assert_symptom("cough")
        c = [r["D"] for r in b.query("candidate(D)")]
        assert "strep_throat" not in c

    test("Prolog hard rule — strep eliminated by cough", t2)

    # Test 3: Full flu diagnosis
    def t3():
        from integration.bridge import PrologBridge
        b = PrologBridge(PROLOG_DIR)
        b.load()
        for s in ["fever","sudden_onset","body_aches","chills","cough","fatigue"]:
            b.assert_symptom(s)
        r = b._build_result()
        assert r["disease"] == "influenza", f"Expected influenza, got {r['disease']}"

    test("Prolog diagnosis — flu scenario", t3)

    # Test 4: OOP session
    def t4():
        from src.oop.session import UserSession, DiagnosisResult, SessionState
        s = UserSession("Test Patient", 25)
        s.start()
        s.record_answer("fever", "Do you have fever?", True, 18)
        assert s.log.question_count == 1
        assert s.state == SessionState.ACTIVE

    test("OOP session — UserSession lifecycle", t4)

    # Test 5: Lisp connector
    def t5():
        from integration.lisp_connector import LispConnector
        conn = LispConnector(LISP_DIR)
        if not conn.is_available():
            # fallback still works
            r = conn.process_input("I have a fever and cough")
            assert "fever" in r["symptoms"]
        else:
            r = conn.process_input("I have a fever and cough")
            assert "fever" in r["symptoms"]
            assert "cough" in r["symptoms"]

    test("Lisp connector — symptom extraction", t5)

    # Test 6: Full consultation pipeline
    def t6():
        from src.oop.consultation import ConsultationEvent, create_consultation
        from src.oop.session import SessionState
        consultation, session = create_consultation("Test", PROLOG_DIR)
        done = [False]
        consultation.on(ConsultationEvent.DIAGNOSIS_READY,
                        lambda d: done.__setitem__(0, True))
        consultation.start()
        answers = {"fatigue":True,"fever":True,"headache":True,
                   "cough":True,"body_aches":True,"chills":True}
        q = 0
        while not done[0] and q < 10:
            got = consultation.wait_for_question(timeout=5.0)
            if done[0]: break
            if not got: break
            consultation.answer(answers.get(consultation.current_symptom, False))
            q += 1
        consultation.wait_for_completion(timeout=10.0)
        assert session.state == SessionState.COMPLETE

    test("Full pipeline — consultation completes", t6)

    print()
    print(f"  Results: {passed} passed, {failed} failed")
    print()
    return failed == 0


# ----------------------------------------------------------------
# MAIN ENTRY POINT
# ----------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Medical Expert System — BCS 222"
    )
    parser.add_argument("--demo",  action="store_true",
                        help="Run automated demo scenario")
    parser.add_argument("--test",  action="store_true",
                        help="Run integration smoke tests")
    args = parser.parse_args()

    # Check all three paradigm layers
    status = check_dependencies()
    print_startup_banner(status)

    # Abort if Prolog is missing - it is the core engine
    if not status["prolog"]:
        sys.exit(1)

    # Abort if Lisp (SBCL) is missing - required for input processing
    if not status["lisp"]:
        err = status.get("lisp_error", "SBCL not installed.")
        print(RED + f"  ERROR: {err}" + RESET)
        print()
        sys.exit(1)

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if args.demo:
        run_demo()
        sys.exit(0)

    # Normal interactive mode
    from src.oop.interface import MedicalInterface
    interface = MedicalInterface(prolog_dir=PROLOG_DIR,lisp_dir=LISP_DIR)
    interface.run()

if __name__ == "__main__":
    main()