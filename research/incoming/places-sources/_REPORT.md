# Report: places and sources (research/incoming/places-sources)

Agent run of 2026-11-02. Nothing in this folder is marked "verified". All claims are "pending" or "disputed".

## Working conditions (read first)

* Direct page fetching was blocked: en.wikipedia.org and www.wikidata.org do not resolve in this session (they would have to be allowed in the session network settings). Following the error guidance, I did not try further hosts. All evidence came from WebSearch result summaries. No catalogue page, gazetteer record or edition was opened and read in full.
* The shared WebSearch budget (200 per turn) ran out partway through Part B. Sixteen of the 32 source records therefore rest on **model recall** for their bibliographic data. Their `citation` claim is sourced as `model_recall` and says so. These are: src-clayton-philo-2012, src-vecce-1998, src-pedretti-1978-architetto, src-pedretti-1973-chronology, src-pedretti-1957-studi, src-marinoni-atlantico, src-edizione-nazionale, src-popham-1946, src-clark-1939, src-bramly-1988, src-nicholl-2004, src-isaacson-2017, src-e-leo, src-leonardo-theka, src-shell-sironi-1991 and src-vecce-2023-caterina. src-rct-online has a real url, but its catalogue page was not opened.
* Coordinates are web values (Wikipedia infobox figures as quoted in search results, or gazetteer and coordinate sites). Each one has a `coords` claim of type "web" with the url. They are good enough for map display, not for anything precise.

## Entities written (107 files)

**Places (75).**
* Regions: geo-tuscany, geo-lombardy, geo-romagna, geo-apulia, geo-loire-valley.
* Towns: geo-vinci, geo-anchiano, geo-florence, geo-milan, geo-pavia, geo-vaprio-d-adda, geo-mantua, geo-venice, geo-rome, geo-vatican, geo-amboise, geo-romorantin, geo-imola, geo-cesena, geo-urbino, geo-pesaro, geo-rimini, geo-piombino, geo-pisa, geo-lyon, geo-bologna, geo-correggio, geo-careggi, geo-paris, geo-london, geo-windsor, geo-madrid, geo-turin, geo-krakow, geo-saint-petersburg, geo-munich, geo-washington, geo-parma.
* History lane context places (minimal records): geo-constantinople, geo-mainz, geo-wittenberg, geo-otranto, geo-granada, geo-marignano, geo-florence-cathedral.
* Buildings and sites: geo-santa-maria-delle-grazie, geo-castello-sforzesco, geo-corte-vecchia-milan, geo-santissima-annunziata, geo-palazzo-vecchio, geo-santa-maria-novella, geo-santa-maria-nuova, geo-belvedere-vatican, geo-clos-luce, geo-chateau-amboise, geo-saint-florentin-amboise, geo-leonardo-vineyard-milan, geo-verrocchio-workshop.
* Holdings: geo-louvre, geo-uffizi, geo-national-gallery-london, geo-royal-collection-windsor, geo-ambrosiana, geo-institut-de-france, geo-biblioteca-nacional-madrid, geo-british-library, geo-biblioteca-reale-turin, geo-czartoryski-krakow, geo-hermitage, geo-alte-pinakothek, geo-vatican-pinacoteca, geo-national-gallery-washington, geo-v-and-a, geo-biblioteca-trivulziana, geo-galleria-nazionale-parma.

Every place has `located_in` relations through `within`.

**Places with no coordinates yet:** geo-correggio, geo-careggi, geo-windsor, geo-turin, geo-saint-petersburg, geo-santa-maria-nuova, geo-saint-florentin-amboise, geo-verrocchio-workshop, the history context places and the regions.

**Not created:** a Bill Gates entity for the owner of the Codex Leicester. It is a person or owner entity (pe-), so it belongs to the persons lane.

**Sources (32).**
* All 15 registry ids are present, plus src-richter-1939.
* Others: src-vecce-1998, src-pedretti-1978-architetto, src-pedretti-1973-chronology, src-pedretti-1957-studi, src-marinoni-atlantico, src-edizione-nazionale, src-popham-1946, src-clark-1939, src-bramly-1988, src-nicholl-2004, src-isaacson-2017, src-rct-online, src-e-leo, src-leonardo-theka, src-shell-sironi-1991, src-vecce-2023-caterina.
* Frey's Anonimo edition is src-anonimo-gaddiano, with "src-frey-1892" listed as a variant, not as a separate id.
* Each source has a `citation` claim and an `admission` claim.
* Not admitted: Bramly, Nicholl, Isaacson, the RCT online catalogue, e Leo, Leonardo//thek@ and Vecce 2023 (a novel; the 1452 document behind it is admissible once cited from the archive).

