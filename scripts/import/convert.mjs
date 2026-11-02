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
const normInv = (s) => String(s).toLowerCase().replace(/^(n\.?\s*)?inv(entory)?\.?\s*(no\.?)?\s*/, '').replace(/\s+(recto|verso|r|v)$/, '').replace(/\s+/g, ' ').trim();

// ---------- index of existing entities ----------
const byIdent = {}, byLabel = {};
for (const e of entities.values()) {
  if (!['work', 'manuscript'].includes(e.type)) continue;
  for (const [k, v] of Object.entries(e.identifiers || {})) byIdent[`${k}:${v}`] = e.id;
  if (e.inventory) for (const part of String(e.inventory).split(/;\s*/)) byIdent[`inventory:${normInv(part)}`] = e.id;
  const m = e.id.match(/(9\d{5})$/); if (m) byIdent[`rcin:${m[1]}`] = e.id;
  const mi = String(e.inventory || '').match(/RCIN\s*(\d{6})/); if (mi) byIdent[`rcin:${mi[1]}`] = e.id;
  for (const v of [].concat(e.identifiers?.wikidata || [])) byIdent[`wikidata:${v}`] = e.id;
  for (const l of [e.label, ...(e.variants || [])]) if (l) (byLabel[norm(l)] = byLabel[norm(l)] || new Set()).add(e.id);
}

// ---------- vocab mapping ----------
const L = (q) => (wd && wd.labels[q]) || q;
const LABEL_FORM = [[/^(studies|sheet of studies|recto|various studies)|\bstudies (of|for)\b.*\band\b/, 'sheet_of_studies'], [/^(sketch|sketches|rough sketch)/, 'sketch'], [/^(study|studies) (of|for)/, 'study'],
  [/^(map|plan of the town|bird.s.eye view)/, 'map'], [/^(design|designs) for (a |an )?(machine|device|cannon|bombard|wheel|crossbow|pump|mill|boat|ship|flying)|machine|mechanism|cannon|bombard|crossbow|catapult|gear|pulley|winch/, 'technical_drawing'],
  [/^(plan|elevation|design for a (church|palace|building|villa|stable|tomb|fortress)|church|centrally planned)/, 'architectural_drawing'], [/^(cartoon)/, 'cartoon'], [/^(geometr|diagram)/, 'diagram']];
const FORM = [[/folio|slip of paper/, 'sheet_of_studies'], [/invention|combat vehicle|humanoid robot|kite/, 'engineering_project'], [/fresco|mural|wall painting/, 'mural'], [/cartoon/, 'cartoon'], [/sketch/, 'sketch'], [/study/, 'study'], [/map/, 'map'], [/painting|panel painting/, 'painting'],
  [/manuscript|codex|notebook/, 'MS'], [/sculpture|equestrian statue|monument/, 'sculpture_project'], [/architectur/, 'architectural_drawing'], [/drawing|print|artwork/, 'drawing']];
const TECH = [[/oil/, 'oil'], [/tempera/, 'tempera'], [/red chalk|sanguine/, 'red_chalk'], [/black chalk/, 'black_chalk'], [/charcoal/, 'charcoal'], [/metalpoint|silverpoint|silver point|leadpoint/, 'metalpoint'],
  [/\bink\b|\bpen\b|iron gall|feather|quill/, 'pen_and_ink'], [/wash|watercolou?r|bistre/, 'wash'], [/white (heighten|gouache|lead)|lead white|bodycolou?r/, 'white_heightening'], [/stylus/, 'stylus'], [/pricked|pouncing/, 'pricking']];
const SUPPORT = [[/poplar/, 'panel_poplar'], [/walnut/, 'panel_walnut'], [/blue.*paper|paper.*blue/, 'blue_paper'], [/prepared paper|coloured ground|tinted paper|grounded paper/, 'prepared_paper'], [/canvas/, 'canvas'], [/parchment|vellum/, 'parchment'], [/plaster|wall/, 'wall'], [/paper/, 'paper'], [/panel|wood/, 'panel']];
const SUBJ = [[/portrait/, 'portrait'], [/virgin|madonna|christ|saint|annunciation|adoration|apostle|religious|biblical|jerome|john the baptist|last supper|nativity/, 'religious'], [/leda|myth|allegor/, 'mythology'],
  [/anatom|skull|heart|muscle|skeleton|fo?etus|uterus|vessel/, 'anatomy'], [/\bhorses?\b/, 'horse'], [/landscape/, 'landscape'], [/plant|flower|botan|tree/, 'botany'], [/\bmaps?\b/, 'cartography'], [/machine|mechan/, 'mechanics'],
  [/flying|\bflight\b|\bwings?\b|\bbirds?\b/, 'flight'], [/weapon|military|cannon|fortif/, 'military'], [/grotesque|caricature|head/, 'head'], [/deluge|storm|flood/, 'deluge'], [/water|river|canal/, 'water'], [/architect|church|palace|building/, 'architecture'], [/battle/, 'battle'], [/drapery|figure|nude/, 'figure']];
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
const newIds = new Set();

