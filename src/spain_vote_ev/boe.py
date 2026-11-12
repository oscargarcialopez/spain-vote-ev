"""Parse the Junta Electoral Central's result publications in the BOE.

Each publication has three tables per election: Cuadro I (electors, voters, valid, candidate,
blank and null votes by constituency), Cuadro II (votes and seats of the lists that won a seat)
and Cuadro III (votes of the lists that did not). The BOE serves them as HTML tables inside its
XML, except where the HTML shows an image of the table; there the PDF's text layer is read
instead (Cuadro I in November 2019 and 2023; all of 2016).

Output, one row per constituency and list: election, code, list, abbr, votes, seats; and one
row per constituency for Cuadro I.
"""

from __future__ import annotations

import contextlib
import re
from pathlib import Path

import pandas as pd
from lxml import etree

from .provinces import CODES, code_of

SUMMARY_COLS = ["electors", "voters", "valid", "candidates", "blank", "null"]


def num(text: str) -> int:
    """'1.234.567' -> 1234567; blanks, dots and dashes (empty cells) -> 0."""
    t = re.sub(r"[^\d]", "", text or "")
    return int(t) if t else 0


def clean(text: str) -> str:
    return " ".join((text or "").replace("\xa0", " ").split())


# --- HTML tables ------------------------------------------------------------------------------


def grid(table) -> tuple[list[list[str]], list[list[str]]]:
    """Header and body rows of an HTML table, with colspans repeated across their columns.
    The header is every row before the first constituency row, wherever the BOE put it."""
    def expand(tr):
        out = []
        for cell in tr.xpath("./th|./td"):
            out += [clean("".join(cell.itertext()))] * int(cell.get("colspan", 1))
        return out
    rows = [expand(tr) for tr in table.iter("tr")]
    first = next((i for i, r in enumerate(rows) if r and code_of(r[0])), len(rows))
    return rows[:first], rows[first:]


def html_tables(xml_path: Path):
    root = etree.parse(str(xml_path), etree.XMLParser(recover=True, huge_tree=True)).getroot()
    return [grid(t) for t in root.iter("table")]


def _province_rows(body):
    for row in body:
        if not row:
            continue
        code = code_of(row[0])
        if code:
            yield code, row


