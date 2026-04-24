:- encoding(utf8).
% ================================================================
% knowledge_base.pl
% Medical Expert System — BCS 222 Programming Paradigms
% Role: Declarative facts about diseases, symptoms, and tests.
%       Pure data — no inference logic lives here.
% ================================================================

:- module(knowledge_base, [
    disease_group/2,
    symptom_of/2,
    test_required/2,
    test_confirms/3,
    symptom_question/2,
    disease_description/2
]).

:- discontiguous symptom_of/2.
:- discontiguous test_required/2.
:- discontiguous disease_group/2.


% ================================================================
% GROUP A — RESPIRATORY (3 diseases)
% ================================================================

disease_group(influenza,    respiratory).
disease_group(common_cold,  respiratory).
disease_group(pneumonia,    respiratory).

% --- Influenza ---
symptom_of(influenza, fever).
symptom_of(influenza, cough).
symptom_of(influenza, fatigue).
symptom_of(influenza, headache).
symptom_of(influenza, body_aches).
symptom_of(influenza, chills).
symptom_of(influenza, sudden_onset).
test_required(influenza, rapid_flu_test).

% --- Common cold ---
symptom_of(common_cold, cough).
symptom_of(common_cold, sore_throat).
symptom_of(common_cold, fatigue).
symptom_of(common_cold, runny_nose).
symptom_of(common_cold, sneezing).

% --- Pneumonia ---
symptom_of(pneumonia, fever).
symptom_of(pneumonia, cough).
symptom_of(pneumonia, fatigue).
symptom_of(pneumonia, chest_pain).
symptom_of(pneumonia, difficulty_breathing).
symptom_of(pneumonia, productive_cough).
test_required(pneumonia, chest_xray).
test_required(pneumonia, blood_culture).


% ================================================================
% GROUP B — VIRAL / INFECTIOUS (3 diseases)
% ================================================================

disease_group(covid19,       viral_infectious).
disease_group(dengue_fever,  viral_infectious).
disease_group(malaria,       viral_infectious).

% --- COVID-19 ---
symptom_of(covid19, fever).
symptom_of(covid19, cough).
symptom_of(covid19, fatigue).
symptom_of(covid19, loss_of_smell).
symptom_of(covid19, loss_of_taste).
symptom_of(covid19, shortness_of_breath).
test_required(covid19, pcr_test).
test_required(covid19, rapid_antigen_test).

% --- Dengue fever ---
symptom_of(dengue_fever, fever).
symptom_of(dengue_fever, headache).
symptom_of(dengue_fever, fatigue).
symptom_of(dengue_fever, severe_joint_pain).
symptom_of(dengue_fever, skin_rash).
symptom_of(dengue_fever, pain_behind_eyes).
test_required(dengue_fever, ns1_antigen_test).
test_required(dengue_fever, platelet_count).

% --- Malaria ---
symptom_of(malaria, fever).
symptom_of(malaria, chills).
symptom_of(malaria, headache).
symptom_of(malaria, fatigue).
symptom_of(malaria, nausea).
symptom_of(malaria, cyclical_fever).
symptom_of(malaria, sweating_episodes).
test_required(malaria, blood_smear).
test_required(malaria, rdt_malaria_test).


% ================================================================
% GROUP C — GASTROINTESTINAL (2 diseases)
% ================================================================

disease_group(gastroenteritis, gastrointestinal).
disease_group(appendicitis,    gastrointestinal).

% --- Gastroenteritis ---
symptom_of(gastroenteritis, nausea).
symptom_of(gastroenteritis, vomiting).
symptom_of(gastroenteritis, abdominal_pain).
symptom_of(gastroenteritis, diarrhea).
symptom_of(gastroenteritis, cramping).
symptom_of(gastroenteritis, low_grade_fever).

% --- Appendicitis ---
symptom_of(appendicitis, nausea).
symptom_of(appendicitis, vomiting).
symptom_of(appendicitis, fever).
symptom_of(appendicitis, right_lower_quad_pain).
symptom_of(appendicitis, rebound_tenderness).
test_required(appendicitis, ultrasound).
test_required(appendicitis, elevated_wbc).


