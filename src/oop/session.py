# ================================================================
# session.py
# Medical Expert System — BCS 222 Programming Paradigms
# Role: OOP state management layer.
#       Defines UserSession, MedicalRecord, and ConsultationLog.
#       These classes handle ALL persistence of conversation state
#       so Prolog stays stateless between Python calls.
#
# Paradigm justification:
#   OOP is ideal here because we need mutable, identity-tracked
#   objects that persist across many method calls. A patient
#   session has identity (who is this patient?), state (what
#   symptoms have been confirmed?), and behaviour (log a Q&A,
#   export a report). These are exactly the things classes model.
# ================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional
import uuid
import json


# ----------------------------------------------------------------
# ENUMS — session and diagnosis states
# ----------------------------------------------------------------

class SessionState(Enum):
    """Lifecycle states of a consultation session."""
    PENDING    = auto()   # created, not yet started
    ACTIVE     = auto()   # questions being asked
    COMPLETE   = auto()   # diagnosis reached
    INCOMPLETE = auto()   # ended without diagnosis


class ConfidenceLevel(Enum):
    """Human-readable confidence tier derived from numeric %."""
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
# DATACLASSES — lightweight immutable records
# ----------------------------------------------------------------

@dataclass
class QAEntry:
    """
    A single question-answer exchange in the consultation.
    Immutable record — once logged it is never modified.
    """
    symptom:       str            # Prolog atom e.g. 'fever'
    question_text: str            # Human-readable question shown to patient
    answer:        bool           # True = yes, False = no
    timestamp:     datetime = field(default_factory=datetime.now)
    candidates_remaining: int = 0  # how many diseases were still possible

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
    """
    Final output of a consultation.
    Produced by the inference engine, stored in MedicalRecord.
    """
    disease:      str
    confidence:   float
    description:  str
    tests:        list[dict]      # [{"test": ..., "confirms": ...}]
    timestamp:    datetime = field(default_factory=datetime.now)
    is_conclusive: bool = True

    @property
    def confidence_level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_pct(self.confidence)

    def to_dict(self) -> dict:
        return {
            "disease":       self.disease,
            "confidence":    round(self.confidence, 1),
            "confidence_level": self.confidence_level.value,
            "description":   self.description,
            "tests":         self.tests,
            "is_conclusive": self.is_conclusive,
            "timestamp":     self.timestamp.isoformat()
        }


# ----------------------------------------------------------------
# MEDICAL RECORD — patient symptom tracking
# ----------------------------------------------------------------

class MedicalRecord:
    """
    Tracks the patient's confirmed and denied symptoms.
    Acts as the source of truth for what the patient has reported.

    Separated from ConsultationLog deliberately — symptom data
    is clinical information, Q&A history is conversational data.
    They have different lifetimes and export formats.
    """

    def __init__(self, patient_name: str):
        self._patient_name   = patient_name
        self._confirmed:  list[str] = []
        self._denied:     list[str] = []
        self._created_at  = datetime.now()

    # ---- properties ----

    @property
    def patient_name(self) -> str:
        return self._patient_name

    @property
    def confirmed_symptoms(self) -> list[str]:
        """Symptoms the patient said YES to."""
        return list(self._confirmed)

    @property
    def denied_symptoms(self) -> list[str]:
        """Symptoms the patient said NO to."""
        return list(self._denied)

    @property
    def all_reported(self) -> list[str]:
        """Every symptom that has been asked about."""
        return self._confirmed + self._denied

    # ---- mutation ----

    def record_yes(self, symptom: str) -> None:
        """Patient confirmed this symptom."""
        if symptom not in self._confirmed:
            self._confirmed.append(symptom)

    def record_no(self, symptom: str) -> None:
        """Patient denied this symptom."""
        if symptom not in self._denied:
            self._denied.append(symptom)

    def has_symptom(self, symptom: str) -> bool:
        return symptom in self._confirmed

    def was_asked(self, symptom: str) -> bool:
        return symptom in self.all_reported

    # ---- export ----

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
# CONSULTATION LOG — full conversation history
# ----------------------------------------------------------------

