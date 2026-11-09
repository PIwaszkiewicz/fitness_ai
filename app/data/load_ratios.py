"""Przeliczniki ciężaru: z 1RM pięciu ćwiczeń z kwestionariusza na ćwiczenia z atlasu.

Dla każdego ćwiczenia z obciążeniem zapisano ćwiczenie odniesienia (lift) i przelicznik:
szacowany 1RM ćwiczenia = przelicznik · 1RM ćwiczenia odniesienia. Przy hantlach i kettlebell
przelicznik dotyczy jednego przyrządu, a `implements` mówi, ile przyrządów się trzyma.
Przykład: wyciskanie hantli leżąc ≈ 0,41 · 1RM wyciskania sztangi na każdy z 2 hantli.

Przeliczniki odmian wyciskania leżąc pochodzą z badań (Saeterbakken i in. 2011 i 2017),
pozostałe są przybliżeniem opartym na typowych proporcjach obciążeń (np. przysiad przedni
≈ 80% przysiadu klasycznego); źródła i założenia: docs/ZRODLA.md, B21.
Dlatego plan podaje ciężar jako wskazówkę, którą użytkownik sprawdza w pierwszej serii.

None oznacza ćwiczenie na przyrządzie, w którym obciążeniem jest masa ciała (np. pompki na
poręczach, ławka rzymska), więc ciężaru w kilogramach się nie podaje. Ćwiczeń z gumą i cardio
nie ma w tabeli: opór gumy i tempa nie da się wyrazić w kilogramach.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadRatio:
    """Ćwiczenie odniesienia, przelicznik 1RM i liczba trzymanych przyrządów."""

    lift: str  # nazwa z LIFTS w app/services/strength.py
    ratio: float
    implements: int = 1


SQ, DL, BP, OHP, PU = "squat", "deadlift", "bench_press", "overhead_press", "pull_up"

LOAD_RATIOS: dict[str, LoadRatio | None] = {
    # Przysiady i wykroki: odniesieniem jest przysiad ze sztangą
    "Przysiad ze sztangą": LoadRatio(SQ, 1.0),
    "Przysiad przedni ze sztangą": LoadRatio(SQ, 0.8),
    "Półprzysiad w szerokim rozkroku ze sztangą": LoadRatio(SQ, 1.0),
    "Półprzysiad z hantlami": LoadRatio(SQ, 0.25, implements=2),
    "Thruster z hantlami": LoadRatio(OHP, 0.4, implements=2),  # ogranicza wyciskanie nad głowę
    "Przysiad goblet z kettlebell": LoadRatio(SQ, 0.3),
    "Przysiad sumo z kettlebell": LoadRatio(SQ, 0.3),
    "Wypychanie nóg na suwnicy": LoadRatio(SQ, 1.5),
    "Przysiad na maszynie hack": LoadRatio(SQ, 0.9),
    "Przysiad bułgarski z hantlami": LoadRatio(SQ, 0.2, implements=2),
    "Wykroki z hantlami": LoadRatio(SQ, 0.2, implements=2),
    "Wejścia na skrzynię z hantlami": LoadRatio(SQ, 0.2, implements=2),
    # Ruchy biodrem (zawias): odniesieniem jest martwy ciąg
    "Martwy ciąg klasyczny": LoadRatio(DL, 1.0),
    "Martwy ciąg sumo": LoadRatio(DL, 1.0),
    "Martwy ciąg na prostych nogach ze sztangą": LoadRatio(DL, 0.7),
    "Hip thrust ze sztangą": LoadRatio(DL, 1.0),
    "Skłon w przód ze sztangą na karku": LoadRatio(DL, 0.4),
    "Martwy ciąg rumuński z hantlami": LoadRatio(DL, 0.3, implements=2),
    "Martwy ciąg na jednej nodze z hantlem": LoadRatio(DL, 0.15),
    "Swing z kettlebell": LoadRatio(DL, 0.25),
    "Rwanie kettlebell": LoadRatio(DL, 0.15),
    "Wyprosty tułowia na ławce rzymskiej": None,
    "Wyprosty tułowia na maszynie": LoadRatio(DL, 0.3),
    # Wyciskanie poziome: odniesieniem jest wyciskanie sztangi leżąc.
    # Skos ±25° i wąski chwyt: 6RM w Saeterbakken i in. 2017 (skos −21,5%, w dół −2,5%,
    # wąski chwyt −11,1%). Hantle: 1RM o 17% niższy niż ze sztangą, czyli 0,83 na parę
    # (Saeterbakken i in. 2011), a na ławce skośnej dodatkowo · 0,82.
    "Wyciskanie sztangi na ławce płaskiej": LoadRatio(BP, 1.0),
    "Wyciskanie sztangi na ławce skośnej głową do góry": LoadRatio(BP, 0.82),
    "Wyciskanie sztangi na ławce skośnej głową w dół": LoadRatio(BP, 0.98),
    "Wyciskanie sztangi wąskim chwytem leżąc": LoadRatio(BP, 0.9),
    "Wyciskanie hantli leżąc na ławce płaskiej": LoadRatio(BP, 0.41, implements=2),
    "Wyciskanie hantli na ławce skośnej": LoadRatio(BP, 0.34, implements=2),
    "Naprzemienne wyciskanie hantli leżąc z łokciami przy tułowiu": LoadRatio(BP, 0.3, implements=2),
    # Wiosłowanie: odniesieniem jest wyciskanie leżąc (wiosłowanie ≈ 75% wyciskania)
    "Wiosłowanie sztangą w opadzie": LoadRatio(BP, 0.75),
    "Wiosłowanie końcem sztangi w opadzie tułowia": LoadRatio(BP, 0.75),
    "Wiosłowanie hantlem jednorącz": LoadRatio(BP, 0.35),
    "Wiosłowanie kettlebell w opadzie": LoadRatio(BP, 0.3),
    "Wiosłowanie na maszynie": LoadRatio(BP, 0.8),
    "Wiosłowanie sztangą T z podpórką brzuszną": LoadRatio(BP, 0.75),
    # Wyciskanie pionowe: odniesieniem jest wyciskanie sztangi nad głowę
    "Wyciskanie sztangi nad głowę": LoadRatio(OHP, 1.0),
    "Wyciskanie sztangi zza karku": LoadRatio(OHP, 0.85),
    "Wyciskanie hantli nad głowę": LoadRatio(OHP, 0.37, implements=2),
    "Wyciskanie hantli z rotacją nadgarstków": LoadRatio(OHP, 0.33, implements=2),
    "Pompki na poręczach": None,
    "Podciąganie sztangi wzdłuż tułowia szerokim chwytem": LoadRatio(OHP, 0.6),
    "Podciąganie sztangi wzdłuż tułowia wąskim chwytem": LoadRatio(OHP, 0.6),
    # Ciągnięcie pionowe: odniesieniem jest podciąganie (1RM z masą ciała)
    "Podciąganie na drążku": LoadRatio(PU, 1.0),
    "Podciąganie na drążku podchwytem": LoadRatio(PU, 1.0),
    "Podciąganie z asystą gumy": None,
    "Ściąganie drążka wyciągu górnego": LoadRatio(PU, 0.75),
    "Ściąganie drążka wyciągu górnego za kark": LoadRatio(PU, 0.65),
    "Ściąganie wyciągu górnego wąskim uchwytem do klatki": LoadRatio(PU, 0.75),
    "Ściąganie drążka wyciągu górnego prostymi ramionami": LoadRatio(PU, 0.3),
    # Izolowane: ramiona (odniesienie: wyciskanie leżąc)
    "Uginanie ramion ze sztangą": LoadRatio(BP, 0.35),
    "Uginanie przedramion ze sztangą na modlitewniku": LoadRatio(BP, 0.3),
    "Uginanie przedramion ze sztangą nachwytem": LoadRatio(BP, 0.28),
    "Prostowanie nadgarstków ze sztangą nachwytem": LoadRatio(BP, 0.2),
    "Zginanie nadgarstków ze sztangą podchwytem": LoadRatio(BP, 0.25),
    "Wyciskanie francuskie sztangi leżąc": LoadRatio(BP, 0.35),
    "Wyciskanie francuskie sztangą łamaną siedząc": LoadRatio(BP, 0.3),
    "Uginanie ramion z hantlami": LoadRatio(BP, 0.14, implements=2),
    "Uginanie przedramion z hantlami chwytem młotkowym": LoadRatio(BP, 0.15, implements=2),
    "Uginanie przedramienia z hantlem z łokciem opartym na udzie": LoadRatio(BP, 0.13),
    "Wyciskanie francuskie z hantlem": LoadRatio(BP, 0.25),
    "Prostowanie ramion z hantlami leżąc": LoadRatio(BP, 0.12, implements=2),
    "Prostowanie ramienia z hantlem w opadzie tułowia": LoadRatio(BP, 0.1),
    "Prostowanie ramion na wyciągu": LoadRatio(BP, 0.3),
    "Prostowanie ramion na wyciągu górnym podchwytem": LoadRatio(BP, 0.25),
    "Naprzemienne uginanie przedramion na wyciągu dolnym": LoadRatio(BP, 0.12),
    "Uginanie ramion na wyciągu górnym": LoadRatio(BP, 0.15),
    "Uginanie przedramion na modlitewniku (maszyna)": LoadRatio(BP, 0.3),
    # Izolowane: plecy i klatka
    "Szrugsy ze sztangą": LoadRatio(DL, 0.6),
    "Szrugsy z hantlami": LoadRatio(DL, 0.25, implements=2),
    "Szrugsy na maszynie": LoadRatio(DL, 0.6),
    "Przenoszenie sztangi leżąc na ławce płaskiej": LoadRatio(BP, 0.3),
    "Rozpiętki z hantlami": LoadRatio(BP, 0.12, implements=2),
    "Rozpiętki z hantlami na ławce skośnej głową do góry": LoadRatio(BP, 0.1, implements=2),
    "Przenoszenie hantla leżąc": LoadRatio(BP, 0.25),
    "Rozpiętki na maszynie": LoadRatio(BP, 0.4),
    "Rozpiętki na wyciągu stojąc": LoadRatio(BP, 0.1, implements=2),
    # Izolowane: pośladki i nogi (odniesienie: przysiad lub martwy ciąg)
    "Prostowanie biodra na wyciągu dolnym": LoadRatio(DL, 0.1),
    "Prostowanie biodra na maszynie": LoadRatio(DL, 0.25),
    "Odwodzenie biodra stojąc na wyciągu dolnym": LoadRatio(DL, 0.08),
    "Odwodzenie biodra stojąc na maszynie": LoadRatio(DL, 0.2),
    "Odwodzenie nóg siedząc na maszynie": LoadRatio(SQ, 0.4),
    "Wyprosty nóg na maszynie": LoadRatio(SQ, 0.4),
    "Uginanie nóg na maszynie": LoadRatio(SQ, 0.3),
    "Uginanie nogi stojąc na maszynie": LoadRatio(SQ, 0.15),
    "Przywodzenie nogi na wyciągu dolnym": LoadRatio(SQ, 0.1),
    "Przywodzenie nóg na maszynie": LoadRatio(SQ, 0.4),
    "Wspięcia na palce stojąc na maszynie": LoadRatio(SQ, 0.8),
    "Wspięcia na palce w skłonie tułowia": LoadRatio(SQ, 0.8),
    "Wspięcia na palce siedząc na maszynie": LoadRatio(SQ, 0.4),
    "Wspięcia na palce siedząc ze sztangą na kolanach": LoadRatio(SQ, 0.4),
    "Wspięcia na palce jednonóż z hantlem": LoadRatio(SQ, 0.15),
    # Izolowane: barki (odniesienie: wyciskanie nad głowę)
    "Unoszenie sztangi w przód nachwytem": LoadRatio(OHP, 0.35),
    "Unoszenie hantli bokiem": LoadRatio(OHP, 0.12, implements=2),
    "Unoszenie hantli w przód": LoadRatio(OHP, 0.15, implements=2),
    "Unoszenie hantli bokiem w opadzie tułowia": LoadRatio(OHP, 0.1, implements=2),
    "Unoszenie ramienia z hantlem w leżeniu bokiem": LoadRatio(OHP, 0.08),
    "Naprzemienne unoszenie ramienia bokiem na wyciągu dolnym": LoadRatio(OHP, 0.1),
    "Naprzemienne unoszenie ramienia w przód na wyciągu dolnym": LoadRatio(OHP, 0.12),
    "Odwodzenie ramion na wyciągu na tylną część barków": LoadRatio(OHP, 0.1, implements=2),
    "Unoszenie ramion bokiem na wyciągu dolnym w opadzie tułowia": LoadRatio(OHP, 0.1, implements=2),
    "Unoszenie ramion bokiem na maszynie": LoadRatio(OHP, 0.3),
    "Odwodzenie ramion na maszynie na tylną część barków": LoadRatio(OHP, 0.3),
    # Brzuch: na ławkach i drążku obciążeniem jest masa ciała
    "Skłony boczne z hantlem": LoadRatio(DL, 0.25),
    "Brzuszki na wyciągu górnym": LoadRatio(DL, 0.25),
    "Brzuszki na maszynie": LoadRatio(DL, 0.25),
    "Skręty tułowia na maszynie": LoadRatio(DL, 0.2),
    "Unoszenie tułowia na skośnej ławce": None,
    "Unoszenie tułowia w zwisie na ławce": None,
    "Unoszenie nóg na skośnej ławce": None,
    "Unoszenie kolan na poręczach": None,
    "Zginanie tułowia w bok na ławce": None,
    "Unoszenie nóg w zwisie": None,
}
