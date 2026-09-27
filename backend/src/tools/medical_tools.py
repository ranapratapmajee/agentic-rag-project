from langchain.tools import tool

@tool
def update_prescription(patient_id: str, medication: str, dosage: str) -> str:
    """Update or prescribe medication and dosage for a patient. High-risk operation."""
    return f"Successfully updated prescription for patient {patient_id}: {medication} at {dosage}."