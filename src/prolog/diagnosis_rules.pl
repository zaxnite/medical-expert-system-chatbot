:- encoding(utf8).
% ================================================================
% diagnosis_rules.pl
% Medical Expert System — BCS 222 Programming Paradigms
% Role: Inference engine — candidates, scoring, hard rules,
%       next question selection, and final diagnosis output.
% ================================================================

:- module(diagnosis_rules, [
    candidate/1,
    diagnosis/1,
    next_question/1,
    consult_result/3,
    needs_tests/2,
    symptom_match_score/2,
    all_candidates/1,
    assert_symptom/1,
    deny_symptom/1,
    reset_session/0,
    consultation_complete/1,
    increment_question_count/0,
    question_count/1,
    top_diagnoses/1,
    confidence/2,
    symptom/1,
    denied/1,
    asked/1,
    symptom_rarity/2
]).

:- use_module(knowledge_base, [
    disease_group/2,
    symptom_of/2,
    test_required/2,
    test_confirms/3,
    symptom_question/2,
    disease_description/2
]).

:- dynamic symptom/1.
:- dynamic denied/1.
:- dynamic asked/1.


% ================================================================
% SECTION 1 — SESSION CONTROL
% ================================================================

assert_symptom(S) :-
    (\+ symptom(S) -> assertz(diagnosis_rules:symptom(S)) ; true),
    (\+ asked(S)   -> assertz(diagnosis_rules:asked(S))   ; true).

deny_symptom(S) :-
    (\+ denied(S) -> assertz(diagnosis_rules:denied(S)) ; true),
    (\+ asked(S)  -> assertz(diagnosis_rules:asked(S))  ; true).

reset_session :-
    retractall(symptom(_)),
    retractall(denied(_)),
    retractall(asked(_)),
    retractall(question_count(_)),
    assertz(question_count(0)).


% ================================================================
% SECTION 2 — HARD RULES
% Each rule: if patient HAS this symptom, disease is ruled out.
% Demonstrates negation-as-failure and closed-world assumption.
% ================================================================

% --- Common cold: mild upper respiratory only ---
hard_rule(common_cold, not(fever)).
hard_rule(common_cold, not(body_aches)).
hard_rule(common_cold, not(sudden_onset)).
hard_rule(common_cold, not(nausea)).
hard_rule(common_cold, not(vomiting)).
hard_rule(common_cold, not(chills)).
hard_rule(common_cold, not(diarrhea)).

% --- Influenza: acute systemic — ruled out by GI-only symptoms ---
hard_rule(influenza, not(diarrhea)).
hard_rule(influenza, not(neck_stiffness)).
hard_rule(influenza, not(weight_gain)).           % acute illness — no chronic metabolic change
hard_rule(influenza, not(loss_of_smell)).         % anosmia is COVID-19 hallmark, not flu
hard_rule(influenza, not(loss_of_taste)).         % same — COVID differentiator
hard_rule(influenza, not(right_lower_quad_pain)). % surgical/GI sign, not respiratory
hard_rule(influenza, not(rebound_tenderness)).    % peritoneal sign — incompatible
hard_rule(influenza, not(excessive_thirst)).      % metabolic symptom, not acute viral

% --- Pneumonia: respiratory — ruled out by non-respiratory dominance ---
hard_rule(pneumonia, not(diarrhea)).
hard_rule(pneumonia, not(neck_stiffness)).
hard_rule(pneumonia, not(weight_gain)).
hard_rule(pneumonia, not(excessive_thirst)).
hard_rule(pneumonia, not(loss_of_smell)).         % anosmia = COVID, not pneumonia
hard_rule(pneumonia, not(loss_of_taste)).         % same
hard_rule(pneumonia, not(severe_joint_pain)).     % dengue-specific arthralgia
hard_rule(pneumonia, not(right_lower_quad_pain)). % surgical sign, not respiratory
hard_rule(pneumonia, not(rebound_tenderness)).    % peritoneal sign

% --- COVID-19 ---
hard_rule(covid19, not(neck_stiffness)).
hard_rule(covid19, not(weight_gain)).
hard_rule(covid19, not(diarrhea)).
hard_rule(covid19, not(severe_joint_pain)).     % bone-breaking joint pain = dengue hallmark
hard_rule(covid19, not(right_lower_quad_pain)). % surgical sign
hard_rule(covid19, not(rebound_tenderness)).    % peritoneal sign
hard_rule(covid19, not(cyclical_fever)).        % periodic fever = malaria pattern
hard_rule(covid19, not(rose_spot_rash)).        % typhoid-specific rash
hard_rule(covid19, not(slow_heart_rate)).       % relative bradycardia = typhoid sign

% --- Dengue fever: tropical viral ---
hard_rule(dengue_fever, not(neck_stiffness)).
hard_rule(dengue_fever, not(diarrhea)).
hard_rule(dengue_fever, not(weight_gain)).
hard_rule(dengue_fever, not(loss_of_smell)).         % anosmia = COVID
hard_rule(dengue_fever, not(loss_of_taste)).         % same
hard_rule(dengue_fever, not(right_lower_quad_pain)). % surgical sign
hard_rule(dengue_fever, not(rebound_tenderness)).    % peritoneal sign
hard_rule(dengue_fever, not(excessive_thirst)).      % metabolic, not acute viral
hard_rule(dengue_fever, not(slow_heart_rate)).       % relative bradycardia = typhoid sign

% --- Malaria: cyclical fever pattern ---
hard_rule(malaria, not(neck_stiffness)).
hard_rule(malaria, not(weight_gain)).
hard_rule(malaria, not(diarrhea)).
hard_rule(malaria, not(loss_of_smell)).         % anosmia = COVID
hard_rule(malaria, not(right_lower_quad_pain)). % surgical sign
hard_rule(malaria, not(rebound_tenderness)).    % peritoneal sign
hard_rule(malaria, not(severe_joint_pain)).     % bone-breaking joint pain = dengue
hard_rule(malaria, not(slow_heart_rate)).       % relative bradycardia = typhoid sign

