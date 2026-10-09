"""Definicja pytań kwestionariusza.

Pytania są danymi, a nie kodem formularza: frontend pobiera tę listę przez
GET /api/v1/questionnaire i sam buduje formularz. Zmiana pytania nie wymaga zmian we frontendzie.
Zakresy min/max muszą być zgodne ze schematem UserProfileCreate (pilnuje tego test).
"""

from enum import StrEnum

from app.models.enums import (
    CARDIOVASCULAR_LIMITATIONS,
    ActivityLevel,
    Equipment,
    Gender,
    Limitation,
    TrainingExperience,
    TrainingGoal,
)
from app.schemas.questionnaire import Option, Question, ShowIf

# Polskie etykiety wartości słownikowych wyświetlane użytkownikowi.
LABELS = {
    Gender.MALE: "Mężczyzna",
    Gender.FEMALE: "Kobieta",
    TrainingGoal.WEIGHT_LOSS: "Redukcja masy ciała",
    TrainingGoal.MUSCLE_GAIN: "Budowa masy mięśniowej",
    TrainingGoal.STRENGTH: "Zwiększenie siły",
    TrainingGoal.ENDURANCE: "Poprawa wytrzymałości",
    TrainingGoal.GENERAL_FITNESS: "Ogólna sprawność",
    ActivityLevel.SEDENTARY: "Siedzący tryb życia, brak ćwiczeń",
    ActivityLevel.LIGHT: "Niska: ruch 1–2 razy w tygodniu",
    ActivityLevel.MODERATE: "Umiarkowana: ruch 3–4 razy w tygodniu",
    ActivityLevel.ACTIVE: "Wysoka: ruch 5–6 razy w tygodniu",
    ActivityLevel.VERY_ACTIVE: "Bardzo wysoka: codziennie lub praca fizyczna",
    TrainingExperience.NONE: "Nie trenuję regularnie",
    TrainingExperience.LESS_THAN_1_YEAR: "Poniżej roku",
    TrainingExperience.FROM_1_TO_3_YEARS: "Od roku do 3 lat",
    TrainingExperience.MORE_THAN_3_YEARS: "Ponad 3 lata",
    Limitation.KNEE: "Kolano",
    Limitation.HIP: "Biodro",
    Limitation.ANKLE: "Staw skokowy",
    Limitation.LOWER_BACK: "Odcinek lędźwiowy kręgosłupa",
    Limitation.SHOULDER: "Bark",
    Limitation.ELBOW: "Łokieć",
    Limitation.WRIST: "Nadgarstek",
    Limitation.NECK: "Odcinek szyjny kręgosłupa",
    Limitation.HYPERTENSION: "Nadciśnienie tętnicze",
    Limitation.HEART_CONDITION: "Choroba serca",
    Equipment.NONE: "Brak sprzętu (ćwiczenia z masą ciała)",
    Equipment.DUMBBELLS: "Hantle",
    Equipment.BARBELL: "Sztanga",
    Equipment.KETTLEBELL: "Kettlebell",
    Equipment.RESISTANCE_BAND: "Guma oporowa",
    Equipment.PULL_UP_BAR: "Drążek do podciągania",
    Equipment.MACHINE: "Maszyny na siłowni",
}


def options_for(enum_class: type[StrEnum]) -> list[Option]:
    """Zamienia enum na listę odpowiedzi do wyboru z polskimi etykietami."""
    return [Option(value=item.value, label=LABELS[item]) for item in enum_class]


BASIC = "Dane podstawowe"
HEALTH = "Zdrowie i ograniczenia"
TESTS = "Testy sprawności"
PREFERENCES = "Preferencje treningowe"

QUESTIONS = [
    # Dane podstawowe
    Question(id="age", section=BASIC, text="Ile masz lat?", type="integer", required=True,
             unit="lat", min=16, max=100),
    Question(id="gender", section=BASIC, text="Płeć", type="choice", required=True,
             options=options_for(Gender)),
    Question(id="height_cm", section=BASIC, text="Wzrost", type="number", required=True,
             unit="cm", min=120, max=230),
    Question(id="weight_kg", section=BASIC, text="Masa ciała", type="number", required=True,
             unit="kg", min=30, max=300),
    Question(id="training_goal", section=BASIC, text="Jaki jest Twój główny cel treningowy?",
             type="choice", required=True, options=options_for(TrainingGoal)),
    Question(id="activity_level", section=BASIC, text="Jak aktywny jesteś na co dzień?",
             type="choice", required=True, options=options_for(ActivityLevel)),
    Question(id="training_experience", section=BASIC, text="Jak długo regularnie trenujesz?",
             type="choice", required=False, options=options_for(TrainingExperience)),
    # Zdrowie i ograniczenia
    Question(id="limitations", section=HEALTH,
             text="Czy masz kontuzje lub schorzenia, które ograniczają ruch?",
             type="multi_choice", required=False, options=options_for(Limitation),
             hint="Zostaw puste, jeśli żadne nie dotyczy."),
    Question(id="pain_level", section=HEALTH,
             text="Jak silny ból odczuwasz w zgłoszonych miejscach podczas ruchu?",
             type="integer", required=False, min=1, max=10,
             hint="1 – ledwo odczuwalny, 10 – najsilniejszy wyobrażalny.",
             show_if=ShowIf(field="limitations", any_of=[item.value for item in Limitation])),
    Question(id="medical_clearance", section=HEALTH,
             text="Czy lekarz wyraził zgodę na Twój wysiłek fizyczny?",
             type="boolean", required=False,
             show_if=ShowIf(field="limitations",
                            any_of=[item.value for item in CARDIOVASCULAR_LIMITATIONS])),
    # Testy sprawności
    Question(id="pushups", section=TESTS,
             text="Ile pompek wykonasz bez przerwy (z kolan, jeśli klasyczne są za trudne)?",
             type="integer", required=False, unit="powtórzeń", min=0, max=150),
    Question(id="squats", section=TESTS, text="Ile przysiadów wykonasz w ciągu 1 minuty?",
             type="integer", required=False, unit="powtórzeń", min=0, max=150),
    Question(id="plank_seconds", section=TESTS, text="Jak długo utrzymasz deskę (plank)?",
             type="integer", required=False, unit="s", min=0, max=600),
    Question(id="resting_heart_rate", section=TESTS,
             text="Jakie jest Twoje tętno spoczynkowe?", type="integer", required=False,
             unit="uderzeń/min", min=30, max=150,
             hint="Zmierz rano, przed wstaniem z łóżka, przez 60 sekund."),
    # Preferencje treningowe
    Question(id="training_days_per_week", section=PREFERENCES,
             text="Ile dni w tygodniu chcesz trenować?", type="integer", required=False,
             min=1, max=7),
    Question(id="session_minutes", section=PREFERENCES,
             text="Ile minut może trwać jeden trening?", type="integer", required=False,
             unit="min", min=15, max=180),
    Question(id="available_equipment", section=PREFERENCES,
             text="Do jakiego sprzętu masz dostęp?", type="multi_choice", required=False,
             options=options_for(Equipment)),
]
