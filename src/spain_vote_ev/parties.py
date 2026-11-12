"""Which party each list belongs to, how the 2026 lists follow from the 2023 ones, and the two
blocs that the 2023 investiture votes define.

Every list in the official results gets a short label (PP, PSOE, VOX, ...). The rules are
regular expressions on the list's name and abbreviation, tried in order; a list that matches
none is 'OTH'. Labels are bookkeeping, not judgements: a coalition is labelled by the party
that leads it, and regional partners of a national party share its label, as the polls do.
"""

from __future__ import annotations

import re
import unicodedata

# (label, pattern). Order matters: coalitions first, then the parties inside them.
RULES: list[tuple[str, str]] = [
    ("PP", r"UPN-PP|PARTIDO POPULAR|PARTIT POPULAR|^PP$|\bPP-PAR\b|\bPP-FORO\b"),
    ("UPN", r"UNION DEL PUEBLO NAVARRO"),
    ("NAS", r"NAVARRA SUMA"),
    ("PSOE", r"PSOE|\bPSC\b|SOCIALISTES DE CATALUNYA"),
    ("VOX", r"^VOX\b|\(VOX\)|\bVOX$"),
    ("CS", r"CIUDADANOS\s*-\s*PARTIDO DE LA CIUDADANIA|^C'S$|^CS$"),
    ("FA", r"UNIDAD DEL PUEBLO CANARIO|FRENTE AMPLI|FRONT AMPLI|FRONTE AMPLA|ARAMES"),
    ("FV", r"FRONT VALENCIA"),
    ("SUMAR", r"\bSUMAR\b"),
    ("MP", r"MAS PAIS|M\.\s*PAIS|MES COMPROMIS"),
    ("PODEMOS", r"PODEM|EN COMU|EN MAREA|UNIDAS PODEMOS|UNIDOS PODEMOS"),
    ("COMPROMIS", r"COMPROMIS\b"),
    ("IU", r"UNIDAD POPULAR"),
    ("ERC", r"ESQUERRA REPUBLICANA"),
    ("JUNTS", r"\bJUNTS\b|JXCAT|DEMOCRACIA I LLIBERTAT|CONVERGENCIA DEMOCRATICA"),
    ("PNV", r"EAJ-PNV|NACIONALISTA VASCO"),
    ("BILDU", r"BILDU"),
    ("BNG", r"\bBNG\b|B\.N\.G\.|BLOQUE NACIONALISTA GALEGO|NOS-CANDIDATURA GALEGA"),
    ("CC", r"COALICION CANARIA|\bCCA\b"),
    ("NC", r"NUEVA CANARIAS"),
    ("CUP", r"UNITAT POPULAR"),
    ("PRC", r"REGIONALISTA DE CANTABRIA"),
    ("TE", r"TERUEL EXISTE|COALICION EXISTE|^EXISTE$"),
    ("SY", r"SORIA .?YA"),
    ("SALF", r"SE ACABO LA FIESTA"),
    ("AA", r"ADELANTE ANDALUCIA"),
    ("PACMA", r"PACMA|ANIMALISTA"),
    ("UPYD", r"UNION PROGRESO Y DEMOCRACIA"),
]


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).upper().strip()


def label(name: str, abbr: str = "") -> str:
    """The label of a list from its name and abbreviation (see RULES)."""
    n, a = _norm(name), _norm(abbr)
    for lab, pattern in RULES:
        if re.search(pattern, n) or (a and re.search(pattern, a)):
            # The Podemos lists of 2015-2019 ran with IU and the regional confluences: the
            # polls call that family 'UP' (Unidos/Unidas Podemos); it is relabelled below.
            return lab
    return "OTH"


def label_for(election: str, name: str, abbr: str = "") -> str:
    lab = label(name, abbr)
    if lab == "PODEMOS" and election in ("2015", "2016", "2019A", "2019N"):
        return "UP"
    return lab


# --- the two blocs ---------------------------------------------------------------------------
# Defined only by the two investiture votes of the 2023 legislature, so that no party is placed
# by anyone's judgement. Coalición Canaria voted yes in both, so it is in both.
#   Feijóo, 27 Sep 2023: 172 yes = PP 137, Vox 33, UPN 1, CC 1 (Diario de Sesiones 15-PL-5).
#   Sánchez, 16 Nov 2023: 179 yes = PSOE 121, Sumar 31, ERC 7, Junts 7, EH Bildu 6, PNV 5,
#   BNG 1, CC 1 (Diario de Sesiones 15-PL-8).
# 2026 lists inherit the vote of the 2023 group they come from: PP's lists include UPN in
# Navarra; Frente Amplio (with Compromís-Front Valencià) and Podemos both sat in the Sumar group.
# Lists with no seat in 2023 (SALF, Adelante Andalucía, local lists) are in neither bloc.
BLOC_F = ("PP", "VOX", "CC")
BLOC_S = ("PSOE", "FA", "PODEMOS", "ERC", "JUNTS", "BILDU", "PNV", "BNG", "CC")
BLOC_S_NO_JUNTS = tuple(p for p in BLOC_S if p != "JUNTS")
MAJORITY = 176

INVESTITURES = {
    "feijoo": {
        "date": "2023-09-27", "candidate": "Alberto Núñez Feijóo", "yes": 172, "no": 178,
        "yes_by_party": {"PP": 137, "VOX": 33, "UPN": 1, "CC": 1},
        "source": "Diario de Sesiones del Congreso, XV legislatura, Pleno núm. 5",
        "url": "https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-5.PDF",
    },
    "sanchez": {
        "date": "2023-11-16", "candidate": "Pedro Sánchez", "yes": 179, "no": 171,
        "yes_by_party": {"PSOE": 121, "SUMAR": 31, "ERC": 7, "JUNTS": 7, "BILDU": 6,
                         "PNV": 5, "BNG": 1, "CC": 1},
        "source": "Diario de Sesiones del Congreso, XV legislatura, Pleno núm. 8",
        "url": "https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-8.PDF",
    },
}

# Seats in the Congreso elected in July 2023, by parliamentary label (official results).
SEATS_2023 = {"PP": 137, "PSOE": 121, "VOX": 33, "SUMAR": 31, "ERC": 7, "JUNTS": 7,
              "BILDU": 6, "PNV": 5, "BNG": 1, "CC": 1, "UPN": 1}

# Display names, neutral and short.
DISPLAY = {
    "PP": "PP", "PSOE": "PSOE", "VOX": "Vox", "FA": "Frente Amplio", "PODEMOS": "Podemos",
    "SALF": "SALF", "AA": "Adelante Andalucía", "ERC": "ERC", "JUNTS": "Junts",
    "BILDU": "EH Bildu", "PNV": "PNV", "BNG": "BNG", "CC": "CC", "TE": "Teruel Existe",
    "SY": "Soria ¡Ya!", "SUMAR": "Sumar", "UP": "Unidas Podemos", "CS": "Cs", "MP": "Más País",
    "CUP": "CUP", "PRC": "PRC", "UPN": "UPN", "OTH": "others", "BLANK": "blank",
}
