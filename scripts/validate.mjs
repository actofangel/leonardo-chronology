#!/usr/bin/env node
// Validator for the Leonardo Chronology data.
//
// Reads the base records from index.html, plus reviews.json and extra.json,
// and enforces the update protocol stated on the page:
//   * record shape (id, title, dates, evidence tier, text, basis)
//   * reviews refer to existing records and use the allowed vocabulary
//   * "verified" requires at least one source of an admitted type
//   * history lines are append only (when --base <git ref> is given)
//   * notation: no dash characters in any data text
//
// Usage: node scripts/validate.mjs [--base <git ref>]
// Exit code 1 on any error. Warnings are printed but do not fail.

import { readFileSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const LANES = ['places', 'works', 'people', 'events', 'popes', 'history'];
const LANE_CONST = { places: 'PLACES', works: 'WORKS', people: 'PEOPLE', events: 'EVENTS', popes: 'POPES', history: 'HISTORY' };
const TIERS = ['D', 'S', 'T'];
const STATUSES = ['pending', 'verified', 'disputed', 'corrected', 'rejected'];
const ADMITTED = ['edition', 'catalogue', 'ms_study', 'monograph', 'archive_publication'];
const SOURCE_TYPES = [...ADMITTED, 'web', 'model_recall', 'other'];
const Y0 = 1450, Y1 = 1520;
// Hyphen-like and dash characters forbidden by the project notation rule.
// The plain ASCII hyphen inside words (e.g. "ldv-chronology") is allowed; a doubled one is not.
const DASHES = /[‐-―−⸺⸻﹘﹣－─-╿]|--/;

const errors = [], warnings = [];
const err = (m) => errors.push(m);
const warn = (m) => warnings.push(m);

function loadBase() {
  const html = readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const start = html.indexOf('/* DATA PART 1');
  const end = html.indexOf('/* PLATFORM APP');
  if (start < 0 || end < 0) throw new Error('Could not locate the data block in index.html');
  const code = html.slice(start, end) +
    '\n;globalThis.__out = {ERAS, PLACES, WORKS, PEOPLE, EVENTS, POPES, HISTORY};';
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  return ctx.__out;
}

function readJSON(name, text) {
  try { return JSON.parse(text ?? readFileSync(path.join(ROOT, name), 'utf8')); }
  catch (e) { err(`${name}: cannot parse (${e.message})`); return null; }
}

function checkText(where, value) {
  if (typeof value === 'string') {
    if (DASHES.test(value)) err(`${where}: contains a dash character: ${JSON.stringify(value.slice(0, 80))}`);
  } else if (Array.isArray(value)) value.forEach((v, i) => checkText(`${where}[${i}]`, v));
  else if (value && typeof value === 'object') for (const [k, v] of Object.entries(value)) {
    if (k === 'url') continue;
    checkText(`${where}.${k}`, v);
  }
}

function checkRecord(r, where) {
  for (const f of ['id', 'title', 'date', 'text', 'basis']) {
    if (typeof r[f] !== 'string' || !r[f].trim()) err(`${where}: missing field "${f}"`);
  }
  if (typeof r.start !== 'number' || r.start < Y0 || r.start > Y1) err(`${where}: start must be a number between ${Y0} and ${Y1}`);
  if (r.end !== undefined && (typeof r.end !== 'number' || r.end < r.start)) err(`${where}: end must be a number not before start`);
  if (!TIERS.includes(r.tier)) err(`${where}: tier must be one of ${TIERS.join(', ')}`);
  for (const f of ['status', 'flags', 'sources', 'history']) {
    if (f in r) err(`${where}: "${f}" belongs in reviews.json, not on the record`);
  }
  checkText(where, r);
}

// ---------- base records ----------
let base;
try { base = loadBase(); } catch (e) { err(e.message); }
const ids = new Map();
if (base) {
  base.ERAS.forEach((e, i) => checkText(`ERAS[${i}]`, e));
  for (const lane of LANES) {
    base[LANE_CONST[lane]].forEach((r, i) => {
      const where = `${lane}/${r.id ?? '#' + i}`;
      checkRecord(r, where);
      if (ids.has(r.id)) err(`${where}: duplicate id (also in ${ids.get(r.id)})`);
      ids.set(r.id, lane);
    });
  }
}

// ---------- extra.json ----------
const extra = readJSON('extra.json');
if (extra) {
  if (extra.schema !== 'ldv-chronology-extra/1') err('extra.json: schema must be "ldv-chronology-extra/1"');
  if (!Array.isArray(extra.records)) err('extra.json: records must be an array');
  else extra.records.forEach((r, i) => {
    const where = `extra.json/${r.id ?? '#' + i}`;
    if (!LANES.includes(r.lane)) err(`${where}: unknown lane "${r.lane}"`);
    checkRecord(r, where);
    if (ids.has(r.id)) err(`${where}: duplicate id (also in ${ids.get(r.id)})`);
    ids.set(r.id, 'extra');
  });
}

// ---------- reviews.json ----------
const reviews = readJSON('reviews.json');
const counts = Object.fromEntries(STATUSES.map((s) => [s, 0]));
if (reviews) {
  if (reviews.schema !== 'ldv-chronology-reviews/1') err('reviews.json: schema must be "ldv-chronology-reviews/1"');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(reviews.updated ?? '')) err('reviews.json: updated must be YYYY-MM-DD');
  for (const [id, rv] of Object.entries(reviews.reviews ?? {})) {
    const where = `reviews.json/${id}`;
    if (!ids.has(id)) err(`${where}: no record with this id`);
    const status = rv.status ?? 'pending';
    if (!STATUSES.includes(status)) { err(`${where}: unknown status "${status}"`); continue; }
    counts[status]++;
    const sources = rv.sources ?? [];
    sources.forEach((s, i) => {
      if (!SOURCE_TYPES.includes(s.type)) err(`${where}.sources[${i}]: unknown type "${s.type}"`);
      if (typeof s.cite !== 'string' || !s.cite.trim()) err(`${where}.sources[${i}]: cite is required`);
    });
    const admitted = sources.some((s) => ADMITTED.includes(s.type));
    if (status === 'verified' && !admitted) err(`${where}: verified without a source of an admitted type`);
    if (status === 'corrected' && !(rv.history ?? []).length) err(`${where}: corrected needs a history line saying what changed`);
    if (status === 'disputed' && !(rv.flags ?? []).length && !rv.proposed) warn(`${where}: disputed with neither flags nor a proposed change`);
    (rv.history ?? []).forEach((h, i) => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(h.at ?? '') || !h.by || !h.note) err(`${where}.history[${i}]: needs at (YYYY-MM-DD), by and note`);
    });
    checkText(where, rv);
  }
}

