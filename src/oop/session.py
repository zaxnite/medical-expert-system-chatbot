# session.py
# Medical Expert System - BCS 222 Programming Paradigms
# OOP state management. Defines UserSession, MedicalRecord, and ConsultationLog
# so Prolog stays stateless between calls and all session data lives in Python.

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional
import uuid
import json


# ----------------------------------------------------------------
# ENUMS
# ----------------------------------------------------------------

class SessionState(Enum):
    PENDING    = auto()   # created, not started yet
    ACTIVE     = auto()   # questions being asked
    COMPLETE   = auto()   # diagnosis reached
    INCOMPLETE = auto()   # ended without diagnosis


class ConfidenceLevel(Enum):
    HIGH      = "High"
    MODERATE  = "Moderate"
    LOW       = "Low"
    UNCERTAIN = "Uncertain"

    @staticmethod
    def from_pct(pct: float) -> ConfidenceLevel:
        if pct >= 75:
            return ConfidenceLevel.HIGH
        elif pct >= 50:
            return ConfidenceLevel.MODERATE
        elif pct > 0:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.UNCERTAIN


# ----------------------------------------------------------------
# DATACLASSES
# ----------------------------------------------------------------

@dataclass
class QAEntry:
    symptom:       str
    question_text: str
    answer:        bool
    timestamp:     datetime = field(default_factory=datetime.now)
    candidates_remaining: int = 0  # how many diseases were still possible at this point

    def to_dict(self) -> dict:
        return {
            "symptom":              self.symptom,
            "question":             self.question_text,
            "answer":               "yes" if self.answer else "no",
            "timestamp":            self.timestamp.isoformat(),
            "candidates_remaining": self.candidates_remaining
        }


@dataclass
class DiagnosisResult:
    disease:       str
    confidence:    float
    description:   str
    tests:         list[dict]   # [{"test": ..., "confirms": ...}]
    timestamp:     datetime = field(default_factory=datetime.now)
    is_conclusive: bool = True

    @property
    def confidence_level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_pct(self.confidence)

    def to_dict(self) -> dict:
        return {
            "disease":          self.disease,
            "confidence":       round(self.confidence, 1),
            "confidence_level": self.confidence_level.value,
            "description":      self.description,
            "tests":            self.tests,
            "is_conclusive":    self.is_conclusive,
            "timestamp":        self.timestamp.isoformat()
        }


# ----------------------------------------------------------------
# MEDICAL RECORD
# ----------------------------------------------------------------

class MedicalRecord:
    # tracks which symptoms the patient confirmed or denied

    def __init__(self, patient_name: str):
        self._patient_name = patient_name
        self._confirmed:  list[str] = []
        self._denied:     list[str] = []
        self._created_at  = datetime.now()

    @property
    def patient_name(self) -> str:
        return self._patient_name

    @property
    def confirmed_symptoms(self) -> list[str]:
        return list(self._confirmed)

    @property
    def denied_symptoms(self) -> list[str]:
        return list(self._denied)

    @property
    def all_reported(self) -> list[str]:
        return self._confirmed + self._denied

    def record_yes(self, symptom: str) -> None:
        if symptom not in self._confirmed:
            self._confirmed.append(symptom)

    def record_no(self, symptom: str) -> None:
        if symptom not in self._denied:
            self._denied.append(symptom)

    def has_symptom(self, symptom: str) -> bool:
        return symptom in self._confirmed

    def was_asked(self, symptom: str) -> bool:
        return symptom in self.all_reported

    def to_dict(self) -> dict:
        return {
            "patient_name":       self._patient_name,
            "confirmed_symptoms": self._confirmed,
            "denied_symptoms":    self._denied,
            "created_at":         self._created_at.isoformat()
        }

    def __repr__(self) -> str:
        return (f"MedicalRecord(patient='{self._patient_name}', "
                f"confirmed={len(self._confirmed)}, "
                f"denied={len(self._denied)})")


# ----------------------------------------------------------------
# CONSULTATION LOG
# ----------------------------------------------------------------

