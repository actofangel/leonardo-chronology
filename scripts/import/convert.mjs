#!/usr/bin/env node
// Convert raw API records (research/api/raw/) into ldv-entity files under
// research/incoming/api-<date>/, matched against existing entities.
//
//   node scripts/import/convert.mjs [--date 2026-11-02] [--map research/api/match-overrides.json]
//
// Every value taken from an external record becomes a claim whose source is
// that record (type "other" for museum APIs, "web" for Wikidata and
// Wikipedia), status "pending". Nothing is verified by this script.
// Output also includes research/api/match-report.md for human review.
import { readFileSync, writeFileSync, mkdirSync, existsSync, rmSync } from 'node:fs';
import path from 'node:path';
import { ROOT, loadAll } from '../lib.mjs';

const arg = (n, d) => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : d; };
const DATE = arg('--date', new Date().toISOString().slice(0, 10));
const RAW = path.join(ROOT, 'research', 'api', 'raw');
const OUT = path.join(ROOT, 'research', 'incoming', `api-${DATE}`);
const readRaw = (f) => existsSync(path.join(RAW, f)) ? JSON.parse(readFileSync(path.join(RAW, f), 'utf8')) : null;
const wd = readRaw('wikidata.json'), met = readRaw('met.json'), louvre = readRaw('louvre.json'), wiki = readRaw('wikipedia.json'), rct = readRaw('rct.json');
const overridesPath = arg('--map', path.join(ROOT, 'research', 'api', 'match-overrides.json'));
const overrides = existsSync(overridesPath) ? JSON.parse(readFileSync(overridesPath, 'utf8')) : {};

