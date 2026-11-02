#!/usr/bin/env node
// Validator for the Leonardo database (data/, ldv-entity/1). See SCHEMA.md.
//
//   node scripts/validate.mjs                 validate the working tree
//   node scripts/validate.mjs --base <ref>    also check append-only history against a git ref
//   node scripts/validate.mjs --strict        treat warnings as errors
//
// Exit code 1 on any error.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import {
  ROOT, FOLDERS, LANES, TIERS, REVIEW_STATUSES, CLAIM_STATUSES, LAYERS, GRADES,
  ADMITTED, SOURCE_TYPES, loadAll, loadView, isAdmitted, sourceType
} from './lib.mjs';

const errors = [], warnings = [];
const err = (m) => errors.push(m), warn = (m) => warnings.push(m);
const Y0 = 1450, Y1 = 1520;
const ID = /^[a-z][a-z0-9]*(-[a-z0-9]+)*$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;
// Dash characters forbidden by the project notation rule; ASCII hyphen inside words is allowed, a doubled one is not.
const DASHES = /[‐-―−⸺⸻﹘﹣－─-╿]|--/;
const SKIP_TEXT = new Set(['url', 'id', 'target', 'ref', 'from']);

function checkText(where, v, key) {
  if (SKIP_TEXT.has(key)) return;
  if (typeof v === 'string') { if (DASHES.test(v)) err(`${where}: dash character in ${JSON.stringify(v.slice(0, 70))}`); }
  else if (Array.isArray(v)) v.forEach((x, i) => checkText(`${where}[${i}]`, x));
  else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) checkText(`${where}.${k}`, x, k);
}

const { entities, files, problems } = loadAll();
problems.forEach(err);

const SOURCE_FIELD_TYPES = new Set([...SOURCE_TYPES]);
for (const [id, e] of entities) {
  const file = files.get(id);
  const where = file;
  const folder = file.split('/')[1];
  if (path.basename(file, '.json') !== e.id) err(`${where}: file name must equal id "${e.id}"`);
  if (!ID.test(e.id || '')) err(`${where}: id must be lowercase words joined by single hyphens`);
  if (e.type !== FOLDERS[folder]) err(`${where}: type "${e.type}" does not belong in data/${folder}/`);
  if (typeof e.label !== 'string' || !e.label.trim()) err(`${where}: label is required`);

  // relations
  for (const [i, r] of (e.relations || []).entries()) {
    if (!r.rel || !r.target) err(`${where}.relations[${i}]: rel and target are required`);
    else if (!entities.has(r.target)) warn(`${where}.relations[${i}]: target "${r.target}" does not exist yet`);
    if (r.claim && !(e.claims || []).some((c) => c.id === r.claim)) err(`${where}.relations[${i}]: claim "${r.claim}" not found on this entity`);
  }

  // claims
  const cids = new Set();
  for (const [i, c] of (e.claims || []).entries()) {
    const cw = `${where}#${c.id ?? i}`;
    if (!c.id || cids.has(c.id)) err(`${cw}: claim id missing or duplicated`);
    cids.add(c.id);
    if (!c.about) err(`${cw}: about is required`);
    if (!LAYERS.includes(c.layer)) err(`${cw}: layer must be one of ${LAYERS.join(', ')}`);
    if (c.grade && !GRADES.includes(c.grade)) err(`${cw}: unknown grade "${c.grade}"`);
    if (!CLAIM_STATUSES.includes(c.status)) err(`${cw}: status must be one of ${CLAIM_STATUSES.join(', ')}`);
    if (!Array.isArray(c.sources) || !c.sources.length) err(`${cw}: at least one source is required`);
    for (const [k, s] of (c.sources || []).entries()) {
      if (s.ref) { if (!entities.has(s.ref)) warn(`${cw}.sources[${k}]: source "${s.ref}" does not exist yet`); else if (entities.get(s.ref).type !== 'source') err(`${cw}.sources[${k}]: "${s.ref}" is not a source entity`); }
      else {
        if (!SOURCE_FIELD_TYPES.has(s.type)) err(`${cw}.sources[${k}]: unknown type "${s.type}"`);
        if (!s.cite) err(`${cw}.sources[${k}]: cite is required`);
        if (s.type === 'primary' && !s.url && !/f\.|fol|RL|inv|folio/i.test(s.cite || '')) warn(`${cw}.sources[${k}]: primary source without folio, inventory or url`);
      }
    }
    if (c.status === 'verified' && !isAdmitted(c, entities)) err(`${cw}: verified without a source of an admitted type`);
    if (c.layer === 'hypothesis' && c.grade === 'fact') err(`${cw}: a hypothesis claim cannot have grade fact`);
    for (const a of c.alternative_to || []) if (!cids.has(a) && !(e.claims || []).some((x) => x.id === a)) err(`${cw}: alternative_to "${a}" not found`);
  }
  if (e.layer === 'hypothesis') err(`${where}: layer belongs on claims, not on the entity`);

  // type specific
  if (e.type === 'source') {
    if (!SOURCE_TYPES.includes(e.source_type)) err(`${where}: source_type must be one of ${SOURCE_TYPES.join(', ')}`);
    if (!e.citation) err(`${where}: citation is required`);
  }
  if (e.type === 'place' && e.coords) {
    const { lat, lon } = e.coords;
    if (typeof lat !== 'number' || typeof lon !== 'number' || Math.abs(lat) > 90 || Math.abs(lon) > 180) err(`${where}: coords must be numeric lat and lon`);
  }
  if (e.type === 'hypothesis') {
    if (!['working_hypothesis', 'speculation'].includes(e.status)) err(`${where}: hypothesis status must be working_hypothesis or speculation`);
    if (!e.statement) err(`${where}: statement is required`);
    if (!Array.isArray(e.falsified_if) || !e.falsified_if.length) err(`${where}: falsified_if must list at least one condition`);
    for (const ref of e.assumes || []) {
      const [eid, cid] = ref.split('#');
      if (!entities.has(eid) || !(entities.get(eid).claims || []).some((c) => c.id === cid)) err(`${where}: assumes "${ref}", which does not exist`);
    }
  }

  // timeline
  if (e.timeline) {
    const t = e.timeline, tw = `${where}.timeline`;
    if (!LANES.includes(t.lane)) err(`${tw}: unknown lane "${t.lane}"`);
    for (const f of ['kind', 'date', 'text', 'basis', 'place']) if (typeof t[f] !== 'string' || !t[f].trim()) err(`${tw}: ${f} is required`);
    if (typeof t.start !== 'number' || t.start < Y0 || t.start > Y1) err(`${tw}: start must be a number between ${Y0} and ${Y1}`);
    if (t.end !== undefined && (typeof t.end !== 'number' || t.end < t.start)) err(`${tw}: end must not be before start`);
    if (!TIERS.includes(t.tier)) err(`${tw}: tier must be one of ${TIERS.join(', ')}`);
  }

  // review
  if (e.review) {
    const rv = e.review, rw = `${where}.review`, st = rv.status ?? 'pending';
    if (!REVIEW_STATUSES.includes(st)) err(`${rw}: unknown status "${st}"`);
    const admitted = (rv.sources || []).some((s) => ADMITTED.includes(s.ref ? sourceType(s, entities) : s.type));
    if (st === 'verified' && !admitted) err(`${rw}: verified without a source of an admitted type`);
    if (st === 'corrected' && !(rv.history || []).length) err(`${rw}: corrected needs a history line`);
    for (const [i, h] of (rv.history || []).entries()) if (!DATE.test(h.at || '') || !h.by || !h.note) err(`${rw}.history[${i}]: needs at (YYYY-MM-DD), by and note`);
    if (!e.timeline) warn(`${rw}: review without a timeline block has no effect on the chronology`);
  }

  checkText(where, e);
}

