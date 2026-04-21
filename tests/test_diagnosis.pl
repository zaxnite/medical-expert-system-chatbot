:- encoding(utf8).
:- load_files([
    '../src/prolog/knowledge_base',
    '../src/prolog/diagnosis_rules',
    '../src/prolog/inference_engine'
], []).

run_test(Disease, Symptoms) :-
    reset_session,
    forall(member(S, Symptoms), assert_symptom(S)),
    (   consult_result(D, Pct, _)
    ->  (   D == Disease
        ->  format('  PASS  ~w (~1f%)~n', [D, Pct])
        ;   format('  FAIL  ~w  ->  got ~w~n', [Disease, D])
        )
    ;   format('  FAIL  ~w  ->  no result~n', [Disease])
    ),
    reset_session.

run_all :-
    writeln(''),
    writeln('============================================================'),
    writeln(' FULL DIAGNOSIS TEST — 20 DISEASES'),
    writeln('============================================================'),

    writeln('--- Group A: Respiratory ---'),
    run_test(influenza,      [fever,cough,fatigue,headache,body_aches,chills,sudden_onset]),
    run_test(common_cold,    [cough,sore_throat,fatigue,runny_nose,sneezing]),
    run_test(pneumonia,      [fever,cough,fatigue,chest_pain,difficulty_breathing,productive_cough]),
    run_test(bronchitis,     [cough,fatigue,sore_throat,persistent_cough,mucus_production,mild_fever]),

    writeln('--- Group B: Viral / Infectious ---'),
    run_test(covid19,        [fever,cough,fatigue,loss_of_smell,loss_of_taste,shortness_of_breath]),
    run_test(dengue_fever,   [fever,headache,fatigue,severe_joint_pain,skin_rash,pain_behind_eyes]),
    run_test(malaria,        [fever,chills,headache,fatigue,cyclical_fever,sweating_episodes,nausea]),
    run_test(typhoid_fever,  [fever,headache,fatigue,rose_spot_rash,abdominal_pain,slow_heart_rate]),

    writeln('--- Group C: Gastrointestinal ---'),
    run_test(gastroenteritis,[nausea,vomiting,abdominal_pain,diarrhea,cramping,low_grade_fever]),
    run_test(appendicitis,   [nausea,vomiting,fever,right_lower_quad_pain,rebound_tenderness]),
    run_test(gerd,           [nausea,chest_discomfort,heartburn,acid_reflux,regurgitation]),
    run_test(peptic_ulcer,   [nausea,abdominal_pain,burning_stomach_pain,pain_worse_when_empty,bloating]),

    writeln('--- Group D: Neurological / ENT ---'),
    run_test(meningitis,     [fever,headache,neck_stiffness,light_sensitivity,confusion]),
    run_test(migraine,       [headache,nausea,light_sensitivity,pulsating_pain,visual_aura,one_sided_pain]),
    run_test(strep_throat,   [fever,sore_throat,tonsillar_exudate,swollen_lymph_nodes]),
    run_test(sinusitis,      [headache,fatigue,sore_throat,facial_pain,nasal_congestion,post_nasal_drip,reduced_smell]),

    writeln('--- Group E: Metabolic / Systemic ---'),
    run_test(diabetes_t2,    [fatigue,excessive_thirst,frequent_urination,blurred_vision,slow_wound_healing]),
    run_test(hypothyroidism, [fatigue,weight_gain,cold_intolerance,dry_skin,constipation,hair_loss]),
    run_test(anemia,         [fatigue,headache,pale_skin,dizziness,cold_hands_and_feet,shortness_of_breath]),
    run_test(hypertension,   [headache,fatigue,dizziness,nosebleeds,blurred_vision]),

    writeln('============================================================'),
    writeln(' HARD RULE TESTS'),
    writeln('============================================================'),

    % strep eliminated by cough
    reset_session,
    assert_symptom(cough),
    all_candidates(C1),
    (   \+ member(strep_throat, C1)
    ->  writeln('  PASS  strep_throat eliminated by cough')
    ;   writeln('  FAIL  strep_throat should be gone after cough')
    ),
    reset_session,

    % common_cold eliminated by fever
    assert_symptom(fever),
    all_candidates(C2),
    (   \+ member(common_cold, C2)
    ->  writeln('  PASS  common_cold eliminated by fever')
    ;   writeln('  FAIL  common_cold should be gone after fever')
    ),
    reset_session,

    % migraine eliminated by fever
    assert_symptom(fever),
    all_candidates(C3),
    (   \+ member(migraine, C3)
    ->  writeln('  PASS  migraine eliminated by fever')
    ;   writeln('  FAIL  migraine should be gone after fever')
    ),
    reset_session,

    % appendicitis eliminated by diarrhea
    assert_symptom(diarrhea),
    all_candidates(C4),
    (   \+ member(appendicitis, C4)
    ->  writeln('  PASS  appendicitis eliminated by diarrhea')
    ;   writeln('  FAIL  appendicitis should be gone after diarrhea')
    ),
    reset_session,

    writeln('============================================================'),
    writeln(' ALL TESTS COMPLETE'),
    writeln('============================================================'),
    nl.

:- run_all, halt.