% ================================================================
% GROUP D — NEUROLOGICAL / ENT (3 diseases)
% ================================================================

disease_group(meningitis,   neurological_ent).
disease_group(migraine,     neurological_ent).
disease_group(strep_throat, neurological_ent).

% --- Meningitis ---
symptom_of(meningitis, fever).
symptom_of(meningitis, headache).
symptom_of(meningitis, neck_stiffness).
symptom_of(meningitis, light_sensitivity).
symptom_of(meningitis, confusion).
test_required(meningitis, lumbar_puncture).
test_required(meningitis, ct_scan).

% --- Migraine ---
symptom_of(migraine, headache).
symptom_of(migraine, nausea).
symptom_of(migraine, light_sensitivity).
symptom_of(migraine, pulsating_pain).
symptom_of(migraine, visual_aura).
symptom_of(migraine, one_sided_pain).

% --- Strep throat ---
symptom_of(strep_throat, fever).
symptom_of(strep_throat, sore_throat).
symptom_of(strep_throat, tonsillar_exudate).
symptom_of(strep_throat, swollen_lymph_nodes).
test_required(strep_throat, rapid_strep_test).
test_required(strep_throat, throat_culture).


% ================================================================
% GROUP E — METABOLIC / SYSTEMIC (4 diseases)
% ================================================================

disease_group(diabetes_t2,    metabolic_systemic).
disease_group(hypothyroidism, metabolic_systemic).
disease_group(anemia,         metabolic_systemic).
disease_group(typhoid_fever,  metabolic_systemic).

% --- Diabetes type 2 ---
symptom_of(diabetes_t2, fatigue).
symptom_of(diabetes_t2, excessive_thirst).
symptom_of(diabetes_t2, frequent_urination).
symptom_of(diabetes_t2, blurred_vision).
symptom_of(diabetes_t2, slow_wound_healing).
test_required(diabetes_t2, fasting_blood_glucose).
test_required(diabetes_t2, hba1c_test).

% --- Hypothyroidism ---
symptom_of(hypothyroidism, fatigue).
symptom_of(hypothyroidism, weight_gain).
symptom_of(hypothyroidism, cold_intolerance).
symptom_of(hypothyroidism, dry_skin).
symptom_of(hypothyroidism, constipation).
symptom_of(hypothyroidism, hair_loss).
test_required(hypothyroidism, tsh_blood_test).
test_required(hypothyroidism, t4_level_test).

% --- Anemia ---
symptom_of(anemia, fatigue).
symptom_of(anemia, headache).
symptom_of(anemia, pale_skin).
symptom_of(anemia, dizziness).
symptom_of(anemia, cold_hands_and_feet).
symptom_of(anemia, shortness_of_breath).
test_required(anemia, cbc_blood_test).
test_required(anemia, serum_ferritin).

% --- Typhoid fever ---
symptom_of(typhoid_fever, fever).
symptom_of(typhoid_fever, headache).
symptom_of(typhoid_fever, fatigue).
symptom_of(typhoid_fever, abdominal_pain).
symptom_of(typhoid_fever, rose_spot_rash).
symptom_of(typhoid_fever, slow_heart_rate).
test_required(typhoid_fever, widal_test).
test_required(typhoid_fever, blood_culture).




% ================================================================
% GROUP A — RESPIRATORY (continued)
% ================================================================

% --- Tuberculosis ---
symptom_of(tuberculosis, chronic_cough).
symptom_of(tuberculosis, productive_cough).
symptom_of(tuberculosis, night_sweats).
symptom_of(tuberculosis, weight_loss).
symptom_of(tuberculosis, fatigue).
symptom_of(tuberculosis, low_grade_fever).
symptom_of(tuberculosis, chest_pain).
symptom_of(tuberculosis, haemoptysis).
disease_group(tuberculosis, respiratory).
test_required(tuberculosis, sputum_culture).
test_required(tuberculosis, chest_xray).
test_required(tuberculosis, tuberculin_test).

% ================================================================
% GROUP B — VIRAL / INFECTIOUS (continued)
% ================================================================