% --- Gastroenteritis: GI only ---
hard_rule(gastroenteritis, not(chest_pain)).
hard_rule(gastroenteritis, not(neck_stiffness)).
hard_rule(gastroenteritis, not(weight_gain)).
hard_rule(gastroenteritis, not(loss_of_smell)).
hard_rule(gastroenteritis, not(severe_joint_pain)).     % not a GI infection feature
hard_rule(gastroenteritis, not(right_lower_quad_pain)). % RLQ pain = appendicitis, not gastro
hard_rule(gastroenteritis, not(rebound_tenderness)).    % rebound = appendicitis
hard_rule(gastroenteritis, not(slow_heart_rate)).       % typhoid-specific bradycardia
hard_rule(gastroenteritis, not(rose_spot_rash)).        % typhoid-specific rash

% --- Appendicitis: ruled out by diarrhea (favours gastroenteritis) ---
hard_rule(appendicitis, not(diarrhea)).
hard_rule(appendicitis, not(weight_gain)).
hard_rule(appendicitis, not(loss_of_smell)).
hard_rule(appendicitis, not(neck_stiffness)).    % meningeal sign, not appendicitis
hard_rule(appendicitis, not(cyclical_fever)).    % malarial pattern
hard_rule(appendicitis, not(severe_joint_pain)). % dengue hallmark
hard_rule(appendicitis, not(slow_heart_rate)).   % typhoid-specific

% --- Meningitis: neurological emergency ---
hard_rule(meningitis, not(diarrhea)).
hard_rule(meningitis, not(weight_gain)).
hard_rule(meningitis, not(runny_nose)).
hard_rule(meningitis, not(loss_of_smell)).         % anosmia = COVID
hard_rule(meningitis, not(severe_joint_pain)).     % dengue hallmark
hard_rule(meningitis, not(right_lower_quad_pain)). % surgical sign
hard_rule(meningitis, not(rebound_tenderness)).    % peritoneal sign
hard_rule(meningitis, not(excessive_thirst)).      % metabolic sign
hard_rule(meningitis, not(slow_heart_rate)).       % typhoid-specific

% --- Migraine: pure neurological — no systemic or infectious ---
hard_rule(migraine, not(fever)).
hard_rule(migraine, not(neck_stiffness)).
hard_rule(migraine, not(vomiting)).
hard_rule(migraine, not(chills)).
hard_rule(migraine, not(cough)).
hard_rule(migraine, not(sore_throat)).
hard_rule(migraine, not(diarrhea)).
hard_rule(migraine, not(weight_gain)).

% --- Strep throat: ENT bacterial, no GI or systemic ---
hard_rule(strep_throat, not(cough)).
hard_rule(strep_throat, not(diarrhea)).
hard_rule(strep_throat, not(weight_gain)).
hard_rule(strep_throat, not(loss_of_smell)).
hard_rule(strep_throat, not(nausea)).
hard_rule(strep_throat, not(vomiting)).
hard_rule(strep_throat, not(abdominal_pain)).
hard_rule(strep_throat, not(chills)).

% --- Diabetes T2: chronic metabolic ---
hard_rule(diabetes_t2, not(fever)).
hard_rule(diabetes_t2, not(vomiting)).
hard_rule(diabetes_t2, not(neck_stiffness)).
hard_rule(diabetes_t2, not(chills)).
hard_rule(diabetes_t2, not(runny_nose)).
hard_rule(diabetes_t2, not(sneezing)).
hard_rule(diabetes_t2, not(loss_of_smell)).         % anosmia = COVID
hard_rule(diabetes_t2, not(severe_joint_pain)).     % dengue hallmark, not metabolic
hard_rule(diabetes_t2, not(right_lower_quad_pain)). % surgical sign
hard_rule(diabetes_t2, not(rebound_tenderness)).    % peritoneal sign
hard_rule(diabetes_t2, not(skin_rash)).             % not a T2 diabetes feature
hard_rule(diabetes_t2, not(slow_heart_rate)).       % typhoid-specific

% --- Hypothyroidism: chronic systemic ---
hard_rule(hypothyroidism, not(fever)).
hard_rule(hypothyroidism, not(vomiting)).
hard_rule(hypothyroidism, not(neck_stiffness)).
hard_rule(hypothyroidism, not(chills)).
hard_rule(hypothyroidism, not(runny_nose)).
hard_rule(hypothyroidism, not(sneezing)).
hard_rule(hypothyroidism, not(diarrhea)).
hard_rule(hypothyroidism, not(loss_of_smell)).         % anosmia = COVID
hard_rule(hypothyroidism, not(severe_joint_pain)).     % dengue hallmark
hard_rule(hypothyroidism, not(right_lower_quad_pain)). % surgical sign
hard_rule(hypothyroidism, not(rebound_tenderness)).    % peritoneal sign
hard_rule(hypothyroidism, not(skin_rash)).             % not a hypothyroidism feature
% NOTE: slow_heart_rate NOT excluded — hypothyroidism can cause bradycardia

% --- Anemia: chronic — no infection symptoms ---
hard_rule(anemia, not(fever)).
hard_rule(anemia, not(vomiting)).
hard_rule(anemia, not(neck_stiffness)).
hard_rule(anemia, not(chills)).
hard_rule(anemia, not(runny_nose)).
hard_rule(anemia, not(diarrhea)).
hard_rule(anemia, not(sneezing)).
hard_rule(anemia, not(loss_of_smell)).          % anosmia = COVID
hard_rule(anemia, not(severe_joint_pain)).      % dengue hallmark
hard_rule(anemia, not(right_lower_quad_pain)).  % surgical sign
hard_rule(anemia, not(rebound_tenderness)).     % peritoneal sign
hard_rule(anemia, not(skin_rash)).              % not an anemia feature
hard_rule(anemia, not(slow_heart_rate)).        % typhoid-specific
hard_rule(anemia, not(excessive_thirst)).       % metabolic (diabetes), not anemia

