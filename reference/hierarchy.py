# Reference copy from the author's own Topic Map project (topicmap/hierarchy.py). It is not standalone: it imports
# DATA / MAP paths and load_atoms / load_topics from that project's other modules, and reads data/map.json,
# data/topics.json, data/atoms.jsonl and (optionally) data/lexicon.json. Read it for the logic: filing unnamed
# topics under the closest invariant, plain-Python clusters, lexicon links and "unexpected" links. The output
# format it writes is described in docs/hierarchy-format.md.
"""The hierarchy behind the disk view (/disk) — plain Python, no model.

One tree, read from the centre out:  you → the invariants ("currents") → the topics → each topic's labels → a few
of your top ideas, plus the lexicon terms that live in each topic's conversations. A topic can belong to several
invariants (or parent ideas); it keeps one tree parent and the others become "also" links. Most topics aren't named
by any invariant, so they're filed under the one whose topics they share the most conversations with ("inferred").

Cross-links that aren't parent/child:
  cooccur     topics that come up in the same conversations (the map's edges)
  lexicon     a term's "related", "travels_with" and "synonyms" entries, and the topics it shares conversations with
  unexpected  pairs that share an unusual share of their conversations but have no direct link and sit under
              different invariants — the harder-to-see connections

Lenses rearrange the top of the tree: "invariants" (from the develop stage), "clusters" (plain Python, communities
of co-occurring topics), and one per parent-idea ontology written by the optional Opus stage:

  python -m topicmap hierarchy                                 rebuild data/hierarchy.json (also runs after analyze)
  python -m topicmap ontology                                  Opus proposes 8–15 parent ideas over the topics (1 call)
  python -m topicmap ontology --lens "what is each topic FOR?" --name purpose     another lens, stored by its name
"""
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

from .config import DATA, MAP
from .consolidate import load_atoms, load_topics

HIERARCHY = DATA / "hierarchy.json"
ONTOLOGIES = DATA / "ontologies.json"   # cached Opus runs, one per lens name
LABELS_PER_TOPIC = 8
IDEAS_PER_LABEL = 2
TERMS_PER_TOPIC_LINKS = 2    # extra topics a term is linked to, besides its tree parent
UNEXPECTED = 60              # how many hidden connections to keep
THREADS_PER_NODE = 5         # top conversations listed in a node's panel
CLUSTER_RESOLUTION = 1.5     # >1 splits the co-occurrence clusters finer (1.5 → ~10 clusters here)


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "default"


def infer_group(tid, groups, sim):
    """The group (invariant / parent idea) whose topics this topic shares the most conversations with —
    cosine overlap averaged over the group, so a group with one huge topic doesn't swallow everything."""
    best, best_s = None, 0.0
    for gid, members in groups.items():
        ms = [m for m in members if m != tid]
        if not ms:
            continue
        s = sum(sim.get((min(tid, m), max(tid, m)), 0) for m in ms) / len(ms)
        if s > best_s:
            best, best_s = gid, s
    return best


def lens_from_groups(name, label, groups, topics, sim, kind, extra=None):
    """groups: {group_id: [topic ids, strongest first]} → {parent: {topic: group}, also: [[topic, group]]}."""
    parent, also = {}, []
    member_of = defaultdict(list)
    for gid, members in groups.items():
        for t in members:
            if t in topics:
                member_of[t].append(gid)
    for t in topics:
        gs = member_of.get(t)
        if gs:  # tree parent: where it's listed strongest (earliest), then the smaller group
            gs = sorted(gs, key=lambda g: (groups[g].index(t) / len(groups[g]), len(groups[g])))
            parent[t] = gs[0]
            also += [[t, g] for g in gs[1:]]
    known = {g: [t for t in ms if t in topics] for g, ms in groups.items()}
    inferred = []
    for t in topics:
        if t not in parent:
            g = infer_group(t, known, sim) or next(iter(groups))
            parent[t] = g
            inferred.append(t)
    return {"name": name, "label": label, "kind": kind, "groups": list(groups), "parent": parent, "also": also,
            "inferred": inferred, **(extra or {})}