class ConsultationLog:
    """
    Records every Q&A exchange in the consultation.
    Ensures the chatbot never asks the same question twice
    by tracking which symptoms have already been addressed.

    This is the primary object the interface layer queries
    when building the chat display.
    """

    def __init__(self):
        self._entries:   list[QAEntry] = []
        self._asked_set: set[str]      = set()  # O(1) duplicate check
        self._intake_count: int        = 0      # entries from free-text intake

    # ---- logging ----

    def log(self, symptom: str, question_text: str,
            answer: bool, candidates_remaining: int = 0,
            from_intake: bool = False) -> QAEntry:
        """
        Record a single Q&A exchange.
        from_intake=True marks this as a preloaded symptom from the
        free-text phase — it is stored for the full record but is NOT
        counted as a question asked by the system.
        Returns the created QAEntry for immediate use.
        """
        entry = QAEntry(
            symptom               = symptom,
            question_text         = question_text,
            answer                = answer,
            candidates_remaining  = candidates_remaining
        )
        self._entries.append(entry)
        self._asked_set.add(symptom)
        if from_intake:
            self._intake_count += 1
        return entry

    # ---- queries ----

    def already_asked(self, symptom: str) -> bool:
        """O(1) check — has this symptom already been asked?"""
        return symptom in self._asked_set

    @property
    def entries(self) -> list[QAEntry]:
        return list(self._entries)

    @property
    def question_count(self) -> int:
        """Total entries including free-text intake."""
        return len(self._entries)

    @property
    def asked_question_count(self) -> int:
        """Only questions actually asked by the system (excludes intake)."""
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

    # ---- export ----

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
# USER SESSION — the top-level session object
# ----------------------------------------------------------------

class UserSession:
    """
    Root object for a single patient consultation.
    Owns the MedicalRecord and ConsultationLog.
    Tracks lifecycle state and timing.

    The Python interface layer creates one UserSession per
    consultation and passes it to the Consultation controller.
    The Prolog bridge is also held here so the controller
    can call reset_session() cleanly on a new consultation.

    This class is the direct answer to the assignment's
    requirement: 'OOP handles the persistence of the
    conversation' — this is that persistence layer.
    """

    def __init__(self, patient_name: str, patient_age: Optional[int] = None):
        self.session_id:   str            = str(uuid.uuid4())[:8]
        self.patient_name: str            = patient_name
        self.patient_age:  Optional[int]  = patient_age
        self.state:        SessionState   = SessionState.PENDING

        # Sub-objects
        self.record:  MedicalRecord  = MedicalRecord(patient_name)
        self.log:     ConsultationLog = ConsultationLog()

        # Diagnosis result — None until consultation completes
        self.result: Optional[DiagnosisResult] = None

        # Timing
        self._created_at:  datetime           = datetime.now()
        self._started_at:  Optional[datetime] = None
        self._finished_at: Optional[datetime] = None

    # ---- lifecycle ----

    def start(self) -> None:
        """Mark session as active and record start time."""
        if self.state != SessionState.PENDING:
            raise RuntimeError(
                f"Cannot start session in state {self.state}"
            )
        self.state = SessionState.ACTIVE
        self._started_at = datetime.now()

    def complete(self, result: DiagnosisResult) -> None:
        """Mark session complete with a diagnosis result."""
        self.result = result
        self.state  = SessionState.COMPLETE
        self._finished_at = datetime.now()

    def end_incomplete(self) -> None:
        """Mark session ended without a clear diagnosis."""
        self.state = SessionState.INCOMPLETE
        self._finished_at = datetime.now()

    # ---- convenience methods ----

    def record_answer(self, symptom: str, question_text: str,
                      answer: bool, candidates_remaining: int = 0,
                      from_intake: bool = False) -> None:
        """
        Single call to update both MedicalRecord and ConsultationLog.
        from_intake=True means this symptom came from the free-text
        description phase — it is recorded in MedicalRecord (so
        confirmed/denied lists are complete) but is NOT counted as
        a question asked by the system in asked_question_count.
        """
        # Update medical record
        if answer:
            self.record.record_yes(symptom)
        else:
            self.record.record_no(symptom)

        # Update conversation log
        self.log.log(symptom, question_text, answer, candidates_remaining,
                     from_intake=from_intake)

    @property
    def is_active(self) -> bool:
        return self.state == SessionState.ACTIVE

    @property
    def duration_seconds(self) -> Optional[float]:
        """How long the consultation took in seconds."""
        if self._started_at and self._finished_at:
            return (self._finished_at - self._started_at).total_seconds()
        return None

    # ---- export / reporting ----

    def to_dict(self) -> dict:
        """Full session export — used for the report and saving logs."""
        return {
            "session_id":   self.session_id,
            "patient_name": self.patient_name,
            "patient_age":  self.patient_age,
            "state":        self.state.name,
            "created_at":   self._created_at.isoformat(),
            "started_at":   self._started_at.isoformat() if self._started_at else None,
            "finished_at":  self._finished_at.isoformat() if self._finished_at else None,
            "medical_record": self.record.to_dict(),
            "consultation_log": self.log.to_dict(),
            "diagnosis":    self.result.to_dict() if self.result else None
        }

    def export_json(self, filepath: str) -> None:
        """Save full session to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def summary(self) -> str:
        """Short human-readable summary for terminal display."""
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