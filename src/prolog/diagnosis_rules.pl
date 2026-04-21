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

% --- Pneumonia: respiratory — ruled out by non-respiratory dominance ---
hard_rule(pneumonia, not(diarrhea)).
hard_rule(pneumonia, not(neck_stiffness)).
hard_rule(pneumonia, not(weight_gain)).
hard_rule(pneumonia, not(excessive_thirst)).

% --- COVID-19 ---
hard_rule(covid19, not(neck_stiffness)).
hard_rule(covid19, not(weight_gain)).
hard_rule(covid19, not(diarrhea)).

% --- Dengue fever: tropical viral ---
hard_rule(dengue_fever, not(neck_stiffness)).
hard_rule(dengue_fever, not(diarrhea)).
hard_rule(dengue_fever, not(weight_gain)).

% --- Malaria: cyclical fever pattern ---
hard_rule(malaria, not(neck_stiffness)).
hard_rule(malaria, not(weight_gain)).
hard_rule(malaria, not(diarrhea)).

% --- Gastroenteritis: GI only ---
hard_rule(gastroenteritis, not(chest_pain)).
hard_rule(gastroenteritis, not(neck_stiffness)).
hard_rule(gastroenteritis, not(weight_gain)).
hard_rule(gastroenteritis, not(loss_of_smell)).

% --- Appendicitis: ruled out by diarrhea (favours gastroenteritis) ---
hard_rule(appendicitis, not(diarrhea)).
hard_rule(appendicitis, not(weight_gain)).
hard_rule(appendicitis, not(loss_of_smell)).

% --- Meningitis: neurological emergency ---
hard_rule(meningitis, not(diarrhea)).
hard_rule(meningitis, not(weight_gain)).
hard_rule(meningitis, not(runny_nose)).

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

% --- Hypothyroidism: chronic systemic ---
hard_rule(hypothyroidism, not(fever)).
hard_rule(hypothyroidism, not(vomiting)).
hard_rule(hypothyroidism, not(neck_stiffness)).
hard_rule(hypothyroidism, not(chills)).
hard_rule(hypothyroidism, not(runny_nose)).
hard_rule(hypothyroidism, not(sneezing)).
hard_rule(hypothyroidism, not(diarrhea)).

% --- Anemia: chronic — no infection symptoms ---
hard_rule(anemia, not(fever)).
hard_rule(anemia, not(vomiting)).
hard_rule(anemia, not(neck_stiffness)).
hard_rule(anemia, not(chills)).
hard_rule(anemia, not(runny_nose)).
hard_rule(anemia, not(diarrhea)).

% --- Typhoid fever: systemic bacterial ---
hard_rule(typhoid_fever, not(neck_stiffness)).
hard_rule(typhoid_fever, not(weight_gain)).
hard_rule(typhoid_fever, not(runny_nose)).
hard_rule(typhoid_fever, not(sneezing)).


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