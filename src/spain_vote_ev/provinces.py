"""The 52 constituencies of the Congreso: INE code, a short name, the autonomous community,
and every spelling the BOE and the INE use for them."""

from __future__ import annotations

import re
import unicodedata

# (INE code, short name, autonomous community, aliases). Codes are the INE province codes;
# 51 and 52 are Ceuta and Melilla. The order is the BOE's (alphabetical, Ceuta and Melilla last).
PROVINCES: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("02", "Albacete", "CLM", ("Albacete",)),
    ("03", "Alicante", "VAL", ("Alicante/Alacant", "Alicante / Alacant", "Alicante")),
    ("04", "Almería", "AND", ("Almería",)),
    ("01", "Álava", "PVA", ("Araba/Álava", "Araba / Álava", "Álava")),
    ("33", "Asturias", "AST", ("Asturias",)),
    ("05", "Ávila", "CYL", ("Ávila",)),
    ("06", "Badajoz", "EXT", ("Badajoz",)),
    ("07", "Baleares", "BAL", ("Balears (Illes)", "Balears, Illes", "Illes Balears", "Baleares")),
    ("08", "Barcelona", "CAT", ("Barcelona",)),
    ("48", "Bizkaia", "PVA", ("Bizkaia", "Vizcaya")),
    ("09", "Burgos", "CYL", ("Burgos",)),
    ("10", "Cáceres", "EXT", ("Cáceres",)),
    ("11", "Cádiz", "AND", ("Cádiz",)),
    ("39", "Cantabria", "CAN", ("Cantabria",)),
    ("12", "Castellón", "VAL", ("Castellón/Castelló", "Castellón / Castelló", "Castellón")),
    ("13", "Ciudad Real", "CLM", ("Ciudad Real",)),
    ("14", "Córdoba", "AND", ("Córdoba",)),
    ("15", "A Coruña", "GAL", ("Coruña (A)", "Coruña, A", "A Coruña")),
    ("16", "Cuenca", "CLM", ("Cuenca",)),
    ("20", "Gipuzkoa", "PVA", ("Gipuzkoa", "Guipúzcoa")),
    ("17", "Girona", "CAT", ("Girona",)),
    ("18", "Granada", "AND", ("Granada",)),
    ("19", "Guadalajara", "CLM", ("Guadalajara",)),
    ("21", "Huelva", "AND", ("Huelva",)),
    ("22", "Huesca", "ARA", ("Huesca",)),
    ("23", "Jaén", "AND", ("Jaén",)),
    ("24", "León", "CYL", ("León",)),
    ("25", "Lleida", "CAT", ("Lleida",)),
    ("27", "Lugo", "GAL", ("Lugo",)),
    ("28", "Madrid", "MAD", ("Madrid",)),
    ("29", "Málaga", "AND", ("Málaga",)),
    ("30", "Murcia", "MUR", ("Murcia",)),
    ("31", "Navarra", "NAV", ("Navarra",)),
    ("32", "Ourense", "GAL", ("Ourense",)),
    ("34", "Palencia", "CYL", ("Palencia",)),
    ("35", "Las Palmas", "CNR", ("Palmas (Las)", "Palmas, Las", "Las Palmas")),
    ("36", "Pontevedra", "GAL", ("Pontevedra",)),
    ("26", "La Rioja", "RIO", ("Rioja (La)", "Rioja, La", "La Rioja")),
    ("37", "Salamanca", "CYL", ("Salamanca",)),
    ("38", "S. C. Tenerife", "CNR", ("Santa Cruz de Tenerife", "S/C Tenerife",
                                      "S.C. Tenerife")),
    ("40", "Segovia", "CYL", ("Segovia",)),
    ("41", "Sevilla", "AND", ("Sevilla",)),
    ("42", "Soria", "CYL", ("Soria",)),
    ("43", "Tarragona", "CAT", ("Tarragona",)),
    ("44", "Teruel", "ARA", ("Teruel",)),
    ("45", "Toledo", "CLM", ("Toledo",)),
    ("46", "Valencia", "VAL", ("Valencia/València", "Valencia / València", "Valencia")),
    ("47", "Valladolid", "CYL", ("Valladolid",)),
    ("49", "Zamora", "CYL", ("Zamora",)),
    ("50", "Zaragoza", "ARA", ("Zaragoza",)),
    ("51", "Ceuta", "CEU", ("Ceuta",)),
    ("52", "Melilla", "MEL", ("Melilla",)),
]

CODES = [p[0] for p in PROVINCES]
NAME = {p[0]: p[1] for p in PROVINCES}
CCAA = {p[0]: p[2] for p in PROVINCES}
SINGLE_SEAT = ("51", "52")  # Ceuta and Melilla: one seat each, by plurality


def norm(text: str) -> str:
    """Lower case, no accents, letters only: 'Alicante/\\nAlacant.' -> 'alicantealacant'."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", text.lower())


_ALIASES = {norm(a): code for code, _, _, aliases in PROVINCES for a in aliases}


def code_of(name: str) -> str | None:
    """INE code of a constituency name as the BOE or the INE spell it; None if not one."""
    return _ALIASES.get(norm(name))
