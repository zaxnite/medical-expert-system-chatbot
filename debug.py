"""
debug_lisp2.py — focused --script diagnostics for Windows SBCL.

Run from project root:
    python debug_lisp2.py
"""

import os
import subprocess
import shutil
from pathlib import Path

sbcl     = shutil.which("sbcl")
base     = Path(__file__).parent
lisp_dir = base / "src" / "lisp"

def run(label, script_content, cwd=None):
    tmp = lisp_dir / "_dbg.lisp"
    tmp.write_text(script_content, encoding="utf-8")
    r = subprocess.run(
        [sbcl, "--noinform", "--non-interactive", "--script", str(tmp)],
        capture_output=True, text=True, timeout=15,
        cwd=str(cwd or lisp_dir)
    )
    tmp.unlink(missing_ok=True)
    print(f"\n--- {label} ---")
    print(f"  rc     : {r.returncode}")
    print(f"  stdout : {repr(r.stdout[:300])}")
    print(f"  stderr : {repr(r.stderr[:300])}")
    return r

# Test 1: absolute minimum
run("T1: write-line only",
    '(write-line "HELLO")\n')

# Test 2: load symptom_mapper with relative path
run("T2: load symptom_mapper (relative)",
    '(load "symptom_mapper.lisp")\n(write-line "MAPPER_OK")\n')

# Test 3: load symptom_mapper with absolute path
run("T3: load symptom_mapper (absolute)",
    f'(load "{str(lisp_dir / "symptom_mapper.lisp").replace(chr(92), "/")}")\n'
    '(write-line "MAPPER_OK")\n')

# Test 4: defpackage then load
run("T4: defpackage + load symptom_mapper",
    '(defpackage :me (:use :cl))\n'
    '(in-package :me)\n'
    '(load "symptom_mapper.lisp")\n'
    '(write-line "PKG_MAPPER_OK")\n')

# Test 5: load input_processor (which internally loads symptom_mapper)
run("T5: load input_processor directly",
    '(defpackage :me (:use :cl))\n'
    '(in-package :me)\n'
    '(load "input_processor.lisp")\n'
    '(write-line "PROCESSOR_OK")\n')

# Test 6: full call
run("T6: full med-process-input call",
    '(defpackage :me (:use :cl))\n'
    '(in-package :me)\n'
    '(load "input_processor.lisp")\n'
    '(let* ((r (med-process-input "throbbing headache flashing lights"))\n'
    '       (f (format-result-for-python r)))\n'
    '  (write-line f)\n'
    '  (finish-output))\n')

# Test 7: use the medical-expert package name (matches defpackage in input_processor.lisp)
run("T7: use :medical-expert package",
    '(load "input_processor.lisp")\n'
    '(let* ((r (medical-expert:med-process-input "throbbing headache flashing lights"))\n'
    '       (f (medical-expert:format-result-for-python r)))\n'
    '  (write-line f)\n'
    '  (finish-output))\n')

print("\n=== done ===\n")