% --- Chickenpox ---
symptom_of(chickenpox, fever).
symptom_of(chickenpox, fatigue).
symptom_of(chickenpox, itchy_rash).
symptom_of(chickenpox, vesicular_rash).
symptom_of(chickenpox, loss_of_appetite).
symptom_of(chickenpox, headache).
symptom_of(chickenpox, chills).
disease_group(chickenpox, viral_infectious).
test_required(chickenpox, tzanck_smear).
test_required(chickenpox, varicella_pcr).

% ================================================================
% GROUP C — GASTROINTESTINAL (continued)
% ================================================================

% --- Peptic Ulcer Disease ---
symptom_of(peptic_ulcer, burning_epigastric_pain).
symptom_of(peptic_ulcer, nausea).
symptom_of(peptic_ulcer, bloating).
symptom_of(peptic_ulcer, loss_of_appetite).
symptom_of(peptic_ulcer, vomiting).
disease_group(peptic_ulcer, gastrointestinal).
test_required(peptic_ulcer, endoscopy).
test_required(peptic_ulcer, h_pylori_breath_test).

% --- Irritable Bowel Syndrome ---
symptom_of(irritable_bowel_syndrome, cramping).
symptom_of(irritable_bowel_syndrome, abdominal_pain).
symptom_of(irritable_bowel_syndrome, bloating).
symptom_of(irritable_bowel_syndrome, diarrhea).
symptom_of(irritable_bowel_syndrome, constipation).
disease_group(irritable_bowel_syndrome, gastrointestinal).
test_required(irritable_bowel_syndrome, colonoscopy).
test_required(irritable_bowel_syndrome, stool_analysis).

% ================================================================
% GROUP D — NEUROLOGICAL / ENT (continued)
% ================================================================

% --- Tension Headache ---
symptom_of(tension_headache, headache).
symptom_of(tension_headache, fatigue).
symptom_of(tension_headache, dizziness).
symptom_of(tension_headache, light_sensitivity).
symptom_of(tension_headache, neck_stiffness).
disease_group(tension_headache, neurological_ent).
% No tests — tension headache is a clinical diagnosis

% ================================================================
% SYMPTOM QUESTIONS — what the chatbot asks the patient
% ================================================================

