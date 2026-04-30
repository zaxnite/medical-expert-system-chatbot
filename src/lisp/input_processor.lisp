;;;; ================================================================
;;;; input_processor.lisp
;;;; Medical Expert System — BCS 222 Programming Paradigms
;;;; Role: Stateless text processing pipeline.
;;;;       Takes raw patient input strings and maps them to
;;;;       structured symptom data the Prolog engine understands.
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
;;; SECTION 1 — STRING UTILITIES
;;; ================================================================

(defun string-downcase-trim (str)
  "Lowercase and strip leading/trailing whitespace from STR."
  (string-trim '(#\Space #\Tab #\Newline #\Return)
               (string-downcase str)))


(defun split-by-char (str char)
  "Split STR into a list of substrings on CHAR."
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
   Applies: lowercase -> trim -> remove punctuation -> collapse spaces."
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
   Uses space-padding trick to enforce word boundaries."
  (let ((padded-text (concatenate 'string " " text " "))
        (padded-word (concatenate 'string " " word " ")))
    (not (null (search padded-word padded-text :test #'string=)))))


(defun detect-negation (text)
  "Return T if TEXT contains a negation word as a WHOLE WORD.
   Uses word-boundary-match-p to prevent false matches."
  (some #'(lambda (neg)
              (word-boundary-match-p text neg))
        *negation-words*))


;;; ----------------------------------------------------------------
;;; NEGATION WINDOW SCOPING — per-symptom negation
;;; ----------------------------------------------------------------
;;;
;;; Core idea:
;;;   A negation word (e.g. "not", "dont") opens a NEGATION WINDOW.
;;;   The window closes when a SCOPE BREAKER is encountered:
;;;     - a coordinating conjunction that resets scope: "and", "also",
;;;       "plus", "as well", "but", "however", "although", etc.
;;;   Any symptom phrase whose position in the text falls INSIDE a
;;;   negation window is considered denied; all others are confirmed.
;;;
;;;   Examples:
;;;     "I am not hungry and have a fever"
;;;       negation window: [pos("not") .. pos("and")]
;;;       "hungry"  -> inside window  -> denied
;;;       "fever"   -> after "and"    -> confirmed   ✓
;;;
;;;     "I dont have a fever but I am tired"
;;;       negation window: [pos("dont") .. pos("but")]
;;;       "fever"   -> inside window  -> denied      ✓
;;;       "tired"   -> after "but"    -> confirmed   ✓
;;;
;;;     "I have a fever and no cough"
;;;       no negation before "fever" -> confirmed
;;;       negation window: [pos("no") .. end]
;;;       "cough"   -> inside window  -> denied      ✓

(defparameter *scope-breakers*
  '("and" "also" "plus" "as well" "but" "however" "although"
    "though" "yet" "while" "whereas" "except" "apart from"
    "other than" "additionally" "furthermore" "moreover")
  "Words/phrases that close a negation window.
   After any of these, negation scope resets to positive.")


(defun find-first-occurrence (text phrases)
  "Return the position of the first occurrence of any phrase from PHRASES
   in TEXT (as a padded whole-word search), or NIL if none found.
   Returns the position in the original TEXT string."
  (let ((padded-text (concatenate 'string " " text " "))
        (best nil))
    (dolist (phrase phrases best)
      (let* ((padded-phrase (concatenate 'string " " phrase " "))
             (pos (search padded-phrase padded-text :test #'string=)))
        (when pos
          ;; adjust for the leading space we added
          (let ((real-pos (1- pos)))
            (when (or (null best) (< real-pos best))
              (setf best real-pos))))))))



(defun position-in-text (text phrase)
  "Return the character position of PHRASE in TEXT, or NIL if not present."
  (search phrase text :test #'string=))


(defun in-any-window-p (pos windows)
  "Return T if POS falls inside any of the (start . end) WINDOWS."
  (some #'(lambda (w)
            (and (>= pos (car w))
                 (<  pos (cdr w))))
        windows))


(defun matched-phrase-spans (text)
  "Return a list of (start . end) spans for every phrase in *symptom-map*
   that appears in TEXT.  Used to mask out negation words that are part of
   a matched phrase rather than free-standing negation triggers.

   Example: in 'i am not hungry and have a fever', the phrase 'not hungry'
   spans positions 5-15.  The word 'not' at position 5 is inside this span
   and must NOT open a negation window."
  (let ((spans '()))
    (dolist (pair *symptom-map* spans)
      (let* ((phrase (car pair))
             (pos    (search phrase text :test #'string=)))
        (when pos
          (push (cons pos (+ pos (length phrase))) spans))))))


(defun pos-inside-any-span-p (pos spans)
  "Return T if POS falls inside any of the (start . end) SPANS."
  (some #'(lambda (s)
            (and (>= pos (car s))
                 (<  pos (cdr s))))
        spans))


(defun negation-windows-masked (text matched-spans)
  "Like negation-windows but ignores negation words whose position in TEXT
   falls inside one of MATCHED-SPANS.
   This prevents phrases like 'not hungry' or 'no appetite' from opening
   windows — the negation in those phrases is part of the symptom mapping,
   not a free-standing patient denial."
  (let ((padded-text (concatenate 'string " " text " "))
        (windows '()))
    (dolist (neg *negation-words*)
      (let* ((padded-neg (concatenate 'string " " neg " "))
             (neg-pos    (search padded-neg padded-text :test #'string=)))
        (when neg-pos
          (let ((real-pos (1- neg-pos)))   ; position in original text
            ;; only open a window if this negation word is NOT inside
            ;; a span already claimed by a matched symptom phrase
            (unless (pos-inside-any-span-p real-pos matched-spans)
              (let* ((search-from (+ neg-pos (length padded-neg) -1))
                     (rest-text   (if (< search-from (length text))
                                      (subseq text search-from)
                                      ""))
                     (breaker-offset (find-first-occurrence rest-text
                                                            *scope-breakers*))
                     (win-end (if breaker-offset
                                  (+ search-from breaker-offset)
                                  (length text))))
                (push (cons real-pos win-end) windows)))))))
    windows))


(defun symptom-negated-in-context-p (symptom-phrase full-text)
  "Return T if SYMPTOM-PHRASE should be treated as a denied symptom.

   The mapper already encodes meaning: ('not hungry' . loss_of_appetite)
   means the patient HAS loss_of_appetite.  So phrases whose own negation
   words are part of the matched span must never be denied by the window
   system.

   Algorithm:
   1. Collect all matched phrase spans in full-text.
   2. Build negation windows, masking out negation words inside those spans.
   3. Find the position of symptom-phrase in full-text.
   4. Return T if that position falls inside a (masked) negation window.
   5. Fallback: if phrase not found in full-text, use global detect-negation
      only if the full text has no matched spans (completely free-form text)."
  (let* ((spans   (matched-phrase-spans full-text))
         (windows (negation-windows-masked full-text spans))
         (pos     (position-in-text full-text symptom-phrase)))
    (cond
      ;; phrase found — check against masked windows only
      (pos  (in-any-window-p pos windows))
      ;; phrase not found (stop-word removal altered text) —
      ;; fallback to global negation only when no spans were matched
      ;; (i.e. we are in completely free-form unmatched text territory)
      (t    (and (null spans)
                 (detect-negation full-text))))))


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


(defun match-symptom-phrase-tagged (normalised-text full-text phrase-atom-pair)
  "Return a tagged pair (atom . negated-p) if PHRASE appears in NORMALISED-TEXT.
   FULL-TEXT is used for per-clause negation lookup (before stop-word removal).
   Returns NIL if no match."
  (let ((phrase (car phrase-atom-pair))
        (atom   (cdr phrase-atom-pair)))
    (when (string-contains-p normalised-text phrase)
      (cons atom (symptom-negated-in-context-p phrase full-text)))))


(defun find-all-matches (text symptom-map)
  "Apply match-symptom-phrase across all entries in SYMPTOM-MAP.
   Uses MAPCAR (higher-order) then filters NILs.
   Returns a list of matched Prolog atoms may contain duplicates."
  (remove-if #'null
             (mapcar #'(lambda (pair)
                         (match-symptom-phrase text pair))
                     symptom-map)))


(defun find-all-matches-tagged (normalised-text full-text symptom-map)
  "Like find-all-matches but returns (atom . negated-p) pairs.
   NORMALISED-TEXT is the cleaned text used for phrase matching.
   FULL-TEXT is the normalised-but-NOT-stop-word-stripped text,
   used for clause-level negation detection."
  (remove-if #'null
             (mapcar #'(lambda (pair)
                         (match-symptom-phrase-tagged
                           normalised-text full-text pair))
                     symptom-map)))


(defun deduplicate (lst)
  "Remove duplicate items from LST using REDUCE.
   Uses string= for string comparison, eql for symbols."
  (reduce #'(lambda (acc item)
              (if (member item acc :test #'equal)
                  acc
                  (append acc (list item))))
          lst
          :initial-value '()))


(defun deduplicate-tagged (tagged-list)
  "Deduplicate (atom . negated-p) pairs by atom.
   First occurrence wins (preserves negation status of first match)."
  (reduce #'(lambda (acc pair)
              (if (assoc (car pair) acc :test #'equal)
                  acc
                  (append acc (list pair))))
          tagged-list
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


(defun extract-symptoms-tagged (normalised-text full-text)
  "Like extract-symptoms but returns (atom . negated-p) pairs.
   Allows each symptom to carry its own negation flag.
   FULL-TEXT is the pre-stop-word-removal text for clause negation."
  (let* ((raw-tagged  (find-all-matches-tagged normalised-text full-text
                                               *symptom-map*))
         (deduped     (deduplicate-tagged raw-tagged))
         ;; subsumption: extract just atoms, run subsumption, then filter pairs
         (atoms-only  (mapcar #'car deduped))
         (kept-atoms  (subsume-generic-symptoms atoms-only)))
    (remove-if-not #'(lambda (pair)
                       (member (car pair) kept-atoms :test #'equal))
                   deduped)))


(defparameter *subsumption-map*
  '(
    (fever . ("low_grade_fever" "cyclical_fever"))
    ("skin_rash" . ("itchy_rash" "vesicular_rash" "rose_spot_rash"))
    (difficulty_breathing . ("shortness_of_breath")))
  "Alist of (generic . (specific...)).
  If ANY specific atom is present in the matched list, the generic is removed.
  Cough is handled at the mapper level -- generic cough phrases are written
  to not overlap with compound cough phrases.")


(defun subsume-generic-symptoms (symptom-list)
  "Remove generic symptom atoms when a more specific variant is present."
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

     (:confirmed  (fatigue cough ...)   <- symptoms patient HAS
      :denied     (fever ...)           <- symptoms patient does NOT have
      :negated    T/NIL                 <- global flag (kept for compatibility)
      :raw        original text
      :normalised cleaned text)"
  (let* ((normalised  (normalise-input raw-text))
         (cleaned     (remove-stop-words normalised))
         ;; tagged = list of (atom . negated-p)
         (tagged      (extract-symptoms-tagged cleaned normalised))
         (confirmed   (mapcar #'car
                        (remove-if #'cdr tagged)))
         (denied      (mapcar #'car
                        (remove-if-not #'cdr tagged)))
         ;; keep global :negated flag for any code that checks it
         (any-negated (some #'cdr tagged)))
    (list
      :confirmed  confirmed
      :denied     denied
      :symptoms   confirmed          ; backward-compat alias
      :negated    (if any-negated t nil)
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
  "Count how many symptoms from SYMPTOM-LIST appear in CANDIDATE-SYMPTOMS."
  (length
    (remove-if-not
      #'(lambda (s) (member s candidate-symptoms))
      symptom-list)))


(defun symptom-coverage-score (input-symptoms disease-symptoms)
  "Calculate what fraction of INPUT-SYMPTOMS appear in DISEASE-SYMPTOMS.
   Returns a float between 0.0 and 1.0."
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
     CONFIRMED:fatigue,cough|DENIED:fever|NEGATED:T

   CONFIRMED = symptoms the patient has.
   DENIED    = symptoms the patient explicitly does not have.
   NEGATED   = T if any negation was detected (kept for diagnostics).

   The Python bridge splits on | then on : to extract values.
   Old format SYMPTOMS:...|NEGATED:... is replaced by this richer format."
  (let* ((confirmed  (getf result :confirmed))
         (denied     (getf result :denied))
         (negated    (getf result :negated))
         (conf-strs  (symptoms-to-string-list confirmed))
         (deny-strs  (symptoms-to-string-list denied))
         (conf-part  (if conf-strs
                         (reduce #'(lambda (a b) (concatenate 'string a "," b))
                                 conf-strs)
                         ""))
         (deny-part  (if deny-strs
                         (reduce #'(lambda (a b) (concatenate 'string a "," b))
                                 deny-strs)
                         ""))
         (neg-part   (if negated "T" "NIL")))
    (concatenate 'string
                 "CONFIRMED:" conf-part
                 "|DENIED:"   deny-part
                 "|NEGATED:"  neg-part)))


;;; ================================================================
;;; SECTION 7 — ENTRY POINT FOR SUBPROCESS MODE
;;; ================================================================

(defun med-run-processor ()
  "Entry point when called as a subprocess by lisp_connector.py.
   Reads input text from command-line argument."
  (let* ((args      sb-ext:*posix-argv*)
         (raw-input (if (> (length args) 1)
                        (car (last args))
                        ""))
         (result    (med-process-input raw-input))
         (formatted (format-result-for-python result)))
    (write-line formatted)
    (finish-output)))