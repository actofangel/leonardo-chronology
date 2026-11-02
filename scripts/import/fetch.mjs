#!/usr/bin/env node
// Fetch raw records about Leonardo's works from public collection APIs.
// Runs in GitHub Actions (open network). Writes raw, unmodified responses to
// research/api/raw/ so every later conversion step can be audited.
//
//   node scripts/import/fetch.mjs [--only wikidata,met,louvre,wikipedia,rct]
//
// Sources:
//   Wikidata  SPARQL + wbgetentities: every item whose creator (P170) is Leonardo (Q762),
//             with qualifiers (attribution, nature of statement), all claims and sitelinks.
//   Met       Collection API (collectionapi.metmuseum.org), objects whose constituents include Leonardo.
//   Louvre    collections.louvre.fr ARK records (.json), ARK ids taken from Wikidata.
//   Wikipedia REST page summaries (en, it, fr) for Wikidata sitelinks. Background only, never a ground.
//   RCT       rct.uk collection pages for RCIN numbers found in Wikidata; title and metadata only.
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const OUT = path.join(ROOT, 'research', 'api', 'raw');
mkdirSync(OUT, { recursive: true });
const UA = 'LeonardoDatabase/0.1 (https://github.com/actofangel/leonardo-chronology; research use)';
const only = (() => { const i = process.argv.indexOf('--only'); return i > 0 ? new Set(process.argv[i + 1].split(',')) : null; })();
const want = (s) => !only || only.has(s);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const save = (name, data) => { writeFileSync(path.join(OUT, name), JSON.stringify(data, null, 1) + '\n'); log('wrote', name); };

async function get(url, { json = true, tries = 4, headers = {} } = {}) {
  for (let t = 1; t <= tries; t++) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': UA, Accept: json ? 'application/json' : 'text/html', ...headers } });
      if (r.status === 404) return null;
      if (r.status === 429 || r.status >= 500) throw new Error('HTTP ' + r.status);
      if (!r.ok) { log('fail', r.status, url); return null; }
      return json ? await r.json() : await r.text();
    } catch (e) { if (t === tries) { log('error', e.message, url); return null; } await sleep(1500 * t); }
  }
}

const manifest = { fetched: new Date().toISOString(), sources: {} };

// ---------- Wikidata ----------
let wd = null;
if (want('wikidata') || want('louvre') || want('wikipedia') || want('rct')) {
  const q = `SELECT DISTINCT ?item ?attribution ?nature WHERE {
    ?item p:P170 ?st . ?st ps:P170 wd:Q762 .
    OPTIONAL { ?st pq:P5102 ?attribution }
    OPTIONAL { ?st pq:P1480 ?nature }
  }`;
  const res = await get('https://query.wikidata.org/sparql?format=json&query=' + encodeURIComponent(q), { headers: { Accept: 'application/sparql-results+json' } });
  const rows = res ? res.results.bindings : [];
  const qid = (u) => u && u.value.split('/').pop();
  const quals = {};
  for (const b of rows) {
    const id = qid(b.item); quals[id] = quals[id] || { attribution: [], nature: [] };
    if (b.attribution) quals[id].attribution.push(qid(b.attribution));
    if (b.nature) quals[id].nature.push(qid(b.nature));
  }
  const ids = Object.keys(quals);
  log('wikidata items with creator Leonardo:', ids.length);
  const entities = {};
  for (let i = 0; i < ids.length; i += 50) {
    const r = await get(`https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=${ids.slice(i, i + 50).join('|')}&props=labels|descriptions|aliases|claims|sitelinks&languages=en|it|fr|de`);
    Object.assign(entities, r?.entities || {});
    await sleep(300);
  }
  // labels for every item and property referenced in claims
  const refs = new Set();
  for (const e of Object.values(entities)) for (const [p, cl] of Object.entries(e.claims || {})) {
    refs.add(p);
    for (const c of cl) {
      const v = c.mainsnak?.datavalue?.value; if (v && v.id) refs.add(v.id);
      if (v && v.unit && v.unit.includes('/entity/')) refs.add(v.unit.split('/').pop());
      for (const [qp, qs] of Object.entries(c.qualifiers || {})) { refs.add(qp); for (const s of qs) if (s.datavalue?.value?.id) refs.add(s.datavalue.value.id); }
    }
  }
  for (const q of Object.values(quals)) [...q.attribution, ...q.nature].forEach((x) => refs.add(x));
  const refList = [...refs], labels = {};
  for (let i = 0; i < refList.length; i += 50) {
    const r = await get(`https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids=${refList.slice(i, i + 50).join('|')}&props=labels&languages=en|it|fr`);
    for (const [k, v] of Object.entries(r?.entities || {})) labels[k] = v.labels?.en?.value || v.labels?.it?.value || v.labels?.fr?.value || k;
    await sleep(300);
  }
  wd = { query: q, qualifiers: quals, entities, labels };
  if (want('wikidata')) save('wikidata.json', wd);
  manifest.sources.wikidata = { items: ids.length, url: 'https://query.wikidata.org/' };
}