def clusters(topics, sim, min_size=3, resolution=CLUSTER_RESOLUTION):
    """Communities of topics that share conversations: greedy modularity merging (Clauset–Newman–Moore style)
    on the cosine overlap of their conversation sets. Deterministic, plain Python, ~125 topics in well under a second.
    Returns {representative topic: [members, most central first]}."""
    w = defaultdict(dict)
    for (a, b), s in sim.items():
        if s > 0:
            w[a][b] = w[b][a] = s
    deg = {t: sum(w[t].values()) for t in topics}
    total = sum(deg.values()) / 2 or 1
    comm = {t: {t} for t in topics}
    cdeg = dict(deg)
    between = defaultdict(float)  # (c1, c2) → summed weight between communities
    for a in topics:
        for b, s in w[a].items():
            if a < b:
                between[(a, b)] += s
    while True:
        best, gain = None, 0.0
        for (a, b), e in between.items():
            dq = e / total - resolution * cdeg[a] * cdeg[b] / (2 * total * total)
            if dq > gain:
                best, gain = (a, b), dq
        if not best:
            break
        a, b = best
        comm[a] |= comm.pop(b)
        cdeg[a] += cdeg.pop(b)
        merged = defaultdict(float)
        for (x, y), e in between.items():
            if (x, y) == (a, b):
                continue
            x, y = (a if x == b else x), (a if y == b else y)
            if x != y:
                merged[(min(x, y), max(x, y))] += e
        between = merged
    groups = {}
    for ms in comm.values():
        ms = sorted(ms, key=lambda t: -sum(w[t].get(o, 0) for o in ms))  # most central first
        groups[ms[0]] = ms
    big = {g: ms for g, ms in groups.items() if len(ms) >= min_size} or groups
    for g, ms in groups.items():
        if g not in big:
            for t in ms:
                max(big.values(), key=lambda bs: sum(w[t].get(o, 0) for o in bs) / len(bs)).append(t)
    return big


