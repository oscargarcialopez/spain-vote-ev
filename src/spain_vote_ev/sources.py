"""Every input file: where it comes from and what it holds. `voteev download` fetches them into
data/raw/ and records a SHA-256 manifest; nothing else in the pipeline touches the network.

Official results come from the Junta Electoral Central's publications in the BOE, the legal
record of the general count (escrutinio general) in every constituency. The Ministry of the
Interior's infoelectoral download area holds the same counts as fixed-width .DAT files, but it
sits behind a browser challenge that a script cannot pass, so it is not used.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

USER_AGENT = "spain-vote-ev/0.1 (open research script)"

BOE_XML = "https://www.boe.es/diario_boe/xml.php?id={id}"
BOE_PDF = "https://www.boe.es/boe/dias/{date}/pdfs/{id}.pdf"
WIKI_PARSE = ("https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=text|revid"
              "&formatversion=2&page={title}")


@dataclass(frozen=True)
class Source:
    file: str
    url: str
    what: str
    kind: str = "file"  # "file" or "wiki" (MediaWiki parse API: JSON with the HTML and revid)


def boe_xml(boe_id: str, what: str) -> Source:
    return Source(f"{boe_id}.xml", BOE_XML.format(id=boe_id), what)


def boe_pdf(boe_id: str, date: str, what: str) -> Source:
    return Source(f"{boe_id}.pdf", BOE_PDF.format(date=date, id=boe_id), what)


def wiki(title: str, what: str) -> Source:
    return Source(f"wiki-{title}.json", WIKI_PARSE.format(title=title), what, kind="wiki")


# Election keys used throughout: congress elections and the 2024 European Parliament election.
ELECTIONS = ["2015", "2016", "2019A", "2019N", "2023"]
ELECTION_DATE = {"2015": "2015-12-20", "2016": "2016-06-26", "2019A": "2019-04-28",
                 "2019N": "2019-11-10", "2023": "2023-07-23", "EP2024": "2024-06-09",
                 "2026": "2026-11-29"}
ELECTION_LABEL = {"2015": "2015", "2016": "2016", "2019A": "April 2019",
                  "2019N": "November 2019", "2023": "2023", "2026": "2026"}

SOURCES: list[Source] = [
    # Congreso results, JEC publications in the BOE (Cuadro I: electors, voters, valid, blank,
    # null by constituency; Cuadros II and III: votes and seats of every list).
    boe_xml("BOE-A-2016-867", "2015 Congreso results, all three tables"),
    boe_pdf("BOE-A-2016-7133", "2016/07/22", "2016 Congreso results (the HTML has images)"),
    boe_xml("BOE-A-2019-8070", "April 2019 Congreso results, all three tables"),
    boe_pdf("BOE-A-2019-17344", "2019/12/02", "November 2019 Congreso results (Cuadro I)"),
    boe_xml("BOE-A-2019-18147", "November 2019 Cuadros II and III, corrected and republished"),
    boe_xml("BOE-A-2023-18907", "2023 Congreso results, Cuadros II and III"),
    boe_pdf("BOE-A-2023-18907", "2023/09/01", "2023 Congreso results (Cuadro I is an image "
            "in the HTML)"),
    boe_xml("BOE-A-2024-13092", "2024 European Parliament results by province"),
    boe_xml("BOE-A-2024-15344", "correction of two national totals in the 2024 EP results"),
    # The 2026 election: the decree with the seats per constituency, the electorate, the
    # population.
    boe_xml("BOE-A-2026-20742", "Real Decreto 806/2026: dissolution, election on 29 Nov 2026, "
            "seats per constituency (annex)"),
    boe_xml("BOE-A-2026-23103", "candidacies proclaimed for 29 Nov 2026, every constituency"),
    boe_xml("BOE-A-2026-23383", "correction of errors in the proclaimed candidacies"),
    Source("INE-EG2026.pdf", "https://www.ine.es/dyngs/Prensa/EG2026.pdf",
           "INE press release of 9 Oct 2026: electors per constituency for 29 Nov 2026"),
    Source("INE-ECP3T26.pdf", "https://www.ine.es/dyngs/Prensa/ECP3T26.pdf",
           "INE Estadística Continua de Población, 1 Oct 2026 (provisional)"),
    # The 2023 investiture votes (Diario de Sesiones del Congreso).
    Source("DSCD-15-PL-5.pdf",
           "https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-5.PDF",
           "Diario de Sesiones, 27 Sep 2023: Feijóo investiture vote, 172 yes, 178 no"),
    Source("DSCD-15-PL-8.pdf",
           "https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-8.PDF",
           "Diario de Sesiones, 16 Nov 2023: Sánchez investiture vote, 179 yes, 171 no"),
    # National polls (English Wikipedia lists).
    wiki("Opinion_polling_for_the_2015_Spanish_general_election", "polls, 2015"),
    wiki("Opinion_polling_for_the_2016_Spanish_general_election", "polls, 2016"),
    wiki("Opinion_polling_for_the_April_2019_Spanish_general_election", "polls, April 2019"),
    wiki("Opinion_polling_for_the_November_2019_Spanish_general_election",
         "polls, November 2019"),
    wiki("Opinion_polling_for_the_2023_Spanish_general_election", "polls, 2023"),
    wiki("Opinion_polling_for_the_2026_Spanish_general_election", "polls, 2026"),
]

POLL_PAGES = {
    "2015": "wiki-Opinion_polling_for_the_2015_Spanish_general_election.json",
    "2016": "wiki-Opinion_polling_for_the_2016_Spanish_general_election.json",
    "2019A": "wiki-Opinion_polling_for_the_April_2019_Spanish_general_election.json",
    "2019N": "wiki-Opinion_polling_for_the_November_2019_Spanish_general_election.json",
    "2023": "wiki-Opinion_polling_for_the_2023_Spanish_general_election.json",
    "2026": "wiki-Opinion_polling_for_the_2026_Spanish_general_election.json",
}