## Conflicts found (with ids)

1. **Vineyard date.** The draft e-vineyard says 1498. Web sources tie the grant to a ducal letter of 26 April 1499. Others put possession in 1497 (August) or 1498, from a later document about a neighbouring property. See geo-leonardo-vineyard-milan c2 and c3.
2. **Vineyard area.** About 16 pertiche (FAI) against about 15 pertiche (Wikipedia). See geo-leonardo-vineyard-milan c4.
3. **Vineyard confiscation.** The vineyard was confiscated in 1502 and given to Leonardo Biglia (Wikipedia). The draft does not mention this. See c5.
4. **Burial and tomb.**
   * The demolition of Saint Florentin is dated 1806 to 1810, 1807 or 1808, depending on the source.
   * The transfer of the remains to Saint Hubert is dated 1874 by one source and "mid nineteenth century" by others.
   * The identity of the remains is doubted.
   * See geo-saint-florentin-amboise c2 to c4.
5. **Birthplace.** The draft e-birth gives the place as "Anchiano, near Vinci" at tier D. The Anchiano identification is a tradition, not stated in Antonio's note as far as I could check. See geo-anchiano c2.
6. **Verrocchio's workshop.** Two locations are given: the Via dell'Agnolo and Via de' Macci house in the parish of Sant'Ambrogio, or Via Ghibellina near the Stinche, with a move toward the Duomo before 1480. See geo-verrocchio-workshop c1 and c2.
7. **Bibliographic discrepancies.**
   * Beltrami 1919 collation: xii, 224 p. or X, 221 p.
   * Clark and Pedretti imprint: London 1968 or New York 1968 to 1969.
   * Anonimo Gaddiano shelfmark: XVII 17 or XVI 17.
   * Marani has several editions (1999 Italian, 2000 English, 2019 revised), and Zöllner has several printings (2003, 2007, 2019). Catalogue numbers should name their edition.

## Proposed corrections to the draft chronology (proposals only)

* **e-vineyard:** change the date to "1497 to 26 April 1499" (grant confirmed by a letter of 26 April 1499), or keep 1499 with tier D only once Villata confirms it. Mention the 1502 confiscation.
* **e-birth:** change the place to "Vinci (Anchiano by tradition)". Lower the place part to tier T unless a document names Anchiano.
* **pl-flor1a and pl-flor1b:** if workshop places are shown, give them as "Verrocchio's workshop, location disputed".
* **e-death and pl-france:** add a note that the original grave at Saint Florentin was lost with the church's demolition (c.1806 to 1810). The present tomb in the chapel of Saint Hubert holds remains of uncertain identity.
* **pl-rome:** the "Belvedere" lodging needs a document check. The draft basis "Vatican payment lists" was not confirmed.

## Most important checks a human must make in an admitted edition

1. **Villata 1999:**
   * the vineyard documents (1497 to 1499, 1502, 1507) and the will of 23 April 1519 (burial at Saint Florentin, vineyard bequest)
   * the 1457 catasto (Vinci household)
   * the Sala del Papa documents of October 1503
   * the Belvedere works of December 1513
   * the Santa Maria Nuova deposit records.
2. **Antonio da Vinci's 1452 note** (Villata or Beltrami): does it name any place of birth?
3. **Catalogue opening (WorldCat or SBN OPAC) for the 16 recall only sources.** Above all, Shell and Sironi 1991: I recall it as Burlington Magazine 133, no. 1055, pp. 95 to 108, but this is unverified. Also check the Marinoni and Edizione Nazionale volume lists, and the urls for e Leo and Leonardo//thek@.
4. **Codicological check of Romorantin and Piombino dating:** Codex Arundel, Codex Atlanticus and Madrid II folios.
5. **Gazetteer confirmation (GeoNames or Wikidata) of single source coordinates:** Santissima Annunziata, Galleria Nazionale di Parma, Biblioteca Reale, Pinacoteca Vaticana. The Pinacoteca point is for the whole museum complex.
