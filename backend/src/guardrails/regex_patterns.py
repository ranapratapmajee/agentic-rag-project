from presidio_analyzer import Pattern, PatternRecognizer

mrn_pattern = Pattern(name="mrn_pattern", regex=r"\bMRN-\d{6,8}\b", score=1.0)
patient_id_pattern = Pattern(name="patient_id_pattern", regex=r"\bPID-\d{5}\b", score=1.0)

CUSTOM_RECOGNIZERS = [
    PatternRecognizer(supported_entity="MRN", patterns=[mrn_pattern]),
    PatternRecognizer(supported_entity="PATIENT_ID", patterns=[patient_id_pattern]),
]