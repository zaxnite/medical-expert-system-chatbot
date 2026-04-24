;;;; ================================================================
;;;; symptom_mapper.lisp
;;;; Medical Expert System — BCS 222 Programming Paradigms
;;;; Role: Pure declarative mapping tables.
;;;;       Converts natural language phrases into Prolog symptom
;;;;       atoms used by knowledge_base.pl (15 diseases only).
;;;;
;;;; Functional paradigm justification:
;;;;   This file is entirely side-effect free — a collection of
;;;;   pure association lists (alists) that are never mutated.
;;;;   Lisp's native list processing makes these tables concise,
;;;;   readable, and trivially extensible.
;;;; ================================================================

(defparameter *symptom-map*
  '(
    ;; --- fever ---
    ("fever"                    . fever)
    ("high temperature"         . fever)
    ("high temp"                . fever)
    ("running a fever"          . fever)
    ("feeling hot"              . fever)
    ("elevated temp"            . fever)
    ("hyperthermia"             . fever)
    ("febrile"                  . fever)
    ("burning up"               . fever)
    ("temperature"              . fever)
    ("pyrexia"                  . fever)

    ;; --- cough ---
    ("cough"                    . cough)
    ("coughing"                 . cough)
    ("dry cough"                . cough)
    ("coughs"                   . cough)
    ("hacking"                  . cough)
    ("whooping cough"           . cough)
    ("tussis"                   . cough)

    ;; --- productive cough ---
    ("productive cough"         . "productive_cough")
    ("wet cough"                . "productive_cough")
    ("coughing up phlegm"       . "productive_cough")
    ("coughing up mucus"        . "productive_cough")
    ("sputum production"        . "productive_cough")
    ("phlegm"                   . "productive_cough")
    ("mucus"                    . "productive_cough")

    ;; --- fatigue ---
    ("fatigue"                  . fatigue)
    ("tired"                    . fatigue)
    ("tiredness"                . fatigue)
    ("exhausted"                . fatigue)
    ("exhaustion"               . fatigue)
    ("no energy"                . fatigue)
    ("weak"                     . fatigue)
    ("weakness"                 . fatigue)
    ("lethargy"                 . fatigue)
    ("lethargic"                . fatigue)
    ("sleepy"                   . fatigue)
    ("drowsy"                   . fatigue)    
    ("asthenia"                . fatigue)
    ("adynamia"                . fatigue)    

    ;; --- headache ---
    ("headache"                 . headache)
    ("head pain"                . headache)
    ("head hurts"               . headache)
    ("head ache"                . headache)
    ("cephalgia"                . headache)
    ("cephalalgic"              . headache)

    ;; --- sore throat ---
    ("sore throat"              . "sore_throat")
    ("throat pain"              . "sore_throat")
    ("painful throat"           . "sore_throat")
    ("throat hurts"             . "sore_throat")
    ("scratchy throat"          . "sore_throat")
    ("dysphagia"                . "sore_throat")
    ("odynophagia"              . "sore_throat")
    ("raw throat"               . "sore_throat")

    ;; --- nausea ---
    ("nausea"                   . nausea)
    ("nauseous"                 . nausea)
    ("feel sick"                . nausea)
    ("feeling sick"             . nausea)
    ("queasy"                   . nausea)

    ;; --- vomiting ---
    ("vomiting"                 . vomiting)
    ("vomit"                    . vomiting)
    ("throwing up"              . vomiting)
    ("threw up"                 . vomiting)
    ("emesis"                   . vomiting)
    ("regurgitation"            . vomiting)

    ;; --- chills ---
    ("chills"                   . chills)
    ("shivering"                . chills)
    ("shivery"                  . chills)
    ("shaking"                  . chills)
    ("feeling cold"             . chills)
    ("cold shivers"             . chills)

    ;; --- body aches ---
    ("body aches"               . "body_aches")
    ("muscle pain"              . "body_aches")
    ("muscle ache"              . "body_aches")
    ("aching muscles"           . "body_aches")
    ("body pain"                . "body_aches")
    ("everything hurts"         . "body_aches")
    ("myalgia"                  . "body_aches")

    ;; --- sudden onset ---
    ("sudden onset"             . "sudden_onset")
    ("came on suddenly"         . "sudden_onset")
    ("started suddenly"         . "sudden_onset")
    ("came on fast"             . "sudden_onset")
    ("hit me suddenly"          . "sudden_onset")

    ;; --- runny nose ---
    ("runny nose"               . "runny_nose")
    ("nose running"             . "runny_nose")
    ("nasal discharge"          . "runny_nose")
    ("runny"                    . "runny_nose")

    ;; --- sneezing ---
    ("sneezing"                 . sneezing)
    ("sneeze"                   . sneezing)
    ("keep sneezing"            . sneezing)

    ;; --- chest pain ---
    ("chest pain"               . "chest_pain")
    ("chest hurts"              . "chest_pain")
    ("pain in chest"            . "chest_pain")
    ("chest tightness"          . "chest_pain")
    ("tight chest"              . "chest_pain")

    ;; --- difficulty breathing ---
    ("difficulty breathing"     . "difficulty_breathing")
    ("hard to breathe"          . "difficulty_breathing")
    ("cant breathe"             . "difficulty_breathing")
    ("trouble breathing"        . "difficulty_breathing")
    ("breathless"               . "difficulty_breathing")

    ;; --- shortness of breath ---
    ("shortness of breath"      . "shortness_of_breath")
    ("short of breath"          . "shortness_of_breath")
    ("out of breath"            . "shortness_of_breath")

    ;; --- loss of smell ---
    ("loss of smell"            . "loss_of_smell")
    ("cant smell"               . "loss_of_smell")
    ("no sense of smell"        . "loss_of_smell")
    ("lost smell"               . "loss_of_smell")
    ("lost sense of smell"      . "loss_of_smell")
    ("lost my sense of smell"   . "loss_of_smell")
    ("lost my smell"            . "loss_of_smell")
    ("smell and taste"          . "loss_of_smell")
    ("lost smell and taste"     . "loss_of_smell")
    ("cannot smell"             . "loss_of_smell")
    ("unable to smell"          . "loss_of_smell")
    ("smell is gone"            . "loss_of_smell")
    ("lost ability to smell"    . "loss_of_smell")
    ("anosmia"                  . "loss_of_smell")

    ;; --- loss of taste ---
    ("loss of taste"            . "loss_of_taste")
    ("cant taste"               . "loss_of_taste")
    ("no sense of taste"        . "loss_of_taste")
    ("lost taste"               . "loss_of_taste")
    ("lost sense of taste"      . "loss_of_taste")
    ("lost my sense of taste"   . "loss_of_taste")
    ("lost my taste"            . "loss_of_taste")
    ("taste and smell"          . "loss_of_taste")
    ("lost taste and smell"     . "loss_of_taste")
    ("cannot taste"             . "loss_of_taste")
    ("unable to taste"          . "loss_of_taste")
    ("taste is gone"            . "loss_of_taste")
    ("lost ability to taste"    . "loss_of_taste")
    ("ageusia"                  . "loss_of_taste")

    ;; --- severe joint pain ---
    ("severe joint pain"        . "severe_joint_pain")
    ("joint pain"               . "severe_joint_pain")
    ("joints hurt"              . "severe_joint_pain")
    ("aching joints"            . "severe_joint_pain")
    ("arthralgia"               . "severe_joint_pain")
    ("joint ache"               . "severe_joint_pain")

    ;; --- skin rash ---
    ("skin rash"                . "skin_rash")
    ("rash"                     . "skin_rash")
    ("spots on skin"            . "skin_rash")

    ;; --- pain behind eyes ---
    ("pain behind eyes"         . "pain_behind_eyes")
    ("behind eye pain"          . "pain_behind_eyes")
    ("eye pain"                 . "pain_behind_eyes")

    ;; --- cyclical fever ---
    ("cyclical fever"           . "cyclical_fever")
    ("fever comes and goes"     . "cyclical_fever")
    ("intermittent fever"       . "cyclical_fever")
    ("recurring fever"          . "cyclical_fever")

    ;; --- sweating episodes ---
    ("sweating"                 . "sweating_episodes")
    ("sweating episodes"        . "sweating_episodes")
    ("sweating at night old"    . "sweating_episodes")  ; kept for malaria sweating
    ("heavy sweating"           . "sweating_episodes")

    ;; --- abdominal pain ---
    ("abdominal pain"           . "abdominal_pain")
    ("stomach pain"             . "abdominal_pain")
    ("belly pain"               . "abdominal_pain")
    ("tummy ache"               . "abdominal_pain")
    ("stomach cramps"           . "abdominal_pain")

    ;; --- diarrhea ---
    ("diarrhea"                 . diarrhea)
    ("diarrhoea"                . diarrhea)
    ("loose stools"             . diarrhea)
    ("watery stools"            . diarrhea)
    ("loose motions"            . diarrhea)
    ("diarrhoeal"               . diarrhea)
    ("gastroenteritis"          . diarrhea)

    ;; --- cramping ---
    ("cramping"                 . cramping)
    ("cramps"                   . cramping)
    ("stomach cramp"            . cramping)

    ;; --- low grade fever ---
    ("low grade fever"          . "low_grade_fever")
    ("mild fever"               . "low_grade_fever")
    ("slight fever"             . "low_grade_fever")

    ;; --- right lower quad pain ---
    ("right lower abdominal pain" . "right_lower_quad_pain")
    ("pain lower right"           . "right_lower_quad_pain")
    ("lower right pain"           . "right_lower_quad_pain")
    ("right side stomach pain"    . "right_lower_quad_pain")

    ;; --- rebound tenderness ---
    ("rebound tenderness"       . "rebound_tenderness")
    ("stomach tender"           . "rebound_tenderness")
    ("abdomen tender"           . "rebound_tenderness")

    ;; --- neck stiffness ---
    ("neck stiffness"           . "neck_stiffness")
    ("stiff neck"               . "neck_stiffness")
    ("cant move neck"           . "neck_stiffness")
    ("neck pain"                . "neck_stiffness")
    ("neck stiff"               . "neck_stiffness")
    ("neck very stiff"          . "neck_stiffness")

    ;; --- light sensitivity ---
    ("light sensitivity"        . "light_sensitivity")
    ("sensitive to light"       . "light_sensitivity")
    ("light hurts eyes"         . "light_sensitivity")
    ("photophobia"              . "light_sensitivity")

    ;; --- confusion ---
    ("confusion"                . confusion)
    ("confused"                 . confusion)
    ("disoriented"              . confusion)
    ("mental fog"               . confusion)
    ("delirium"                 . confusion)
    ("altered mental status"    . confusion)

    ;; --- pulsating pain ---
    ("pulsating pain"           . "pulsating_pain")
    ("throbbing headache"       . "pulsating_pain")
    ("throbbing pain"           . "pulsating_pain")
    ("pounding headache"        . "pulsating_pain")

    ;; --- visual aura ---
    ("visual aura"              . "visual_aura")
    ("aura"                     . "visual_aura")
    ("flashing lights"          . "visual_aura")
    ("blind spots"              . "visual_aura")

    ;; --- one sided pain ---
    ("one sided pain"           . "one_sided_pain")
    ("one side headache"        . "one_sided_pain")
    ("headache one side"        . "one_sided_pain")

    ;; --- tonsillar exudate ---
    ("white patches throat"     . "tonsillar_exudate")
    ("white spots throat"       . "tonsillar_exudate")
    ("pus on tonsils"           . "tonsillar_exudate")
    ("tonsillar exudate"        . "tonsillar_exudate")

    ;; --- swollen lymph nodes ---
    ("swollen lymph nodes"      . "swollen_lymph_nodes")
    ("swollen glands"           . "swollen_lymph_nodes")
    ("lumps in neck"            . "swollen_lymph_nodes")

    ;; --- excessive thirst ---
    ("excessive thirst"         . "excessive_thirst")
    ("very thirsty"             . "excessive_thirst")
    ("always thirsty"           . "excessive_thirst")
    ("drinking a lot"           . "excessive_thirst")
    ("polydipsia"               . "excessive_thirst")

    ;; --- frequent urination ---
    ("frequent urination"       . "frequent_urination")
    ("urinating a lot"          . "frequent_urination")
    ("peeing a lot"             . "frequent_urination")
    ("pee a lot"                . "frequent_urination")
    ("polyuria"                 . "frequent_urination")

    ;; --- blurred vision ---
    ("blurred vision"           . "blurred_vision")
    ("blurry vision"            . "blurred_vision")
    ("vision blurry"            . "blurred_vision")
    ("cant see clearly"         . "blurred_vision")
    ("fuzzy vision"             . "blurred_vision")

    ;; --- slow wound healing ---
    ("slow wound healing"       . "slow_wound_healing")
    ("wounds not healing"       . "slow_wound_healing")
    ("cuts not healing"         . "slow_wound_healing")
    ("slow healing"             . "slow_wound_healing")

    ;; --- weight gain ---
    ("weight gain"              . "weight_gain")
    ("gaining weight"           . "weight_gain")
    ("put on weight"            . "weight_gain")

    ;; --- cold intolerance ---
    ("cold intolerance"         . "cold_intolerance")
    ("always cold"              . "cold_intolerance")
    ("feel cold all the time"   . "cold_intolerance")
    ("feeling cold all the time". "cold_intolerance")
    ("feeling cold all time"    . "cold_intolerance")
    ("cant stand cold"          . "cold_intolerance")

    ;; --- dry skin ---
    ("dry skin"                 . "dry_skin")
    ("flaky skin"               . "dry_skin")
    ("rough skin"               . "dry_skin")

    ;; --- constipation ---
    ("constipation"             . constipation)
    ("cant go to toilet"        . constipation)
    ("no bowel movement"        . constipation)
    ("costiveness"              . constipation)
    ("obstructed bowels"        . constipation)

    ;; --- hair loss ---
    ("hair loss"                . "hair_loss")
    ("losing hair"              . "hair_loss")
    ("hair falling out"         . "hair_loss")
    ("alopecia"                 . "hair_loss")

    ;; --- pale skin ---
    ("pale skin"                . "pale_skin")
    ("pallor"                   . "pale_skin")
    ("looking pale"             . "pale_skin")
    ("skin looks pale"          . "pale_skin")

    ;; --- dizziness ---
    ("dizziness"                . dizziness)
    ("dizzy"                    . dizziness)
    ("lightheaded"              . dizziness)
    ("vertigo"                  . dizziness)
    ("feel faint"               . dizziness)
    ("giddiness"                . dizziness)
    ("presyncope"               . dizziness)

    ;; --- cold hands and feet ---
    ("cold hands and feet"      . "cold_hands_and_feet")
    ("cold hands"               . "cold_hands_and_feet")
    ("cold feet"                . "cold_hands_and_feet")
    ("hands always cold"        . "cold_hands_and_feet")

    ;; --- rose spot rash ---
    ("rose spots"               . "rose_spot_rash")
    ("rose spot rash"           . "rose_spot_rash")
    ("pink spots abdomen"       . "rose_spot_rash")

    ;; --- slow heart rate ---
    ("slow heart rate"          . "slow_heart_rate")
    ("slow pulse"               . "slow_heart_rate")
    ("bradycardia"              . "slow_heart_rate")
    ("low heart rate"           . "slow_heart_rate")

    ;; --- chronic cough (tuberculosis) ---
    ("chronic cough"            . "chronic_cough")
    ("cough for weeks"          . "chronic_cough")
    ("cough for months"         . "chronic_cough")
    ("persistent cough"         . "chronic_cough")
    ("coughing for a long time" . "chronic_cough")
    ("long term cough"          . "chronic_cough")

    ;; --- night sweats (tuberculosis) ---
    ("night sweats"             . "night_sweats")
    ("sweating at night"        . "night_sweats")
    ("wake up sweating"         . "night_sweats")
    ("sweat at night"           . "night_sweats")
    ("nocturnal sweating"       . "night_sweats")

    ;; --- weight loss (tuberculosis) ---
    ("weight loss"              . "weight_loss")
    ("losing weight"            . "weight_loss")
    ("lost weight"              . "weight_loss")
    ("unexplained weight loss"  . "weight_loss")
    ("unintentional weight loss". "weight_loss")
    ("dropped weight"           . "weight_loss")

    ;; --- haemoptysis (tuberculosis) ---
    ("coughing up blood"        . "haemoptysis")
    ("blood in sputum"          . "haemoptysis")
    ("blood when coughing"      . "haemoptysis")
    ("haemoptysis"              . "haemoptysis")
    ("hemoptysis"               . "haemoptysis")
    ("bloody phlegm"            . "haemoptysis")
    ("blood in mucus"           . "haemoptysis")

    ;; --- itchy rash (chickenpox) ---
    ("itchy rash"               . "itchy_rash")
    ("rash that itches"         . "itchy_rash")
    ("itchy spots"              . "itchy_rash")
    ("scratching rash"          . "itchy_rash")
    ("itching rash"             . "itchy_rash")
    ("pruritic rash"            . "itchy_rash")

    ;; --- vesicular rash (chickenpox) ---
    ("blisters"                 . "vesicular_rash")
    ("blister rash"             . "vesicular_rash")
    ("fluid filled blisters"    . "vesicular_rash")
    ("vesicular rash"           . "vesicular_rash")
    ("chickenpox"               . "vesicular_rash")
    ("pox"                      . "vesicular_rash")
    ("vesicles"                 . "vesicular_rash")

    ;; --- loss of appetite (chickenpox / peptic ulcer) ---
    ("loss of appetite"         . "loss_of_appetite")
    ("no appetite"              . "loss_of_appetite")
    ("not hungry"               . "loss_of_appetite")
    ("lost appetite"            . "loss_of_appetite")
    ("dont want to eat"         . "loss_of_appetite")
    ("anorexia"                 . "loss_of_appetite")
    ("not eating"               . "loss_of_appetite")

    ;; --- burning epigastric pain (peptic ulcer) ---
    ("burning stomach"          . "burning_epigastric_pain")
    ("burning pain stomach"     . "burning_epigastric_pain")
    ("burning pain in upper stomach" . "burning_epigastric_pain")
    ("burning upper stomach"    . "burning_epigastric_pain")
    ("epigastric pain"          . "burning_epigastric_pain")
    ("stomach burning"          . "burning_epigastric_pain")
    ("heartburn"                . "burning_epigastric_pain")
    ("acid pain"                . "burning_epigastric_pain")
    ("burning in stomach"       . "burning_epigastric_pain")
    ("ulcer pain"               . "burning_epigastric_pain")

    ;; --- bloating (peptic ulcer / IBS) ---
    ("bloating"                 . "bloating")
    ("bloated"                  . "bloating")
    ("feel bloated"             . "bloating")
    ("full of gas"              . "bloating")
    ("gassy"                    . "bloating")
    ("gas and bloating"         . "bloating")
    ("distended stomach"        . "bloating")
    ("abdominal distension"     . "bloating")
  ))

;;; ----------------------------------------------------------------
;;; NEGATION WORDS
;;; ----------------------------------------------------------------
(defparameter *negation-words*
  '("no" "not" "dont" "don't" "without" "never"
    "no sign of" "no signs of" "absent"
    "haven't" "havent" "didnt" "didn't"))

;;; ----------------------------------------------------------------
;;; STOP WORDS
;;; ----------------------------------------------------------------
(defparameter *stop-words*
  '("i" "i'm" "im" "i've" "ive" "i have" "i am"
    "have" "has" "had" "been" "am" "are" "is" "was"
    "a" "an" "the" "some" "any" "very" "quite" "really"
    "bit" "little" "lot" "lots" "much" "many"
    "also" "and" "or" "but" "so" "with" "my" "me"
    "feel" "feeling" "felt" "seems" "seem" "think"
    "getting" "got" "having" "experiencing"
    "since" "for" "about" "from" "still" "patient" "appears" ))