def parse_html(xml_path: Path, election: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cuadros I, II and III from the HTML tables of a BOE XML document."""
    lists, summary = [], []
    for head, body in html_tables(xml_path):
        flat = [c for row in head for c in row]
        if any(c.lower() == "electores" for c in flat):  # Cuadro I
            cols = [c.lower() for c in head[0]]
            idx = {k: cols.index(n) for k, n in [
                ("electors", "electores"), ("voters", "votantes"), ("valid", "votos válidos"),
                ("candidates", "votos a candidaturas"), ("blank", "votos en blanco"),
                ("null", "votos nulos")]}
            for code, row in _province_rows(body):
                summary.append({"election": election, "code": code,
                                **{k: num(row[i]) for k, i in idx.items()}})
            continue
        sub = head[-1] if head else []
        if not sub or not all(c in ("Votos", "Escaños") for c in sub if c):
            continue  # Senate tables and lists of names
        names = head[0]
        abbrs = head[1] if len(head) == 3 else [""] * len(names)
        with_seats = "Escaños" in sub
        # head[0] carries the leading row headers ('', 'Total escaños'), which span the
        # sub-header rows, so those rows are shifted left by their number.
        offset = len(names) - len(sub)
        for code, row in _province_rows(body):
            j = 0
            while j < len(sub):
                col = j + offset
                if sub[j] != "Votos":
                    j += 1
                    continue
                name = names[col]
                if len(abbrs) == len(names):
                    abbr = abbrs[col]
                elif len(abbrs) == len(sub):
                    abbr = abbrs[j]
                elif with_seats and 2 * len(abbrs) == len(sub):
                    abbr = abbrs[j // 2]
                else:
                    abbr = ""
                votes = num(row[col]) if col < len(row) else 0
                seats = num(row[col + 1]) if with_seats and col + 1 < len(row) else 0
                if name and (votes or seats):
                    lists.append({"election": election, "code": code, "list": name,
                                  "abbr": abbr, "votes": votes, "seats": seats})
                j += 2 if with_seats else 1
    return pd.DataFrame(lists), pd.DataFrame(summary)


# --- PDF text -------------------------------------------------------------------------------


def pdf_text(pdf_path: Path, first: int = 0, last: int | None = None) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = reader.pages[first:last]
    return [p.extract_text() or "" for p in pages]


NUMBER = r"\d{1,3}(?:\.\d{3})*"


def parse_pdf_summary(pdf_path: Path, election: str) -> pd.DataFrame:
    """Cuadro I from the PDF text: 52 rows of six numbers, in the BOE's constituency order
    (the province names are missing from some rows of the text layer, so the order is used
    and checked against the names where they are present)."""
    pages = pdf_text(pdf_path, 0, 6)
    text = "\n".join(pages)
    start = text.find("CUADRO I")
    end = text.find("CUADRO II", start)
    rows = []
    for line in text[start:end].splitlines():
        nums = re.findall(rf"(?<![\d.]){NUMBER}(?![\d.])", line)
        if len(nums) == 6:
            name = re.sub(rf"{NUMBER}", "", line).strip(" .")
            rows.append(([num(n) for n in nums], name))
    if len(rows) < 52:
        raise ValueError(f"{pdf_path.name}: {len(rows)} Cuadro I rows")
    out = []
    for code, (vals, name) in zip(CODES, rows[:52], strict=True):
        if name and code_of(name) not in (None, code):
            raise ValueError(f"{pdf_path.name}: row for {name} where {code} was expected")
        out.append({"election": election, "code": code, **dict(zip(SUMMARY_COLS, vals,
                                                                    strict=True))})
    return pd.DataFrame(out)


# 2016: the seat-winning lists of Cuadro II, page by page, as (name, abbreviation). The PDF
# breaks the long names over several lines, so the column order is written out here and checked
# against the published national totals of votes and seats (test_boe.py).
LISTS_2016 = [
    [("PARTIDO POPULAR", "PP"), ("PARTIDO SOCIALISTA OBRERO ESPAÑOL", "PSOE"),
     ("UNIDOS PODEMOS", "PODEMOS-IU-EQUO"), ("CIUDADANOS-PARTIDO DE LA CIUDADANÍA", "C's"),
     ("EN COMÚ PODEM-GUANYEM EL CANVI", "ECP")],
    [("COMPROMÍS-PODEMOS-EUPV: A LA VALENCIANA", "COMPROMÍS-PODEMOS-EUPV"),
     ("ESQUERRA REPUBLICANA/CATALUNYA SÍ", "ERC-CATSÍ"),
     ("PARTIT DELS SOCIALISTES DE CATALUNYA (PSC-PSOE)", "PSC"),
     ("CONVERGÈNCIA DEMOCRÀTICA DE CATALUNYA", "CDC"),
     ("EN MAREA", "PODEMOS-EN MAREA-ANOVA-EU")],
    [("EUZKO ALDERDI JELTZALEA-PARTIDO NACIONALISTA VASCO", "EAJ-PNV"),
     ("PARTIDO POPULAR EN COALICIÓN CON EL PARTIDO ARAGONÉS", "PP-PAR"),
     ("PARTIDO SOCIALISTA OBRERO ESPAÑOL-NUEVA CANARIAS", "PSOE-NCa"),
     ("PARTIDO POPULAR-FORO", "PP-FORO"),
     ("EUSKAL HERRIA BILDU", "EH Bildu")],
    [("UNIÓN DEL PUEBLO NAVARRO EN COALICIÓN CON EL PARTIDO POPULAR", "UPN-PP"),
     ("COALICIÓN CANARIA-PARTIDO NACIONALISTA CANARIO", "CCa-PNC")],
]


def parse_pdf_seat_lists_2016(pdf_path: Path) -> pd.DataFrame:
    """Cuadro II of 2016 from the PDF text (lists with seats). Lists without seats are the
    difference between Cuadro I's candidate votes and these, kept as 'others'."""
    pages = pdf_text(pdf_path, 2, 6)
    out = []
    for page, lists in zip(pages, LISTS_2016, strict=True):
        if "CUADRO II" not in page:
            raise ValueError("2016: unexpected page layout")
        for line in page.splitlines():
            m = re.match(r"^\s*([^\d]+?)\s+(\d+(?:\s+(?:\.|" + NUMBER + r"))+)\s*$", line)
            if not m:
                continue
            code = code_of(m.group(1))
            if not code:
                continue
            toks = m.group(2).split()[1:]  # drop the constituency's total seats
            for k, (name, abbr) in enumerate(lists):
                votes, seats = num(toks[2 * k]), num(toks[2 * k + 1])
                if votes or seats:
                    out.append({"election": "2016", "code": code, "list": name, "abbr": abbr,
                                "votes": votes, "seats": seats})
    return pd.DataFrame(out)


def national_totals_2016(pdf_path: Path) -> dict[str, tuple[int, int]]:
    """The published 'Total estatal' row of each Cuadro II page: abbr -> (votes, seats)."""
    pages = pdf_text(pdf_path, 2, 6)
    out = {}
    for page, lists in zip(pages, LISTS_2016, strict=True):
        line = next(ln for ln in page.splitlines() if ln.strip().startswith("Total estatal"))
        toks = line.split()[3:]  # 'Total', 'estatal', total seats
        for k, (_, abbr) in enumerate(lists):
            out[abbr] = (num(toks[2 * k]), num(toks[2 * k + 1]))
    return out


# --- the 2026 decree ------------------------------------------------------------------------

WORDS = {"uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
         "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13,
         "catorce": 14, "quince": 15, "dieciséis": 16, "diecisiete": 17, "dieciocho": 18,
         "diecinueve": 19, "veinte": 20}


def spanish_number(text: str) -> int:
    t = text.lower().strip(" .")
    if t in WORDS:
        return WORDS[t]
    tens = {"veinti": 20, "treinta": 30, "cuarenta": 40}
    if t.startswith("veinti"):
        return 20 + WORDS[t[len("veinti"):]]
    for word, value in tens.items():
        if t.startswith(word):
            rest = t[len(word):].replace(" y ", "").strip()
            return value + (WORDS[rest] if rest else 0)
    raise ValueError(f"not a number word: {text!r}")


def parse_decree_seats(xml_path: Path) -> pd.DataFrame:
    """The annex of Real Decreto 806/2026: seats per constituency, written out in words."""
    root = etree.parse(str(xml_path), etree.XMLParser(recover=True)).getroot()
    rows = []
    for table in root.iter("table"):
        _, body = grid(table)
        for row in body:
            if len(row) >= 2 and code_of(row[0]):
                rows.append({"code": code_of(row[0]), "seats": spanish_number(row[1])})
    if not rows:  # the annex as paragraphs
        text = [clean("".join(p.itertext())) for p in root.iter("p")]
        for name, words in zip(text, text[1:], strict=False):
            if code_of(name):
                with contextlib.suppress(ValueError, KeyError):
                    rows.append({"code": code_of(name), "seats": spanish_number(words)})
    df = pd.DataFrame(rows).drop_duplicates("code")
    return df.set_index("code").loc[CODES].reset_index()


# --- INE: electors 2026, population ------------------------------------------------------------


def parse_ine_electors(pdf_path: Path) -> pd.DataFrame:
    """Electors per constituency for 29 Nov 2026 (total, residents in Spain, abroad)."""
    text = "\n".join(pdf_text(pdf_path))
    rows = []
    for line in text.splitlines():
        m = re.match(rf"^\s*(\d\d)\s+(.+?)\s+({NUMBER})\s+({NUMBER})\s+({NUMBER})\s*$", line)
        if m and m.group(1) in CODES and code_of(m.group(2)) == m.group(1):
            rows.append({"code": m.group(1), "electors": num(m.group(3)),
                         "electors_spain": num(m.group(4)), "electors_abroad": num(m.group(5))})
    df = pd.DataFrame(rows).drop_duplicates("code")
    total = re.search(rf"Total general\s+({NUMBER})\s+({NUMBER})\s+({NUMBER})", text)
    if len(df) != 52 or df["electors"].sum() != num(total.group(1)):
        raise ValueError("INE electors: rows do not add up to the published total")
    return df.set_index("code").loc[CODES].reset_index()


def parse_ine_population(pdf_path: Path) -> tuple[int, str]:
    text = " ".join(pdf_text(pdf_path, 0, 1))
    m = re.search(rf"se situó\s+en\s+({NUMBER})\s+habitantes\s+a\s+(1 de \w+ de \d{{4}})", text)
    return num(m.group(1)), m.group(2)


# --- the 2026 candidacies ---------------------------------------------------------------------


def _text_lines(xml_path: Path) -> list[str]:
    root = etree.parse(str(xml_path), etree.XMLParser(recover=True, huge_tree=True)).getroot()
    texto = root.find("texto") if root.find("texto") is not None else root
    out = []
    for el in texto.iter("p"):
        line = clean("".join(el.itertext()).replace(" ", " "))
        if line:
            out.append(line)
    return out


def _header(lines: list[str], i: int) -> tuple[str, int]:
    """A list's header may break over several lines ('... (EH', 'BILDU-ERC', ')')."""
    line = lines[i]
    i += 1
    while line.count("(") > line.count(")") and i < len(lines):
        line += " " + lines[i]
        i += 1
    return line, i


def parse_candidacies(xml_path: Path) -> pd.DataFrame:
    """The Congreso lists proclaimed in every constituency: code, number, name, abbr.

    Under each 'JUNTA ELECTORAL DE …', the 'CONGRESO DE LOS DIPUTADOS' section numbers its
    lists 1, 2, 3…; each list is followed by its candidates, also numbered, whose lines end in
    a full stop. A list is the line carrying the next expected number that does not end in a
    full stop (most end with the abbreviation in brackets; a few have none)."""
    lines = _text_lines(xml_path)
    rows, code, section, expect, i = [], None, None, 1, 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^JUNTA ELECTORAL (?:PROVINCIAL )?DE (.+)$", line)
        if m:
            code, section, expect, i = code_of(m.group(1)), None, 1, i + 1
            continue
        if line.startswith("CONGRESO DE LOS DIPUTADOS"):
            section, i = "C", i + 1
            continue
        if line.startswith("SENADO"):
            section, i = "S", i + 1
            continue
        m = re.match(r"^(\d+)\.\s+\S", line)
        if section == "C" and code and m and int(m.group(1)) == expect:
            full, j = _header(lines, i)
            if not full.endswith("."):
                body = re.sub(r"^\d+\.\s+", "", full)
                ab = re.search(r"\(([^()]*(?:\([^()]*\))?[^()]*)\)\s*$", body)
                rows.append({"code": code, "number": expect, "name": body,
                             "abbr": ab.group(1).strip() if ab else body})
                expect, i = expect + 1, j
                continue
        i += 1
    return pd.DataFrame(rows)


def apply_candidacy_corrections(cands: pd.DataFrame, xml_path: Path) -> pd.DataFrame:
    """Apply the renamings of Congreso lists in a correction of errors ('Donde dice: «N. old»
    Debe decir: «N. new»'); corrections to candidates' names do not change the lists."""
    lines = _text_lines(xml_path)
    out = cands.copy()
    code, section = None, None
    for k, line in enumerate(lines):
        m = re.match(r"^JUNTA ELECTORAL (?:PROVINCIAL )?DE (.+)$", line)
        if m:
            code, section = code_of(m.group(1)), None
        elif line.startswith("CONGRESO DE LOS DIPUTADOS"):
            section = "C"
        elif line.startswith("SENADO"):
            section = "S"
        elif section == "C" and line.startswith("Donde dice"):
            old, j = _header(lines, k + 1)
            if not old.startswith("«") or not lines[j].startswith("Debe decir"):
                continue
            new, _ = _header(lines, j + 1)
            mo = re.match(r"^«(\d+)\.\s+(.+?)»?$", old)
            mn = re.match(r"^«(\d+)\.\s+(.+?)»$", new)
            if mo and mn and mo.group(1) == mn.group(1) and mn.group(2).endswith(")"):
                body = mn.group(2)
                ab = re.search(r"\(([^()]+)\)\s*$", body)
                sel = (out["code"] == code) & (out["number"] == int(mn.group(1)))
                out.loc[sel, "name"] = body
                out.loc[sel, "abbr"] = ab.group(1).strip() if ab else body
    return out
