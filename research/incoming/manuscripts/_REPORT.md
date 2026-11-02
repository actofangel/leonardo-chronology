# Manuscripts and codices: research report (2026-11-02)

Scope: type "manuscript". 30 files written in this folder. Every claim has status "pending" or "disputed". None is "verified", because no admitted source text was read in this session.

## Working conditions (please read first)

* WebFetch could not reach any external host. The hosts that failed were searcharchives.bl.uk, collections.vam.ac.uk, mostre.museogalileo.it and leonardo-online.mpiwg-berlin.mpg.de. They would have to be allowed in the session's network settings. As a result every fact here comes from web search result summaries, and the cites say so where it matters (for example "seen only as a search summary").
* Official pages (British Library, V&A, RCT, Museo Galileo, Ambrosiana on Google Arts and Culture) are typed "other". Wikipedia and popular sites are typed "web" and marked as background only. No claim uses type "primary", because no folio was viewed.
* Shelfmarks are included only where a page returned by the search stated them, and the url is given in the same claim. Every folio of a dated note is "to locate".

## Entities written

Legacy ids, now with type "manuscript": w-atlanticus, w-leicester, w-trivulz, w-flightcodex, w-msb, w-madrid1.

New manuscripts:
* ms-arundel
* ms-paris-a, ms-paris-c, ms-paris-d, ms-paris-e, ms-paris-f, ms-paris-g, ms-paris-h, ms-paris-i, ms-paris-k, ms-paris-l, ms-paris-m (B is w-msb)
* ms-ashburnham-2037, ms-ashburnham-2038
* ms-forster-1, ms-forster-2, ms-forster-3
* ms-madrid-1, ms-madrid-2
* ms-windsor
* ms-codex-urbinas

New events (lane "events", all within 1450 to 1520; each comes from a dated autograph note whose folio is still to locate):
* e-ms-c-begun (23 April 1490)
* e-forster1-begun (July 1505)
* e-arundel-begun (22 March 1508)

All later manuscript history is recorded as claims on the manuscripts, not as events. That covers Leoni, Arconati 1637, Paris 1796, the 1815 return, Libri, Ashburnham, the sales and the restorations.

### Design decisions
* **Madrid.** w-madrid1 is kept as a group record, "Madrid Codices I and II", and has_part links it to ms-madrid-1 (Ms. 8937) and ms-madrid-2 (Ms. 8936). The two codices differ in shelfmark, size and date: Codex I is c.1493 to 1495, and Codex II is c.1503 to 1505 with an earlier part from c.1491 to 1493. A single record cannot carry those dates honestly. Keeping the legacy id as the pair preserves the draft record's meaning.
* **Ashburnham.** The ids use the Ashburnham numbers (2037, 2038) instead of "I" and "II", because sources apply those labels inconsistently. The pairing 2037 = leaves from B = Institut Ms. 2184, and 2038 = leaves from A = Ms. 2185, is an interpretation built from the Institut shelfmark records. The reverse pairing is recorded as disputed.
* **Windsor.** One record, ms-windsor. Anatomical Manuscripts A, B and C are a claim on it, not separate entities, because no RCIN ranges were confirmed. They could be split out later.
* **Paris manuscripts.** The "contents" lists for A and C to M come from model recall, and a model_recall claim on each says so. They need checking before display.

## Conflicts found (sources against each other, or against the first draft)