def build(log=print):
    if not MAP.exists():
        raise SystemExit("No map yet — run `python -m topicmap analyze` first.")
    m = json.loads(MAP.read_text(encoding="utf-8"))
    tx = load_topics()
    atoms = load_atoms()
    weeks_all = m["range"]["weeks"]
    stats = {s["id"]: s for s in m["topics"]}
    topics = list(stats)
    threads_meta = m.get("threads", {})

    # ---- what lives under each topic: labels, ideas, conversations ----
    label_atoms = defaultdict(list)          # (topic, label) → atoms
    topic_threads = defaultdict(Counter)     # topic → thread → ideas
    for a in atoms:
        seen = set()
        for l in a["labels"]:
            t = tx["labels"].get(l)
            if t in stats:
                label_atoms[(t, l)].append(a)
                if t not in seen:
                    topic_threads[t][a["thread"]] += 1
                    seen.add(t)
    per_topic_labels = defaultdict(list)
    for (t, l), items in label_atoms.items():
        per_topic_labels[t].append((l, items))

    cooc = {(min(e["a"], e["b"]), max(e["a"], e["b"])): e["w"] for e in m.get("edges", [])}
    sizes = {t: max(1, stats[t]["count"]) for t in topics}
    topic_sets = {t: set(topic_threads[t]) for t in topics}
    sim = {}  # cosine overlap of every pair of topics' conversations
    for i, a in enumerate(topics):
        for b in topics[i + 1:]:
            shared = len(topic_sets[a] & topic_sets[b])
            if shared:
                sim[(min(a, b), max(a, b))] = shared / math.sqrt(len(topic_sets[a]) * len(topic_sets[b]))

    nodes = {}
    used_threads = set()

    def top_threads(counter):
        out = [tid for tid, _ in counter.most_common(THREADS_PER_NODE) if tid in threads_meta]
        used_threads.update(out)
        return out

    nodes["you"] = {"id": "you", "kind": "root", "name": "you", "emoji": "✶",
                    "essence": f"{len(atoms):,} ideas from {len(threads_meta):,} conversations, "
                               f"{m['range']['first'][:10]} → {m['range']['last'][:10]}"}

    for t in topics:
        s = stats[t]
        nodes[t] = {"id": t, "kind": "topic", "name": s["name"], "emoji": s["emoji"], "essence": s.get("essence", ""),
                    "count": s["count"], "span": s["span_days"], "first": s["first"][:10], "last": s["last"][:10],
                    "returns": s["returns"], "invariance": s["invariance"], "invariant": s["invariant"],
                    "nthreads": s["threads"], "weeks": s["weeks"], "samples": s.get("samples", [])[:3],
                    "grade": s.get("grade"), "threads": top_threads(topic_threads[t]),
                    "size": round(math.sqrt(s["count"] * (s["span_days"] + 30)), 2)}  # ideas × span

    # labels (sub-topics) and their best ideas
    n_labels = n_ideas = 0
    for t, ls in per_topic_labels.items():
        ls.sort(key=lambda li: (-len(li[1]), li[0]))
        keep = [li for li in ls if len(li[1]) >= 2][:LABELS_PER_TOPIC] or ls[:3]
        for l, items in keep:
            lid = f"l:{t}:{slug(l)}"
            wk = Counter(a["week"] for a in items)
            nodes[lid] = {"id": lid, "kind": "label", "parent": t, "name": l, "count": len(items), "weeks": dict(wk),
                          "first": min(a["time"] for a in items)[:10], "last": max(a["time"] for a in items)[:10],
                          "threads": top_threads(Counter(a["thread"] for a in items)),
                          "size": round(math.sqrt(len(items) * 40), 2)}
            n_labels += 1
            for a in sorted(items, key=lambda a: (-a["weight"], a["time"]))[:IDEAS_PER_LABEL]:
                iid = "i:" + a["id"]
                if iid in nodes:
                    continue
                if a["thread"] in threads_meta:
                    used_threads.add(a["thread"])
                nodes[iid] = {"id": iid, "kind": "idea", "parent": lid, "name": a["text"], "type": a["type"],
                              "week": a["week"], "time": a["time"][:10], "thread": a["thread"],
                              "verified": a.get("verified"), "size": 3 + a["weight"]}
                n_ideas += 1

    # ---- lexicon terms, attached to topics through the conversations they share ----
    links = []
    lex = load_json(DATA / "lexicon.json", {}).get("terms", [])
    terms = [c for c in lex if c.get("definition") and not c.get("hidden")]
    term_ids = {}
    for c in terms:
        ths = set(c.get("cap_threads", []))
        score = []
        for t in topics:
            shared = len(ths & topic_sets[t])
            if shared >= 2:
                score.append((shared / math.sqrt(len(topic_sets[t]) * len(ths)), shared, t))
        if not score:
            continue
        score.sort(reverse=True)
        tid = "w:" + c["key"]
        term_ids[c["key"]] = tid
        nodes[tid] = {"id": tid, "kind": "term", "parent": score[0][2], "key": c["key"], "name": c["term"],
                      "emoji": c.get("symbol") or "", "termkind": c.get("kind"), "essence": c.get("definition", ""),
                      "count": c.get("me_msgs", 0), "ai": c.get("ai_msgs", 0), "nthreads": len(ths),
                      "first": (c.get("first_me") or c.get("cap_first") or "")[:10],
                      "last": (c.get("last_me") or c.get("cap_last") or "")[:10],
                      "threads": top_threads(Counter({x: threads_meta[x].get("started") or "" for x in ths if x in threads_meta})),
                      "size": round(math.sqrt(max(1, c.get("me_msgs", 1)) * 20), 2)}
        for sc, shared, t in score[1:1 + TERMS_PER_TOPIC_LINKS]:
            links.append({"a": tid, "b": t, "kind": "lexicon", "why": f"{shared} shared conversations",
                          "w": round(sc, 3)})
    seen_pairs = set()
    for c in terms:
        a = term_ids.get(c["key"])
        if not a:
            continue
        for f in ("synonyms", "related", "travels_with"):
            for x in c.get(f) or []:
                b = term_ids.get(x.get("k") if isinstance(x, dict) else None)
                if b and b != a and (min(a, b), max(a, b)) not in seen_pairs:
                    seen_pairs.add((min(a, b), max(a, b)))
                    links.append({"a": a, "b": b, "kind": "lexicon", "why": f.replace("_", " "), "w": 1})

    for (a, b), w in cooc.items():
        if a in nodes and b in nodes:
            links.append({"a": a, "b": b, "kind": "cooccur", "why": f"{w} shared conversations", "w": w})

    # ---- lenses ----
    currents = m.get("currents", [])
    for c in currents:
        nodes[c["id"]] = {"id": c["id"], "kind": "group", "lens": "invariants", "name": c["name"], "emoji": c["emoji"],
                          "essence": c.get("essence", ""), "question": c.get("question", "")}
    lenses = []
    if currents:
        groups = {c["id"]: c["topics"] for c in currents}
        lenses.append(lens_from_groups("invariants", "Invariants", groups, topics, sim, "invariants"))
    cl = clusters(topics, sim)
    cgroups = {}
    for i, (g, ms) in enumerate(sorted(cl.items(), key=lambda kv: -sum(sizes[t] for t in kv[1]))):
        gid = f"k{i}"
        head = ms[0]
        nodes[gid] = {"id": gid, "kind": "group", "lens": "clusters", "name": f"around {stats[head]['name']}",
                      "emoji": stats[head]["emoji"],
                      "essence": "Topics that keep coming up together: " + ", ".join(stats[t]["name"] for t in ms[:6])
                                 + ("…" if len(ms) > 6 else "")}
        cgroups[gid] = ms
    lens = lens_from_groups("clusters", "Clusters (co-occurrence)", cgroups, topics, sim, "clusters")
    for t in topics:  # a topic also belongs to a second cluster it's nearly as tied to
        tie = {g: sum(sim.get((min(t, o), max(t, o)), 0) for o in ms if o != t) / max(1, len(ms)) for g, ms in cgroups.items()}
        home_g = lens["parent"][t]
        g, v = max(((g, v) for g, v in tie.items() if g != home_g), key=lambda gv: gv[1], default=(None, 0))
        if g and v > 0 and v >= 0.9 * tie[home_g]:
            lens["also"].append([t, g])
    lenses.append(lens)
    for name, o in load_json(ONTOLOGIES, {}).items():
        og = {}
        for p in o.get("parents", []):
            gid = f"o:{name}:{p['id']}"
            nodes[gid] = {"id": gid, "kind": "group", "lens": "o:" + name, "name": p["name"], "emoji": p.get("emoji", ""),
                          "essence": p.get("essence", "")}
            og[gid] = [t for t in p.get("topics", []) if t in stats]
        if og:
            lenses.append(lens_from_groups("o:" + name, f"Parent ideas · {name}", og, topics, sim, "ontology",
                                           {"question": o.get("lens"), "engine": o.get("engine"),
                                            "generated": o.get("generated")}))

    # ---- unexpected: high shared-conversation overlap, no direct link, different invariants ----
    inv = lenses[0]["parent"] if lenses else {}
    clu = lens["parent"]
    linked = {(min(l["a"], l["b"]), max(l["a"], l["b"])) for l in links}
    def topic_of(n):
        while n in nodes and nodes[n]["kind"] != "topic" and nodes[n].get("parent"):
            n = nodes[n]["parent"]
        return n
    cand = {t: topic_sets[t] for t in topics if len(topic_sets[t]) >= 3}
    for c in terms:
        if c["key"] in term_ids and len(c.get("cap_threads", [])) >= 3:
            cand[term_ids[c["key"]]] = set(c["cap_threads"])
    keys = sorted(cand)
    found = []
    for i, a in enumerate(keys):
        A = cand[a]
        for b in keys[i + 1:]:
            if (a, b) in linked or nodes[a].get("parent") == b or nodes[b].get("parent") == a:
                continue
            ta, tb = topic_of(a), topic_of(b)
            if ta == tb or not inv.get(ta) or inv.get(ta) == inv.get(tb) or clu.get(ta) == clu.get(tb):
                continue  # under the same invariant or in the same co-occurrence cluster: not hidden
            shared = len(A & cand[b])
            if shared < 3:
                continue
            cos = shared / math.sqrt(len(A) * len(cand[b]))
            found.append((cos * math.log1p(shared), shared, shared / min(len(A), len(cand[b])), a, b))
    found.sort(reverse=True)
    per_node, kept = Counter(), 0
    for score, shared, overlap, a, b in found:
        if kept >= UNEXPECTED:
            break
        if per_node[a] >= 3 or per_node[b] >= 3:  # spread them out, so one hub term doesn't take them all
            continue
        per_node[a] += 1
        per_node[b] += 1
        kept += 1
        links.append({"a": a, "b": b, "kind": "unexpected", "w": round(score, 3),
                      "why": f"{shared} shared conversations ({overlap:.0%} of the smaller one), yet different invariants and clusters"})

    out = {"generated": datetime.now().isoformat(timespec="seconds"),
           "range": {"first": m["range"]["first"], "last": m["range"]["last"], "weeks": weeks_all},
           "lenses": lenses, "nodes": list(nodes.values()), "links": links,
           "threads": {tid: {"title": threads_meta[tid]["title"], "emoji": threads_meta[tid].get("emoji", ""),
                             "started": (threads_meta[tid].get("started") or "")[:10]}
                       for tid in sorted(used_threads) if tid in threads_meta}}
    HIERARCHY.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    kinds = Counter(l["kind"] for l in links)
    log(f"Hierarchy written: {len(currents)} invariants, {len(topics)} topics, {n_labels} labels, {n_ideas} ideas, "
        f"{len(term_ids)} terms; links: " + ", ".join(f"{k} {v}" for k, v in kinds.most_common())
        + f"; lenses: {', '.join(l['name'] for l in lenses)}.")
    return out


