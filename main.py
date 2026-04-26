# main.py
# Medical Expert System - BCS 222 Programming Paradigms
# Entry point. Wires OOP (Python), Logic (Prolog), and Functional (Lisp) together
# and launches the terminal interface.

import sys
from pathlib import Path

# ----------------------------------------------------------------
# PATH RESOLUTION
# ----------------------------------------------------------------

BASE_DIR   = Path(__file__).resolve().parent
PROLOG_DIR = BASE_DIR / "src" / "prolog"
LISP_DIR   = BASE_DIR / "src" / "lisp"
OOP_DIR    = BASE_DIR / "src" / "oop"

sys.path.insert(0, str(OOP_DIR))
sys.path.insert(0, str(BASE_DIR / "integration"))


# ----------------------------------------------------------------
# DEPENDENCY CHECK
# ----------------------------------------------------------------

def check_dependencies() -> dict:
    status = {
        "prolog": False,
        "lisp":   False,
        "python": True
    }

    prolog_files = ["knowledge_base.pl", "diagnosis_rules.pl", "inference_engine.pl"]
    status["prolog"] = all((PROLOG_DIR / f).exists() for f in prolog_files)

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
        print(RED + "  ERROR: Prolog files not found in:" + RESET)
        print(f"         {PROLOG_DIR}")
        print(f"  Make sure knowledge_base.pl, diagnosis_rules.pl,")
        print(f"  and inference_engine.pl are in src/prolog/")
        print()

    if not status["lisp"]:
        print(AMBER + "  WARNING: Lisp not available." + RESET)
        print(f"  Install sbcl and place .lisp files in src/lisp/")
        print()


# ----------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------

def main():
    status = check_dependencies()
    print_startup_banner(status)

    if not status["prolog"]:
        sys.exit(1)

    if not status["lisp"]:
        err = status.get("lisp_error", "SBCL not installed.")
        print(RED + f"  ERROR: {err}" + RESET)
        print()
        sys.exit(1)

    from src.oop.interface import MedicalInterface
    interface = MedicalInterface(prolog_dir=PROLOG_DIR, lisp_dir=LISP_DIR)
    interface.run()

if __name__ == "__main__":
    main()