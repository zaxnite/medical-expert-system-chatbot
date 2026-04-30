:- encoding(utf8).
% ================================================================
% inference_engine.pl
% Medical Expert System - BCS 222 Programming Paradigms
% Drives the consultation loop. Decides when to ask, when to stop,
% and how to present the final result.
% This file is the ONLY one called directly by Python.
% ================================================================

:- module(inference_engine, [
    run_consultation/0,
    run_consultation_step/3,
    present_result/0,
    engine_status/1
]).

:- use_module(knowledge_base, [
    symptom_of/2,
    symptom_question/2,
    disease_description/2,
    test_required/2
]).

:- use_module(diagnosis_rules, [
    candidate/1,
    diagnosis/1,
    next_question/1,
    consult_result/3,
    all_candidates/1,
    assert_symptom/1,
    deny_symptom/1,
    reset_session/0,
    symptom_match_score/2,
    consultation_complete/1,
    increment_question_count/0,
    question_count/1,
    top_diagnoses/1,
    confidence/2,
    symptom/1,
    denied/1,
    asked/1
]).

% SECTION 1 - ENTRY POINT
% run_consultation/0
% Called by Python bridge to start a fresh consultation.
% Resets all dynamic state then enters the loop.

run_consultation :-
    reset_session,
    print_greeting,
    consultation_loop.

print_greeting :-
    nl,
    writeln('============================================'),
    writeln('   Medical Expert System — Consultation'),
    writeln('   Please answer each question: yes / no'),
    writeln('============================================'),
    nl.

% SECTION 2 - CONSULTATION LOOP
% consultation_loop/0
% Recursive loop - base cases first, recursive case last.
% Prolog evaluates clauses top-to-bottom so exit conditions
% are checked BEFORE asking another question.

consultation_loop :-
    consultation_complete(Reason), !,
    handle_completion(Reason).

consultation_loop :-
    ask_next,
    consultation_loop.   % tail-recursive - keeps looping

% handle_completion(+Reason)
% Routes to the correct output handler based on why we stopped.
handle_completion(diagnosed)        :- present_result.
handle_completion(max_questions)     :- present_result.
handle_completion(no_questions_left) :- present_result.

% SECTION 3 - ASK NEXT QUESTION
% ask_next/0
% Gets the best symptom from diagnosis_rules, retrieves its question text,
% reads the patient's answer, and processes it.

ask_next :-
    next_question(Symptom),
    symptom_question(Symptom, QuestionText),
    ask_question(QuestionText, Symptom),
    increment_question_count.

% ask_question(+Text, +Symptom)
% Prints question, reads answer, routes to process_answer.
ask_question(Text, Symptom) :-
    question_count(N),
    Q is N + 1,
    format("~nQ~w: ~w~n", [Q, Text]),
    show_candidate_count,
    read_answer(Answer),
    process_answer(Symptom, Answer).

% show_candidate_count/0
% Shows the patient how many diseases are still being considered.
show_candidate_count :-
    all_candidates(List),
    length(List, N),
    format("   [~w condition(s) still possible]~n", [N]).

% read_answer(-Answer)
% Reads yes/no from stdin. Loops on invalid input.
% Accepts: yes, y, no, n (case-insensitive via atom_string)
read_answer(Answer) :-
    write('   Your answer (yes/no): '),
    read_term(Raw, [atom_chars(true)]),
    (valid_answer(Raw, Answer)
    ->  true
    ;   writeln('   Please type yes or no.'),
        read_answer(Answer)   % retry on bad input
    ).

valid_answer(yes, yes). valid_answer(y, yes).
valid_answer(no,  no).  valid_answer(n, no).

% process_answer(+Symptom, +Answer)
% Updates dynamic facts based on patient answer.
process_answer(Symptom, yes) :-
    assert_symptom(Symptom),
    check_early_exit.

process_answer(Symptom, no) :-
    deny_symptom(Symptom).
% SECTION 4 - EARLY EXIT OPTIMISATION
% check_early_exit/0
% After every YES answer, check if we already have a confident single diagnosis.
% This prevents asking unnecessary questions - if the patient confirms
% loss_of_smell + loss_of_taste + fever, we know it is COVID-19 without
% asking all 15 questions.

check_early_exit :-
    all_candidates(Candidates),
    length(Candidates, 1),         % only one candidate left
    Candidates = [Disease],
    confidence(Disease, Pct),
    Pct >= 70, !,                    % confident enough
    assertz(asked(early_exit_flag)).  % triggers consultation_complete