# ---------- optional: parent ideas, proposed by Opus (stage "ontology") ----------

ONTOLOGY_SCHEMA = {
    "type": "object",
    "properties": {"parents": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "name": {"type": "string"}, "emoji": {"type": "string"},
                       "essence": {"type": "string"},
                       "topics": {"type": "array", "items": {"type": "string"}}},
        "required": ["id", "name", "emoji", "essence", "topics"], "additionalProperties": False}}},
    "required": ["parents"], "additionalProperties": False,
}

ONTOLOGY_PROMPT = """Below are {n} topics one person keeps returning to across ~2 years of AI conversations, each with an id,
emoji, name, a one-line essence, how many of their ideas fall under it, and a few of their own sample sentences.

Propose 8–15 PARENT IDEAS: larger ideas that several of these topics are really instances, tools or faces of.
Lens for this pass — group the topics by this question: {lens}

Rules:
- Every topic id must appear under at least one parent. A topic MAY sit under 2–3 parents when it truly serves both;
  list each parent's topics strongest-fitting first.
- A parent idea is an idea, not a bucket: name it in 2–5 words the person might use themselves; emoji = one symbol;
  essence = one sentence in second person saying what this larger idea is for them.
- Prefer parents that reveal non-obvious kinship (topics that look unrelated but serve the same idea) over grouping
  by surface vocabulary.
- id: p_snake_case. Use only the topic ids given.

## Topics
{topics}
"""


