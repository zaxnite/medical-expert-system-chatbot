;;;; ================================================================
;;;; symptom_mapper.lisp
;;;; Medical Expert System — BCS 222 Programming Paradigms
;;;; Role: Pure declarative mapping tables.
;;;;       Converts natural language phrases into Prolog symptom
;;;;       atoms used by knowledge_base.pl (20 diseases).
;;;;
;;;; Disease labels shown for symptoms specific to 1-3 diseases.
;;;; Symptoms shared by 4+ diseases have no label.
;;;;
;;;; Overlap policy: shorter generic phrases (cough, fever, rash)
;;;; are kept because find-all-matches collects ALL matches —
;;;; both the generic and the specific atom will fire, which is
;;;; the correct behaviour. Dangerous overlaps (where the short
;;;; phrase maps to the WRONG atom) have been removed or rephrased.
;;;; ================================================================

(defparameter *symptom-map*
  '(
    ;; ================================================================
    ;; GROUP A — RESPIRATORY SYMPTOMS
    ;; ================================================================

    ;; --- fever (shared by 10+ diseases — no label) ---
    ("fever"                        . fever)
    ("high temperature"             . fever)
    ("high temp"                    . fever)
    ("running a fever"              . fever)
    ("feeling hot"                  . fever)
    ("elevated temp"                . fever)
    ("hyperthermia"                 . fever)
    ("febrile"                      . fever)
    ("temperature"                  . fever)
    ("pyrexia"                      . fever)
    ("got a fever"                  . fever)
    ("have a fever"                 . fever)
    ("body is hot"                  . fever)
    ("feel feverish"                . fever)
    ("feverish"                     . fever)

    ;; --- low grade fever — Gastroenteritis / Tuberculosis ---
    ("low grade fever"              . "low_grade_fever")
    ("mild fever"                   . "low_grade_fever")
    ("slight fever"                 . "low_grade_fever")
    ("low fever"                    . "low_grade_fever")
    ("low grade temperature"        . "low_grade_fever")
    ("persistent low fever"         . "low_grade_fever")
    ("mildly feverish"              . "low_grade_fever")
    ("slightly elevated temperature" . "low_grade_fever")
    ("temperature a little high"    . "low_grade_fever")

    ;; --- cyclical fever — Malaria ---
    ("cyclical fever"               . "cyclical_fever")
    ("fever comes and goes"         . "cyclical_fever")
    ("intermittent fever"           . "cyclical_fever")
    ("recurring fever"              . "cyclical_fever")
    ("fever every few days"         . "cyclical_fever")
    ("fever keeps coming back"      . "cyclical_fever")
    ("periodic fever"               . "cyclical_fever")
    ("fever in cycles"              . "cyclical_fever")
    ("fever on and off"             . "cyclical_fever")
    ("recurrent fever"              . "cyclical_fever")

    ;; --- cough (shared by 4+ diseases — no label) ---
    ;; NOTE: "cough" and "coughing" are intentionally NOT listed as bare
    ;; single-word phrases because string-contains-p would match them inside
    ;; "productive cough", "chronic cough", "coughing up phlegm" etc.,
    ;; causing the generic atom to fire alongside the specific one.
    ;; Only phrases that cannot appear inside a more specific cough entry
    ;; are listed here.
    ("i have a cough"              . cough)
    ("got a cough"                 . cough)
    ("have a cough"                . cough)
    ("dry cough"                   . cough)
    ("hacking cough"               . cough)
    ("whooping cough"              . cough)
    ("tussis"                      . cough)
    ("cant stop coughing"          . cough)
    ("keep coughing"               . cough)
    ("tickly cough"                . cough)
    ("irritating cough"            . cough)
    ("barking cough"               . cough)
    ("coughs a lot"                . cough)
    ("cough a lot"                 . cough)
    ("non stop coughing"           . cough)

    ;; --- productive cough — Pneumonia / Tuberculosis ---
    ("productive cough"             . "productive_cough")
    ("wet cough"                    . "productive_cough")
    ("coughing up phlegm"           . "productive_cough")
    ("coughing up mucus"            . "productive_cough")
    ("sputum production"            . "productive_cough")
    ("phlegm"                        . "productive_cough")
    ("phlegm when coughing"         . "productive_cough")
    ("chesty cough"                 . "productive_cough")
    ("cough with mucus"             . "productive_cough")
    ("bringing up phlegm"           . "productive_cough")
    ("spitting up mucus"            . "productive_cough")
    ("thick mucus from cough"       . "productive_cough")

    ;; --- chronic cough — Tuberculosis ---
    ("chronic cough"                . "chronic_cough")
    ("cough for weeks"              . "chronic_cough")
    ("cough for months"             . "chronic_cough")
    ("persistent cough"             . "chronic_cough")
    ("coughing for a long time"     . "chronic_cough")
    ("long term cough"              . "chronic_cough")
    ("prolonged cough"              . "chronic_cough")
    ("cough that wont go away"      . "chronic_cough")
    ("cough that doesnt go away"    . "chronic_cough")
    ("months of coughing"           . "chronic_cough")
    ("weeks of coughing"            . "chronic_cough")

    ;; --- haemoptysis — Tuberculosis ---
    ("coughing up blood"            . "haemoptysis")
    ("blood in sputum"              . "haemoptysis")
    ("blood when coughing"          . "haemoptysis")
    ("haemoptysis"                  . "haemoptysis")
    ("hemoptysis"                   . "haemoptysis")
    ("bloody phlegm"                . "haemoptysis")
    ("blood in mucus from lungs"    . "haemoptysis")
    ("blood stained mucus"          . "haemoptysis")
    ("spitting blood"               . "haemoptysis")
    ("cough up blood"               . "haemoptysis")
    ("blood in cough"               . "haemoptysis")

    ;; --- chest pain — Pneumonia / Tuberculosis ---
    ("chest pain"                   . "chest_pain")
    ("chest hurts"                  . "chest_pain")
    ("pain in chest"                . "chest_pain")
    ("chest tightness"              . "chest_pain")
    ("tight chest"                  . "chest_pain")
    ("pressure in chest"            . "chest_pain")
    ("chest pressure"               . "chest_pain")
    ("chest feels tight"            . "chest_pain")
    ("pain in my chest"             . "chest_pain")
    ("chest ache"                   . "chest_pain")

    ;; --- difficulty breathing — Pneumonia ---
    ("difficulty breathing"         . "difficulty_breathing")
    ("hard to breathe"              . "difficulty_breathing")
    ("cant breathe"                 . "difficulty_breathing")
    ("trouble breathing"            . "difficulty_breathing")
    ("breathless"                   . "difficulty_breathing")
    ("laboured breathing"           . "difficulty_breathing")
    ("struggling to breathe"        . "difficulty_breathing")
    ("breathing is difficult"       . "difficulty_breathing")
    ("breathing problems"           . "difficulty_breathing")
    ("cannot breathe properly"      . "difficulty_breathing")
    ("breathing hard"               . "difficulty_breathing")

    ;; --- shortness of breath — Covid19 / Anemia ---
    ("shortness of breath"          . "shortness_of_breath")
    ("short of breath"              . "shortness_of_breath")
    ("out of breath"                . "shortness_of_breath")
    ("get winded easily"            . "shortness_of_breath")
    ("winded"                       . "shortness_of_breath")
    ("cant catch my breath"         . "shortness_of_breath")
    ("panting"                      . "shortness_of_breath")
    ("dyspnoea"                     . "shortness_of_breath")
    ("dyspnea"                      . "shortness_of_breath")
    ("losing breath"                . "shortness_of_breath")

    ;; ================================================================
    ;; GROUP B — SYSTEMIC / INFECTIOUS SYMPTOMS
    ;; ================================================================

    ;; --- fatigue (shared by 13 diseases — no label) ---
    ("fatigue"                      . fatigue)
    ("tired"                        . fatigue)
    ("tiredness"                    . fatigue)
    ("exhausted"                    . fatigue)
    ("exhaustion"                   . fatigue)
    ("no energy"                    . fatigue)
    ("weak"                         . fatigue)
    ("weakness"                     . fatigue)
    ("lethargy"                     . fatigue)
    ("lethargic"                    . fatigue)
    ("sleepy"                       . fatigue)
    ("drowsy"                       . fatigue)
    ("asthenia"                     . fatigue)
    ("adynamia"                     . fatigue)
    ("run down"                     . fatigue)
    ("wiped out"                    . fatigue)
    ("no strength"                  . fatigue)
    ("cant get out of bed"          . fatigue)
    ("always tired"                 . fatigue)
    ("drained of energy"            . fatigue)

    ;; --- body aches — Influenza ---
    ("body aches"                   . "body_aches")
    ("muscle pain"                  . "body_aches")
    ("muscle ache"                  . "body_aches")
    ("aching muscles"               . "body_aches")
    ("body pain"                    . "body_aches")
    ("everything hurts"             . "body_aches")
    ("myalgia"                      . "body_aches")
    ("muscles aching"               . "body_aches")
    ("all over pain"                . "body_aches")
    ("muscles sore"                 . "body_aches")
    ("sore muscles"                 . "body_aches")
    ("aching all over"              . "body_aches")

    ;; --- chills — Influenza / Malaria / Chickenpox ---
    ("chills"                       . chills)
    ("shivering"                    . chills)
    ("shivery"                      . chills)
    ("shaking with cold"            . chills)
    ("feeling cold and shaking"     . chills)
    ("cold shivers"                 . chills)
    ("rigor"                        . chills)
    ("rigors"                       . chills)
    ("teeth chattering"             . chills)
    ("trembling from cold"          . chills)
    ("goosebumps all over"          . chills)

    ;; --- sudden onset — Influenza ---
    ("sudden onset"                 . "sudden_onset")
    ("came on suddenly"             . "sudden_onset")
    ("started suddenly"             . "sudden_onset")
    ("came on fast"                 . "sudden_onset")
    ("hit me suddenly"              . "sudden_onset")
    ("came on out of nowhere"       . "sudden_onset")
    ("started all at once"          . "sudden_onset")
    ("happened overnight"           . "sudden_onset")
    ("felt fine then suddenly sick" . "sudden_onset")
    ("rapid onset"                  . "sudden_onset")

    ;; --- night sweats — Tuberculosis ---
    ("night sweats"                 . "night_sweats")
    ("sweating at night"            . "night_sweats")
    ("wake up sweating"             . "night_sweats")
    ("sweat at night"               . "night_sweats")
    ("nocturnal sweating"           . "night_sweats")
    ("soaked in sweat at night"     . "night_sweats")
    ("drenched in sweat at night"   . "night_sweats")
    ("waking up wet with sweat"     . "night_sweats")
    ("sheets soaked in sweat"       . "night_sweats")
    ("excessive sweating at night"  . "night_sweats")
    ("soaking the sheets"           . "night_sweats")

    ;; --- sweating episodes — Malaria ---
    ("sweating"                     . "sweating_episodes")
    ("sweating episodes"            . "sweating_episodes")
    ("heavy sweating"               . "sweating_episodes")
    ("profuse sweating"             . "sweating_episodes")
    ("drenching sweats"             . "sweating_episodes")
    ("episodes of sweating"         . "sweating_episodes")
    ("hot sweats"                   . "sweating_episodes")
    ("soaking sweats"               . "sweating_episodes")
    ("diaphoresis"                  . "sweating_episodes")

    ;; --- weight loss — Tuberculosis ---
    ("weight loss"                  . "weight_loss")
    ("losing weight"                . "weight_loss")
    ("lost weight"                  . "weight_loss")
    ("unexplained weight loss"      . "weight_loss")
    ("unintentional weight loss"    . "weight_loss")
    ("dropped weight"               . "weight_loss")
    ("losing a lot of weight"       . "weight_loss")
    ("lost a lot of weight"         . "weight_loss")
    ("dramatic weight loss"         . "weight_loss")
    ("getting thinner"              . "weight_loss")
    ("clothes too big now"          . "weight_loss")
    ("wasting away"                 . "weight_loss")

    ;; --- weight gain — Hypothyroidism ---
    ("weight gain"                  . "weight_gain")
    ("gaining weight"               . "weight_gain")
    ("put on weight"                . "weight_gain")
    ("putting on weight"            . "weight_gain")
    ("getting heavier"              . "weight_gain")
    ("gained a lot of weight"       . "weight_gain")
    ("keep gaining weight"          . "weight_gain")
    ("unexplained weight gain"      . "weight_gain")
    ("clothes getting tight"        . "weight_gain")
    ("body getting bigger"          . "weight_gain")

    ;; ================================================================
    ;; GROUP C — HEAD / NEURO / ENT SYMPTOMS
    ;; ================================================================

    ;; --- headache (shared by 9 diseases — no label) ---
    ("headache"                     . headache)
    ("head pain"                    . headache)
    ("head hurts"                   . headache)
    ("head ache"                    . headache)
    ("cephalgia"                    . headache)
    ("my head hurts"                . headache)
    ("sore head"                    . headache)
    ("splitting headache"           . headache)
    ("bad headache"                 . headache)
    ("severe headache"              . headache)
    ("head is killing me"           . headache)

    ;; --- pulsating pain — Migraine ---
    ("pulsating pain"               . "pulsating_pain")
    ("throbbing headache"           . "pulsating_pain")
    ("throbbing pain in head"       . "pulsating_pain")
    ("pounding headache"            . "pulsating_pain")
    ("pulsing pain"                 . "pulsating_pain")
    ("heartbeat in my head"         . "pulsating_pain")
    ("head pounds"                  . "pulsating_pain")
    ("pulsating headache"           . "pulsating_pain")
    ("rhythmic head pain"           . "pulsating_pain")
    ("banging in my head"           . "pulsating_pain")

    ;; --- one sided pain — Migraine ---
    ("one sided pain"               . "one_sided_pain")
    ("one side headache"            . "one_sided_pain")
    ("headache one side"            . "one_sided_pain")
    ("pain on one side of head"     . "one_sided_pain")
    ("left side headache"           . "one_sided_pain")
    ("right side headache"          . "one_sided_pain")
    ("hemicrania"                   . "one_sided_pain")
    ("half head pain"               . "one_sided_pain")
    ("unilateral headache"          . "one_sided_pain")
    ("headache on one side"         . "one_sided_pain")

    ;; --- visual aura — Migraine ---
    ("visual aura"                  . "visual_aura")
    ("aura"                         . "visual_aura")
    ("flashing lights"              . "visual_aura")
    ("blind spots in vision"        . "visual_aura")
    ("seeing flashing lights"       . "visual_aura")
    ("zigzag lines in vision"       . "visual_aura")
    ("visual disturbance"           . "visual_aura")
    ("shimmering vision"            . "visual_aura")
    ("spots in vision"              . "visual_aura")
    ("tunnel vision"                . "visual_aura")
    ("scotoma"                      . "visual_aura")
    ("lights before headache"       . "visual_aura")

    ;; --- light sensitivity — Meningitis / Migraine / Tension Headache ---
    ("light sensitivity"            . "light_sensitivity")
    ("sensitive to light"           . "light_sensitivity")
    ("light hurts eyes"             . "light_sensitivity")
    ("photophobia"                  . "light_sensitivity")
    ("light is painful"             . "light_sensitivity")
    ("cant stand bright light"      . "light_sensitivity")
    ("eyes hurt in light"           . "light_sensitivity")
    ("bright light hurts"           . "light_sensitivity")
    ("eyes sensitive to light"      . "light_sensitivity")
    ("light bothers me"             . "light_sensitivity")
    ("squinting in light"           . "light_sensitivity")

    ;; --- confusion — Meningitis ---
    ("confusion"                    . confusion)
    ("confused"                     . confusion)
    ("disoriented"                  . confusion)
    ("mental fog"                   . confusion)
    ("delirium"                     . confusion)
    ("altered mental status"        . confusion)
    ("not thinking clearly"         . confusion)
    ("brain fog"                    . confusion)
    ("cant think straight"          . confusion)
    ("muddled thinking"             . confusion)
    ("disorientated"                . confusion)
    ("dont know where i am"         . confusion)

    ;; --- neck stiffness — Meningitis / Tension Headache ---
    ("neck stiffness"               . "neck_stiffness")
    ("stiff neck"                   . "neck_stiffness")
    ("cant move neck"               . "neck_stiffness")
    ("neck pain"                    . "neck_stiffness")
    ("neck stiff"                   . "neck_stiffness")
    ("neck very stiff"              . "neck_stiffness")
    ("cant turn neck"               . "neck_stiffness")
    ("neck feels rigid"             . "neck_stiffness")
    ("stiffness in neck"            . "neck_stiffness")
    ("nuchal rigidity"              . "neck_stiffness")
    ("neck wont move"               . "neck_stiffness")

    ;; --- sore throat — Common Cold / Strep Throat ---
    ("sore throat"                  . "sore_throat")
    ("throat pain"                  . "sore_throat")
    ("painful throat"               . "sore_throat")
    ("throat hurts"                 . "sore_throat")
    ("scratchy throat"              . "sore_throat")
    ("dysphagia"                    . "sore_throat")
    ("odynophagia"                  . "sore_throat")
    ("raw throat"                   . "sore_throat")
    ("throat is sore"               . "sore_throat")
    ("pain swallowing"              . "sore_throat")
    ("hard to swallow"              . "sore_throat")
    ("throat feels rough"           . "sore_throat")
    ("burning throat"               . "sore_throat")

    ;; --- tonsillar exudate — Strep Throat ---
    ("white patches throat"         . "tonsillar_exudate")
    ("white spots throat"           . "tonsillar_exudate")
    ("pus on tonsils"               . "tonsillar_exudate")
    ("tonsillar exudate"            . "tonsillar_exudate")
    ("white coating on throat"      . "tonsillar_exudate")
    ("white stuff on tonsils"       . "tonsillar_exudate")
    ("white patches on tonsils"     . "tonsillar_exudate")
    ("pus patches on throat"        . "tonsillar_exudate")
    ("exudate on tonsils"           . "tonsillar_exudate")
    ("throat covered in white"      . "tonsillar_exudate")

    ;; --- swollen lymph nodes — Strep Throat ---
    ("swollen lymph nodes"          . "swollen_lymph_nodes")
    ("swollen glands"               . "swollen_lymph_nodes")
    ("lumps in neck"                . "swollen_lymph_nodes")
    ("glands in neck swollen"       . "swollen_lymph_nodes")
    ("tender neck glands"           . "swollen_lymph_nodes")
    ("lymph nodes swollen"          . "swollen_lymph_nodes")
    ("swollen neck glands"          . "swollen_lymph_nodes")
    ("glands up"                    . "swollen_lymph_nodes")
    ("neck glands swollen"          . "swollen_lymph_nodes")
    ("lymphadenopathy"              . "swollen_lymph_nodes")

    ;; --- runny nose — Common Cold ---
    ("runny nose"                   . "runny_nose")
    ("nose running"                 . "runny_nose")
    ("nasal discharge"              . "runny_nose")
    ("runny"                        . "runny_nose")
    ("nose dripping"                . "runny_nose")
    ("nasal mucus discharge"        . "runny_nose")
    ("snot"                         . "runny_nose")
    ("rhinorrhoea"                  . "runny_nose")
    ("rhinorrhea"                   . "runny_nose")
    ("streaming nose"               . "runny_nose")
    ("nose wont stop running"       . "runny_nose")

    ;; --- sneezing — Common Cold ---
    ("sneezing"                     . sneezing)
    ("sneeze"                       . sneezing)
    ("keep sneezing"                . sneezing)
    ("sneezes a lot"                . sneezing)
    ("cant stop sneezing"           . sneezing)
    ("constant sneezing"            . sneezing)
    ("sneezing a lot"               . sneezing)
    ("frequent sneezing"            . sneezing)
    ("fit of sneezing"              . sneezing)

    ;; --- pain behind eyes — Dengue Fever ---
    ("pain behind eyes"             . "pain_behind_eyes")
    ("behind eye pain"              . "pain_behind_eyes")
    ("eye pain"                     . "pain_behind_eyes")
    ("pain behind my eyes"          . "pain_behind_eyes")
    ("pressure behind eyes"         . "pain_behind_eyes")
    ("eyes aching deeply"           . "pain_behind_eyes")
    ("sore eyes deep"               . "pain_behind_eyes")
    ("retro-orbital pain"           . "pain_behind_eyes")
    ("retroorbital pain"            . "pain_behind_eyes")
    ("deep pain in eyes"            . "pain_behind_eyes")

    ;; --- loss of smell — Covid19 ---
    ("loss of smell"                . "loss_of_smell")
    ("cant smell"                   . "loss_of_smell")
    ("no sense of smell"            . "loss_of_smell")
    ("lost smell"                   . "loss_of_smell")
    ("lost sense of smell"          . "loss_of_smell")
    ("lost my sense of smell"       . "loss_of_smell")
    ("lost my smell"                . "loss_of_smell")
    ("smell and taste gone"         . "loss_of_smell")
    ("cannot smell"                 . "loss_of_smell")
    ("unable to smell"              . "loss_of_smell")
    ("smell is gone"                . "loss_of_smell")
    ("lost ability to smell"        . "loss_of_smell")
    ("anosmia"                      . "loss_of_smell")
    ("nose cant smell anything"     . "loss_of_smell")
    ("food has no smell"            . "loss_of_smell")

    ;; --- loss of taste — Covid19 ---
    ("loss of taste"                . "loss_of_taste")
    ("cant taste"                   . "loss_of_taste")
    ("no sense of taste"            . "loss_of_taste")
    ("lost taste"                   . "loss_of_taste")
    ("lost sense of taste"          . "loss_of_taste")
    ("lost my sense of taste"       . "loss_of_taste")
    ("lost my taste"                . "loss_of_taste")
    ("taste and smell gone"         . "loss_of_taste")
    ("cannot taste"                 . "loss_of_taste")
    ("unable to taste"              . "loss_of_taste")
    ("taste is gone"                . "loss_of_taste")
    ("lost ability to taste"        . "loss_of_taste")
    ("ageusia"                      . "loss_of_taste")
    ("food has no taste"            . "loss_of_taste")
    ("everything tastes the same"   . "loss_of_taste")

    ;; ================================================================
    ;; GROUP D — GASTROINTESTINAL SYMPTOMS
    ;; ================================================================

    ;; --- nausea (shared by 5 diseases — no label) ---
    ("nausea"                       . nausea)
    ("nauseous"                     . nausea)
    ("feel sick"                    . nausea)
    ("feeling sick"                 . nausea)
    ("queasy"                       . nausea)
    ("stomach turning"              . nausea)
    ("sick to my stomach"           . nausea)
    ("urge to be sick"              . nausea)
    ("wave of nausea"               . nausea)
    ("bile rising"                  . nausea)
    ("about to be sick"             . nausea)

    ;; --- vomiting — Gastroenteritis / Appendicitis / Peptic Ulcer ---
    ("vomiting"                     . vomiting)
    ("vomit"                        . vomiting)
    ("throwing up"                  . vomiting)
    ("threw up"                     . vomiting)
    ("emesis"                       . vomiting)
    ("regurgitation"                . vomiting)
    ("being sick"                   . vomiting)
    ("puking"                       . vomiting)
    ("puke"                         . vomiting)
    ("retching"                     . vomiting)
    ("heaving"                      . vomiting)
    ("bringing food back up"        . vomiting)

    ;; --- abdominal pain — Gastroenteritis / Typhoid Fever / Irritable Bowel Syndrome ---
    ("abdominal pain"               . "abdominal_pain")
    ("stomach pain"                 . "abdominal_pain")
    ("belly pain"                   . "abdominal_pain")
    ("tummy ache"                   . "abdominal_pain")
    ("gut pain"                     . "abdominal_pain")
    ("stomach ache"                 . "abdominal_pain")
    ("abdo pain"                    . "abdominal_pain")
    ("my stomach hurts"             . "abdominal_pain")
    ("pain in my stomach"           . "abdominal_pain")
    ("abdomen pain"                 . "abdominal_pain")
    ("stomachache"                  . "abdominal_pain")
    ("stomach is hurting"           . "abdominal_pain")

    ;; --- diarrhea — Gastroenteritis / Irritable Bowel Syndrome ---
    ("diarrhea"                     . diarrhea)
    ("diarrhoea"                    . diarrhea)
    ("loose stools"                 . diarrhea)
    ("watery stools"                . diarrhea)
    ("loose motions"                . diarrhea)
    ("diarrhoeal"                   . diarrhea)
    ("the runs"                     . diarrhea)
    ("watery poo"                   . diarrhea)
    ("frequent loose stools"        . diarrhea)
    ("loose bowels"                 . diarrhea)
    ("bowel upset"                  . diarrhea)
    ("runny stomach"                . diarrhea)
    ("upset stomach with loose poo" . diarrhea)

    ;; --- cramping — Gastroenteritis / Irritable Bowel Syndrome ---
    ("cramping"                     . cramping)
    ("cramps"                       . cramping)
    ("stomach cramp"                . cramping)
    ("abdominal cramps"             . cramping)
    ("gut cramps"                   . cramping)
    ("bowel cramps"                 . cramping)
    ("intestinal cramps"            . cramping)
    ("gripping pain in stomach"     . cramping)
    ("stomach spasms"               . cramping)
    ("spasms in gut"                . cramping)

    ;; --- right lower quad pain — Appendicitis ---
    ("right lower abdominal pain"   . "right_lower_quad_pain")
    ("pain lower right"             . "right_lower_quad_pain")
    ("lower right pain"             . "right_lower_quad_pain")
    ("right side stomach pain"      . "right_lower_quad_pain")
    ("pain right side abdomen"      . "right_lower_quad_pain")
    ("right lower stomach pain"     . "right_lower_quad_pain")
    ("pain in right lower abdomen"  . "right_lower_quad_pain")
    ("right iliac fossa pain"       . "right_lower_quad_pain")
    ("hurts lower right side"       . "right_lower_quad_pain")
    ("pain lower right belly"       . "right_lower_quad_pain")

    ;; --- rebound tenderness — Appendicitis ---
    ("rebound tenderness"           . "rebound_tenderness")
    ("stomach tender"               . "rebound_tenderness")
    ("abdomen tender"               . "rebound_tenderness")
    ("stomach very tender"          . "rebound_tenderness")
    ("touch hurts my stomach"       . "rebound_tenderness")
    ("pressing on stomach hurts"    . "rebound_tenderness")
    ("belly very tender"            . "rebound_tenderness")
    ("tender abdomen when touched"  . "rebound_tenderness")
    ("cant touch my stomach"        . "rebound_tenderness")
    ("peritonism"                   . "rebound_tenderness")

    ;; --- constipation — Hypothyroidism / Irritable Bowel Syndrome ---
    ("constipation"                 . constipation)
    ("cant go to toilet"            . constipation)
    ("no bowel movement"            . constipation)
    ("costiveness"                  . constipation)
    ("obstructed bowels"            . constipation)
    ("not able to poo"              . constipation)
    ("blocked up"                   . constipation)
    ("bowels not moving"            . constipation)
    ("hard to pass stool"           . constipation)
    ("straining to go toilet"       . constipation)
    ("irregular bowels"             . constipation)

    ;; --- bloating — Peptic Ulcer / Irritable Bowel Syndrome ---
    ("bloating"                     . "bloating")
    ("bloated"                      . "bloating")
    ("feel bloated"                 . "bloating")
    ("full of gas"                  . "bloating")
    ("gassy"                        . "bloating")
    ("gas and bloating"             . "bloating")
    ("distended stomach"            . "bloating")
    ("abdominal distension"         . "bloating")
    ("trapped wind"                 . "bloating")
    ("stomach feels swollen"        . "bloating")
    ("swollen belly from gas"       . "bloating")
    ("belly feels full"             . "bloating")

    ;; --- burning epigastric pain — Peptic Ulcer ---
    ("burning stomach"              . "burning_epigastric_pain")
    ("burning pain in stomach"      . "burning_epigastric_pain")
    ("burning pain in upper stomach" . "burning_epigastric_pain")
    ("burning upper stomach"        . "burning_epigastric_pain")
    ("epigastric pain"              . "burning_epigastric_pain")
    ("stomach is burning"           . "burning_epigastric_pain")
    ("heartburn"                    . "burning_epigastric_pain")
    ("acid pain"                    . "burning_epigastric_pain")
    ("burning in stomach"           . "burning_epigastric_pain")
    ("ulcer pain"                   . "burning_epigastric_pain")
    ("acid reflux"                  . "burning_epigastric_pain")
    ("burning feeling after eating" . "burning_epigastric_pain")
    ("pain after eating"            . "burning_epigastric_pain")
    ("upper abdominal burning"      . "burning_epigastric_pain")
    ("gnawing stomach pain"         . "burning_epigastric_pain")

    ;; --- loss of appetite — Chickenpox / Peptic Ulcer ---
    ("loss of appetite"             . "loss_of_appetite")
    ("no appetite"                  . "loss_of_appetite")
    ("not hungry"                   . "loss_of_appetite")
    ("lost appetite"                . "loss_of_appetite")
    ("dont want to eat"             . "loss_of_appetite")
    ("anorexia"                     . "loss_of_appetite")
    ("not eating"                   . "loss_of_appetite")
    ("cant eat"                     . "loss_of_appetite")
    ("off food"                     . "loss_of_appetite")
    ("no desire to eat"             . "loss_of_appetite")
    ("food not appealing"           . "loss_of_appetite")
    ("lost interest in food"        . "loss_of_appetite")

    ;; ================================================================
    ;; GROUP E — SKIN SYMPTOMS
    ;; ================================================================

    ;; --- skin rash — Dengue Fever ---
    ("skin rash"                    . "skin_rash")
    ("rash"                         . "skin_rash")
    ("spots on skin"                . "skin_rash")
    ("rash on body"                 . "skin_rash")
    ("marks on skin"                . "skin_rash")
    ("skin eruption"                . "skin_rash")
    ("rash spreading"               . "skin_rash")
    ("skin breaking out"            . "skin_rash")
    ("red patches on skin"          . "skin_rash")
    ("rash all over"                . "skin_rash")

    ;; --- itchy rash — Chickenpox ---
    ("itchy rash"                   . "itchy_rash")
    ("rash that itches"             . "itchy_rash")
    ("itchy spots"                  . "itchy_rash")
    ("scratching rash"              . "itchy_rash")
    ("itching rash"                 . "itchy_rash")
    ("pruritic rash"                . "itchy_rash")
    ("rash with itching"            . "itchy_rash")
    ("itching all over"             . "itchy_rash")
    ("really itchy spots"           . "itchy_rash")
    ("rash is very itchy"           . "itchy_rash")
    ("intensely itchy spots"        . "itchy_rash")

    ;; --- vesicular rash — Chickenpox ---
    ("blisters"                     . "vesicular_rash")
    ("blister rash"                 . "vesicular_rash")
    ("fluid filled blisters"        . "vesicular_rash")
    ("vesicular rash"               . "vesicular_rash")
    ("chickenpox"                   . "vesicular_rash")
    ("pox"                          . "vesicular_rash")
    ("vesicles"                     . "vesicular_rash")
    ("water blisters"               . "vesicular_rash")
    ("spots with fluid inside"      . "vesicular_rash")
    ("blistery rash"                . "vesicular_rash")
    ("pustules"                     . "vesicular_rash")
    ("small fluid bubbles on skin"  . "vesicular_rash")

    ;; --- rose spot rash — Typhoid Fever ---
    ("rose spots"                   . "rose_spot_rash")
    ("rose spot rash"               . "rose_spot_rash")
    ("pink spots on abdomen"        . "rose_spot_rash")
    ("pink spots on stomach"        . "rose_spot_rash")
    ("small pink spots"             . "rose_spot_rash")
    ("salmon coloured spots"        . "rose_spot_rash")
    ("flat pink rash"               . "rose_spot_rash")
    ("faint pink spots"             . "rose_spot_rash")
    ("maculopapular rash"           . "rose_spot_rash")

    ;; --- pale skin — Anemia ---
    ("pale skin"                    . "pale_skin")
    ("pallor"                       . "pale_skin")
    ("looking pale"                 . "pale_skin")
    ("skin looks pale"              . "pale_skin")
    ("very pale"                    . "pale_skin")
    ("washed out complexion"        . "pale_skin")
    ("colour gone from face"        . "pale_skin")
    ("pasty skin"                   . "pale_skin")
    ("ashen complexion"             . "pale_skin")
    ("sallow skin"                  . "pale_skin")

    ;; --- dry skin — Hypothyroidism ---
    ("dry skin"                     . "dry_skin")
    ("flaky skin"                   . "dry_skin")
    ("rough skin"                   . "dry_skin")
    ("skin peeling"                 . "dry_skin")
    ("skin is very dry"             . "dry_skin")
    ("cracked skin"                 . "dry_skin")
    ("scaly skin"                   . "dry_skin")
    ("skin feels tight"             . "dry_skin")
    ("xerosis"                      . "dry_skin")
    ("skin flaking off"             . "dry_skin")

    ;; --- severe joint pain — Dengue Fever ---
    ("severe joint pain"            . "severe_joint_pain")
    ("joint pain"                   . "severe_joint_pain")
    ("joints hurt"                  . "severe_joint_pain")
    ("aching joints"                . "severe_joint_pain")
    ("arthralgia"                   . "severe_joint_pain")
    ("joint ache"                   . "severe_joint_pain")
    ("pain in joints"               . "severe_joint_pain")
    ("joints are painful"           . "severe_joint_pain")
    ("joints very painful"          . "severe_joint_pain")
    ("bone breaking pain"           . "severe_joint_pain")
    ("excruciating joint pain"      . "severe_joint_pain")
    ("all joints hurt"              . "severe_joint_pain")

    ;; ================================================================
    ;; GROUP F — METABOLIC / CHRONIC SYMPTOMS
    ;; ================================================================

    ;; --- excessive thirst — Diabetes T2 ---
    ("excessive thirst"             . "excessive_thirst")
    ("very thirsty"                 . "excessive_thirst")
    ("always thirsty"               . "excessive_thirst")
    ("drinking a lot"               . "excessive_thirst")
    ("polydipsia"                   . "excessive_thirst")
    ("cant quench thirst"           . "excessive_thirst")
    ("thirsty all the time"         . "excessive_thirst")
    ("constantly thirsty"           . "excessive_thirst")
    ("drink lots of water"          . "excessive_thirst")
    ("unquenchable thirst"          . "excessive_thirst")
    ("thirsty"                      . "excessive_thirst")
    ("so thirsty"                   . "excessive_thirst")
    ("keep drinking water"          . "excessive_thirst")
    ("drinking water all the time"  . "excessive_thirst")
    ("thirst all the time"          . "excessive_thirst")

    ;; --- frequent urination — Diabetes T2 ---
    ("frequent urination"           . "frequent_urination")
    ("urinating a lot"              . "frequent_urination")
    ("peeing a lot"                 . "frequent_urination")
    ("pee a lot"                    . "frequent_urination")
    ("polyuria"                     . "frequent_urination")
    ("going to toilet often"        . "frequent_urination")
    ("need to pee all the time"     . "frequent_urination")
    ("constant urge to urinate"     . "frequent_urination")
    ("waking at night to urinate"   . "frequent_urination")
    ("nocturia"                     . "frequent_urination")
    ("passing lots of urine"        . "frequent_urination")
    ("need to pee"                  . "frequent_urination")
    ("need to urinate"              . "frequent_urination")
    ("urge to pee"                  . "frequent_urination")
    ("keep needing to pee"          . "frequent_urination")
    ("keep needing to urinate"      . "frequent_urination")
    ("bathroom a lot"               . "frequent_urination")
    ("toilet a lot"                 . "frequent_urination")
    ("going to bathroom often"      . "frequent_urination")
    ("running to toilet"            . "frequent_urination")
    ("always need to pee"           . "frequent_urination")
    ("urinate frequently"           . "frequent_urination")
    ("pee frequently"               . "frequent_urination")

    ;; --- blurred vision — Diabetes T2 ---
    ("blurred vision"               . "blurred_vision")
    ("blurry vision"                . "blurred_vision")
    ("vision blurry"                . "blurred_vision")
    ("cant see clearly"             . "blurred_vision")
    ("fuzzy vision"                 . "blurred_vision")
    ("vision going blurry"          . "blurred_vision")
    ("eyes blurry"                  . "blurred_vision")
    ("sight blurry"                 . "blurred_vision")
    ("vision not clear"             . "blurred_vision")
    ("difficulty seeing clearly"    . "blurred_vision")
    ("eyes out of focus"            . "blurred_vision")

    ;; --- slow wound healing — Diabetes T2 ---
    ("slow wound healing"           . "slow_wound_healing")
    ("wounds not healing"           . "slow_wound_healing")
    ("cuts not healing"             . "slow_wound_healing")
    ("slow healing"                 . "slow_wound_healing")
    ("wounds take long to heal"     . "slow_wound_healing")
    ("cuts wont heal"               . "slow_wound_healing")
    ("wounds heal slowly"           . "slow_wound_healing")
    ("sores that wont heal"         . "slow_wound_healing")
    ("injuries slow to heal"        . "slow_wound_healing")
    ("healing is very slow"         . "slow_wound_healing")

    ;; --- cold intolerance — Hypothyroidism ---
    ("cold intolerance"             . "cold_intolerance")
    ("always cold"                  . "cold_intolerance")
    ("feel cold all the time"       . "cold_intolerance")
    ("feeling cold all the time"    . "cold_intolerance")
    ("cant stand cold"              . "cold_intolerance")
    ("cant tolerate cold"           . "cold_intolerance")
    ("body always feels cold"       . "cold_intolerance")
    ("constantly cold"              . "cold_intolerance")
    ("sensitive to cold weather"    . "cold_intolerance")
    ("always freezing cold"         . "cold_intolerance")

    ;; --- hair loss — Hypothyroidism ---
    ("hair loss"                    . "hair_loss")
    ("losing hair"                  . "hair_loss")
    ("hair falling out"             . "hair_loss")
    ("alopecia"                     . "hair_loss")
    ("hair thinning"                . "hair_loss")
    ("bald patches"                 . "hair_loss")
    ("going bald"                   . "hair_loss")
    ("hair coming out"              . "hair_loss")
    ("losing my hair"               . "hair_loss")
    ("hair getting thin"            . "hair_loss")
    ("clumps of hair falling out"   . "hair_loss")

    ;; --- slow heart rate — Typhoid Fever ---
    ("slow heart rate"              . "slow_heart_rate")
    ("slow pulse"                   . "slow_heart_rate")
    ("bradycardia"                  . "slow_heart_rate")
    ("low heart rate"               . "slow_heart_rate")
    ("heart beats slowly"           . "slow_heart_rate")
    ("low pulse"                    . "slow_heart_rate")
    ("heart rate too slow"          . "slow_heart_rate")
    ("heart beating slow"           . "slow_heart_rate")
    ("pulse is slow"                . "slow_heart_rate")
    ("low bpm"                      . "slow_heart_rate")

    ;; ================================================================
    ;; GROUP G — CIRCULATORY / PAIN SYMPTOMS
    ;; ================================================================

    ;; --- dizziness — Anemia / Tension Headache ---
    ("dizziness"                    . dizziness)
    ("dizzy"                        . dizziness)
    ("lightheaded"                  . dizziness)
    ("vertigo"                      . dizziness)
    ("feel faint"                   . dizziness)
    ("giddiness"                    . dizziness)
    ("presyncope"                   . dizziness)
    ("head spinning"                . dizziness)
    ("room spinning"                . dizziness)
    ("unsteady on feet"             . dizziness)
    ("off balance"                  . dizziness)
    ("woozy"                        . dizziness)
    ("spinning feeling"             . dizziness)

    ;; --- cold hands and feet — Anemia ---
    ("cold hands and feet"          . "cold_hands_and_feet")
    ("cold hands"                   . "cold_hands_and_feet")
    ("cold feet"                    . "cold_hands_and_feet")
    ("hands perpetually cold"       . "cold_hands_and_feet")
    ("extremities cold"             . "cold_hands_and_feet")
    ("ice cold hands"               . "cold_hands_and_feet")
    ("ice cold feet"                . "cold_hands_and_feet")
    ("hands and feet freezing"      . "cold_hands_and_feet")
    ("poor circulation in hands"    . "cold_hands_and_feet")
    ("numb hands and feet"          . "cold_hands_and_feet")

  ))

;;; ----------------------------------------------------------------
;;; NEGATION WORDS
;;; ----------------------------------------------------------------
(defparameter *negation-words*
  '("no" "not" "dont" "don't" "without" "never"
    "no sign of" "no signs of" "absent"
    "haven't" "havent" "didnt" "didn't"
    "none" "lack" "lacking" "free of"
    "do not have" "does not have" "cannot"))

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
    "since" "for" "about" "from" "still" "patient" "appears"
    "kind" "sort" "type" "just" "only"
    "sometimes" "often" "usually" "recently"
    "keep" "keeps" "kept"))