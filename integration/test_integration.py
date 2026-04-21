# ================================================================
# test_diagnosis.py
# Medical Expert System — BCS 222 Programming Paradigms
# Role: Automated scenario tests for all 15 diseases + edge cases.
#
# Run from project root:
#     python tests/test_diagnosis.py
# ================================================================

import sys
from pathlib import Path

# Resolve paths
BASE_DIR   = Path(__file__).resolve().parent.parent
PROLOG_DIR = BASE_DIR / "src" / "prolog"
sys.path.insert(0, str(BASE_DIR / "src" / "oop"))
sys.path.insert(0, str(BASE_DIR / "integration"))

from bridge import PrologBridge

# ----------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = failed = warned = 0

def fresh_bridge():
    b = PrologBridge(PROLOG_DIR)
    b.load()
    b.reset_session()
    return b

def run_scenario(name, confirmed, denied, expected_disease,
                 min_confidence=65, expect_inconclusive=False):
    global passed, failed, warned
    b = fresh_bridge()
    for s in confirmed: b.assert_symptom(s)
    for s in denied:    b.deny_symptom(s)
    result = b._build_result()

    disease    = result["disease"]
    confidence = result["confidence"]

    if expect_inconclusive:
        ok = disease in ("inconclusive", "insufficient_data")
        label = PASS if ok else FAIL
        if ok: passed += 1
        else:  failed += 1
        print(f"  {label}  {name:<28} -> {disease} (expected inconclusive)")
        return

    ok = (disease == expected_disease and confidence >= min_confidence)
    if disease == expected_disease and confidence < min_confidence:
        label = WARN
        warned += 1
        print(f"  {label}  {name:<28} -> {disease} ({confidence:.0f}% — low confidence)")
    elif ok:
        label = PASS
        passed += 1
        print(f"  {label}  {name:<28} -> {disease} ({confidence:.0f}%)")
    else:
        label = FAIL
        failed += 1
        print(f"  {label}  {name:<28} -> {disease} ({confidence:.0f}%) [expected {expected_disease}]")

def section(title):
    print(f"\n  {BOLD}{title}{RESET}")
    print(f"  {'─'*54}")

# ----------------------------------------------------------------
# LEVEL 1 — HAPPY PATH: classic symptom profiles
# ----------------------------------------------------------------

section("Level 1 — Classic presentations (all 15 diseases)")

run_scenario("Influenza",
    confirmed=["fever","sudden_onset","body_aches","chills","cough","fatigue","headache"],
    denied=[], expected_disease="influenza")

run_scenario("Common cold",
    confirmed=["runny_nose","sneezing","cough","sore_throat","fatigue"],
    denied=["fever","body_aches","chills","sudden_onset"],
    expected_disease="common_cold")

run_scenario("Pneumonia",
    confirmed=["fever","cough","fatigue","chest_pain","difficulty_breathing","productive_cough"],
    denied=[], expected_disease="pneumonia")

run_scenario("COVID-19",
    confirmed=["fever","cough","fatigue","loss_of_smell","loss_of_taste"],
    denied=[], expected_disease="covid19")

run_scenario("Dengue fever",
    confirmed=["fever","headache","severe_joint_pain","skin_rash","pain_behind_eyes"],
    denied=[], expected_disease="dengue_fever")

run_scenario("Malaria",
    confirmed=["fever","chills","headache","nausea","cyclical_fever","sweating_episodes"],
    denied=[], expected_disease="malaria")

run_scenario("Gastroenteritis",
    confirmed=["nausea","vomiting","abdominal_pain","diarrhea","cramping"],
    denied=[], expected_disease="gastroenteritis")

run_scenario("Appendicitis",
    confirmed=["nausea","vomiting","fever","right_lower_quad_pain","rebound_tenderness"],
    denied=["diarrhea"], expected_disease="appendicitis")

run_scenario("Meningitis",
    confirmed=["fever","headache","neck_stiffness","light_sensitivity","confusion"],
    denied=[], expected_disease="meningitis")

run_scenario("Migraine",
    confirmed=["headache","light_sensitivity","pulsating_pain","visual_aura","one_sided_pain"],
    denied=["fever","neck_stiffness","vomiting","chills"],
    expected_disease="migraine")

run_scenario("Strep throat",
    confirmed=["fever","sore_throat","tonsillar_exudate","swollen_lymph_nodes"],
    denied=["cough"], expected_disease="strep_throat")

run_scenario("Diabetes T2",
    confirmed=["fatigue","excessive_thirst","frequent_urination","blurred_vision","slow_wound_healing"],
    denied=["fever"], expected_disease="diabetes_t2")

run_scenario("Hypothyroidism",
    confirmed=["fatigue","weight_gain","cold_intolerance","dry_skin","hair_loss"],
    denied=["fever","chills"], expected_disease="hypothyroidism")

run_scenario("Anemia",
    confirmed=["fatigue","pale_skin","dizziness","cold_hands_and_feet","headache"],
    denied=["fever","chills"], expected_disease="anemia")