// ---------- append-only history ----------
const baseIdx = process.argv.indexOf('--base');
if (baseIdx > 0 && reviews) {
  const ref = process.argv[baseIdx + 1];
  let old = null;
  try { old = JSON.parse(execFileSync('git', ['show', `${ref}:reviews.json`], { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })); }
  catch { warn(`append-only check skipped: reviews.json not found at ${ref}`); }
  if (old) for (const [id, prev] of Object.entries(old.reviews ?? {})) {
    const before = prev.history ?? [];
    const now = reviews.reviews?.[id]?.history ?? [];
    const kept = before.every((h, i) => JSON.stringify(h) === JSON.stringify(now[i]));
    if (!kept) err(`reviews.json/${id}: history lines were edited or removed since ${ref} (history is append only)`);
  }
}

// ---------- entities/*.json (research dossiers) ----------
const CLAIM_LAYERS = ['fact', 'interpretation', 'hypothesis'];
const CLAIM_STATUSES = ['pending', 'verified', 'disputed', 'rejected'];
const ENTITY_FILES = { 'entities/people.json': ['ldv-entities-people/1', 'people'] };
for (const [file, [schema, key]] of Object.entries(ENTITY_FILES)) {
  let text;
  try { text = readFileSync(path.join(ROOT, file), 'utf8'); } catch { continue; }
  const doc = readJSON(file, text);
  if (!doc) continue;
  if (doc.schema !== schema) err(`${file}: schema must be "${schema}"`);
  const seen = new Set();
  (doc[key] ?? []).forEach((e, i) => {
    const where = `${file}/${e.id ?? '#' + i}`;
    if (!e.id || !e.name) err(`${where}: id and name are required`);
    if (seen.has(e.id)) err(`${where}: duplicate entity id`);
    seen.add(e.id);
    (e.records ?? []).forEach((r) => { if (!ids.has(r)) err(`${where}: links to unknown record "${r}"`); });
    const claimIds = new Set();
    (e.claims ?? []).forEach((c, j) => {
      const cw = `${where}.claims[${c.id ?? j}]`;
      if (!c.id || claimIds.has(c.id)) err(`${cw}: claim id missing or duplicated`);
      claimIds.add(c.id);
      if (!CLAIM_LAYERS.includes(c.layer)) err(`${cw}: layer must be one of ${CLAIM_LAYERS.join(', ')}`);
      if (!CLAIM_STATUSES.includes(c.status)) err(`${cw}: status must be one of ${CLAIM_STATUSES.join(', ')}`);
      if (!Array.isArray(c.sources) || !c.sources.length) err(`${cw}: at least one source is required`);
      (c.sources ?? []).forEach((s, k) => {
        if (!SOURCE_TYPES.includes(s.type)) err(`${cw}.sources[${k}]: unknown type "${s.type}"`);
        if (!s.cite) err(`${cw}.sources[${k}]: cite is required`);
      });
      if (c.status === 'verified' && !(c.sources ?? []).some((s) => ADMITTED.includes(s.type))) err(`${cw}: verified without a source of an admitted type`);
    });
    checkText(where, e);
  });
}

// ---------- research/*.patch.json (unapplied review patches) ----------

let patchFiles = [];
try { patchFiles = readdirSync(path.join(ROOT, 'research')).filter((f) => f.endsWith('.patch.json')); } catch {}
for (const f of patchFiles) {
  const file = `research/${f}`;
  const doc = readJSON(file);
  if (!doc) continue;
  for (const [id, rv] of Object.entries(doc.reviews ?? {})) {
    const where = `${file}/${id}`;
    if (!ids.has(id)) err(`${where}: no record with this id`);
    if (rv.status && !STATUSES.includes(rv.status)) err(`${where}: unknown status "${rv.status}"`);
    if (rv.status === 'verified' && !(rv.sources ?? []).some((s) => ADMITTED.includes(s.type))) err(`${where}: verified without a source of an admitted type`);
    const existing = reviews?.reviews?.[id]?.flags ?? [];
    if (rv.flags && !existing.every((x) => rv.flags.includes(x))) warn(`${where}: flags replace the current list and would drop an existing flag`);
    checkText(where, rv);
  }
}

// ---------- report ----------
const total = ids.size;
const reviewed = Object.keys(reviews?.reviews ?? {}).length;
console.log(`Records: ${total} (base and extra). Review entries: ${reviewed}.`);
console.log('By review status: ' + STATUSES.map((s) => `${s} ${counts[s]}`).join(', ') + `, no review entry ${total - reviewed}.`);
warnings.forEach((w) => console.log('warning: ' + w));
errors.forEach((e) => console.log('error: ' + e));
console.log(errors.length ? `FAILED with ${errors.length} error(s).` : 'OK');
process.exit(errors.length ? 1 : 0);