function match(keys, labels) {
  for (const k of keys) if (byIdent[k]) return { id: byIdent[k], how: k };
  const cands = new Set();
  for (const l of labels) for (const id of byLabel[norm(l)] || []) cands.add(id);
  if (cands.size === 1) return { id: [...cands][0], how: 'label' };
  if (cands.size > 1) return { ambiguous: [...cands] };
  return null;
}
function newId(prefix, label, num) {
  const STOP = new Set(['a', 'an', 'the', 'of', 'and', 'in', 'with', 'for', 'to', 'on', 'at', 'from', 'by', 'two', 'three', 'recto', 'verso', 'study', 'studies', 'sketch', 'sketches', 'drawing']);
  const words = slug(label).split('-').filter((w) => w && !STOP.has(w));
  const core = (words.length ? words : slug(label).split('-')).slice(0, 5).join('-');
  let base = `${prefix}-${core || 'untitled'}${num ? '-' + num : ''}`;
  base = base.replace(/-+/g, '-').slice(0, 70).replace(/-$/, '');
  let id = base, n = 2; while (taken.has(id)) id = `${base}-${n++}`;
  taken.add(id); return id;
}
function emit(e) {
  const f = path.join(OUT, e.id + '.json');
  if (existsSync(f)) {
    const prev = JSON.parse(readFileSync(f, 'utf8'));
    for (const [k, v] of Object.entries(e.identifiers || {})) {
      const cur = [].concat(prev.identifiers?.[k] || []);
      for (const x of [].concat(v)) if (!cur.includes(x)) cur.push(x);
      (prev.identifiers = prev.identifiers || {})[k] = cur.length === 1 ? cur[0] : cur;
    }
    for (const k of ['claims', 'images', 'background', 'variants']) if (e[k]) prev[k] = (prev[k] || []).concat(e[k].filter((x) => !(prev[k] || []).some((y) => JSON.stringify(y) === JSON.stringify(x))));
    e = prev;
  }
  writeFileSync(f, JSON.stringify(e, null, 2) + '\n');
}

let cn = 0;
const C = (about, value, layer, statement, source, extra = {}) => ({ id: `api${++cn}`, about, ...(value !== undefined ? { value } : {}), layer, status: 'pending', statement: clean(statement), sources: [source], ...extra });

// Pre-pass: how many imported items share each title, and how many items would title-match each entity.
const labelCount = {}, labelTargets = {};
for (const e of Object.values(wd?.entities || {})) { const l = norm(e.labels?.en?.value || ''); if (l) labelCount[l] = (labelCount[l] || 0) + 1; }
for (const e of Object.values(wd?.entities || {})) { const l = norm(e.labels?.en?.value || ''); if (labelCount[l] === 1) for (const id of byLabel[l] || []) labelTargets[id] = (labelTargets[id] || 0) + 1; }