def topics_block(m):
    lines = []
    for s in sorted(m["topics"], key=lambda s: -s["count"]):
        samples = " | ".join(x[:140] for x in s.get("samples", [])[:2])
        lines.append(f'{s["id"]}  {s["emoji"]} {s["name"]} — {s.get("essence", "")} ({s["count"]} ideas) e.g. {samples}')
    return "\n".join(lines)


def ontology(lens="", name=None, redo=False, yes=False, log=print):
    from .llm import LLM, engine_for
    if not MAP.exists():
        raise SystemExit("No map yet — run `python -m topicmap analyze` first.")
    lens = lens.strip() or "what larger idea is each topic part of?"
    name = slug(name or ("default" if lens.startswith("what larger idea") else lens))
    store = load_json(ONTOLOGIES, {})
    if name in store and store[name].get("lens") == lens and not redo:
        log(f"Ontology '{name}' is cached ({len(store[name]['parents'])} parent ideas) — use --redo to ask again.")
        return build(log)
    m = json.loads(MAP.read_text(encoding="utf-8"))
    prompt = ONTOLOGY_PROMPT.format(n=len(m["topics"]), lens=lens, topics=topics_block(m))
    engine = engine_for("ontology")
    shell_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    log(f"Ontology '{name}' — lens: {lens}\n  1 call to {engine} (~{len(prompt) // 4:,} prompt tokens). "
        + ("Bills the API: ANTHROPIC_API_KEY is set in this shell." if engine.startswith("claude:") and shell_key else
           "Runs on your Claude Code subscription." if engine.startswith("claude:") else
           "Bills the API (pay per token)." if engine.startswith("api:") else "Runs locally."))
    if not yes:
        try:
            if input("  Go ahead? [y/N] ").strip().lower() not in ("y", "yes"):
                return log("  Skipped.")
        except EOFError:
            return log("  Skipped (no answer — pass --yes to run without asking).")
    llm = LLM("ontology")
    r = llm.json(prompt, ONTOLOGY_SCHEMA, effort="medium")
    known = {s["id"] for s in m["topics"]}
    parents = []
    for p in r.get("parents", []):
        p["topics"] = [t for t in dict.fromkeys(p.get("topics", [])) if t in known]
        p["id"] = slug(p.get("id") or p["name"])
        if p["topics"]:
            parents.append(p)
    missing = known - {t for p in parents for t in p["topics"]}
    store[name] = {"lens": lens, "engine": str(llm), "generated": datetime.now().isoformat(timespec="seconds"),
                   "parents": parents, "unplaced": sorted(missing)}
    ONTOLOGIES.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    multi = sum(1 for t in known if sum(t in p["topics"] for p in parents) > 1)
    log(f"  {len(parents)} parent ideas; {multi} topics sit under more than one"
        + (f"; {len(missing)} left unplaced (filed by co-occurrence)" if missing else "") + ":")
    for p in parents:
        log(f"    {p['emoji']} {p['name']} ({len(p['topics'])})")
    return build(log)
