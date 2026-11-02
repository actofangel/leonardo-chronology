#!/usr/bin/env node
// Merge research output (research/incoming/<batch>/*.json) into data/.
//
//   node scripts/merge-incoming.mjs research/incoming/paintings [more folders...]
//
// New ids become new files. For an existing id the merge is additive only:
// claims are appended (renumbered if their ids collide), relations and
// variants are added if new, empty fields are filled. Existing values,
// timeline and review blocks are never overwritten.
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { ROOT, FOLDERS, loadAll } from './lib.mjs';

const TYPE_FOLDER = Object.fromEntries(Object.entries(FOLDERS).map(([f, t]) => [t, f]));
const PROTECTED = new Set(['id', 'type', 'timeline', 'review', 'claims', 'relations', 'variants', 'open_questions']);
const dirs = process.argv.slice(2);
if (!dirs.length) { console.error('usage: merge-incoming.mjs <folder> [...]'); process.exit(2); }

const { entities, files } = loadAll();
let created = 0, merged = 0, claimsAdded = 0;
const log = [];

for (const dir of dirs) {
  for (const f of readdirSync(dir).filter((x) => x.endsWith('.json') && !x.startsWith('_')).sort()) {
    let inc;
    try { inc = JSON.parse(readFileSync(path.join(dir, f), 'utf8')); }
    catch (e) { log.push(`skip ${dir}/${f}: ${e.message}`); continue; }
    if (!inc.id) { log.push(`skip ${dir}/${f}: no id`); continue; }
    const cur = entities.get(inc.id);
    if (!cur) {
      if (inc.timeline === undefined) delete inc.timeline;
      delete inc.review;
      const folder = TYPE_FOLDER[inc.type];
      if (!folder) { log.push(`skip ${inc.id}: unknown type ${inc.type}`); continue; }
      mkdirSync(path.join(ROOT, 'data', folder), { recursive: true });
      const rel = `data/${folder}/${inc.id}.json`;
      writeFileSync(path.join(ROOT, rel), JSON.stringify(inc, null, 2) + '\n');
      entities.set(inc.id, inc); files.set(inc.id, rel);
      created++; claimsAdded += (inc.claims || []).length;
      continue;
    }
    // additive merge
    const e = cur;
    for (const [k, v] of Object.entries(inc)) {
      if (PROTECTED.has(k)) continue;
      if (e[k] === undefined || e[k] === '' || (Array.isArray(e[k]) && !e[k].length)) e[k] = v;
      else if (Array.isArray(e[k]) && Array.isArray(v)) { for (const x of v) if (!e[k].some((y) => JSON.stringify(y) === JSON.stringify(x))) e[k].push(x); }
      else if (JSON.stringify(e[k]) !== JSON.stringify(v)) log.push(`${e.id}: kept existing ${k}; incoming value differs (left in research/incoming)`);
    }
    if (inc.type && inc.type !== e.type) log.push(`${e.id}: incoming type ${inc.type} ignored, entity stays ${e.type}`);
    if (inc.label && inc.label !== e.label && !(e.variants || []).includes(inc.label)) (e.variants = e.variants || []).push(inc.label);
    for (const v of inc.variants || []) if (!(e.variants || []).includes(v) && v !== e.label) (e.variants = e.variants || []).push(v);
    // claims, with renumbering
    const used = new Set((e.claims || []).map((c) => c.id));
    let n = (e.claims || []).length;
    const map = {};
    for (const c of inc.claims || []) {
      let id = c.id;
      if (!id || used.has(id)) { do { n++; id = 'c' + n; } while (used.has(id)); }
      map[c.id] = id; used.add(id);
    }
    for (const c of inc.claims || []) {
      const copy = Object.assign({}, c, { id: map[c.id] });
      if (copy.alternative_to) copy.alternative_to = copy.alternative_to.map((a) => map[a] || a);
      (e.claims = e.claims || []).push(copy); claimsAdded++;
    }
    for (const r of inc.relations || []) {
      const rr = Object.assign({}, r); if (rr.claim) rr.claim = map[rr.claim] || rr.claim;
      if (!(e.relations || []).some((x) => x.rel === rr.rel && x.target === rr.target)) (e.relations = e.relations || []).push(rr);
    }
    for (const q of inc.open_questions || []) if (!(e.open_questions || []).includes(q)) (e.open_questions = e.open_questions || []).push(q);
    // keep timeline and review at the end of the file for readability
    const { timeline, review, ...rest } = e;
    const out = Object.assign(rest, timeline ? { timeline } : {}, review ? { review } : {});
    writeFileSync(path.join(ROOT, files.get(e.id)), JSON.stringify(out, null, 2) + '\n');
    entities.set(e.id, out);
    merged++;
  }
}
console.log(`Created ${created}, merged into ${merged} existing, ${claimsAdded} claims added.`);
log.forEach((l) => console.log('note: ' + l));