* **Arconati donation:** 1636 or 21 January 1637. Marcuccio 2022 reads the original deed as 21 January 1637. See w-atlanticus c7 and c8.
* **Grottaferrata restoration of the Atlanticus:** 1962 to 1972 in Italian reports, 1968 to 1972 in English sources (w-atlanticus c11).
* **Seizure of the Atlanticus:** 1796 in most sources, 1795 in one (w-atlanticus c9).
* **w-leicester date:** the draft has c.1504 to 1510. The sources seen give c.1508 to 1510 (c2 against c3). Coke's purchase is dated 1717 or 1719. Ghezzi's ownership is dated 1689 or c.1690. Museo Galileo gives della Porta's ownership as 1537, which conflicts with his biography.
* **w-madrid1, rediscovery year:** 1965 (Piccus, Wikipedia, NYRB), 1966 (draft, Kunstchronik) or February 1967 (facsimile sellers). The draft says Codex II belongs to the Florence years, but part of it is dated c.1491 to 1493.
* **ms-madrid-2:** 158 or 157 folios.
* **w-flightcodex:** 18 folios or "38 pages". Manzoni's purchase is dated 1867 or 1868. The 1893 gift went to Queen Margherita or to King Umberto I.
* **ms-paris-d:** the consensus is c.1508 to 1509; Corbeau proposed 1513 to 1516.
* **ms-paris-f:** one summary dates entries to 1493 to 1494, which is probably a confusion.
* **ms-arundel:** the Earl of Arundel acquired it c.1630 or c.1636.
* **ms-windsor:** about 550 or nearly 600 drawings. The album may have come to the crown under Charles II or Charles I.
* **Ashburnham return:** 1888 (sale to the BnF) or 1890 (arrival at the Institut).
* **ms-codex-urbinas:** dated c.1540 or c.1540 to 1550.

## Proposed corrections to the draft chronology (proposals only)

1. **w-leicester:** change the date to c.1508 to 1510, or widen it explicitly to "c.1506 to 1510", once the Museo Galileo 2018 catalogue has been checked. Nothing seen supports 1504.
2. **w-madrid1:** replace "rediscovered in Madrid in 1966" with "reported in 1965 (some accounts 1966 or 1967)". Qualify "the second to the years in Florence" to say "mostly c.1503 to 1505, with an earlier Milanese part".
3. **w-atlanticus:** the place field "Milan, Biblioteca Ambrosiana" mixes the place of making with the holding. Suggest using holding = geo-ambrosiana and dropping place from the timeline bar.
4. **w-flightcodex:** the draft text is fine. Add the provenance through Libri, because the notebook was separated from the Institut de France manuscripts.
5. **e-letter:** the draft cites "Codex Atlanticus" with no folio. A folio from Pedretti 1978 or Marinoni is needed before the record can be verified.

## What a human must check in admitted editions (priority order)

1. **Pedretti 1978 to 1979 (src-pedretti-1978-atlanticus)** and **Marinoni's Codice Atlantico introduction:** the Atlanticus sheet count and dimensions, Leoni's acquisition window (1582 to 1590), the sale to Arconati, and the 1637 deed with the list of twelve volumes. Also which manuscript Arconati exchanged for the Trivulzianus.
2. **Pedretti (ed.), Il Codice Arundel 263, 1998:** the folio and Italian text of the note of 22 March 1508 in the house of Piero di Braccio Martelli, and the sheet chronology.
3. **Marinoni's edition of the Institut de France manuscripts (1986 to 1990)** and **Ravaisson Mollien:** folio counts and dimensions for A to M, the donor and date for each notebook, the Italian text and folio of the Manuscript C note of 23 April 1490, the dated notes in I (1497), and the Libri removals from A, B and E (with Delisle 1888).
4. **Marinoni (ed.), I Codici Forster, 1992,** and the V&A records: folio counts, dimensions, the July 1505 note, and the Bulwer Lytton purchase (Vienna, 1862?).
5. **Reti 1974 (Madrid Codices):** the rediscovery date, the Espina provenance, and when the codices entered the royal library (1712 or before 1830).
6. **Keele and Pedretti Corpus; Clark and Pedretti 1968; Clayton and Philo 2012:** the Windsor count, the RCIN ranges of Anatomical MSS A, B and C, the 2 April 1489 note, and the Leoni to Arundel to Royal Collection chain.
7. **Pedretti and Vecce 1995 (Libro di pittura):** the folio count of Urb. lat. 1270, Melzi's list of source notebooks, and the arrival at the Vatican in 1657.

## Ids referenced but not created here (for other agents)

* **Persons:** pe-pompeo-leoni, pe-galeazzo-arconati, pe-guglielmo-libri, pe-thomas-howard-arundel, pe-bertram-ashburnham, pe-john-forster, pe-carlo-trivulzio, pe-thomas-coke.
* **Places:** geo-biblioteca-apostolica-vaticana, geo-seattle, geo-turin, geo-madrid.
* **Relation types used beyond the brief's examples:** has_part, part_of, separated_from, related_to, bequeathed_in, recorded_in, compiled_by.