symptom_question(fever,               "Do you have a fever or feel unusually hot?").
symptom_question(cough,               "Do you have a cough?").
symptom_question(fatigue,             "Are you feeling unusually tired or weak?").
symptom_question(headache,            "Do you have a headache?").
symptom_question(sore_throat,         "Do you have a sore or painful throat?").
symptom_question(nausea,              "Are you feeling nauseous?").
symptom_question(vomiting,            "Have you been vomiting?").
symptom_question(chills,              "Are you experiencing chills or shivering?").
symptom_question(body_aches,          "Do you have aching muscles or body pain?").
symptom_question(sudden_onset,        "Did your symptoms come on very suddenly?").
symptom_question(runny_nose,          "Do you have a runny or stuffy nose?").
symptom_question(sneezing,            "Are you sneezing frequently?").
symptom_question(chest_pain,          "Do you have pain or tightness in your chest?").
symptom_question(difficulty_breathing,"Are you having difficulty breathing?").
symptom_question(productive_cough,    "Are you coughing up mucus or phlegm?").
symptom_question(loss_of_smell,       "Have you lost your sense of smell?").
symptom_question(loss_of_taste,       "Have you lost your sense of taste?").
symptom_question(shortness_of_breath, "Do you feel short of breath easily?").
symptom_question(severe_joint_pain,   "Do you have severe pain in your joints?").
symptom_question(skin_rash,           "Do you have a skin rash anywhere on your body?").
symptom_question(pain_behind_eyes,    "Do you feel pain behind your eyes?").
symptom_question(cyclical_fever,      "Does your fever come and go in regular cycles?").
symptom_question(sweating_episodes,   "Do you have sudden episodes of heavy sweating?").
symptom_question(abdominal_pain,      "Do you have pain in your abdomen or stomach area?").
symptom_question(diarrhea,            "Are you experiencing diarrhea?").
symptom_question(cramping,            "Do you have stomach cramps?").
symptom_question(low_grade_fever,     "Do you have a mild persistent low-grade fever?").
symptom_question(right_lower_quad_pain,"Do you have sharp pain in the lower right of your abdomen?").
symptom_question(rebound_tenderness,  "Does your abdominal pain worsen when pressure is released?").
symptom_question(neck_stiffness,      "Is it painful or difficult to move your neck?").
symptom_question(light_sensitivity,   "Does light hurt your eyes or make you uncomfortable?").
symptom_question(confusion,           "Are you feeling confused or disoriented?").
symptom_question(pulsating_pain,      "Is your headache throbbing or pulsating?").
symptom_question(visual_aura,         "Do you see flashing lights or blind spots before headaches?").
symptom_question(one_sided_pain,      "Is the headache pain only on one side of your head?").
symptom_question(tonsillar_exudate,   "Do you see white patches on the back of your throat?").
symptom_question(swollen_lymph_nodes, "Do you have swollen or tender lumps in your neck?").
symptom_question(excessive_thirst,    "Are you feeling unusually thirsty throughout the day?").
symptom_question(frequent_urination,  "Are you urinating much more frequently than usual?").
symptom_question(blurred_vision,      "Is your vision blurry or unclear?").
symptom_question(slow_wound_healing,  "Are cuts or wounds taking longer than usual to heal?").
symptom_question(weight_gain,         "Have you gained weight without a clear reason?").
symptom_question(cold_intolerance,    "Do you feel unusually cold even in warm environments?").
symptom_question(dry_skin,            "Is your skin unusually dry or flaky?").
symptom_question(constipation,        "Are you experiencing constipation?").
symptom_question(hair_loss,           "Have you noticed unusual hair loss recently?").
symptom_question(pale_skin,           "Has anyone told you your skin looks pale or washed out?").
symptom_question(dizziness,           "Are you feeling dizzy or lightheaded?").
symptom_question(cold_hands_and_feet, "Are your hands and feet often cold?").
symptom_question(rose_spot_rash,      "Do you have small rose-coloured spots on your abdomen?").
symptom_question(slow_heart_rate,     "Have you been told your heart rate is unusually slow?").

symptom_question(chronic_cough,          "Have you had a persistent cough lasting more than 3 weeks?").
symptom_question(night_sweats,           "Do you wake up drenched in sweat at night?").
symptom_question(weight_loss,            "Have you lost weight recently without trying?").
symptom_question(haemoptysis,            "Have you coughed up blood or blood-stained mucus?").
symptom_question(itchy_rash,             "Do you have an itchy rash on your body?").
symptom_question(vesicular_rash,         "Do you have a rash with small fluid-filled blisters?").
symptom_question(loss_of_appetite,       "Have you lost your appetite or interest in eating?").
symptom_question(burning_epigastric_pain,"Do you have a burning pain in your upper stomach area?").
symptom_question(bloating,               "Do you feel bloated or full of gas?").



% ================================================================
% TEST CONFIRMATIONS
% ================================================================

