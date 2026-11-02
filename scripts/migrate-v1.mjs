#!/usr/bin/env node
// One-off migration (kept for the audit trail): turns the single-file
// chronology (index.html + reviews.json + entities/people.json) into the
// one-file-per-entity database under data/, and the page into a template.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = process.cwd();
const html = readFileSync('index.html', 'utf8');
const A = html.indexOf('/* DATA PART 1'), B = html.indexOf('/* PLATFORM APP');
const ctx = {}; vm.createContext(ctx);
vm.runInContext(html.slice(A, B) + ';globalThis.o={ERAS,PLACES,WORKS,PEOPLE,EVENTS,POPES,HISTORY}', ctx);
const o = ctx.o;
const reviews = JSON.parse(readFileSync('reviews.json', 'utf8')).reviews;
const dossiers = JSON.parse(readFileSync('entities/people.json', 'utf8')).people;

const DRAFT = 'First chronology draft (Leonardo Chronology, 2026-10-09), entered from model recall.';
const LAYER = { D: 'fact', S: 'interpretation', T: 'interpretation' };
const GRADE = { D: 'fact', S: 'strong_interpretation', T: 'speculation' };
const WORK_SUB = { Painting: 'painting', Drawing: 'drawing', Engineering: 'engineering', Anatomy: 'anatomy' };

function write(dir, e) {
  mkdirSync(path.join('data', dir), { recursive: true });
  writeFileSync(path.join('data', dir, e.id + '.json'), JSON.stringify(e, null, 2) + '\n');
}

function entity(r, lane, type, subtype) {
  const tl = { lane, kind: r.kind, start: r.start };
  if (r.end !== undefined) tl.end = r.end;
  Object.assign(tl, { date: r.date, tier: r.tier, place: r.place, text: r.text, basis: r.basis });
  const e = { id: r.id, type };
  if (subtype) e.subtype = subtype;
  e.label = r.title;
  e.claims = [{
    id: 'c1', about: 'timeline',
    value: Object.assign({ text: r.date, start: r.start }, r.end !== undefined ? { end: r.end } : {}),
    layer: LAYER[r.tier], grade: GRADE[r.tier], status: 'pending',
    statement: r.text,
    sources: [{ type: 'model_recall', cite: `${DRAFT} Basis stated in the draft: ${r.basis}` }],
    check_in: []
  }];
  if (r.tier === 'T') e.claims[0].note = 'Evidence tier T: rests on later tradition.';
  e.timeline = tl;
  if (reviews[r.id]) e.review = reviews[r.id];
  return e;
}

const out = [];
o.PLACES.forEach((r) => out.push(['events', entity(r, 'places', 'event', 'residence')]));
o.WORKS.forEach((r) => {
  if (r.kind === 'Notebook') out.push(['manuscripts', entity(r, 'works', 'manuscript')]);
  else out.push(['works', entity(r, 'works', 'work', WORK_SUB[r.kind] || r.kind.toLowerCase())]);
});
o.PEOPLE.forEach((r) => out.push(['persons', entity(r, 'people', 'person')]));
o.EVENTS.forEach((r) => out.push(['events', entity(r, 'events', 'event')]));
o.POPES.forEach((r) => out.push(['persons', entity(r, 'popes', 'person', 'pope')]));
o.HISTORY.forEach((r) => out.push(['events', entity(r, 'history', 'event', 'context')]));

// Pilot dossiers: per-x -> pe-x
const ABOUT = { 'pac-1': 'residence', 'pac-2': 'work', 'pac-3': 'attribution', 'pac-4': 'relation',
  'mel-1': 'born', 'mel-2': 'relation', 'mel-3': 'identity', 'mel-4': 'content',
  'lor-1': 'relation', 'lor-2': 'relation', 'lor-3': 'relation',
  'tor-1': 'career', 'tor-2': 'died', 'tor-3': 'relation', 'tor-4': 'content',
  'sal-1': 'relation', 'sal-2': 'died', 'sal-3': 'provenance', 'sal-4': 'provenance' };
for (const d of dossiers) {
  const id = d.id.replace(/^per-/, 'pe-');
  const hit = out.find(([, e]) => e.id === id);
  if (!hit) throw new Error('no record for dossier ' + d.id);
  const e = hit[1];
  const ordered = { id: e.id, type: e.type, label: e.label, variants: d.variants, summary: d.summary,
    relations: d.records.filter((x) => x !== id).map((x) => ({ rel: 'appears_in', target: x })) };
  ordered.claims = e.claims.concat(d.claims.map((c) => {
    const { id: cid, text, ...rest } = c;
    return Object.assign({ id: cid, about: ABOUT[cid] || 'note' }, { layer: rest.layer, status: rest.status, statement: text },
      { sources: rest.sources, check_in: rest.check_in }, rest.bearing ? { bearing: rest.bearing } : {});
  }));
  ordered.timeline = e.timeline;
  if (e.review) ordered.review = e.review;
  ordered.open_questions = d.open_questions;
  hit[1] = ordered;
}

for (const [dir, e] of out) write(dir, e);
mkdirSync('data/views', { recursive: true });
writeFileSync('data/views/chronology.json', JSON.stringify({ schema: 'ldv-view-chronology/1', eras: o.ERAS }, null, 2) + '\n');

// Page template: data block replaced by a placeholder filled at build time.
mkdirSync('site', { recursive: true });
let tpl = html.slice(0, A) + '/*@@DATA@@*/\n\n' + html.slice(B);
tpl = tpl.replace("var ADMITTED = ['edition','catalogue','ms_study','monograph','archive_publication'];",
  "var ADMITTED = ['primary','edition','catalogue','ms_study','monograph','archive_publication'];");
tpl = tpl.replace("var SRC_LABEL = {", "var SRC_LABEL = {primary:'Primary object or manuscript', ");
writeFileSync('site/chronology.html', tpl);
console.log(`Wrote ${out.length} entities.`);
