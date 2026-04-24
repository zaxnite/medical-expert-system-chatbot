;;;; ================================================================
;;;; input_processor.lisp
;;;; Medical Expert System — BCS 222 Programming Paradigms
;;;; Role: Stateless text processing pipeline.
;;;;       Takes raw patient input strings and maps them to
;;;;       structured symptom data the Prolog engine understands.
;;;;
;;;; Functional paradigm justification:
;;;;   Every function here is PURE — given the same input it
;;;;   always returns the same output with zero side effects.
;;;;   This makes the pipeline trivially testable and safe to
;;;;   call from multiple threads without any synchronisation.
;;;;   Higher-order functions (mapcar, remove-if, reduce) are
;;;;   used throughout to demonstrate functional composition.
;;;; ================================================================

(defpackage :medical-expert
  (:use :cl)
  (:export :med-process-input
           :med-run-processor
           :format-result-for-python
           :process-input-list
           :merge-results))
(in-package :medical-expert)

(load (merge-pathnames "symptom_mapper.lisp"
        (or *load-pathname* #p"./")))


;;; ================================================================
;;; SECTION 1 — STRING UTILITIES (pure functions)
;;; ================================================================

(defun string-downcase-trim (str)
  "Lowercase and strip leading/trailing whitespace from STR.
   Pure function — no side effects."
  (string-trim '(#\Space #\Tab #\Newline #\Return)
               (string-downcase str)))


(defun split-by-char (str char)
  "Split STR into a list of substrings on CHAR.
   Pure recursive function — demonstrates functional decomposition."
  (let ((pos (position char str)))
    (if pos
        (cons (subseq str 0 pos)
              (split-by-char (subseq str (1+ pos)) char))
        (list str))))


(defun split-words (str)
  "Split STR into individual words on spaces.
   Filters out empty strings from double spaces."
  (remove-if #'(lambda (w) (string= w ""))
             (split-by-char str #\Space)))


(defun join-words (words)
  "Join a list of WORDS back into a single space-separated string."
  (if (null words)
      ""
      (reduce #'(lambda (a b) (concatenate 'string a " " b))
              words)))


(defun string-contains-p (haystack needle)
  "Return T if NEEDLE appears as a substring in HAYSTACK."
  (not (null (search needle haystack :test #'string=))))


(defun remove-punctuation (str)
  "Strip punctuation characters from STR.
   Keeps spaces, letters, digits, and hyphens."
  (remove-if #'(lambda (c)
                 (member c '(#\. #\, #\! #\? #\; #\: #\'
                             #\" #\( #\) #\/ #\\)))
             str))


;;; ================================================================
;;; SECTION 2 — NORMALISATION PIPELINE
;;; ================================================================

(defun normalise-input (raw-text)
  "Full normalisation pipeline for raw patient input.
   Applies: lowercase -> trim -> remove punctuation -> collapse spaces.
   Pure function — the entry point for all text before matching."
  (let* ((lower    (string-downcase-trim raw-text))
         (no-punct (remove-punctuation lower))
         (trimmed  (string-downcase-trim no-punct)))
    trimmed))


(defun remove-stop-words (text)
  "Remove stop words from TEXT.
   Uses higher-order function REMOVE-IF to filter word list.
   Returns cleaned text as a string."
  (let* ((words   (split-words text))
         (cleaned (remove-if
                    #'(lambda (w) (member w *stop-words* :test #'string=))
                    words)))
    (join-words cleaned)))


(defun word-boundary-match-p (text word)
  "Return T if WORD appears as a whole word in TEXT.
   Uses space-padding trick to enforce word boundaries —
   prevents 'no' matching inside 'nose' or 'runny nose'.
   Pure function — no side effects."
  (let ((padded-text (concatenate 'string " " text " "))
        (padded-word (concatenate 'string " " word " ")))
    (not (null (search padded-word padded-text :test #'string=)))))


(defun detect-negation (text)
  "Return T if TEXT contains a negation word as a WHOLE WORD.
   Uses word-boundary-match-p to prevent false matches —
   e.g. 'no' should not match inside 'runny nose'.
   Pure function — demonstrates higher-order function SOME."
  (some #'(lambda (neg)
              (word-boundary-match-p text neg))
        *negation-words*))


;;; ================================================================
;;; SECTION 3 — SYMPTOM MATCHING
;;; ================================================================

(defun match-symptom-phrase (text phrase-atom-pair)
  "Return the Prolog atom if PHRASE (car of pair) appears in TEXT.
   Returns NIL if no match. Pure function."
  (let ((phrase (car phrase-atom-pair))
        (atom   (cdr phrase-atom-pair)))
    (when (string-contains-p text phrase)
      atom)))


(defun find-all-matches (text symptom-map)
  "Apply match-symptom-phrase across all entries in SYMPTOM-MAP.
   Uses MAPCAR (higher-order) then filters NILs.
   Returns a list of matched Prolog atoms — may contain duplicates."
  (remove-if #'null
             (mapcar #'(lambda (pair)
                         (match-symptom-phrase text pair))
                     symptom-map)))


(defun deduplicate (lst)
  "Remove duplicate items from LST using REDUCE.
   Uses string= for string comparison, eql for symbols.
   Pure functional deduplication — no mutation."
  (reduce #'(lambda (acc item)
              (if (member item acc :test #'equal)
                  acc
                  (append acc (list item))))
          lst
          :initial-value '()))


(defun extract-symptoms (normalised-text)
  "Core matching function.
   Takes NORMALISED-TEXT and returns a deduplicated list
   of matched Prolog symptom atoms.

   Pipeline:
     normalised text
       -> find-all-matches against *symptom-map*
       -> deduplicate
       -> subsume-generic-symptoms (drop generic if specific matched)
       -> result list of atoms"
  (subsume-generic-symptoms
    (deduplicate
      (find-all-matches normalised-text *symptom-map*))))


(defparameter *subsumption-map*
  '(;; If specific fever matched, drop generic fever
    (fever . ("low_grade_fever" "cyclical_fever"))
    ;; If specific rash matched, drop generic skin_rash
    ("skin_rash" . ("itchy_rash" "vesicular_rash" "rose_spot_rash")))
  "Alist of (generic . (specific...)).
   If ANY specific atom is present in the matched list, the generic is removed.
   Cough is handled at the mapper level -- generic cough phrases are written
   to not overlap with compound cough phrases.")


(defun subsume-generic-symptoms (symptom-list)
  "Remove generic symptom atoms when a more specific variant is present.
   E.g. if chronic_cough is matched, cough is redundant and removed.
   Pure function — uses REMOVE-IF with higher-order predicate."
  (remove-if
    #'(lambda (atom)
        (let ((specifics (cdr (assoc atom *subsumption-map* :test #'equal))))
          (and specifics
               (some #'(lambda (specific)
                          (member specific symptom-list :test #'equal))
                     specifics))))
    symptom-list))


;;; ================================================================
;;; SECTION 4 — FULL PROCESSING PIPELINE
;;; ================================================================

(defun med-process-input (raw-text)
  "TOP-LEVEL FUNCTION — called by Python via lisp_connector.py.
   Takes raw patient text, returns a structured result plist:

     (:symptoms  (fever cough fatigue ...)
      :negated   T/NIL
      :raw       original text
      :normalised cleaned text)

   This is a pure function — same input always gives same output.
   The Python bridge reads the :symptoms and :negated keys."
  (let* ((normalised (normalise-input raw-text))
         (negated    (detect-negation normalised))
         (cleaned    (remove-stop-words normalised))
         (symptoms   (extract-symptoms cleaned)))
    (list
      :symptoms   symptoms
      :negated    negated
      :raw        raw-text
      :normalised normalised)))


(defun process-input-list (text-list)
  "Process a LIST of raw input strings.
   Uses MAPCAR to apply process-input to each entry.
   Demonstrates higher-order function usage across a batch.
   Returns a list of result plists."
  (mapcar #'med-process-input text-list))


(defun merge-results (result-list)
  "Merge multiple process-input results into one combined result.
   Collects all symptoms from all results, deduplicates.
   Used when patient has described symptoms across multiple messages."
  (let* ((all-symptoms
           (reduce #'append
                   (mapcar #'(lambda (r)
                               (getf r :symptoms))
                           result-list)
                   :initial-value '()))
         (unique-symptoms (deduplicate all-symptoms))
         (any-negated
           (some #'(lambda (r) (getf r :negated))
                 result-list)))
    (list
      :symptoms  unique-symptoms
      :negated   any-negated
      :count     (length unique-symptoms))))


;;; ================================================================
;;; SECTION 5 — SYMPTOM SCORING
;;; ================================================================

(defun count-matching-symptoms (symptom-list candidate-symptoms)
  "Count how many symptoms from SYMPTOM-LIST appear in CANDIDATE-SYMPTOMS.
   Pure function — used for pre-filtering before Prolog inference."
  (length
    (remove-if-not
      #'(lambda (s) (member s candidate-symptoms))
      symptom-list)))


(defun symptom-coverage-score (input-symptoms disease-symptoms)
  "Calculate what fraction of INPUT-SYMPTOMS appear in DISEASE-SYMPTOMS.
   Returns a float between 0.0 and 1.0.
   Pure arithmetic function — no side effects."
  (if (null input-symptoms)
      0.0
      (/ (float (count-matching-symptoms input-symptoms disease-symptoms))
         (float (length input-symptoms)))))


;;; ================================================================
;;; SECTION 6 — FORMATTING (output to Python)
;;; ================================================================

(defun symptom-atom-to-string (atom)
  "Convert a symptom (symbol or string) to a lowercase string.
   Handles both symbol atoms and string atoms from the map."
  (if (stringp atom)
      (string-downcase atom)
      (string-downcase (symbol-name atom))))


(defun symptoms-to-string-list (symptom-atoms)
  "Convert a list of Prolog atoms to a list of lowercase strings.
   Uses MAPCAR — demonstrates higher-order function on output side."
  (mapcar #'symptom-atom-to-string symptom-atoms))


(defun format-result-for-python (result)
  "Serialize a process-input result to a plain string
   that lisp_connector.py can parse easily.

   Output format (one line):
     SYMPTOMS:fever,cough,fatigue|NEGATED:NIL

   The Python bridge splits on | then on : to extract values."
  (let* ((symptoms (getf result :symptoms))
         (negated  (getf result :negated))
         (sym-strs (symptoms-to-string-list symptoms))
         (sym-part (if sym-strs
                       (reduce #'(lambda (a b)
                                   (concatenate 'string a "," b))
                               sym-strs)
                       ""))
         (neg-part (if negated "T" "NIL")))
    (concatenate 'string
                 "SYMPTOMS:" sym-part
                 "|NEGATED:" neg-part)))


;;; ================================================================
;;; SECTION 7 — ENTRY POINT FOR SUBPROCESS MODE
;;; ================================================================

(defun med-run-processor ()
  "Entry point when called as a subprocess by lisp_connector.py.
   Reads input text from command-line argument (safer than stdin
   in non-interactive SBCL). Python passes text as the last arg."
  (let* ((args      sb-ext:*posix-argv*)
         (raw-input (if (> (length args) 1)
                        (car (last args))
                        ""))
         (result    (med-process-input raw-input))
         (formatted (format-result-for-python result)))
    (write-line formatted)
    (finish-output)))