test_confirms(influenza,    rapid_flu_test,        confirms_viral_strain).
test_confirms(covid19,      pcr_test,              confirms_sars_cov2).
test_confirms(covid19,      rapid_antigen_test,    indicates_active_infection).
test_confirms(dengue_fever, ns1_antigen_test,      confirms_dengue_virus).
test_confirms(dengue_fever, platelet_count,        shows_thrombocytopenia).
test_confirms(malaria,      blood_smear,           confirms_parasite_presence).
test_confirms(malaria,      rdt_malaria_test,      rapid_parasite_detection).
test_confirms(pneumonia,    chest_xray,            shows_lung_consolidation).
test_confirms(pneumonia,    blood_culture,         identifies_bacterial_cause).
test_confirms(appendicitis, ultrasound,            visualises_appendix_swelling).
test_confirms(appendicitis, elevated_wbc,          confirms_infection_response).
test_confirms(meningitis,   lumbar_puncture,       confirms_csf_infection).
test_confirms(meningitis,   ct_scan,               rules_out_brain_lesion).
test_confirms(strep_throat, rapid_strep_test,      detects_group_a_strep).
test_confirms(strep_throat, throat_culture,        confirms_bacterial_strain).
test_confirms(diabetes_t2,  fasting_blood_glucose, shows_elevated_glucose).
test_confirms(diabetes_t2,  hba1c_test,            shows_3month_glucose_avg).
test_confirms(hypothyroidism,tsh_blood_test,       confirms_low_thyroid).
test_confirms(hypothyroidism,t4_level_test,        measures_thyroid_hormone).
test_confirms(anemia,       cbc_blood_test,        shows_low_haemoglobin).
test_confirms(anemia,       serum_ferritin,        measures_iron_stores).
test_confirms(typhoid_fever, widal_test,           detects_salmonella_antibodies).
test_confirms(typhoid_fever, blood_culture,        confirms_salmonella_typhi).
test_confirms(tuberculosis,   sputum_culture,      confirms_mycobacterium_tuberculosis).
test_confirms(tuberculosis,   chest_xray,          shows_lung_infiltrates).
test_confirms(tuberculosis,   tuberculin_test,     indicates_tb_exposure).
test_confirms(chickenpox,     tzanck_smear,        confirms_varicella_zoster).
test_confirms(chickenpox,     varicella_pcr,       detects_vzv_dna).
test_confirms(peptic_ulcer,   endoscopy,           visualises_ulcer_directly).
test_confirms(peptic_ulcer,   h_pylori_breath_test,detects_h_pylori_infection).
test_confirms(irritable_bowel_syndrome, colonoscopy,   rules_out_organic_disease).
test_confirms(irritable_bowel_syndrome, stool_analysis,excludes_infection_or_inflammation).



% ================================================================
% DISEASE DESCRIPTIONS
% ================================================================

disease_description(influenza,
    "Influenza is a contagious viral infection affecting the respiratory system.").
disease_description(common_cold,
    "The common cold is a mild viral infection of the upper respiratory tract.").
disease_description(pneumonia,
    "Pneumonia is an infection that inflames the air sacs in one or both lungs.").
disease_description(covid19,
    "COVID-19 is a respiratory illness caused by the SARS-CoV-2 virus.").
disease_description(dengue_fever,
    "Dengue is a mosquito-borne viral disease common in tropical regions.").
disease_description(malaria,
    "Malaria is a life-threatening disease caused by parasites transmitted by mosquitoes.").
disease_description(gastroenteritis,
    "Gastroenteritis is inflammation of the stomach and intestines, often from infection.").
disease_description(appendicitis,
    "Appendicitis is inflammation of the appendix and requires urgent medical attention.").
disease_description(meningitis,
    "Meningitis is inflammation of the membranes surrounding the brain and spinal cord.").
disease_description(migraine,
    "Migraine is a neurological condition causing intense recurring headaches.").
disease_description(strep_throat,
    "Strep throat is a bacterial infection causing throat pain and inflammation.").
disease_description(diabetes_t2,
    "Type 2 diabetes is a chronic condition affecting how the body processes blood sugar.").
disease_description(hypothyroidism,
    "Hypothyroidism is an underactive thyroid gland that does not produce enough hormones.").
disease_description(anemia,
    "Anemia is a condition where you lack enough red blood cells to carry adequate oxygen.").
disease_description(typhoid_fever,
    "Typhoid is a bacterial infection caused by Salmonella typhi via contaminated food or water.").
disease_description(tuberculosis,
    "Tuberculosis is a bacterial infection caused by Mycobacterium tuberculosis, primarily affecting the lungs.").
disease_description(chickenpox,
    "Chickenpox is a highly contagious viral infection caused by the varicella-zoster virus, causing an itchy blister-like rash.").
disease_description(peptic_ulcer,
    "Peptic ulcer disease is a condition where painful sores develop in the lining of the stomach or upper small intestine.").
disease_description(irritable_bowel_syndrome,
    "Irritable bowel syndrome is a chronic functional gut disorder causing recurrent abdominal pain, bloating, and altered bowel habits.").
disease_description(tension_headache,
    "Tension headache is the most common headache type, causing a dull bilateral pressure, often triggered by stress or posture.").