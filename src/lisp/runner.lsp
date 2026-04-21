;;;; runner.lisp — loaded by lisp_connector.py via SBCL
;;;; cwd is always set to src/lisp/ by lisp_connector.py
(defpackage :medical-expert (:use :cl))
(in-package :medical-expert)
(load "symptom_mapper.lisp")
(load "input_processor.lisp")
(let* ((args      sb-ext:*posix-argv*)
       (raw-input (if (> (length args) 1) (car (last args)) ""))
       (result    (med-process-input raw-input))
       (formatted (format-result-for-python result)))
  (write-line formatted)
  (finish-output))