#!/usr/bin/env node
// Import the project's own reference pages into research/incoming/project-pages/:
//
//   site/views/library.html             The Library of Leonardo da Vinci, a reconstructed catalogue (125 titles)
//   site/views/itinerario-vinciano.html Itinerario Vinciano, places of residence and travel 1452 to 1519
//
// The pages stay published unchanged as views. This script turns their data
// into entities and claims. Both pages are compiled research documents, so
// they are cited as sources of type "other" (src-project-library,
// src-itinerario-vinciano): they point to where to check and never verify.
// The itinerary's own tiers are kept: A and B become fact claims, C an
// interpretation, D a disputed claim; every A or B claim names Villata 1999
// or Beltrami 1919 in check_in.
//
//   node scripts/import/project-pages.mjs
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { ROOT, loadAll } from '../lib.mjs';

const DATE = '2026-11-02';
const OUT = path.join(ROOT, 'research', 'incoming', 'project-pages');
if (existsSync(OUT)) rmSync(OUT, { recursive: true });
mkdirSync(OUT, { recursive: true });
const { entities } = loadAll();
const emit = (e) => writeFileSync(path.join(OUT, e.id + '.json'), JSON.stringify(e, null, 2) + '\n');
const clean = (s) => String(s ?? '').replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&nbsp;/g, ' ').replace(/&#39;|&rsquo;|&#8217;/g, "'").replace(/&quot;|&ldquo;|&rdquo;/g, '"')
  .replace(/(\d)\s*[–—]\s*(\d)/g, '$1 to $2').replace(/\s*[‐-―−]\s*/g, ', ').replace(/--+/g, ', ').replace(/\s+/g, ' ').trim();
const slug = (s) => clean(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

// ---------- sources ----------
emit({
  id: 'src-project-library', type: 'source', source_type: 'other', label: 'The Library of Leonardo da Vinci: A Reconstructed Catalogue (project page)',
  short: 'Project library catalogue', citation: 'Identity of Leonardo da Vinci, The Library of Leonardo da Vinci: A Reconstructed Catalogue, 125 titles, project web page (site/views/library.html), compiled from Vecce (ed.) 2019, the Museo Galileo digital library and Leonardo\'s autograph book lists.',
  url: 'views/library.html', language: 'en',
  claims: [{ id: 'c1', about: 'admission', layer: 'interpretation', status: 'pending', statement: 'A compiled research page of this project. It is reference material, not a ground: every entry points to Leonardo\'s autograph book lists (Codex Trivulzianus f. 2r; Codex Atlanticus f. 559r; Madrid Codex II ff. 2v to 3r) and to Vecce (ed.) 2019, which are where an identification must be checked.', sources: [{ type: 'other', cite: 'Project source admission rules (SCHEMA.md).' }] }]
});
emit({
  id: 'src-vecce-2019-libri', type: 'source', source_type: 'catalogue', label: 'Vecce (ed.), Leonardo and His Books, 2019',
  short: 'Vecce 2019', citation: 'Carlo Vecce (ed.), Leonardo e i suoi libri / Leonardo and His Books: The Library of the Universal Genius, exhibition catalogue, Florence, Museo Galileo, Giunti, 2019.',
  language: 'it', claims: [{ id: 'c1', about: 'citation', layer: 'fact', status: 'pending', statement: 'Citation as given in the project library page; not checked against a library catalogue in this session.', sources: [{ ref: 'src-project-library', loc: 'section Principal sources, no. 2' }] }],
  open_questions: ['Confirm the bibliographic details (title in Italian and English editions, pages) in a library catalogue. Classed as an exhibition catalogue with scholarly apparatus; confirm that it meets the admission rules.']
});
emit({
  id: 'src-itinerario-vinciano', type: 'source', source_type: 'other', label: 'Itinerario Vinciano: Places of Residence and Travel, 1452 to 1519 (project page)',
  short: 'Itinerario Vinciano', citation: 'Identity of Leonardo da Vinci, Itinerario Vinciano: Places of Residence and Travel, 1452 to 1519, project web page (site/views/itinerario-vinciano.html). Grades its statements in tiers A (contemporary documents), B (documents in critical editions or institutional records), C (consensus or sixteenth century tradition), D (contested).',
  url: 'views/itinerario-vinciano.html', language: 'en',
  claims: [{ id: 'c1', about: 'admission', layer: 'interpretation', status: 'pending', statement: 'A compiled research page of this project. It is reference material, not a ground. Its tier A and B statements name documents to be checked in Villata 1999 and Beltrami 1919; its tier labels are kept on the imported claims.', sources: [{ type: 'other', cite: 'Project source admission rules (SCHEMA.md).' }] }]
});

// ---------- library ----------
const lib = readFileSync(path.join(ROOT, 'site', 'views', 'library.html'), 'utf8');
const a = lib.indexOf('const CATS'), b = lib.indexOf('/* ============ RENDER');
const ctx = {}; vm.createContext(ctx); vm.runInContext(lib.slice(a, b) + ';globalThis.o={CATS,B,GAL}', ctx);
const { CATS, B: BOOKS } = ctx.o;
const CAT = Object.fromEntries(CATS.map((c) => [c.id, c.name.replace(/&/g, 'and')]));
let nBooks = 0;
for (const bk of BOOKS) {
  const num = String(bk.n).padStart(3, '0');
  const unidentified = /^\(/.test(bk.or);
  const id = `bk-${num}-${slug(bk.en).split('-').filter((w) => !['a', 'an', 'the', 'of', 'on', 'and'].includes(w)).slice(0, 4).join('-')}`;
  const src = { ref: 'src-project-library', loc: `no. ${bk.n}` };
  const lists = ['Leonardo\'s autograph book lists: Codex Trivulzianus f. 2r; Codex Atlanticus f. 559r; Madrid Codex II ff. 2v to 3r (which list names this title to be established)', 'Vecce (ed.) 2019, entry for this title'];
  const e = {
    id, type: 'book', subtype: unidentified ? 'unidentified' : 'identified', label: clean(bk.en),
    variants: [clean(bk.or), clean(bk.leo)].filter((v) => v && v !== clean(bk.en) && !/^\(/.test(v)),
    library_no: bk.n, category: CAT[bk.c],
    background: [{ source: 'project-library', lang: 'en', url: 'views/library.html', text: clean(bk.note), retrieved: DATE }],
    relations: [{ rel: 'listed_by', target: 'pe-leonardo' }],
    claims: [
      { id: 'c1', about: 'in_library', value: { text: `no. ${bk.n}, ${CAT[bk.c]}` }, layer: 'interpretation', grade: 'strong_interpretation', status: 'pending',
        statement: clean(`Entered as no. ${bk.n} in the reconstructed catalogue of Leonardo's books, under ${CAT[bk.c]}. Leonardo's wording as rendered there: "${bk.leo}".`), sources: [src], check_in: lists },
      { id: 'c2', about: 'identification', value: { text: clean(bk.or) }, layer: 'interpretation', status: 'pending',
        statement: unidentified ? clean(`Not identified with a known text; the catalogue describes it as ${bk.or}.`) : clean(`Identified in the reconstruction as ${bk.or}. The identification of a title in Leonardo's lists with a specific work and edition is an interpretation.`),
        sources: [src], check_in: ['Vecce (ed.) 2019, entry for this title'] }
    ]
  };
  if (bk.y) e.claims.push({ id: 'c3', about: 'text_history', value: { text: clean(bk.y) }, layer: 'interpretation', status: 'pending', statement: clean(`Composition and printing as given in the reconstruction: ${bk.y}.`), sources: [src], check_in: ['ISTC (Incunabula Short Title Catalogue) or Edit16 record for the edition'] });
  if (bk.link) { e.identifiers = { museo_galileo: bk.link }; e.claims[1].sources.push({ type: 'other', cite: 'Museo Galileo, La Biblioteca di Leonardo, record for this title.', url: bk.link }); }
  if (!e.variants.length) delete e.variants;
  emit(e); nBooks++;
}

// ---------- itinerary ----------
const it = readFileSync(path.join(ROOT, 'site', 'views', 'itinerario-vinciano.html'), 'utf8');
const STAGE_EVENTS = { vinci: ['pl-vinci'], firenze1: ['pl-flor1a', 'pl-flor1b'], milano1: ['pl-milan1'], mantova: ['pl-mantua'], venezia: ['pl-mantua'], firenze2: ['pl-flor2a', 'pl-flor2b'],
  romagna: ['pl-romagna'], piombino: [], milano2: ['pl-milan2'], roma: ['pl-rome'], amboise: ['pl-france'] };
const STAGE_PLACE = { vinci: 'geo-vinci', firenze1: 'geo-florence', firenze2: 'geo-florence', milano1: 'geo-milan', milano2: 'geo-milan', mantova: 'geo-mantua', venezia: 'geo-venice', romagna: 'geo-imola', piombino: 'geo-piombino', roma: 'geo-rome', amboise: 'geo-amboise' };
const CONTEXT = /patron|government|terrain|economy|geopolitic|population|church|language|society|institution/i;
const LAYER = { A: ['fact', 'fact', 'pending'], B: ['fact', 'fact', 'pending'], C: ['interpretation', 'strong_interpretation', 'pending'], D: ['interpretation', 'speculation', 'disputed'] };
const placeOut = {};
const getPlace = (gid, label) => {
  if (!placeOut[gid]) placeOut[gid] = entities.has(gid) ? { id: gid, type: 'place', label: entities.get(gid).label, claims: [] } : { id: gid, type: 'place', subtype: 'town', label, claims: [], open_questions: ['Created from the Itinerario Vinciano map; needs sources for the historical connection.'] };
  return placeOut[gid];
};
const eventOut = {};
let nStage = 0, cn = 0;
for (const m of it.matchAll(/<section class="stage" id="([a-z0-9]+)">([\s\S]*?)<\/section>/g)) {
  const [, sid, body] = m;
  if (!(sid in STAGE_EVENTS)) continue;
  nStage++;
  const title = clean((body.match(/<h2>([\s\S]*?)<\/h2>/) || [])[1]);
  const rows = [...body.matchAll(/<tr><th>([\s\S]*?)<\/th><td[^>]*>([\s\S]*?)<\/td><\/tr>/g)].map((r) => ({ th: clean(r[1]), td: r[2] }));
  const loc = (th) => `section ${title}, ${th}`;
  // split a cell into statements, each with its tier
  const parts = (td) => {
    const out = []; let rest = td;
    for (const mm of td.matchAll(/([\s\S]*?)<span class="tier t([ABCD])">[ABCD]<\/span>\s*\.?\s*/g)) { const t = clean(mm[1]).replace(/^[;.,]\s*/, ''); if (t) out.push({ text: t, tier: mm[2] }); rest = rest.replace(mm[0], ''); }
    const tail = clean(rest).replace(/^[;.,]\s*/, ''); if (tail) out.push({ text: tail, tier: null });
    return out;
  };
  const evs = STAGE_EVENTS[sid];
  const gid = STAGE_PLACE[sid];
  for (const r of rows) {
    if (/coordinates/i.test(r.th)) {
      const c = r.td.match(/query=([\d.]+),([\d.]+)/);
      if (c) getPlace(gid, title).claims.push({ id: `iv${++cn}`, about: 'coords', value: { text: `${c[1]}, ${c[2]}` }, layer: 'fact', status: 'pending', statement: `Coordinates given in the Itinerario Vinciano: ${c[1]} N, ${c[2]} E.`, sources: [{ ref: 'src-itinerario-vinciano', loc: loc(r.th) }] });
      continue;
    }
    if (CONTEXT.test(r.th)) {
      const p = getPlace(gid, title);
      (p.background = p.background || []).push({ source: 'itinerario-vinciano', lang: 'en', url: `views/itinerario-vinciano.html#${sid}`, text: clean(`${r.th}: ${clean(r.td)}`), retrieved: DATE });
      continue;
    }
    // period and documentary anchors: claims on the residence events (or on the place when no event exists)
    for (const pt of parts(r.td)) {
      const [layer, grade, status] = pt.tier ? LAYER[pt.tier] : ['interpretation', undefined, 'pending'];
      const claim = { id: `iv${++cn}`, about: /period/i.test(r.th) ? 'period' : 'documentary_anchor', value: { text: pt.text }, layer, ...(grade ? { grade } : {}), status,
        statement: clean(`${pt.text}${pt.tier ? ' (Itinerario tier ' + pt.tier + ')' : ''}`), sources: [{ ref: 'src-itinerario-vinciano', loc: loc(r.th) }],
        check_in: pt.tier === 'A' || pt.tier === 'B' ? ['Villata 1999, the document named', 'Beltrami 1919'] : (pt.tier === 'D' ? ['Itinerario Vinciano, section XIII (contested points)'] : []) };
      if (evs.length) for (const ev of evs) { eventOut[ev] = eventOut[ev] || { id: ev, type: 'event', label: entities.get(ev)?.label || ev, claims: [] }; eventOut[ev].claims.push(Object.assign({}, claim, { id: `iv${++cn}` })); }
      else getPlace(gid, title).claims.push(claim);
    }
  }
  // the narrative paragraphs as background on the residence events
  const prose = [...body.matchAll(/<p>([\s\S]*?)<\/p>/g)].map((x) => clean(x[1])).filter(Boolean).join(' ');
  for (const ev of evs) if (prose) { eventOut[ev] = eventOut[ev] || { id: ev, type: 'event', label: entities.get(ev)?.label || ev, claims: [] }; (eventOut[ev].background = eventOut[ev].background || []).push({ source: 'itinerario-vinciano', lang: 'en', url: `views/itinerario-vinciano.html#${sid}`, text: prose.slice(0, 2400), retrieved: DATE }); }
}
// minor places on the map with their dated notes
const MINOR = { Pavia: 'geo-pavia', Vigevano: 'geo-vigevano', "Vaprio d'Adda": 'geo-vaprio-d-adda', Bologna: 'geo-bologna', Civitavecchia: 'geo-civitavecchia', Tours: 'geo-tours', Blois: 'geo-blois', Romorantin: 'geo-romorantin',
  Urbino: 'geo-urbino', Pesaro: 'geo-pesaro', Rimini: 'geo-rimini', Cesena: 'geo-cesena', Cesenatico: 'geo-cesenatico', Imola: 'geo-imola' };
for (const mm of it.matchAll(/<a href="#[a-z0-9]+" class="mapnode"[^>]*><title>([^<]+)<\/title>/g)) {
  const [name, note] = mm[1].split(' . ');
  const gid = MINOR[name]; if (!gid) continue;
  const p = getPlace(gid, name);
  if (note) p.claims.push({ id: `iv${++cn}`, about: 'leonardo_presence', value: { text: clean(note) }, layer: 'interpretation', status: 'pending', statement: clean(`The Itinerario Vinciano map marks ${name}: ${note}.`), sources: [{ ref: 'src-itinerario-vinciano', loc: 'map of stays (Carta dei soggiorni)' }], check_in: ['Villata 1999 or the dated autograph note concerned'] });
  if (!entities.has(gid)) (p.relations = p.relations || []);
}
// contested points (section XIII): disputed claims on the entities concerned
const notes = (it.match(/<section class="stage" id="notes">([\s\S]*?)<\/section>/) || [])[1] || '';
const NOTE_TARGET = { 'Patron saint of Piombino': 'geo-piombino', 'Patron saint of Amboise': 'geo-amboise', 'Dates of exhumation and translation': 'geo-saint-florentin-amboise', 'Arrival in Milan': 'pl-milan1', 'The mechanical lion': 'w-leonardo-s-mechanical-lion', 'Leonardo and Machiavelli': 'pe-machiavelli' };
let nNotes = 0;
for (const r of notes.matchAll(/<tr>\s*<td>([\s\S]*?)<\/td>\s*<td>([\s\S]*?)<\/td>\s*<\/tr>/g)) {
  const point = clean(r[1]); const target = NOTE_TARGET[point]; if (!target || !entities.has(target)) continue;
  const t = entities.get(target);
  const holder = t.type === 'place' ? getPlace(target, t.label) : (t.type === 'event' ? (eventOut[target] = eventOut[target] || { id: target, type: 'event', label: t.label, claims: [] }) : (placeOut[target] = placeOut[target] || { id: target, type: t.type, label: t.label, claims: [] }));
  holder.claims.push({ id: `iv${++cn}`, about: 'contested_point', value: { text: point }, layer: 'interpretation', status: 'disputed', statement: clean(`${point}: ${clean(r[2])}`), sources: [{ ref: 'src-itinerario-vinciano', loc: 'section XIII, Notes on contested and commonly misstated points' }], check_in: ['The documents and records named in the note'] });
  nNotes++;
}
for (const p of Object.values(placeOut)) emit(p);
for (const e of Object.values(eventOut)) emit(e);
console.log(`books ${nBooks}, itinerary stages ${nStage}, events enriched ${Object.keys(eventOut).length}, places ${Object.keys(placeOut).length}, contested notes ${nNotes} -> ${path.relative(ROOT, OUT)}`);