% --- Typhoid fever: systemic bacterial ---
hard_rule(typhoid_fever, not(neck_stiffness)).
hard_rule(typhoid_fever, not(weight_gain)).
hard_rule(typhoid_fever, not(runny_nose)).
hard_rule(typhoid_fever, not(sneezing)).
hard_rule(typhoid_fever, not(loss_of_smell)).         % anosmia = COVID
hard_rule(typhoid_fever, not(loss_of_taste)).         % same
hard_rule(typhoid_fever, not(severe_joint_pain)).     % dengue hallmark
hard_rule(typhoid_fever, not(right_lower_quad_pain)). % typhoid has diffuse pain, not RLQ
hard_rule(typhoid_fever, not(rebound_tenderness)).    % if present = perforation complication
hard_rule(typhoid_fever, not(cyclical_fever)).        % periodic pattern = malaria
hard_rule(typhoid_fever, not(chest_pain)).            % not a typhoid feature




% --- Tuberculosis: chronic respiratory ---
hard_rule(tuberculosis, not(sudden_onset)).
hard_rule(tuberculosis, not(severe_joint_pain)).
hard_rule(tuberculosis, not(neck_stiffness)).
hard_rule(tuberculosis, not(right_lower_quad_pain)).
hard_rule(tuberculosis, not(rebound_tenderness)).
hard_rule(tuberculosis, not(loss_of_smell)).
hard_rule(tuberculosis, not(loss_of_taste)).
hard_rule(tuberculosis, not(cyclical_fever)).
hard_rule(tuberculosis, not(diarrhea)).
hard_rule(tuberculosis, not(rose_spot_rash)).
hard_rule(tuberculosis, not(slow_heart_rate)).

% --- Chickenpox: viral exanthem ---
hard_rule(chickenpox, not(neck_stiffness)).
hard_rule(chickenpox, not(weight_gain)).
hard_rule(chickenpox, not(right_lower_quad_pain)).
hard_rule(chickenpox, not(rebound_tenderness)).
hard_rule(chickenpox, not(loss_of_smell)).
hard_rule(chickenpox, not(loss_of_taste)).
hard_rule(chickenpox, not(severe_joint_pain)).
hard_rule(chickenpox, not(cyclical_fever)).
hard_rule(chickenpox, not(slow_heart_rate)).
hard_rule(chickenpox, not(excessive_thirst)).
hard_rule(chickenpox, not(diarrhea)).
hard_rule(chickenpox, not(productive_cough)).

% --- Peptic ulcer: localised GI ---
hard_rule(peptic_ulcer, not(fever)).
hard_rule(peptic_ulcer, not(neck_stiffness)).
hard_rule(peptic_ulcer, not(weight_gain)).
hard_rule(peptic_ulcer, not(diarrhea)).
hard_rule(peptic_ulcer, not(loss_of_smell)).
hard_rule(peptic_ulcer, not(severe_joint_pain)).
hard_rule(peptic_ulcer, not(right_lower_quad_pain)).
hard_rule(peptic_ulcer, not(cyclical_fever)).
hard_rule(peptic_ulcer, not(slow_heart_rate)).
hard_rule(peptic_ulcer, not(skin_rash)).
hard_rule(peptic_ulcer, not(chills)).

% --- IBS: functional GI ---
hard_rule(irritable_bowel_syndrome, not(fever)).
hard_rule(irritable_bowel_syndrome, not(neck_stiffness)).
hard_rule(irritable_bowel_syndrome, not(weight_gain)).
hard_rule(irritable_bowel_syndrome, not(loss_of_smell)).
hard_rule(irritable_bowel_syndrome, not(severe_joint_pain)).
hard_rule(irritable_bowel_syndrome, not(right_lower_quad_pain)).
hard_rule(irritable_bowel_syndrome, not(rebound_tenderness)).
hard_rule(irritable_bowel_syndrome, not(slow_heart_rate)).
hard_rule(irritable_bowel_syndrome, not(skin_rash)).
hard_rule(irritable_bowel_syndrome, not(chills)).
hard_rule(irritable_bowel_syndrome, not(vomiting)).

% --- Tension headache: functional ---
hard_rule(tension_headache, not(fever)).
hard_rule(tension_headache, not(vomiting)).
hard_rule(tension_headache, not(visual_aura)).
hard_rule(tension_headache, not(one_sided_pain)).
hard_rule(tension_headache, not(pulsating_pain)).
hard_rule(tension_headache, not(weight_gain)).
hard_rule(tension_headache, not(diarrhea)).
hard_rule(tension_headache, not(loss_of_smell)).
hard_rule(tension_headache, not(severe_joint_pain)).
hard_rule(tension_headache, not(right_lower_quad_pain)).
hard_rule(tension_headache, not(slow_heart_rate)).
hard_rule(tension_headache, not(chills)).
hard_rule(tension_headache, not(skin_rash)).


% ================================================================
% SECTION 2B — EXTENDED HARD RULES (cross-disease elimination)
% New symptoms: vesicular_rash, itchy_rash, chronic_cough,
%   night_sweats, weight_loss, haemoptysis, burning_epigastric_pain,
%   pulsating_pain, visual_aura, one_sided_pain, rose_spot_rash
%   (added with 5 new diseases — pathologist-verified)
% ================================================================

