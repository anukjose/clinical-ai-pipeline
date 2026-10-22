
from typing import Any

from pydantic import BaseModel, ConfigDict


class Doctor(BaseModel):
    employeeId: int
    departmentName: str


class Patient(BaseModel):
    customerId: int
    customerDob: str
    gender: str


class StructuredPrescriptionData(BaseModel):
    label: str
    val1: str
    unit1: str
    val2: str
    unit2: str
    val3: str
    unit3: str
    val4: str
    unit4: str


class TextPrescriptionData(BaseModel):
    text: str


class PrescriptionSection(BaseModel):
    sectionId: int
    sectionName: str
    type: int
    typeLabel: str
    data: list[dict[str, Any]]


class MedicationRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    medicationId: int
    consultationDate: str
    medicationStatus: int
    doctor: Doctor
    patient: Patient
    nextReview: Any | None = None
    prescription: list[PrescriptionSection]