// Wikidata items
for (const [qid, e] of Object.entries(wd?.entities || {})) {
  if (e.missing !== undefined) continue;
  const label = clean(e.labels?.en?.value || e.labels?.it?.value || e.labels?.fr?.value || qid);
  const inst = itemLabels(e, 'P31').join('; ').toLowerCase();
  const genre = itemLabels(e, 'P136').concat(itemLabels(e, 'P180'), itemLabels(e, 'P921')).join('; ').toLowerCase();
  const materials = itemLabels(e, 'P186').join('; ').toLowerCase();
  const collections = claimsOf(e, 'P195').map((c) => L(val(c)?.id)).filter(Boolean);
  const invs = claimsOf(e, 'P217').map((c) => ({ v: val(c), coll: (c.qualifiers?.P195 || []).map((s) => L(s.datavalue?.value?.id))[0] })).filter((x) => typeof x.v === 'string');
  const rcins = [...new Set(extIds(e, /royal collection/i).concat(invs.filter((x) => /^RCIN\s*\d{6}/i.test(x.v) || /royal collection/i.test(x.coll || '')).map((x) => (x.v.match(/(\d{6})/) || [])[1]).filter(Boolean)))];
  const arks = extIds(e, /louvre/i).map((v) => { v = String(v).trim(); return (v.match(/cl\d{9}/) || [])[0] || (/^\d{9}$/.test(v) ? 'cl' + v : null); }).filter(Boolean);
  const metIds = extIds(e, /metropolitan museum|met object/i);
  const formInst = first(FORM, inst + ' ' + genre);
  const formRaw = (formInst === 'drawing' || formInst === 'study' || formInst === 'sketch') ? (first(LABEL_FORM, label.toLowerCase()) || formInst) : formInst;
  const isMs = formRaw === 'MS';
  if (!overrides[qid] && (/^(collection|series|group of|set of)/.test(inst) || (/drawing series|artistic theme/.test(inst) && !/(^|; )drawing(;|$)/.test(inst)))) { report.skipped.push(`${qid} ${label} (${inst}): a grouping, not one object`); continue; }

  const ov = overrides[qid];
  if (ov === 'skip') { report.skipped.push(`${qid} ${label} (override: skip)`); continue; }
  const keys = [`wikidata:${qid}`, ...rcins.map((r) => `rcin:${r}`), ...arks.map((a) => `louvre_ark:${a}`), ...metIds.map((m) => `met:${m}`), ...invs.map((x) => `inventory:${normInv(x.v)}`)];
  // Title matching only when the item has no RCIN, and the title is unique among imported items.
  const labels = rcins.length ? [] : [label, ...(e.aliases?.en || []).map((a) => a.value)].filter((l) => (labelCount[norm(l)] || 0) <= 1);
  let m = ov ? (ov === 'new' ? null : { id: ov, how: 'override' }) : match(keys, labels);
  if (m && m.ambiguous) { report.ambiguous.push(`${qid} "${label}": ${m.ambiguous.join(', ')} (add to research/api/match-overrides.json)`); m = null; }
  if (m && m.how === 'label') {
    const target = entities.get(m.id), trc = target && (String(target.inventory || '').match(/RCIN\s*(\d{6})/) || [])[1];
    if ((labelTargets[m.id] || 0) > 1 || (trc && !rcins.includes(trc))) { report.ambiguous.push(`${qid} "${label}": title matches ${m.id} but not one to one or identifiers differ (add to research/api/match-overrides.json)`); m = null; }
  }

  const src = (p) => ({ type: 'web', cite: `Wikidata, ${qid} (${label}), ${p} ${L(p)}, retrieved ${DATE}. Wikidata is not a ground; check the holding's record.`, url: `https://www.wikidata.org/wiki/${qid}` });
  const out = {
    id: m ? m.id : newId(isMs ? 'ms' : 'w', label, rcins[0]),
    type: m ? (entities.get(m.id)?.type || (m.id.startsWith('ms-') ? 'manuscript' : 'work')) : (isMs ? 'manuscript' : 'work'),
    label
  };
  if (!m || newIds.has(m.id) && false) {
    out.subtype = isMs ? 'manuscript' : (formRaw || 'work');
    const technique = all(TECH, materials), support = first(SUPPORT, materials), subject = all(SUBJ, label.toLowerCase() + ' ' + genre);
    out.classification = isMs ? { ms_form: 'notebook', basis: `Derived automatically from Wikidata ${qid} on ${DATE}; check.` } : Object.assign(
      { form: formRaw || 'drawing' }, technique.length ? { technique } : {}, support ? { support } : {}, { condition: collections.length ? 'extant' : 'lost' },
      subject.length ? { subject } : {}, { basis: `Derived automatically from Wikidata ${qid} (instance of: ${inst || 'none'}; material: ${materials || 'none'}; form refined from the title where the item is a generic drawing) on ${DATE}; check against the holding's record.` });
    if (isMs) delete out.classification.form;
  }
  const fm = label.match(/Codex Atlanticus \(F0*(\d+)\)/);
  if (fm && !m) { out.manuscript = 'w-atlanticus'; out.folio = `f. ${fm[1]}`; out.relations = [{ rel: 'drawn_on', target: 'w-atlanticus' }]; out.label = `Codex Atlanticus, f. ${fm[1]}`; }
  out.identifiers = Object.assign({ wikidata: qid }, rcins[0] ? { rcin: rcins[0] } : {}, arks[0] ? { louvre_ark: arks[0] } : {}, metIds[0] ? { met: metIds[0] } : {}, invs[0] ? { inventory: clean(invs[0].v) } : {});
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
  if (!m) { for (const k of keys) if (!k.startsWith('wikidata:') && !byIdent[k]) byIdent[k] = out.id; newIds.add(out.id); }
  emit(out);
  const isExisting = m && !newIds.has(m.id);
  (isExisting ? report.matched : report.created).push(`${out.id} <- ${qid} "${label}"${m ? ' [' + m.how + ']' : ''}`);
  created[qid] = out.id;
}