% --- influenza (extended) ---
hard_rule(influenza, not(vesicular_rash)). % blistering rash = chickenpox/varicella, not flu
hard_rule(influenza, not(itchy_rash)). % itchy vesicular rash = chickenpox, not flu
hard_rule(influenza, not(rose_spot_rash)). % rose spots = typhoid-specific
hard_rule(influenza, not(slow_heart_rate)). % relative bradycardia = typhoid sign
hard_rule(influenza, not(pulsating_pain)). % throbbing unilateral = migraine, not flu headache
hard_rule(influenza, not(visual_aura)). % aura = migraine hallmark
hard_rule(influenza, not(one_sided_pain)). % unilateral = migraine, flu headache is bilateral
hard_rule(influenza, not(haemoptysis)). % coughing blood = TB, not flu
hard_rule(influenza, not(chronic_cough)). % flu resolves in 2 weeks, not chronic
hard_rule(influenza, not(burning_epigastric_pain)). % epigastric burning = peptic ulcer, not flu

% --- common_cold (extended) ---
hard_rule(common_cold, not(neck_stiffness)). % meningeal sign
hard_rule(common_cold, not(severe_joint_pain)). % dengue arthralgia, not cold
hard_rule(common_cold, not(loss_of_smell)). % anosmia = COVID
hard_rule(common_cold, not(loss_of_taste)). % ageusia = COVID
hard_rule(common_cold, not(right_lower_quad_pain)). % surgical sign
hard_rule(common_cold, not(rebound_tenderness)). % peritoneal sign
hard_rule(common_cold, not(slow_heart_rate)). % typhoid bradycardia
hard_rule(common_cold, not(rose_spot_rash)). % typhoid-specific
hard_rule(common_cold, not(vesicular_rash)). % chickenpox, not cold
hard_rule(common_cold, not(haemoptysis)). % coughing blood = TB, not cold
hard_rule(common_cold, not(pulsating_pain)). % migraine hallmark
hard_rule(common_cold, not(visual_aura)). % migraine hallmark
hard_rule(common_cold, not(chronic_cough)). % cold is self-limiting — not chronic
hard_rule(common_cold, not(weight_gain)). % acute illness — no metabolic change
hard_rule(common_cold, not(weight_loss)). % cold does not cause weight loss
hard_rule(common_cold, not(night_sweats)). % drenching night sweats = TB, not cold
hard_rule(common_cold, not(burning_epigastric_pain)). % peptic ulcer sign, not cold

