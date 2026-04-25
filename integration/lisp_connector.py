# lisp_connector.py
# Medical Expert System - BCS 222 Programming Paradigms
# Python-to-Lisp bridge.
# Calls the Lisp input processor via SBCL subprocess,
# parses the result, and returns clean Python dicts to the consultation layer.

import os
import subprocess
import shutil
import tempfile
from pathlib import Path


_LISP_DIR = Path(__file__).parent.parent / "src" / "lisp"


def _find_sbcl() -> str | None:
    return shutil.which("sbcl")


# ----------------------------------------------------------------
# RESULT PARSER
# ----------------------------------------------------------------

def _parse_lisp_output(raw_output: str) -> dict:
    """
    Parse SYMPTOMS:fever,cough|NEGATED:NIL produced by
    format-result-for-python in input_processor.lisp.
    """
    result = {"symptoms": [], "negated": False}
    if not raw_output or not raw_output.strip():
        return result
    try:
        for part in raw_output.strip().split("|"):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            key = key.strip().upper()
            if key == "SYMPTOMS" and value.strip():
                result["symptoms"] = [
                    s.strip() for s in value.split(",") if s.strip()
                ]
            elif key == "NEGATED":
                result["negated"] = value.strip().upper() == "T"
    except Exception as e:
        result["error"] = str(e)
    return result


# ----------------------------------------------------------------
# LISP CONNECTOR
# ----------------------------------------------------------------

class LispConnector:

    def __init__(self, lisp_dir: Path = None):
        self._dir         = Path(lisp_dir) if lisp_dir else _LISP_DIR
        self._interpreter = _find_sbcl()
        self._processor   = self._dir / "input_processor.lisp"
        self._mapper      = self._dir / "symptom_mapper.lisp"

    def is_available(self) -> bool:
        return (
            self._interpreter is not None
            and self._processor.exists()
            and self._mapper.exists()
        )

    def process_input(self, raw_text: str) -> dict:
        if not self._interpreter:
            raise RuntimeError(
                "SBCL not found.\n"
                "  Windows: https://www.sbcl.org/platform-table.html"
            )
        if not self._processor.exists():
            raise RuntimeError(f"Missing: {self._processor}")
        if not self._mapper.exists():
            raise RuntimeError(f"Missing: {self._mapper}")
        return self._call_sbcl(raw_text)

    def process_batch(self, texts: list[str]) -> list[dict]:
        return [self.process_input(t) for t in texts]

    # ----------------------------------------------------------------
    # CORE: --eval mode, one expression per flag, text via temp file
    # ----------------------------------------------------------------

    @staticmethod
    def _lp(p: Path) -> str:
        """Forward-slash path string safe for Lisp (load ...) on Windows."""
        return str(p.resolve()).replace("\\", "/")

    def _call_sbcl(self, raw_text: str) -> dict:
        """
        Invoke SBCL using one --eval flag per expression.
        """
        txt_path = None
        try:
            # Write patient text to a temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt",
                dir=str(self._dir),
                delete=False, encoding="utf-8"
            ) as tf:
                tf.write(raw_text)
                txt_path = tf.name

            # Forward-slash paths for Lisp
            processor_lp = self._lp(self._processor)
            txt_lp       = self._lp(Path(txt_path))

            # Build --eval chain - one expression per --eval flag (Windows SBCL requirement).
            # Lisp reads the text from the temp file so no escaping is needed.
            evals = [
                f'(load "{processor_lp}")',

                # Read raw text from temp file
                f'(defvar *raw-input* "")',
                f'(with-open-file (s "{txt_lp}" :direction :input) '
                f'  (setf *raw-input* (read-line s nil "")))',

                # Call the Lisp pipeline
                '(defvar *result* (medical-expert:med-process-input *raw-input*))',
                '(defvar *formatted* (medical-expert:format-result-for-python *result*))',
                '(write-line *formatted*)',
                '(finish-output)',
                '(sb-ext:quit)',
            ]

            cmd = [self._interpreter, "--noinform", "--non-interactive"]
            for expr in evals:
                cmd += ["--eval", expr]

            # Run SBCL
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20,
                encoding="utf-8",
                cwd=str(self._dir),
            )

            output_line = self._extract_result_line(proc.stdout)

            if not output_line:
                raise RuntimeError(
                    "No SYMPTOMS:...|NEGATED:... line in SBCL output.\n"
                    "stdout: " + repr(proc.stdout[:400]) + "\n"
                    "stderr: " + repr(proc.stderr[:400])
                )

            parsed = _parse_lisp_output(output_line)
            parsed["raw"]    = raw_text
            parsed["source"] = "lisp"
            return parsed

        finally:
            if txt_path:
                try:
                    os.unlink(txt_path)
                except OSError:
                    pass

    def _extract_result_line(self, stdout: str) -> str:
        for line in stdout.splitlines():
            s = line.strip()
            if s.startswith("SYMPTOMS:"):
                return s
        return ""

    # ----------------------------------------------------------------
    # INTEGRATION HELPER
    # ----------------------------------------------------------------

    def extract_for_session(self, raw_text: str) -> dict:
        result   = self.process_input(raw_text)
        symptoms = result.get("symptoms", [])
        negated  = result.get("negated",  False)
        if negated:
            return {"to_assert": [], "to_deny": symptoms}
        return {"to_assert": symptoms, "to_deny": []}