// helper: string values of a property, and external ids by label pattern
const strings = (e, p) => (e.claims?.[p] || []).map((c) => c.mainsnak?.datavalue?.value).filter((v) => typeof v === 'string');
function externalIds(e, re) {
  const out = [];
  for (const [p, cl] of Object.entries(e.claims || {})) if (re.test(wd.labels[p] || '')) for (const c of cl) { const v = c.mainsnak?.datavalue?.value; if (typeof v === 'string') out.push(v); }
  return out;
}

// ---------- Met ----------
if (want('met')) {
  // Object ids from Wikidata (The Met object ID), plus the search endpoint when it answers.
  const fromWd = wd ? Object.values(wd.entities).flatMap((e) => externalIds(e, /metropolitan museum|met object/i)) : [];
  const s = await get('https://collectionapi.metmuseum.org/public/collection/v1/search?artistOrCulture=true&q=Leonardo%20da%20Vinci');
  const ids = [...new Set([...(s?.objectIDs || []), ...fromWd.map(Number).filter(Boolean)])];
  log('met ids from wikidata:', fromWd.length);
  log('met search hits:', ids.length);
  const objects = [];
  for (const id of ids) {
    const o = await get(`https://collectionapi.metmuseum.org/public/collection/v1/objects/${id}`);
    if (o && (/leonardo da vinci/i.test(o.artistDisplayName || '') || (o.constituents || []).some((c) => /leonardo da vinci/i.test(c.name)))) objects.push(o);
    await sleep(60);
  }
  save('met.json', { search: 'artistOrCulture=true&q=Leonardo da Vinci', hits: ids.length, objects });
  manifest.sources.met = { hits: ids.length, kept: objects.length, url: 'https://metmuseum.github.io/' };
}

// ---------- Louvre (ARK ids from Wikidata) ----------
if (want('louvre') && wd) {
  const records = {};
  for (const [id, e] of Object.entries(wd.entities)) {
    for (const ark of externalIds(e, /louvre/i)) {
      const v = String(ark).trim(); const m = v.match(/cl\d{9}/) || (/^\d{9}$/.test(v) ? ['cl' + v] : null); if (!m) continue;
      const r = await get(`https://collections.louvre.fr/ark:/53355/${m[0]}.json`);
      if (r) records[m[0]] = { wikidata: id, record: r };
      await sleep(400);
    }
  }
  save('louvre.json', records);
  manifest.sources.louvre = { records: Object.keys(records).length, url: 'https://collections.louvre.fr/' };
}

// ---------- Wikipedia summaries ----------
if (want('wikipedia') && wd) {
  const out = {};
  for (const [id, e] of Object.entries(wd.entities)) {
    for (const lang of ['en', 'it', 'fr']) {
      const t = e.sitelinks?.[lang + 'wiki']?.title; if (!t) continue;
      const r = await get(`https://${lang}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(t.replace(/ /g, '_'))}`);
      if (r) (out[id] = out[id] || {})[lang] = { title: r.title, extract: r.extract, url: r.content_urls?.desktop?.page, revision: r.revision, timestamp: r.timestamp };
      await sleep(150);
    }
  }
  save('wikipedia.json', out);
  manifest.sources.wikipedia = { items: Object.keys(out).length };
}

// ---------- Royal Collection Trust pages ----------
if (want('rct') && wd) {
  const out = {}; let refused = 0;
  const pick = (html, re) => { const m = html.match(re); return m ? m[1].replace(/&amp;/g, '&').replace(/&#039;|&#39;/g, "'").replace(/&quot;/g, '"').trim() : null; };
  outer: for (const [id, e] of Object.entries(wd.entities)) {
    const ids = externalIds(e, /royal collection/i).concat(strings(e, 'P217').filter((v) => /^(RCIN )?9\d{5}$/.test(v)).map((v) => v.replace('RCIN ', '')));
    for (const rcin of [...new Set(ids)]) {
      const html = await get(`https://www.rct.uk/collection/${encodeURIComponent(rcin)}`, { json: false, tries: 1 });
      if (!html) { if (++refused >= 3 && !Object.keys(out).length) { log('rct: site refuses automated access; respecting that and stopping. RCT data comes via Wikidata.'); break outer; } continue; }
      const text = html.replace(/<script[\s\S]*?<\/script>/gi, '').replace(/<style[\s\S]*?<\/style>/gi, '');
      const block = pick(text, /(<div[^>]*class="[^"]*object-details[^"]*"[\s\S]{0,6000}?<\/div>\s*<\/div>)/i);
      out[rcin] = {
        wikidata: id, url: `https://www.rct.uk/collection/${rcin}`,
        title: pick(text, /<title>([\s\S]*?)<\/title>/i),
        description: pick(text, /<meta name="description" content="([^"]*)"/i),
        og_description: pick(text, /<meta property="og:description" content="([^"]*)"/i),
        details_text: block ? block.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 4000) : null
      };
      await sleep(500);
    }
  }
  save('rct.json', out);
  manifest.sources.rct = { pages: Object.keys(out).length };
}

save('manifest.json', manifest);