function addLouvre(out, ark, r) {
  const url = r.url || `https://collections.louvre.fr/ark:/53355/${ark}`;
  const src = { type: 'other', cite: `Musée du Louvre, collections database record ${ark} (${clean(r.title || '')}), retrieved ${DATE} through its JSON export.`, url };
  const bib = (r.bibliography || []).filter((b) => !b.comparison).slice(0, 10).map((b) => clean(`${b.bibliographyRef}${b.bibliographyDetail ? ', ' + b.bibliographyDetail : ''}`));
  const extra = bib.length ? { check_in: bib } : {};
  if (r.title && r.title !== out.label) (out.variants = out.variants || []).push(clean(r.title));
  const main = (r.objectNumber || []).find((x) => /principal/i.test(x.type || '')) || (r.objectNumber || [])[0];
  if (main) out.claims.push(C('inventory', { text: clean(main.value) }, 'fact', `Louvre inventory number ${clean(main.value)}.`, src));
  const old = (r.objectNumber || []).filter((x) => x !== main).map((x) => `${x.type}: ${x.value}`);
  if (old.length) out.claims.push(C('inventory_history', { text: clean(old.join('; ')) }, 'fact', `Other numbers in the Louvre's record: ${clean(old.join('; '))}.`, src));
  const disp = clean(String(r.displayDateCreated || '').replace(/^Date de cr\S+ : /i, ''));
  const dc = (r.dateCreated || [])[0];
  if (disp || dc) {
    const v = { text: disp || `${dc.startYear} to ${dc.endYear}` };
    if (dc && dc.startYear) v.start = dc.startYear; if (dc && dc.endYear && dc.endYear !== dc.startYear) v.end = dc.endYear;
    out.claims.push(C('date', v, 'interpretation', `The Louvre's record dates the work: ${v.text}.`, src, extra));
  }
  if (r.materialsAndTechniques) out.claims.push(C('medium', { text: clean(r.materialsAndTechniques) }, 'fact', `Materials and technique in the Louvre's record: ${clean(r.materialsAndTechniques)}`, src));
  const dims = (r.dimension || []).map((d) => `${d.type} ${d.displayDimension || d.value + ' ' + d.unit}${d.anteriorPrecision ? ' (' + d.anteriorPrecision + ')' : ''}`);
  if (dims.length) out.claims.push(C('dimensions', { text: clean(dims.join('; ')) }, 'fact', `Dimensions in the Louvre's record: ${clean(dims.join('; '))}.`, src));
  const creators = (r.creator || []).map((c) => `${c.label}${c.attributionLevel ? ' [' + c.attributionLevel + ']' : ''}${c.creatorRole ? ' (' + c.creatorRole + ')' : ''}`);
  if (creators.length) out.claims.push(C('attribution', { text: clean(creators.join('; ')) }, 'interpretation', `The Louvre's record gives the author as: ${clean(creators.join('; '))}.`, src, extra));
  out.claims.push(C('current_location', { text: clean(`Musée du Louvre, ${r.collection || ''}`) }, 'fact', `Held by the Musée du Louvre, ${clean(r.collection || '')}.`, src));
  if (r.objectHistory) out.claims.push(C('provenance', { text: clean(r.objectHistory) }, 'fact', `History of the object as given in the Louvre's record: ${clean(r.objectHistory)}`, src));
  if (r.inscriptions) out.claims.push(C('inscription', { text: clean(r.inscriptions) }, 'fact', `Inscriptions recorded by the Louvre: ${clean(r.inscriptions)}`, src));
  const img = Array.isArray(r.image) && r.image[0] && (r.image[0].urlThumbnail || r.image[0].urlImage);
  if (img) (out.images = out.images || []).push({ src: img, credit: clean(r.image[0].copyright || 'Musée du Louvre'), page: url });
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
  const qid = Object.entries(wd?.entities || {}).find(([, e]) => extIds(e, /metropolitan museum|met object/i).includes(String(o.objectID)))?.[0];
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