class ConsultationLog:
    # records every Q&A exchange during the session

    def __init__(self):
        self._entries:      list[QAEntry] = []
        self._asked_set:    set[str]      = set()  # O(1) duplicate check
        self._intake_count: int           = 0      # entries from free-text intake, not system questions

    def log(self, symptom: str, question_text: str,
            answer: bool, candidates_remaining: int = 0,
            from_intake: bool = False) -> QAEntry:
        entry = QAEntry(
            symptom              = symptom,
            question_text        = question_text,
            answer               = answer,
            candidates_remaining = candidates_remaining
        )
        self._entries.append(entry)
        self._asked_set.add(symptom)
        if from_intake:
            self._intake_count += 1
        return entry

    def already_asked(self, symptom: str) -> bool:
        return symptom in self._asked_set

    @property
    def entries(self) -> list[QAEntry]:
        return list(self._entries)

    @property
    def question_count(self) -> int:
        return len(self._entries)

    @property
    def asked_question_count(self) -> int:
        # excludes intake entries so the displayed question number stays accurate
        return len(self._entries) - self._intake_count

    @property
    def yes_count(self) -> int:
        return sum(1 for e in self._entries if e.answer)

    @property
    def no_count(self) -> int:
        return sum(1 for e in self._entries if not e.answer)

    def get_confirmed_symptoms(self) -> list[str]:
        return [e.symptom for e in self._entries if e.answer]

    def get_denied_symptoms(self) -> list[str]:
        return [e.symptom for e in self._entries if not e.answer]

    def to_dict(self) -> dict:
        return {
            "total_questions": self.question_count,
            "yes_answers":     self.yes_count,
            "no_answers":      self.no_count,
            "exchanges":       [e.to_dict() for e in self._entries]
        }

    def __repr__(self) -> str:
        return (f"ConsultationLog("
                f"questions={self.question_count}, "
                f"yes={self.yes_count}, no={self.no_count})")


# ----------------------------------------------------------------
# USER SESSION
# ----------------------------------------------------------------

class UserSession:
    # root object for a single patient consultation

    def __init__(self, patient_name: str, patient_age: Optional[int] = None):
        self.session_id:   str           = str(uuid.uuid4())[:8]
        self.patient_name: str           = patient_name
        self.patient_age:  Optional[int] = patient_age
        self.state:        SessionState  = SessionState.PENDING

        self.record: MedicalRecord   = MedicalRecord(patient_name)
        self.log:    ConsultationLog = ConsultationLog()

        self.result: Optional[DiagnosisResult] = None  # set once diagnosis is reached

        self._created_at:  datetime           = datetime.now()
        self._started_at:  Optional[datetime] = None
        self._finished_at: Optional[datetime] = None

    # ---- lifecycle ----

    def start(self) -> None:
        if self.state != SessionState.PENDING:
            raise RuntimeError(f"Cannot start session in state {self.state}")
        self.state = SessionState.ACTIVE
        self._started_at = datetime.now()

    def complete(self, result: DiagnosisResult) -> None:
        self.result = result
        self.state  = SessionState.COMPLETE
        self._finished_at = datetime.now()

    def end_incomplete(self) -> None:
        self.state = SessionState.INCOMPLETE
        self._finished_at = datetime.now()

    # ---- convenience ----

    def record_answer(self, symptom: str, question_text: str,
                      answer: bool, candidates_remaining: int = 0,
                      from_intake: bool = False) -> None:
        if answer:
            self.record.record_yes(symptom)
        else:
            self.record.record_no(symptom)
        self.log.log(symptom, question_text, answer, candidates_remaining,
                     from_intake=from_intake)

    @property
    def is_active(self) -> bool:
        return self.state == SessionState.ACTIVE

    @property
    def duration_seconds(self) -> Optional[float]:
        if self._started_at and self._finished_at:
            return (self._finished_at - self._started_at).total_seconds()
        return None

    # ---- export ----

    def to_dict(self) -> dict:
        return {
            "session_id":       self.session_id,
            "patient_name":     self.patient_name,
            "patient_age":      self.patient_age,
            "state":            self.state.name,
            "created_at":       self._created_at.isoformat(),
            "started_at":       self._started_at.isoformat() if self._started_at else None,
            "finished_at":      self._finished_at.isoformat() if self._finished_at else None,
            "medical_record":   self.record.to_dict(),
            "consultation_log": self.log.to_dict(),
            "diagnosis":        self.result.to_dict() if self.result else None
        }

    def export_json(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def summary(self) -> str:
        lines = [
            f"Session {self.session_id} — {self.patient_name}",
            f"State    : {self.state.name}",
            f"Questions: {self.log.question_count}",
            f"Confirmed: {self.record.confirmed_symptoms}",
        ]
        if self.result:
            lines.append(
                f"Diagnosis: {self.result.disease} "
                f"({self.result.confidence:.1f}% — "
                f"{self.result.confidence_level.value})"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (f"UserSession(id={self.session_id}, "
                f"patient='{self.patient_name}', "
                f"state={self.state.name})")