% --- pneumonia (extended) ---
hard_rule(pneumonia, not(vesicular_rash)). % chickenpox rash, not pneumonia
hard_rule(pneumonia, not(itchy_rash)). % chickenpox, not pneumonia
hard_rule(pneumonia, not(rose_spot_rash)). % typhoid-specific
hard_rule(pneumonia, not(slow_heart_rate)). % relative bradycardia = typhoid sign
hard_rule(pneumonia, not(pulsating_pain)). % migraine hallmark
hard_rule(pneumonia, not(visual_aura)). % migraine hallmark
hard_rule(pneumonia, not(one_sided_pain)). % migraine pattern
hard_rule(pneumonia, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(pneumonia, not(weight_loss)). % TB causes weight loss, not acute pneumonia
hard_rule(pneumonia, not(night_sweats)). % drenching night sweats = TB hallmark
hard_rule(pneumonia, not(chronic_cough)). % pneumonia is acute — chronic cough = TB

% --- covid19 (extended) ---
hard_rule(covid19, not(vesicular_rash)). % blistering rash = chickenpox
hard_rule(covid19, not(itchy_rash)). % chickenpox
hard_rule(covid19, not(pulsating_pain)). % migraine hallmark
hard_rule(covid19, not(visual_aura)). % migraine hallmark
hard_rule(covid19, not(one_sided_pain)). % migraine pattern
hard_rule(covid19, not(haemoptysis)). % coughing blood = TB, not COVID
hard_rule(covid19, not(chronic_cough)). % COVID resolves — not chronic
hard_rule(covid19, not(night_sweats)). % TB hallmark, not COVID
hard_rule(covid19, not(weight_loss)). % significant weight loss = TB, not COVID
hard_rule(covid19, not(burning_epigastric_pain)). % peptic ulcer sign

% --- dengue_fever (extended) ---
hard_rule(dengue_fever, not(vesicular_rash)). % dengue causes flat/macular rash, not vesicular
hard_rule(dengue_fever, not(pulsating_pain)). % migraine hallmark
hard_rule(dengue_fever, not(visual_aura)). % migraine hallmark
hard_rule(dengue_fever, not(one_sided_pain)). % migraine pattern
hard_rule(dengue_fever, not(haemoptysis)). % TB hallmark
hard_rule(dengue_fever, not(chronic_cough)). % dengue is acute — not chronic
hard_rule(dengue_fever, not(weight_loss)). % TB causes weight loss, not dengue
hard_rule(dengue_fever, not(night_sweats)). % TB hallmark
hard_rule(dengue_fever, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(dengue_fever, not(rose_spot_rash)). % typhoid-specific rash

% --- malaria (extended) ---
hard_rule(malaria, not(vesicular_rash)). % chickenpox rash, not malaria
hard_rule(malaria, not(itchy_rash)). % chickenpox, not malaria
hard_rule(malaria, not(rose_spot_rash)). % typhoid-specific
hard_rule(malaria, not(pulsating_pain)). % migraine hallmark
hard_rule(malaria, not(visual_aura)). % migraine hallmark
hard_rule(malaria, not(one_sided_pain)). % migraine pattern
hard_rule(malaria, not(haemoptysis)). % TB hallmark
hard_rule(malaria, not(chronic_cough)). % malaria is episodic — not chronic respiratory
hard_rule(malaria, not(weight_loss)). % significant weight loss = TB
hard_rule(malaria, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(malaria, not(loss_of_taste)). % anosmia/ageusia = COVID

% --- gastroenteritis (extended) ---
hard_rule(gastroenteritis, not(vesicular_rash)). % chickenpox, not GI
hard_rule(gastroenteritis, not(itchy_rash)). % chickenpox, not GI
hard_rule(gastroenteritis, not(pulsating_pain)). % migraine hallmark
hard_rule(gastroenteritis, not(visual_aura)). % migraine hallmark
hard_rule(gastroenteritis, not(one_sided_pain)). % migraine pattern
hard_rule(gastroenteritis, not(haemoptysis)). % TB hallmark
hard_rule(gastroenteritis, not(chronic_cough)). % not a GI feature
hard_rule(gastroenteritis, not(weight_loss)). % significant weight loss = TB
hard_rule(gastroenteritis, not(night_sweats)). % TB hallmark
hard_rule(gastroenteritis, not(loss_of_taste)). % ageusia = COVID
hard_rule(gastroenteritis, not(burning_epigastric_pain)). % that location = peptic ulcer, not gastroenteritis

% --- appendicitis (extended) ---
hard_rule(appendicitis, not(loss_of_taste)). % ageusia = COVID
hard_rule(appendicitis, not(vesicular_rash)). % chickenpox, not appendicitis
hard_rule(appendicitis, not(itchy_rash)). % chickenpox, not appendicitis
hard_rule(appendicitis, not(pulsating_pain)). % migraine hallmark
hard_rule(appendicitis, not(visual_aura)). % migraine hallmark
hard_rule(appendicitis, not(one_sided_pain)). % migraine pattern
hard_rule(appendicitis, not(haemoptysis)). % TB hallmark
hard_rule(appendicitis, not(chronic_cough)). % not appendicitis
hard_rule(appendicitis, not(weight_loss)). % TB hallmark
hard_rule(appendicitis, not(night_sweats)). % TB hallmark
hard_rule(appendicitis, not(burning_epigastric_pain)). % epigastric = peptic ulcer; appendicitis = RLQ

% --- meningitis (extended) ---
hard_rule(meningitis, not(vesicular_rash)). % chickenpox, not meningitis
hard_rule(meningitis, not(itchy_rash)). % chickenpox, not meningitis
hard_rule(meningitis, not(pulsating_pain)). % pulsating = migraine not meningitis headache
hard_rule(meningitis, not(visual_aura)). % migraine hallmark
hard_rule(meningitis, not(one_sided_pain)). % migraine pattern — meningitis headache is global
hard_rule(meningitis, not(haemoptysis)). % TB hallmark
hard_rule(meningitis, not(chronic_cough)). % not meningitis
hard_rule(meningitis, not(weight_loss)). % TB hallmark
hard_rule(meningitis, not(night_sweats)). % TB hallmark
hard_rule(meningitis, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(meningitis, not(loss_of_taste)). % ageusia = COVID

% --- migraine (extended) ---
hard_rule(migraine, not(haemoptysis)). % TB hallmark
hard_rule(migraine, not(vesicular_rash)). % chickenpox, not migraine
hard_rule(migraine, not(itchy_rash)). % chickenpox, not migraine
hard_rule(migraine, not(rose_spot_rash)). % typhoid-specific
hard_rule(migraine, not(slow_heart_rate)). % typhoid bradycardia
hard_rule(migraine, not(night_sweats)). % TB hallmark
hard_rule(migraine, not(chronic_cough)). % TB hallmark
hard_rule(migraine, not(right_lower_quad_pain)). % surgical sign
hard_rule(migraine, not(rebound_tenderness)). % peritoneal sign
hard_rule(migraine, not(loss_of_smell)). % anosmia = COVID
hard_rule(migraine, not(loss_of_taste)). % ageusia = COVID
hard_rule(migraine, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(migraine, not(weight_loss)). % TB hallmark

% --- strep_throat (extended) ---
hard_rule(strep_throat, not(vesicular_rash)). % chickenpox, not strep
hard_rule(strep_throat, not(itchy_rash)). % chickenpox, not strep
hard_rule(strep_throat, not(pulsating_pain)). % migraine hallmark
hard_rule(strep_throat, not(visual_aura)). % migraine hallmark
hard_rule(strep_throat, not(one_sided_pain)). % migraine pattern
hard_rule(strep_throat, not(haemoptysis)). % TB hallmark
hard_rule(strep_throat, not(chronic_cough)). % TB hallmark — strep is acute
hard_rule(strep_throat, not(weight_loss)). % TB hallmark
hard_rule(strep_throat, not(night_sweats)). % TB hallmark
hard_rule(strep_throat, not(neck_stiffness)). % meningeal sign
hard_rule(strep_throat, not(right_lower_quad_pain)). % surgical sign
hard_rule(strep_throat, not(rebound_tenderness)). % peritoneal sign
hard_rule(strep_throat, not(severe_joint_pain)). % dengue hallmark
hard_rule(strep_throat, not(rose_spot_rash)). % typhoid-specific
hard_rule(strep_throat, not(slow_heart_rate)). % typhoid bradycardia
hard_rule(strep_throat, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(strep_throat, not(cyclical_fever)). % periodic fever = malaria

% --- diabetes_t2 (extended) ---
hard_rule(diabetes_t2, not(vesicular_rash)). % chickenpox, not diabetes
hard_rule(diabetes_t2, not(itchy_rash)). % chickenpox, not diabetes
hard_rule(diabetes_t2, not(pulsating_pain)). % migraine hallmark
hard_rule(diabetes_t2, not(visual_aura)). % migraine hallmark
hard_rule(diabetes_t2, not(one_sided_pain)). % migraine pattern
hard_rule(diabetes_t2, not(haemoptysis)). % TB hallmark
hard_rule(diabetes_t2, not(chronic_cough)). % TB hallmark
hard_rule(diabetes_t2, not(weight_loss)). % significant weight loss = TB; T2 patients often gain weight
hard_rule(diabetes_t2, not(night_sweats)). % TB hallmark
hard_rule(diabetes_t2, not(diarrhea)). % not a T2 diabetes feature
hard_rule(diabetes_t2, not(cyclical_fever)). % periodic fever = malaria
hard_rule(diabetes_t2, not(burning_epigastric_pain)). % peptic ulcer sign

% --- hypothyroidism (extended) ---
hard_rule(hypothyroidism, not(vesicular_rash)). % chickenpox, not hypothyroidism
hard_rule(hypothyroidism, not(itchy_rash)). % chickenpox, not hypothyroidism
hard_rule(hypothyroidism, not(pulsating_pain)). % migraine hallmark
hard_rule(hypothyroidism, not(visual_aura)). % migraine hallmark
hard_rule(hypothyroidism, not(one_sided_pain)). % migraine pattern
hard_rule(hypothyroidism, not(haemoptysis)). % TB hallmark
hard_rule(hypothyroidism, not(chronic_cough)). % TB hallmark
hard_rule(hypothyroidism, not(weight_loss)). % hypothyroidism causes weight GAIN not loss
hard_rule(hypothyroidism, not(night_sweats)). % TB hallmark — hypothyroidism causes cold intolerance not sweating
hard_rule(hypothyroidism, not(cyclical_fever)). % periodic fever = malaria
hard_rule(hypothyroidism, not(rose_spot_rash)). % typhoid-specific
hard_rule(hypothyroidism, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(hypothyroidism, not(sudden_onset)). % hypothyroidism develops gradually over months/years

% --- anemia ---
hard_rule(anemia, not(vesicular_rash)). % chickenpox, not anemia
hard_rule(anemia, not(itchy_rash)). % chickenpox, not anemia
hard_rule(anemia, not(pulsating_pain)). % migraine hallmark
hard_rule(anemia, not(visual_aura)). % migraine hallmark
hard_rule(anemia, not(one_sided_pain)). % migraine pattern
hard_rule(anemia, not(haemoptysis)). % TB hallmark
hard_rule(anemia, not(chronic_cough)). % TB hallmark
hard_rule(anemia, not(weight_loss)). % significant weight loss = TB
hard_rule(anemia, not(night_sweats)). % TB hallmark
hard_rule(anemia, not(cyclical_fever)). % periodic fever = malaria
hard_rule(anemia, not(rose_spot_rash)). % typhoid-specific
hard_rule(anemia, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(anemia, not(sudden_onset)). % anemia develops gradually

% --- typhoid_fever (extended) ---
hard_rule(typhoid_fever, not(vesicular_rash)). % chickenpox, not typhoid
hard_rule(typhoid_fever, not(itchy_rash)). % chickenpox, not typhoid
hard_rule(typhoid_fever, not(pulsating_pain)). % migraine hallmark
hard_rule(typhoid_fever, not(visual_aura)). % migraine hallmark
hard_rule(typhoid_fever, not(one_sided_pain)). % migraine pattern
hard_rule(typhoid_fever, not(haemoptysis)). % TB hallmark — typhoid perforations present differently
hard_rule(typhoid_fever, not(chronic_cough)). % TB hallmark
hard_rule(typhoid_fever, not(weight_loss)). % significant weight loss = TB, not typhoid
hard_rule(typhoid_fever, not(night_sweats)). % TB-specific drenching sweats, not typhoid
hard_rule(typhoid_fever, not(diarrhea)). % typhoid causes constipation in adults more than diarrhea
hard_rule(typhoid_fever, not(burning_epigastric_pain)). % peptic ulcer sign

% --- tuberculosis (extended) ---
hard_rule(tuberculosis, not(vesicular_rash)). % chickenpox, not TB
hard_rule(tuberculosis, not(itchy_rash)). % chickenpox, not TB
hard_rule(tuberculosis, not(pulsating_pain)). % migraine hallmark
hard_rule(tuberculosis, not(visual_aura)). % migraine hallmark
hard_rule(tuberculosis, not(one_sided_pain)). % migraine pattern
hard_rule(tuberculosis, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(tuberculosis, not(weight_gain)). % TB causes weight LOSS not gain
hard_rule(tuberculosis, not(excessive_thirst)). % metabolic sign — not TB
hard_rule(tuberculosis, not(frequent_urination)). % metabolic sign — not TB
hard_rule(tuberculosis, not(blurred_vision)). % not a TB feature

% --- chickenpox (extended) ---
hard_rule(chickenpox, not(pulsating_pain)). % migraine hallmark
hard_rule(chickenpox, not(visual_aura)). % migraine hallmark
hard_rule(chickenpox, not(one_sided_pain)). % migraine pattern
hard_rule(chickenpox, not(haemoptysis)). % TB hallmark
hard_rule(chickenpox, not(chronic_cough)). % TB hallmark — chickenpox is acute
hard_rule(chickenpox, not(weight_loss)). % TB hallmark
hard_rule(chickenpox, not(night_sweats)). % TB hallmark
hard_rule(chickenpox, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(chickenpox, not(rose_spot_rash)). % typhoid-specific — distinct from chickenpox rash
hard_rule(chickenpox, not(runny_nose)). % rhinorrhea not typical of chickenpox
hard_rule(chickenpox, not(sneezing)). % not a chickenpox feature
hard_rule(chickenpox, not(sudden_onset)). % chickenpox has 1-2 day prodrome, not truly sudden

% --- peptic_ulcer (extended) ---
hard_rule(peptic_ulcer, not(vesicular_rash)). % chickenpox, not peptic ulcer
hard_rule(peptic_ulcer, not(itchy_rash)). % chickenpox, not peptic ulcer
hard_rule(peptic_ulcer, not(pulsating_pain)). % migraine hallmark
hard_rule(peptic_ulcer, not(visual_aura)). % migraine hallmark
hard_rule(peptic_ulcer, not(one_sided_pain)). % migraine pattern
hard_rule(peptic_ulcer, not(haemoptysis)). % TB hallmark — haematemesis is different
hard_rule(peptic_ulcer, not(chronic_cough)). % TB hallmark
hard_rule(peptic_ulcer, not(weight_loss)). % TB hallmark; peptic ulcer = loss of appetite not major weight loss
hard_rule(peptic_ulcer, not(rose_spot_rash)). % typhoid-specific
hard_rule(peptic_ulcer, not(night_sweats)). % TB hallmark
hard_rule(peptic_ulcer, not(loss_of_taste)). % ageusia = COVID

% --- irritable_bowel_syndrome (extended) ---
hard_rule(irritable_bowel_syndrome, not(vesicular_rash)). % chickenpox, not IBS
hard_rule(irritable_bowel_syndrome, not(itchy_rash)). % chickenpox, not IBS
hard_rule(irritable_bowel_syndrome, not(pulsating_pain)). % migraine hallmark
hard_rule(irritable_bowel_syndrome, not(visual_aura)). % migraine hallmark
hard_rule(irritable_bowel_syndrome, not(one_sided_pain)). % migraine pattern
hard_rule(irritable_bowel_syndrome, not(haemoptysis)). % TB hallmark
hard_rule(irritable_bowel_syndrome, not(chronic_cough)). % TB hallmark — IBS is GI only
hard_rule(irritable_bowel_syndrome, not(weight_loss)). % significant weight loss = TB or cancer, not IBS
hard_rule(irritable_bowel_syndrome, not(cyclical_fever)). % periodic fever = malaria
hard_rule(irritable_bowel_syndrome, not(rose_spot_rash)). % typhoid-specific
hard_rule(irritable_bowel_syndrome, not(night_sweats)). % TB hallmark
hard_rule(irritable_bowel_syndrome, not(loss_of_taste)). % ageusia = COVID
hard_rule(irritable_bowel_syndrome, not(burning_epigastric_pain)). % that location = peptic ulcer not IBS

% --- tension_headache (extended) ---
hard_rule(tension_headache, not(haemoptysis)). % TB hallmark
hard_rule(tension_headache, not(vesicular_rash)). % chickenpox, not tension headache
hard_rule(tension_headache, not(itchy_rash)). % chickenpox, not tension headache
hard_rule(tension_headache, not(rose_spot_rash)). % typhoid-specific
hard_rule(tension_headache, not(night_sweats)). % TB hallmark
hard_rule(tension_headache, not(chronic_cough)). % TB hallmark
hard_rule(tension_headache, not(rebound_tenderness)). % peritoneal sign
hard_rule(tension_headache, not(loss_of_taste)). % ageusia = COVID
hard_rule(tension_headache, not(burning_epigastric_pain)). % peptic ulcer sign
hard_rule(tension_headache, not(weight_loss)). % TB hallmark
hard_rule(tension_headache, not(cyclical_fever)). % periodic fever = malaria

% ================================================================
% SECTION 3 — CANDIDATE FILTER
% ================================================================

% candidate(Disease):
%   Disease must pass all four gates:
%   1. It is a known disease (has a disease_group)
%   2. No hard rule is violated by confirmed symptoms
%   3. Patient has not denied a symptom that is fairly distinctive
%      for this disease (shared by 4 or fewer diseases globally).
%      Threshold raised from 2 to 4 — symptoms like vomiting (3 diseases)
%      and sore_throat (2 diseases) are distinctive enough that denying
%      them should eliminate diseases that require them.
%   4. Patient has not denied a hallmark symptom (required_symptom/2)
%      that is absolutely essential to the disease — diseases without
%      their defining feature cannot be diagnosed.

candidate(Disease) :-
    disease_group(Disease, _),
    \+ hard_rule_violated(Disease),
    \+ denied_required_symptom(Disease),
    \+ denied_hallmark_symptom(Disease).

hard_rule_violated(Disease) :-
    hard_rule(Disease, not(S)),
    symptom(S).

denied_required_symptom(Disease) :-
    denied(S),
    symptom_of(Disease, S),
    symptom_rarity(S, Count),
    Count =< 4.

% denied_hallmark_symptom(+Disease)
% Eliminates a disease when the patient denies its single most
% defining hallmark — a symptom so central that the disease
% essentially cannot exist without it.
denied_hallmark_symptom(Disease) :-
    hallmark_symptom(Disease, S),
    denied(S).

% hallmark_symptom(+Disease, ?Symptom)
% Each entry names a symptom that is the absolute defining feature
% of that disease. Denying it eliminates the disease immediately.
hallmark_symptom(influenza,           fever).
hallmark_symptom(influenza,           sudden_onset).
hallmark_symptom(pneumonia,           fever).
hallmark_symptom(covid19,             fever).
hallmark_symptom(dengue_fever,        fever).
hallmark_symptom(dengue_fever,        severe_joint_pain).
hallmark_symptom(malaria,             fever).
hallmark_symptom(malaria,             chills).
hallmark_symptom(appendicitis,        right_lower_quad_pain).
hallmark_symptom(meningitis,          neck_stiffness).
hallmark_symptom(meningitis,          fever).
hallmark_symptom(strep_throat,        sore_throat).
hallmark_symptom(strep_throat,        fever).
hallmark_symptom(typhoid_fever,       fever).
hallmark_symptom(tuberculosis,        chronic_cough).
hallmark_symptom(chickenpox,          vesicular_rash).
hallmark_symptom(chickenpox,          itchy_rash).
hallmark_symptom(peptic_ulcer,        burning_epigastric_pain).
hallmark_symptom(migraine,            headache).
hallmark_symptom(migraine,            pulsating_pain).
hallmark_symptom(tension_headache,    headache).

% symptom_rarity: how many diseases share this symptom
symptom_rarity(S, Count) :-
    findall(D, symptom_of(D, S), Diseases),
    length(Diseases, Count).

all_candidates(List) :-
    findall(D, candidate(D), List).


% ================================================================
% SECTION 4 — SCORING
% ================================================================

symptom_match_score(Disease, Score) :-
    findall(S, (symptom_of(Disease, S), symptom(S)), Matched),
    sort(Matched, Deduped),   % sort/2 removes duplicates — prevents confidence > 100%
    length(Deduped, Score).

total_symptoms(Disease, Total) :-
    findall(S, symptom_of(Disease, S), All),
    length(All, Total).

confidence(Disease, Pct) :-
    symptom_match_score(Disease, Score),
    total_symptoms(Disease, Total),
    Total > 0,
    Pct is (Score / Total) * 100.


% ================================================================
% SECTION 5 — DIAGNOSIS
% ================================================================

:- dynamic diagnosis_threshold/1.
% Threshold lowered from 70% to 65% to match the early-exit
% threshold in bridge.py. Having two different thresholds (65% for
% early exit, 70% for normal diagnosis) caused cases where the
% early exit fired at 65% but the full loop never diagnosed at 70%,
% leading to inconsistent behaviour across consultation modes.
diagnosis_threshold(65).

diagnosis(Disease) :-
    candidate(Disease),
    confidence(Disease, Pct),
    diagnosis_threshold(Threshold),
    Pct >= Threshold,
    min_confirmed_symptoms(5),
    is_best_candidate(Disease, Pct).

% Require at least 3 confirmed symptoms before any diagnosis
min_confirmed_symptoms(Min) :-
    findall(S, symptom(S), Confirmed),
    length(Confirmed, Count),
    Count >= Min.

is_best_candidate(Disease, Pct) :-
    \+ (
        candidate(Other),
        Other \= Disease,
        confidence(Other, OtherPct),
        OtherPct > Pct
    ).

top_diagnoses(Top3) :-
    findall(Pct-D,
        (candidate(D), confidence(D, Pct), Pct > 0),
    Pairs),
    msort(Pairs, Sorted),
    reverse(Sorted, Desc),
    (length(Desc, L), L >= 3
        -> length(Top3, 3), append(Top3, _, Desc)
        ;  Top3 = Desc
    ).


% ================================================================
% SECTION 6 — NEXT QUESTION ENGINE
% Weighted scoring: balances breadth (coverage) with specificity.
%
% When candidates are many (>4), broad coverage questions narrow
% the field fastest. When candidates are few (<=4), disease-specific
% symptoms that only appear in those candidates are prioritised
% because they have the highest diagnostic value at that point.
%
% Score formula:
%   - Raw coverage = number of candidates that have this symptom
%   - Specificity bonus: if ALL remaining candidates share the
%     symptom, it scores as if it appears in 3 extra candidates
%     (making it the top priority — confirming it seals the diagnosis)
%   - Uniqueness boost: symptoms unique to 1 candidate get +2
%     when fewer than 4 candidates remain (late-stage disambiguation)
% ================================================================

next_question(BestSymptom) :-
    all_candidates(Candidates),
    Candidates \= [],
    length(Candidates, TotalCandidates),
    findall(Score-S,
        (
            member(D, Candidates),
            symptom_of(D, S),
            \+ asked(S),
            \+ symptom(S),
            \+ denied(S),
            symptom_coverage(S, Candidates, RawCount),
            question_score(S, RawCount, TotalCandidates, Score)
        ),
    Pairs),
    Pairs \= [],
    sort(Pairs, Sorted),          % sort/2 deduplicates ties deterministically
    last(Sorted, _-BestSymptom).

% question_score(+Symptom, +RawCoverage, +TotalCandidates, -Score)
% Computes weighted score for symptom selection.
question_score(S, RawCount, TotalCandidates, Score) :-
    % Bonus 1: if symptom covers ALL remaining candidates it is
    % the most decisive question — guaranteed to confirm or rule out
    ( RawCount =:= TotalCandidates
    -> AllBonus = 3
    ;  AllBonus = 0
    ),
    % Bonus 2: in late stage (<=4 candidates), unique symptoms
    % (appearing in only 1 disease globally) get a priority boost
    % so the engine asks the most specific question to close out
    ( TotalCandidates =< 4
    ->  symptom_rarity(S, GlobalCount),
        ( GlobalCount =:= 1 -> UniqueBonus = 2 ; UniqueBonus = 0 )
    ;   UniqueBonus = 0
    ),
    Score is RawCount + AllBonus + UniqueBonus.

symptom_coverage(S, Candidates, Count) :-
    include(has_symptom(S), Candidates, Matching),
    length(Matching, Count),
    Count > 0.

has_symptom(S, D) :- symptom_of(D, S).


% ================================================================
% SECTION 7 — CONSULTATION LOOP CONTROL
% ================================================================

:- dynamic question_count/1.
question_count(0).
% Raised from 15 to 20 — with 20 diseases and smarter elimination,
% some cases (especially metabolic diseases like diabetes) need more
% questions to reach a confident diagnosis since their symptoms are
% shared broadly and only specific follow-ups distinguish them.
max_questions(20).

consultation_complete(diagnosed) :-
    asked(early_exit_flag), !.

consultation_complete(diagnosed) :-
    diagnosis(_), !.

consultation_complete(max_questions) :-
    question_count(N),
    max_questions(Max),
    N >= Max, !.

consultation_complete(no_questions_left) :-
    \+ next_question(_).

increment_question_count :-
    retract(question_count(N)),
    N1 is N + 1,
    assertz(question_count(N1)).


% ================================================================
% SECTION 8 — OUTPUT PREDICATES
% ================================================================

needs_tests(Disease, Tests) :-
    findall(T-C,
        (test_required(Disease, T),
         test_confirms(Disease, T, C)),
    Tests).

consult_result(Disease, Confidence, Tests) :-
    diagnosis(Disease), !,
    confidence(Disease, Confidence),
    needs_tests(Disease, Tests).

consult_result(inconclusive, 0, TopTests) :-
    top_diagnoses(Top3),
    Top3 \= [], !,
    findall(T,
        (member(_-D, Top3), test_required(D, T)),
    TopTests).

consult_result(insufficient_data, 0, []).