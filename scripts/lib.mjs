// Shared loading and precedence logic for build and validate.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const DATA = path.join(ROOT, 'data');

export const FOLDERS = {
  persons: 'person', places: 'place', works: 'work', manuscripts: 'manuscript',
  events: 'event', sources: 'source', hypotheses: 'hypothesis', books: 'book'
};
export const LANES = ['places', 'works', 'people', 'events', 'popes', 'history'];
export const LANE_CONST = { places: 'PLACES', works: 'WORKS', people: 'PEOPLE', events: 'EVENTS', popes: 'POPES', history: 'HISTORY' };
export const TIERS = ['D', 'S', 'T'];
export const REVIEW_STATUSES = ['pending', 'verified', 'disputed', 'corrected', 'rejected'];
export const CLAIM_STATUSES = ['pending', 'verified', 'disputed', 'rejected'];
export const LAYERS = ['fact', 'interpretation', 'hypothesis'];
export const GRADES = ['fact', 'strong_interpretation', 'working_hypothesis', 'speculation'];
export const ADMITTED = ['primary', 'edition', 'catalogue', 'ms_study', 'monograph', 'archive_publication'];
export const SOURCE_TYPES = [...ADMITTED, 'narrative', 'other', 'web', 'model_recall'];
export const SOURCE_RANK = { primary: 7, edition: 7, archive_publication: 7, catalogue: 6, ms_study: 6, monograph: 5, narrative: 4, other: 3, web: 2, model_recall: 1 };
const STATUS_RANK = { verified: 3, pending: 2, disputed: 1, rejected: 0 };
const LAYER_RANK = { fact: 3, interpretation: 2, hypothesis: 1 };

/** Load every entity under data/. Returns { entities: Map(id -> entity), files: Map(id -> relpath), problems: [] } */
export function loadAll(dataDir = DATA) {
  const entities = new Map(), files = new Map(), problems = [];
  for (const folder of Object.keys(FOLDERS)) {
    const dir = path.join(dataDir, folder);
    if (!existsSync(dir)) continue;
    for (const f of readdirSync(dir).filter((x) => x.endsWith('.json')).sort()) {
      const rel = `data/${folder}/${f}`;
      let e;
      try { e = JSON.parse(readFileSync(path.join(dir, f), 'utf8')); }
      catch (err) { problems.push(`${rel}: cannot parse (${err.message})`); continue; }
      if (entities.has(e.id)) { problems.push(`${rel}: duplicate id ${e.id} (also ${files.get(e.id)})`); continue; }
      entities.set(e.id, e); files.set(e.id, rel);
    }
  }
  return { entities, files, problems };
}

export function loadVocab() {
  return JSON.parse(readFileSync(path.join(DATA, 'vocab', 'classification.json'), 'utf8'));
}

export function loadView() {
  return JSON.parse(readFileSync(path.join(DATA, 'views', 'chronology.json'), 'utf8'));
}

/** Resolve a source reference to its effective type. */
export function sourceType(s, entities) {
  if (s.ref) { const src = entities.get(s.ref); return src ? src.source_type : undefined; }
  return s.type;
}

export function bestSourceRank(claim, entities) {
  return Math.max(0, ...(claim.sources || []).map((s) => SOURCE_RANK[sourceType(s, entities)] || 0));
}

/** A source counts as admitted only if its type is admitted and, for a reference, a real locator is given. */
export function admittedSource(s, entities) {
  if (!ADMITTED.includes(sourceType(s, entities))) return false;
  // Every admitted source needs a real locator: page, document number, folio, catalogue or inventory number.
  return typeof s.loc === 'string' && s.loc.trim() !== '' && !/locate|confirm|unknown|\?/i.test(s.loc);
}

export function isAdmitted(claim, entities) {
  return (claim.sources || []).some((s) => admittedSource(s, entities));
}

/**
 * Precedence: pick one claim per `about` key. `forced` is a Set of "entity#claim"
 * refs assumed by an active scenario; forced claims win outright.
 */
export function resolve(entity, entities, forced = new Set()) {
  const groups = {};
  (entity.claims || []).forEach((c, i) => { (groups[c.about] = groups[c.about] || []).push([c, i]); });
  const resolved = {};
  for (const [about, list] of Object.entries(groups)) {
    const ranked = list
      .filter(([c]) => c.status !== 'rejected' || forced.has(`${entity.id}#${c.id}`))
      .map(([c, i]) => ({
        c, key: [
          forced.has(`${entity.id}#${c.id}`) ? 1 : 0,
          c.layer === 'hypothesis' && !forced.has(`${entity.id}#${c.id}`) ? 0 : 1,
          STATUS_RANK[c.status] ?? 0, LAYER_RANK[c.layer] ?? 0, bestSourceRank(c, entities), -i
        ]
      }))
      .sort((a, b) => { for (let k = 0; k < a.key.length; k++) if (a.key[k] !== b.key[k]) return b.key[k] - a.key[k]; return 0; });
    if (!ranked.length) continue;
    resolved[about] = { claim: ranked[0].c.id, alternatives: ranked.slice(1).map((r) => r.c.id), forced: ranked[0].key[0] === 1 };
  }
  return resolved;
}