check_early_exit.  % silent success if conditions not met

% early_exit_flag is checked inside diagnosis_rules:consultation_complete
% via the asked/1 dynamic fact - no redefinition needed here
%SECTION 5 - STEP MODE (for Python bridge)
% run_consultation_step(+Symptom, +Answer, -NextAction)
% Single-step interface for the Python OOP layer.
% Instead of running the full loop in Prolog, Python calls
% this once per question - enabling the threaded architecture.
%
% NextAction is one of:
%   ask(Symptom, QuestionText)   - ask the patient this next
%   result(Disease, Pct, Tests)  - consultation complete
%   inconclusive(Top3, Tests)    - no clear winner

run_consultation_step(Symptom, Answer, NextAction) :-
    process_answer(Symptom, Answer),   % record patient answer
    determine_next_action(NextAction).  % decide what comes next

% determine_next_action(-Action)
% The Python bridge calls this after startup too (Symptom=none, Answer=none)
determine_next_action(result(D, Pct, Tests)) :-
    consultation_complete(_), !,
    consult_result(D, Pct, Tests).

determine_next_action(ask(S, Text)) :-
    next_question(S), !,
    symptom_question(S, Text),
    assertz(asked(S)),
    increment_question_count.

determine_next_action(result(insufficient_data, 0, [])).
% fallthrough - no questions left and no diagnosis
% SECTION 6 - RESULT PRESENTATION
% present_result/0
% Formats and prints the final output to stdout.
% Python can also parse this via the bridge.

present_result :-
    consult_result(Disease, Confidence, Tests),
    Disease \= inconclusive,
    Disease \= insufficient_data, !,
    nl,
    writeln('============================================'),
    writeln('   DIAGNOSIS RESULT'),
    writeln('============================================'),
    format("   Condition : ~w~n", [Disease]),
    format("   Confidence: ~1f%~n", [Confidence]),
    disease_description(Disease, Desc),
    format("   Info       : ~w~n", [Desc]),
    print_symptoms_summary(Disease),
    print_tests(Tests),
    print_disclaimer.

present_result :-
    top_diagnoses(Top3), Top3 \= [], !,
    present_inconclusive(Top3).

present_result :-
    nl,
    writeln('============================================'),
    writeln('   RESULT: Insufficient data.'),
    writeln('   Please consult a doctor directly.'),
    writeln('============================================').

% print_symptoms_summary(+Disease)
% Shows which of the patient's symptoms matched this disease.
print_symptoms_summary(Disease) :-
    findall(S,
        (symptom_of(Disease, S), symptom(S)),
    Matched),
    format("   Matched   : ~w~n", [Matched]).

% print_tests(+Tests)
% Prints recommended confirmatory tests.
print_tests([]) :-
    writeln('   Tests     : None required — clinical diagnosis.').
print_tests(Tests) :-
    writeln('   Tests recommended:'),
    forall(
        member(T-C, Tests),
        format("     - ~w  (confirms: ~w)~n", [T, C])
    ).

% present_inconclusive(+Top3)
% When no clear winner - show top 3 and suggest tests.
present_inconclusive(Top3) :-
    nl,
    writeln('============================================'),
    writeln('   RESULT: Inconclusive'),
    writeln('   Top possible conditions:'),
    forall(
        member(Pct-D, Top3),
        format("     - ~w  (~1f% match)~n", [D, Pct])
    ),
    writeln('   Please visit a doctor for further testing.'),
    writeln('============================================').

% print_disclaimer/0 - important for a medical system
print_disclaimer :-
    nl,
    writeln('   DISCLAIMER: This is not a substitute for'),
    writeln('   professional medical advice. Please consult'),
    writeln('   a qualified doctor to confirm any diagnosis.'),
    writeln('============================================'),
    nl.

%SECTION 7 - ENGINE STATUS (for Python monitoring)
% engine_status(-Status)
% Called by Python at any point to get a snapshot of engine state.

engine_status(status(
    candidates    : Candidates,
    confirmed     : Confirmed,
    denied        : Denied,
    questions_asked: QCount,
    top_candidate : TopDisease,
    top_confidence: TopPct
)) :-
    all_candidates(Candidates),
    findall(S, symptom(S), Confirmed),
    findall(S, denied(S),  Denied),
    question_count(QCount),
    ( top_diagnoses([TopPct-TopDisease|_])
    -> true
    ;  TopDisease = none, TopPct = 0
    ).