run_scenario("Typhoid fever",
    confirmed=["fever","headache","fatigue","abdominal_pain","rose_spot_rash","slow_heart_rate"],
    denied=[], expected_disease="typhoid_fever")


# ----------------------------------------------------------------
# LEVEL 2 — HARD RULES: negation-as-failure
# ----------------------------------------------------------------

section("Level 2 — Hard rule elimination tests")

def check_eliminated(name, symptom_to_assert, disease_that_should_be_gone):
    global passed, failed
    b = fresh_bridge()
    b.assert_symptom(symptom_to_assert)
    cands = [r["D"] for r in b.query("candidate(D)")]
    ok = disease_that_should_be_gone not in cands
    label = PASS if ok else FAIL
    if ok: passed += 1
    else:  failed += 1
    print(f"  {label}  Assert {symptom_to_assert:<22} -> {disease_that_should_be_gone} eliminated: {ok}")

check_eliminated("Cold+fever",       "fever",         "common_cold")
check_eliminated("Strep+cough",      "cough",         "strep_throat")
check_eliminated("Migraine+fever",   "fever",         "migraine")
check_eliminated("Migraine+vomit",   "vomiting",      "migraine")
check_eliminated("Migraine+chills",  "chills",        "migraine")
check_eliminated("Diabetes+fever",   "fever",         "diabetes_t2")
check_eliminated("Hypothyroid+fever","fever",         "hypothyroidism")
check_eliminated("Anemia+fever",     "fever",         "anemia")
check_eliminated("Appndcitis+diarr", "diarrhea",      "appendicitis")
check_eliminated("Cold+nausea",      "nausea",        "common_cold")


# ----------------------------------------------------------------
# LEVEL 3 — EDGE CASES
# ----------------------------------------------------------------

section("Level 3 — Edge cases")

# All-no answers — should return inconclusive
run_scenario("All-no answers",
    confirmed=[],
    denied=["fever","cough","fatigue","headache","nausea"],
    expected_disease="inconclusive",
    expect_inconclusive=True)

# Only one symptom — not enough for diagnosis
run_scenario("Single symptom only",
    confirmed=["fever"],
    denied=[], expected_disease="inconclusive",
    expect_inconclusive=True)

# Contradictory profile — no disease should win cleanly
run_scenario("Contradictory profile",
    confirmed=["fever","runny_nose","neck_stiffness","weight_gain","diarrhea"],
    denied=[], expected_disease="inconclusive",
    expect_inconclusive=True)

# Minimal diabetes — 4 symptoms exactly at threshold
run_scenario("Minimal diabetes (4 symptoms)",
    confirmed=["fatigue","excessive_thirst","frequent_urination","slow_wound_healing"],
    denied=["fever"], expected_disease="diabetes_t2", min_confidence=65)

# Flu vs cold distinction — body_aches + sudden_onset should push to flu
run_scenario("Flu vs cold distinction",
    confirmed=["cough","fatigue","runny_nose","body_aches","sudden_onset","fever"],
    denied=[], expected_disease="influenza")

# Dengue vs malaria distinction — cyclical_fever absent, joint_pain present
run_scenario("Dengue vs malaria (joint pain)",
    confirmed=["fever","headache","severe_joint_pain","skin_rash","pain_behind_eyes"],
    denied=["cyclical_fever","sweating_episodes"],
    expected_disease="dengue_fever")

# Meningitis vs migraine — neck stiffness is the key differentiator
run_scenario("Meningitis vs migraine (neck stiffness)",
    confirmed=["fever","headache","neck_stiffness","light_sensitivity","confusion"],
    denied=[], expected_disease="meningitis")


# ----------------------------------------------------------------
# LEVEL 4 — REAL SESSION REPLAY
# ----------------------------------------------------------------

section("Level 4 — Real session replays from actual runs")

# Session that previously returned wrong 'migraine' result
run_scenario("Previous wrong migraine session",
    confirmed=["headache","cough","sore_throat","abdominal_pain","vomiting",
               "light_sensitivity","chills","weight_gain","visual_aura"],
    denied=["fatigue","fever","nausea","shortness_of_breath"],
    expected_disease="inconclusive",
    expect_inconclusive=True)

# Session that returned correct diabetes result
run_scenario("Diabetes session replay",
    confirmed=["fatigue","slow_wound_healing","frequent_urination","excessive_thirst"],
    denied=["fever","headache","nausea","cough","vomiting","sore_throat",
            "shortness_of_breath","light_sensitivity","chills","weight_gain"],
    expected_disease="diabetes_t2")


# ----------------------------------------------------------------
# SUMMARY
# ----------------------------------------------------------------

total = passed + failed + warned
print(f"\n{'='*56}")
print(f"  {BOLD}TEST RESULTS{RESET}")
print(f"{'='*56}")
print(f"  Total tests : {total}")
print(f"  {PASS}        : {passed}")
print(f"  {FAIL}        : {failed}")
if warned:
    print(f"  {WARN}        : {warned}  (correct disease, low confidence)")
print(f"{'='*56}\n")

sys.exit(0 if failed == 0 else 1)