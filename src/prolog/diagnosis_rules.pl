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
% SECTION 3 — CANDIDATE FILTER
% ================================================================

candidate(Disease) :-
    disease_group(Disease, _),
    \+ hard_rule_violated(Disease),
    \+ denied_required_symptom(Disease).

hard_rule_violated(Disease) :-
    hard_rule(Disease, not(S)),
    symptom(S).

denied_required_symptom(Disease) :-
    denied(S),
    symptom_of(Disease, S),
    symptom_rarity(S, Count),
    Count =< 2.

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
    length(Matched, Score).

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
diagnosis_threshold(75).

diagnosis(Disease) :-
    candidate(Disease),
    confidence(Disease, Pct),
    diagnosis_threshold(Threshold),
    Pct >= Threshold,
    min_confirmed_symptoms(5),
    is_best_candidate(Disease, Pct).

% Require at least 5 confirmed symptoms before any diagnosis
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
% Greedy information-gain: pick symptom covering most candidates
% ================================================================

next_question(BestSymptom) :-
    all_candidates(Candidates),
    Candidates \= [],
    findall(Count-S,
        (
            member(D, Candidates),
            symptom_of(D, S),
            \+ asked(S),
            \+ symptom(S),
            \+ denied(S),
            symptom_coverage(S, Candidates, Count)
        ),
    Pairs),
    Pairs \= [],
    msort(Pairs, Sorted),
    last(Sorted, _-BestSymptom).

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
max_questions(15).

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