const { entities } = loadAll();
// Clean dash characters out of imported text (project notation rule).
const clean = (s) => s == null ? s : String(s).replace(/\s*[–—―]\s*/g, (m) => (/\d\s*[–]\s*\d/.test(m) ? ' to ' : ', ')).replace(/(\d)\s*[‐-―−]\s*(\d)/g, '$1 to $2').replace(/[‐-―−]/g, ' ').replace(/--+/g, ', ').replace(/\s+/g, ' ').trim();
const slug = (s) => clean(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').split('-').slice(0, 6).join('-');
const norm = (s) => slug(s || '').replace(/-/g, ' ');

// ---------- index of existing entities ----------
const byIdent = {}, byLabel = {};
for (const e of entities.values()) {
  if (!['work', 'manuscript'].includes(e.type)) continue;
  for (const [k, v] of Object.entries(e.identifiers || {})) byIdent[`${k}:${v}`] = e.id;
  if (e.inventory) byIdent[`inventory:${String(e.inventory).toLowerCase()}`] = e.id;
  const m = e.id.match(/(9\d{5})$/); if (m) byIdent[`rcin:${m[1]}`] = e.id;
  for (const l of [e.label, ...(e.variants || [])]) if (l) (byLabel[norm(l)] = byLabel[norm(l)] || new Set()).add(e.id);
}

// ---------- vocab mapping ----------
const L = (q) => (wd && wd.labels[q]) || q;
const FORM = [[/fresco|mural|wall painting/, 'mural'], [/cartoon/, 'cartoon'], [/sketch/, 'sketch'], [/study/, 'study'], [/map/, 'map'], [/painting|panel painting/, 'painting'],
  [/manuscript|codex|notebook/, 'MS'], [/sculpture|equestrian statue|monument/, 'sculpture_project'], [/architectur/, 'architectural_drawing'], [/drawing|print|artwork/, 'drawing']];
const TECH = [[/oil/, 'oil'], [/tempera/, 'tempera'], [/red chalk|sanguine/, 'red_chalk'], [/black chalk/, 'black_chalk'], [/charcoal/, 'charcoal'], [/metalpoint|silverpoint|silver point|leadpoint/, 'metalpoint'],
  [/\bink\b|\bpen\b|iron gall/, 'pen_and_ink'], [/wash|watercolou?r|bistre/, 'wash'], [/white (heighten|gouache|lead)|lead white|bodycolou?r/, 'white_heightening'], [/stylus/, 'stylus'], [/pricked|pouncing/, 'pricking']];
const SUPPORT = [[/poplar/, 'panel_poplar'], [/walnut/, 'panel_walnut'], [/blue.*paper|paper.*blue/, 'blue_paper'], [/prepared paper|coloured ground|tinted paper|grounded paper/, 'prepared_paper'], [/canvas/, 'canvas'], [/parchment|vellum/, 'parchment'], [/plaster|wall/, 'wall'], [/paper/, 'paper'], [/panel|wood/, 'panel']];
const SUBJ = [[/portrait/, 'portrait'], [/virgin|madonna|christ|saint|annunciation|adoration|apostle|religious|biblical|jerome|john the baptist|last supper|nativity/, 'religious'], [/leda|myth|allegor/, 'mythology'],
  [/anatom|skull|heart|muscle|skeleton|fo?etus|uterus|vessel/, 'anatomy'], [/horse/, 'horse'], [/landscape/, 'landscape'], [/plant|flower|botan|tree/, 'botany'], [/map/, 'cartography'], [/machine|mechan/, 'mechanics'],
  [/flying|flight|wing/, 'flight'], [/weapon|military|cannon|fortif/, 'military'], [/grotesque|caricature|head/, 'head'], [/deluge|storm|flood/, 'deluge'], [/water|river|canal/, 'water'], [/architect|church|palace|building/, 'architecture'], [/battle/, 'battle'], [/drapery|figure|nude/, 'figure']];
const first = (rules, text) => { for (const [re, v] of rules) if (re.test(text)) return v; return null; };
const all = (rules, text) => [...new Set(rules.filter(([re]) => re.test(text)).map(([, v]) => v))];

// ---------- helpers for Wikidata ----------
const claimsOf = (e, p) => e.claims?.[p] || [];
const val = (c) => c.mainsnak?.datavalue?.value;
const itemLabels = (e, p) => claimsOf(e, p).map(val).filter((v) => v && v.id).map((v) => L(v.id));
function wdTime(v) {
  if (!v || !v.time) return null;
  const y = parseInt(v.time.slice(1, 5), 10), prec = v.precision;
  const text = prec >= 11 ? v.time.slice(1, 11) : prec === 10 ? v.time.slice(1, 8) : prec === 9 ? String(y) : prec === 8 ? `${Math.floor(y / 10) * 10}s` : prec === 7 ? `${Math.ceil(y / 100)}th century` : String(y);
  return { y, text, prec };
}
function wdDate(c) {
  const v = val(c); const t = wdTime(v); if (!t) return null;
  const q = c.qualifiers || {};
  const qt = (p) => (q[p] || []).map((s) => wdTime(s.datavalue?.value)).find(Boolean);
  const start = qt('P1319') || qt('P580'), end = qt('P1326') || qt('P582');
  const circa = (q.P1480 || []).some((s) => /circa|approximately/i.test(L(s.datavalue?.value?.id)));
  const value = { text: (circa ? 'c.' : '') + (start && end ? `${start.y} to ${end.y}` : t.text), start: start ? start.y : t.y };
  if (end) value.end = end.y;
  return value;
}
const qty = (c) => { const v = val(c); if (!v || v.amount === undefined) return null; const u = v.unit && v.unit.includes('/entity/') ? L(v.unit.split('/').pop()) : ''; return `${Number(v.amount)} ${u.replace('centimetre', 'cm').replace('millimetre', 'mm')}`.trim(); };
function extIds(e, re) { const out = []; for (const [p, cl] of Object.entries(e.claims || {})) if (re.test(L(p))) for (const c of cl) { const v = val(c); if (typeof v === 'string') out.push(v); } return out; }

// ---------- build incoming entities ----------
if (existsSync(OUT)) rmSync(OUT, { recursive: true });
mkdirSync(OUT, { recursive: true });
const report = { matched: [], created: [], ambiguous: [], skipped: [] };
const taken = new Set(entities.keys());
const created = {};

function match(keys, labels) {
  for (const k of keys) if (byIdent[k]) return { id: byIdent[k], how: k };
  const cands = new Set();
  for (const l of labels) for (const id of byLabel[norm(l)] || []) cands.add(id);
  if (cands.size === 1) return { id: [...cands][0], how: 'label' };
  if (cands.size > 1) return { ambiguous: [...cands] };
  return null;
}
function newId(prefix, label, num) {
  let base = `${prefix}-${slug(label) || 'untitled'}${num ? '-' + num : ''}`;
  base = base.replace(/-+/g, '-').slice(0, 70).replace(/-$/, '');
  let id = base, n = 2; while (taken.has(id)) id = `${base}-${n++}`;
  taken.add(id); return id;
}
function emit(e) { writeFileSync(path.join(OUT, e.id + '.json'), JSON.stringify(e, null, 2) + '\n'); }

let cn = 0;
const C = (about, value, layer, statement, source, extra = {}) => ({ id: `api${++cn}`, about, ...(value !== undefined ? { value } : {}), layer, status: 'pending', statement: clean(statement), sources: [source], ...extra });

// Wikidata items
for (const [qid, e] of Object.entries(wd?.entities || {})) {
  if (e.missing !== undefined) continue;
  const label = clean(e.labels?.en?.value || e.labels?.it?.value || e.labels?.fr?.value || qid);
  const inst = itemLabels(e, 'P31').join('; ').toLowerCase();
  const genre = itemLabels(e, 'P136').concat(itemLabels(e, 'P180'), itemLabels(e, 'P921')).join('; ').toLowerCase();
  const materials = itemLabels(e, 'P186').join('; ').toLowerCase();
  const collections = claimsOf(e, 'P195').map((c) => L(val(c)?.id)).filter(Boolean);
  const invs = claimsOf(e, 'P217').map((c) => ({ v: val(c), coll: (c.qualifiers?.P195 || []).map((s) => L(s.datavalue?.value?.id))[0] })).filter((x) => typeof x.v === 'string');
  const rcins = [...new Set(extIds(e, /royal collection/i).concat(invs.filter((x) => /^(RCIN )?9\d{5}$/.test(x.v)).map((x) => x.v.replace('RCIN ', ''))))];
  const arks = extIds(e, /louvre/i).map((v) => (String(v).match(/cl\d{9}/) || [])[0]).filter(Boolean);
  const metIds = extIds(e, /metropolitan museum/i);
  const formRaw = first(FORM, inst + ' ' + genre);
  const isMs = formRaw === 'MS';
  if (/^(collection|series|group of|set of)/.test(inst)) { report.skipped.push(`${qid} ${label} (${inst})`); continue; }

  const ov = overrides[qid];
  const keys = [`wikidata:${qid}`, ...rcins.map((r) => `rcin:${r}`), ...arks.map((a) => `louvre_ark:${a}`), ...metIds.map((m) => `met:${m}`), ...invs.map((x) => `inventory:${x.v.toLowerCase()}`)];
  const labels = [label, ...(e.aliases?.en || []).map((a) => a.value)];
  let m = ov ? (ov === 'new' ? null : { id: ov, how: 'override' }) : match(keys, labels);
  if (m && m.ambiguous) { report.ambiguous.push(`${qid} "${label}": ${m.ambiguous.join(', ')} (add to research/api/match-overrides.json)`); m = null; }

  const src = (p) => ({ type: 'web', cite: `Wikidata, ${qid} (${label}), ${p} ${L(p)}, retrieved ${DATE}. Wikidata is not a ground; check the holding's record.`, url: `https://www.wikidata.org/wiki/${qid}` });
  const out = {
    id: m ? m.id : newId(isMs ? 'ms' : 'w', label, rcins[0]),
    type: m ? (entities.get(m.id)?.type || 'work') : (isMs ? 'manuscript' : 'work'),
    label
  };
  if (!m) {
    out.subtype = isMs ? 'manuscript' : (formRaw || 'work');
    const technique = all(TECH, materials), support = first(SUPPORT, materials), subject = all(SUBJ, label.toLowerCase() + ' ' + genre);
    out.classification = isMs ? { ms_form: 'notebook', basis: `Derived automatically from Wikidata ${qid} on ${DATE}; check.` } : Object.assign(
      { form: formRaw || 'drawing' }, technique.length ? { technique } : {}, support ? { support } : {}, { condition: collections.length ? 'extant' : 'lost' },
      subject.length ? { subject } : {}, { basis: `Derived automatically from Wikidata ${qid} (instance of: ${inst || 'none'}; material: ${materials || 'none'}) on ${DATE}; check against the holding's record.` });
    if (isMs) delete out.classification.form;
  }
  out.identifiers = Object.assign({ wikidata: qid }, rcins[0] ? { rcin: rcins[0] } : {}, arks[0] ? { louvre_ark: arks[0] } : {}, metIds[0] ? { met: metIds[0] } : {}, invs[0] ? { inventory: invs[0].v } : {});
  const variants = [...new Set([e.labels?.it?.value, e.labels?.fr?.value, ...(e.aliases?.en || []).map((a) => a.value)].filter((x) => x && x !== label).map(clean))];
  if (variants.length) out.variants = variants.slice(0, 8);
  const img = claimsOf(e, 'P18').map(val).find((v) => typeof v === 'string');
  if (img) out.images = [{ src: `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(img.replace(/ /g, '_'))}?width=640`, credit: 'Wikimedia Commons', page: `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(img.replace(/ /g, '_'))}` }];
  out.claims = [];
  // attribution qualifiers on the creator statement
  const q = wd.qualifiers[qid] || { attribution: [], nature: [] };
  const attr = [...q.attribution, ...q.nature].map(L);
  out.claims.push(C('attribution', { text: attr.length ? `Leonardo da Vinci (${attr.join(', ')})` : 'Leonardo da Vinci' }, 'interpretation',
    `Wikidata records Leonardo da Vinci as creator${attr.length ? ' with the qualification: ' + attr.join(', ') : ''}. This reflects whichever opinion the Wikidata editors followed.`, src('P170')));
  for (const c of claimsOf(e, 'P571')) { const v = wdDate(c); if (v) out.claims.push(C('date', v, 'interpretation', `Wikidata gives the date of creation as ${v.text}.`, src('P571'))); }
  for (const x of invs) out.claims.push(C('inventory', { text: clean(x.v) }, 'fact', `Inventory number ${clean(x.v)}${x.coll ? ' in ' + x.coll : ''}, as recorded in Wikidata.`, src('P217')));
  for (const coll of collections) out.claims.push(C('current_location', { text: clean(coll) }, 'fact', `Held by ${clean(coll)}, as recorded in Wikidata.`, src('P195')));
  if (materials) out.claims.push(C('medium', { text: clean(materials) }, 'fact', `Material recorded in Wikidata: ${clean(materials)}.`, src('P186')));
  const h = claimsOf(e, 'P2048').map(qty).filter(Boolean)[0], w = claimsOf(e, 'P2049').map(qty).filter(Boolean)[0];
  if (h || w) out.claims.push(C('dimensions', { text: `${h || '?'} x ${w || '?'}` }, 'fact', `Dimensions recorded in Wikidata: height ${h || 'not given'}, width ${w || 'not given'}.`, src('P2048')));
  const depicts = itemLabels(e, 'P180');
  if (depicts.length) out.claims.push(C('depicts', { text: clean(depicts.slice(0, 12).join('; ')) }, 'interpretation', `Wikidata lists as depicted: ${clean(depicts.slice(0, 12).join('; '))}. Identifications of what is depicted are interpretations.`, src('P180')));
  // Wikipedia background
  for (const [lang, w] of Object.entries(wiki?.[qid] || {})) if (w.extract) (out.background = out.background || []).push({ source: 'wikipedia', lang, url: w.url, text: clean(w.extract), retrieved: DATE });
  // Louvre record
  for (const ark of arks) { const r = louvre?.[ark]?.record; if (r) addLouvre(out, ark, r); }
  // RCT page
  for (const rc of rcins) { const r = rct?.[rc]; if (r) addRct(out, rc, r); }
  if (out.claims.length === 0) delete out.claims;
  emit(out);
  (m ? report.matched : report.created).push(`${out.id} <- ${qid} "${label}"${m ? ' [' + m.how + ']' : ''}`);
  created[qid] = out.id;
}

function addLouvre(out, ark, r) {
  const url = r.url || `https://collections.louvre.fr/ark:/53355/${ark}`;
  const src = { type: 'other', cite: `Musée du Louvre, collections database record ${ark} (${clean(r.title || '')}), retrieved ${DATE} through its JSON export.`, url };
  const pickText = (v) => Array.isArray(v) ? v.map((x) => (typeof x === 'string' ? x : x?.value || x?.text || x?.label || '')).filter(Boolean).join('; ') : (typeof v === 'object' && v ? (v.value || v.text || v.label || '') : (v || ''));
  const inv = pickText(r.objectNumber || r.inventoryNumber);
  if (inv) out.claims.push(C('inventory', { text: clean(inv) }, 'fact', `Louvre inventory number ${clean(inv)}.`, src));
  const date = pickText(r.displayDateCreated || r.dateCreated);
  if (date) out.claims.push(C('date', { text: clean(date) }, 'interpretation', `The Louvre's record dates the work: ${clean(date)}.`, src));
  const mat = pickText(r.materialsAndTechniques);
  if (mat) out.claims.push(C('medium', { text: clean(mat) }, 'fact', `Materials and technique in the Louvre's record: ${clean(mat)}.`, src));
  const dim = pickText(r.dimension);
  if (dim) out.claims.push(C('dimensions', { text: clean(dim) }, 'fact', `Dimensions in the Louvre's record: ${clean(dim)}.`, src));
  const creator = Array.isArray(r.creator) ? r.creator.map((c) => [c.attributionLevel, c.label, c.creatorRole].filter(Boolean).join(' ')).join('; ') : pickText(r.creator);
  if (creator) out.claims.push(C('attribution', { text: clean(creator) }, 'interpretation', `The Louvre's record gives the author as: ${clean(creator)}.`, src));
  const loc = pickText(r.currentLocation || r.room);
  if (loc) out.claims.push(C('current_location', { text: clean(loc) }, 'fact', `Location in the Louvre's record: ${clean(loc)}.`, src));
  const img = Array.isArray(r.image) && r.image[0] && (r.image[0].urlImage || r.image[0].urlThumbnail);
  if (img) (out.images = out.images || []).push({ src: img, credit: 'Musée du Louvre', page: url });
}
function addRct(out, rc, r) {
  const src = { type: 'other', cite: `Royal Collection Trust, collection page RCIN ${rc}${r.title ? ' (' + clean(r.title) + ')' : ''}, retrieved ${DATE}.`, url: r.url };
  const t = clean(r.title || '').replace(/\s*\|.*$/, '');
  const m = t.match(/(c\.\s?\d{4}(?:\s*(?:to|-)\s*\d{2,4})?|\d{4}(?:\s*to\s*\d{2,4})?)\s*$/);
  if (m) out.claims.push(C('date', { text: clean(m[1]) }, 'interpretation', `The Royal Collection Trust's page title gives the date ${clean(m[1])}.`, src));
  out.claims.push(C('current_location', { text: 'Royal Collection, Windsor' }, 'fact', `Held in the Royal Collection as RCIN ${rc}.`, src));
  if (r.details_text) out.claims.push(C('record', { text: clean(r.details_text).slice(0, 1200) }, 'fact', `Object details as given on the Royal Collection Trust page (text captured, to be split into claims on review).`, src));
  const d = r.og_description || r.description;
  if (d) (out.background = out.background || []).push({ source: 'rct', lang: 'en', url: r.url, text: clean(d), retrieved: DATE });
}

// Met objects
for (const o of met?.objects || []) {
  const label = clean(o.title || `Met ${o.objectID}`);
  const qid = Object.entries(wd?.entities || {}).find(([, e]) => extIds(e, /metropolitan museum/i).includes(String(o.objectID)))?.[0];
  const existingId = (qid && created[qid]) || byIdent[`met:${o.objectID}`] || byIdent[`inventory:${String(o.accessionNumber).toLowerCase()}`];
  const out = existingId && existsSync(path.join(OUT, existingId + '.json')) ? JSON.parse(readFileSync(path.join(OUT, existingId + '.json'), 'utf8')) : { id: existingId || newId('w', label, String(o.objectID)), type: 'work', label };
  const isNew = !existingId;
  const src = { type: 'other', cite: `The Metropolitan Museum of Art, Collection API, object ${o.objectID} (${label}), accession ${o.accessionNumber}, retrieved ${DATE}.`, url: o.objectURL };
  out.identifiers = Object.assign(out.identifiers || {}, { met: String(o.objectID) });
  if (isNew) {
    const text = `${o.classification} ${o.objectName} ${label} ${o.medium}`.toLowerCase();
    out.subtype = (o.classification || 'drawing').toLowerCase();
    const technique = all(TECH, (o.medium || '').toLowerCase()), support = first(SUPPORT, (o.medium || '').toLowerCase()), subject = all(SUBJ, text);
    out.classification = Object.assign({ form: first(FORM, text.replace(/drawings?/, 'drawing')) === 'MS' ? 'drawing' : (first(FORM, text) || 'drawing') }, technique.length ? { technique } : {}, support ? { support } : {}, { condition: 'extant' }, subject.length ? { subject } : {},
      { basis: `Derived automatically from the Met Collection API record ${o.objectID} on ${DATE}; check.` });
  }
  out.claims = out.claims || [];
  const prefix = [o.artistPrefix, o.artistDisplayName, o.artistSuffix].filter(Boolean).join(' ');
  out.claims.push(C('attribution', { text: clean(prefix || 'Leonardo da Vinci') }, 'interpretation', `The Met's record gives the artist as: ${clean(prefix)}${o.attributionQualifier ? ' (' + o.attributionQualifier + ')' : ''}.`, src));
  if (o.objectDate) out.claims.push(C('date', Object.assign({ text: clean(o.objectDate) }, o.objectBeginDate ? { start: o.objectBeginDate } : {}, o.objectEndDate && o.objectEndDate !== o.objectBeginDate ? { end: o.objectEndDate } : {}), 'interpretation', `The Met dates the work ${clean(o.objectDate)}.`, src));
  if (o.medium) out.claims.push(C('medium', { text: clean(o.medium) }, 'fact', `Medium in the Met's record: ${clean(o.medium)}.`, src));
  if (o.dimensions) out.claims.push(C('dimensions', { text: clean(o.dimensions) }, 'fact', `Dimensions in the Met's record: ${clean(o.dimensions)}.`, src));
  out.claims.push(C('inventory', { text: clean(o.accessionNumber) }, 'fact', `Accession number ${clean(o.accessionNumber)}, The Metropolitan Museum of Art${o.creditLine ? '; ' + clean(o.creditLine) : ''}.`, src));
  out.claims.push(C('current_location', { text: 'The Metropolitan Museum of Art, New York' }, 'fact', `Held by The Metropolitan Museum of Art (${clean(o.department || '')}).`, src));
  if (o.primaryImageSmall) (out.images = out.images || []).push({ src: o.primaryImageSmall, credit: 'The Metropolitan Museum of Art', page: o.objectURL });
  emit(out);
  (isNew ? report.created : report.matched).push(`${out.id} <- Met ${o.objectID} "${label}"`);
}

const md = `# API import match report (${DATE})\n\nRaw data: research/api/raw/. Output: ${path.relative(ROOT, OUT)}/.\n\n` +
  `## Matched to existing entities (${report.matched.length})\n\n${report.matched.map((x) => '* ' + x).join('\n')}\n\n` +
  `## New entities (${report.created.length})\n\n${report.created.map((x) => '* ' + x).join('\n')}\n\n` +
  `## Ambiguous, not matched (${report.ambiguous.length})\n\n${report.ambiguous.map((x) => '* ' + x).join('\n')}\n\n` +
  `## Skipped (${report.skipped.length})\n\n${report.skipped.map((x) => '* ' + x).join('\n')}\n`;
writeFileSync(path.join(ROOT, 'research', 'api', 'match-report.md'), md);
console.log(`matched ${report.matched.length}, new ${report.created.length}, ambiguous ${report.ambiguous.length}, skipped ${report.skipped.length} -> ${path.relative(ROOT, OUT)}`);