// view
try { loadView().eras.forEach((x, i) => checkText(`data/views/chronology.json eras[${i}]`, x)); }
catch (e) { err(`data/views/chronology.json: ${e.message}`); }

// research patches
const rdir = path.join(ROOT, 'research');
for (const f of existsSync(rdir) ? readdirSync(rdir).filter((x) => x.endsWith('.patch.json')) : []) {
  let doc; try { doc = JSON.parse(readFileSync(path.join(rdir, f), 'utf8')); } catch (e) { err(`research/${f}: ${e.message}`); continue; }
  for (const [id, rv] of Object.entries(doc.reviews || {})) {
    const w = `research/${f}/${id}`;
    if (!entities.has(id)) { err(`${w}: no entity with this id`); continue; }
    if (rv.status === 'verified' && !(rv.sources || []).some((s) => ADMITTED.includes(s.type))) err(`${w}: verified without an admitted source`);
    const existing = entities.get(id).review?.flags || [];
    if (rv.flags && !existing.every((x) => rv.flags.includes(x))) warn(`${w}: flags replace the current list and would drop an existing flag`);
    checkText(w, rv);
  }
}

// append-only history against a git ref
const bi = process.argv.indexOf('--base');
if (bi > 0) {
  const ref = process.argv[bi + 1];
  for (const [id, e] of entities) {
    let old;
    try { old = JSON.parse(execFileSync('git', ['show', `${ref}:${files.get(id)}`], { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })); }
    catch { continue; }
    const before = old.review?.history || [], now = e.review?.history || [];
    if (!before.every((h, i) => JSON.stringify(h) === JSON.stringify(now[i]))) err(`${files.get(id)}: review history edited or removed since ${ref} (append only)`);
    for (const oc of old.claims || []) {
      const nc = (e.claims || []).find((c) => c.id === oc.id);
      if (!nc) err(`${files.get(id)}#${oc.id}: claim removed since ${ref}. Set status "rejected" instead of deleting`);
    }
  }
}

// report
const byType = {};
let claims = 0, verified = 0;
for (const e of entities.values()) { byType[e.type] = (byType[e.type] || 0) + 1; for (const c of e.claims || []) { claims++; if (c.status === 'verified') verified++; } }
console.log(`Entities: ${entities.size} (${Object.entries(byType).map(([k, v]) => `${k} ${v}`).join(', ')}). Claims: ${claims}, verified ${verified}.`);
const MAXW = 40;
warnings.slice(0, MAXW).forEach((w) => console.log('warning: ' + w));
if (warnings.length > MAXW) console.log(`warning: ... and ${warnings.length - MAXW} more`);
errors.forEach((e) => console.log('error: ' + e));
const strict = process.argv.includes('--strict');
const fail = errors.length || (strict && warnings.length);
console.log(fail ? `FAILED with ${errors.length} error(s)${strict ? ` and ${warnings.length} warning(s)` : ''}.` : `OK (${warnings.length} warning(s)).`);
process.exit(fail ? 1 : 0);
