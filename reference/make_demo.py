"""Write reference/data/hierarchy.json for a made-up person, so the disk viewer can be tried before your own
exports are processed. Everything here is invented. Deterministic: same output every run.

    python make_demo.py
"""
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(7)
OUT = Path(__file__).resolve().parent / "data" / "hierarchy.json"
START, WEEKS = date(2024, 11, 4), 104

# themes (the deeper invariants) → topics: (emoji, name, essence, [labels])
THEMES = [
    ("c_make_it_real", "🛠️", "Make It Real", "You trust an idea once you've built a rough version of it with your hands.",
     "What is the smallest thing I can make this week that proves the idea?", [
        ("🧰", "Building Tools", "You keep making small tools for your own work before anyone asks for them.", ["personal tools", "automation", "workflow design", "scripts"]),
        ("🧱", "Prototyping", "Rough versions first, polish later.", ["paper prototypes", "MVP scope", "throwaway code", "demo day"]),
        ("🕹️", "Game Design", "Rules and play as a way to think.", ["game loops", "level design", "playtesting"]),
        ("🥽", "VR & Spatial", "Putting ideas in space so you can walk around them.", ["WebXR", "spatial UI", "room scale", "Quest"]),
        ("📦", "Shipping", "Getting things out the door, and the fear before it.", ["launch fear", "release notes", "deadlines", "scope cuts"]),
        ("🎛️", "Creative Coding", "Code as a sketchbook.", ["generative art", "shaders", "p5.js"]),
        ("🗂️", "Second Brain", "Systems for keeping what you think.", ["note systems", "tagging", "weekly review", "archives"]),
        ("🧪", "Experiments", "Trying things to find out.", ["A/B tests", "hypotheses", "small bets"]),
        ("🤖", "Working With AI", "Pair-thinking with models.", ["prompting", "agents", "AI critique", "context"]),
        ("📐", "Design Systems", "Consistency you can build on.", ["tokens", "components", "type scale"]),
    ]),
    ("c_body_keeps_score", "🌿", "The Body Keeps Score", "Your energy tells you the truth before your plans do.",
     "What is my body asking for that my calendar ignores?", [
        ("😴", "Sleep & Energy", "Your days rise and fall with your nights.", ["4am waking", "naps", "caffeine", "wind-down"]),
        ("🏃", "Movement", "Thinking moves when you do.", ["running", "walks", "stretching", "strength"]),
        ("🔥", "Burnout Cycles", "The same spring crash, year after year.", ["overcommitting", "warning signs", "recovery", "saying no"]),
        ("🍲", "Food & Rhythm", "Meals as anchors in the day.", ["cooking", "fasting", "meal timing"]),
        ("🌅", "Protected Mornings", "The first two hours are for making.", ["morning routine", "phone-free", "deep work"]),
        ("🧘", "Stillness", "Learning to stop.", ["meditation", "breathwork", "silence"]),
        ("🌡️", "Stress Signals", "Noticing the tension early.", ["jaw tension", "doomscrolling", "irritability"]),
        ("🏔️", "Time Outside", "Nature as reset.", ["hiking", "camping", "weather"]),
    ]),
    ("c_worth_without_permission", "🪙", "Worth Without Permission", "You keep waiting for someone to say your work is worth it.",
     "Whose approval am I still pricing my life around?", [
        ("💸", "Money Fear", "Scarcity runs quietly under many decisions.", ["runway", "debt", "spending guilt", "budgets"]),
        ("🏷️", "Pricing Your Work", "You undercharge, then resent it.", ["workshop pricing", "rates", "discounts", "value"]),
        ("👨‍👦", "You and Your Father", "Old arguments about what counts as a real career.", ["approval", "career talks", "forgiveness"]),
        ("🧭", "Own Path vs Security", "The agency job or your own thing.", ["job offers", "freelance", "risk", "stability"]),
        ("🎤", "Being Seen", "Wanting to be known for your work, fearing it too.", ["posting online", "portfolio", "visibility", "imposter feelings"]),
        ("🤝", "Asking for Help", "Hard for you, every time.", ["mentors", "favors", "collaboration"]),
        ("📈", "Ambition", "How big is enough?", ["goals", "comparison", "growth"]),
        ("🧾", "Contracts & Terms", "Learning to say what you need in writing.", ["scope", "invoices", "negotiation"]),
    ]),
    ("c_memory_outside", "🧠", "Memory Outside the Head", "You think best when your thoughts are objects you can arrange.",
     "What changes in me when my memory lives outside me?", [
        ("🏛️", "Memory Palaces", "Places as containers for ideas.", ["method of loci", "VR palaces", "recall"]),
        ("✍️", "Writing It Down", "Journals, essays and notes as thinking.", ["journaling", "essays", "morning pages", "drafts"]),
        ("🗺️", "Maps of Thought", "Seeing the shape of what you think.", ["mind maps", "graphs", "timelines", "constellations"]),
        ("🪞", "Self-Knowledge", "Patterns you only see from far away.", ["patterns", "blind spots", "reflection"]),
        ("📚", "Reading", "Books that rearranged you.", ["book notes", "highlights", "rereading"]),
        ("🔁", "Weekly Reflection", "Choosing what to carry forward.", ["Sunday ritual", "carry forward", "letting go"]),
        ("🧩", "Symbols You Can Hold", "Emoji, icons and objects as handles for ideas.", ["emoji", "icons", "tokens"]),
        ("🕰️", "Personal History", "Looking back at who you were.", ["old journals", "photos", "turning points"]),
    ]),
    ("c_rooms_for_people", "🏡", "Rooms for People", "You keep designing spaces where people can meet their own thinking.",
     "What kind of room lets people think together?", [
        ("👥", "Community", "Gathering people around shared questions.", ["meetups", "online groups", "hosting"]),
        ("🎓", "Teaching", "Workshops as a way to learn twice.", ["workshops", "curriculum", "feedback"]),
        ("🏠", "Home & Studio", "The physical room you work in.", ["studio setup", "light", "clutter"]),
        ("🎨", "Spatial Design", "Shaping how a space feels.", ["exhibitions", "wayfinding", "materials"]),
        ("🌐", "Shared Worlds", "Places online that feel like places.", ["multiplayer", "virtual rooms", "presence"]),
        ("🎭", "Facilitation", "Holding a room well.", ["prompts", "pacing", "conflict"]),
        ("📷", "Capturing Places", "Scanning real rooms into the digital.", ["gaussian splats", "photogrammetry", "3D scans"]),
    ]),
    ("c_meaning_first", "🔭", "Meaning Before Method", "You want to know why before you optimize how.",
     "What is this actually for, for the person holding it?", [
        ("❓", "Big Questions", "The ones that never quite close.", ["purpose", "mortality", "time"]),
        ("🌀", "Philosophy", "Borrowing other people's lenses.", ["phenomenology", "stoicism", "ethics"]),
        ("🎯", "Focus & Priorities", "Too many good ideas.", ["one thing", "priorities", "abandoning projects"]),
        ("🧬", "Science Curiosity", "How things actually work.", ["neuroscience", "physics", "biology"]),
        ("🗣️", "Language", "Words that shape what you can think.", ["metaphors", "naming things", "coined words"]),
        ("⚖️", "Tech & Society", "What tools do to people.", ["attention", "privacy", "AI risk"]),
        ("🌱", "Growth", "Becoming someone new without losing yourself.", ["habits", "identity", "change"]),
    ]),
]
CLUSTERS = [("k_making", "🛠️", "around Making"), ("k_living", "🌿", "around Living Well"),
            ("k_people", "🤝", "around Other People"), ("k_knowing", "🔭", "around Knowing")]
CLUSTER_OF = {"c_make_it_real": "k_making", "c_body_keeps_score": "k_living", "c_worth_without_permission": "k_people",
              "c_memory_outside": "k_knowing", "c_rooms_for_people": "k_people", "c_meaning_first": "k_knowing"}
TYPES = ["question", "insight", "idea", "plan", "worry", "claim", "desire", "decision"]
STEMS = {
    "question": ["What would change if I took {l} seriously?", "Why do I keep coming back to {l}?", "How do other people handle {l}?"],
    "insight": ["I notice {l} gets louder whenever I'm tired.", "{L} is really about trust, not technique.", "Every time I skip {l}, the week goes sideways."],
    "idea": ["What if {l} were something I could walk around in?", "A tiny tool for {l} could save me an hour a day.", "Turn {l} into a weekly experiment."],
    "plan": ["This week: one small step on {l}.", "Block Tuesday mornings for {l}.", "Write a one-page plan for {l}."],
    "worry": ["I'm afraid {l} is just another way to avoid the real work.", "What if I'm wrong about {l}?", "I keep putting off {l} and it's costing me."],
    "claim": ["{L} matters more than I admit.", "Most advice about {l} ignores the body.", "{L} works best when it's small."],
    "desire": ["I want {l} to feel lighter.", "I'd love a room where {l} happens naturally.", "I want to be someone who does {l} without drama."],
    "decision": ["I'm done treating {l} as optional.", "Decided: {l} gets a fixed slot.", "No more waiting for permission on {l}."],
}
TITLES = ["Late-night idea dump", "Planning the week", "Rough draft feedback", "Talking it through", "Quick question",
          "Brainstorm", "Sunday review", "Stuck on this", "Sketching a plan", "Reading notes", "Morning pages",
          "Prototype help", "Pricing check", "Workshop outline", "Debugging", "Essay draft"]


def week_key(i):
    d = START + timedelta(weeks=i)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def activity(strength):
    """A believable on/off pattern of weeks: bursts, gaps and returns."""
    weeks, i = {}, random.randint(0, 40)
    while i < WEEKS:
        burst = random.randint(1, 4)
        for j in range(burst):
            if i + j < WEEKS:
                weeks[week_key(i + j)] = random.randint(1, 2 + int(strength * 6))
        i += burst + random.randint(1, int(14 - strength * 10) + 1)
    return weeks


nodes = [{"id": "you", "kind": "root", "name": "you", "emoji": "✶",
          "essence": ""}]
threads, links, lens_inv, lens_clu = {}, [], {}, {}
thread_n = 0
topic_threads = {}


def make_thread(day):
    global thread_n
    thread_n += 1
    tid = f"demo:{thread_n:04d}"
    threads[tid] = {"title": random.choice(TITLES), "emoji": "💬", "started": day}
    return tid


for cid, cem, cname, cess, cq, topics in THEMES:
    nodes.append({"id": cid, "kind": "group", "lens": "invariants", "name": cname, "emoji": cem, "essence": cess, "question": cq})
    for rank, (em, name, ess, labels) in enumerate(topics):
        tid = "t_" + name.lower().replace(" & ", "_").replace(" ", "_").replace("-", "_")
        strength = max(.15, 1 - rank / len(topics) + random.uniform(-.25, .25))
        weeks = activity(strength)
        count = sum(weeks.values())
        ws = sorted(weeks)
        first = START + timedelta(weeks=next(i for i in range(WEEKS) if week_key(i) == ws[0]))
        last = START + timedelta(weeks=next(i for i in range(WEEKS) if week_key(i) == ws[-1]))
        returns = sum(1 for a, b in zip(ws, ws[1:]) if ws.index(b) and
                      (int(b[-2:]) - int(a[-2:])) % 52 >= 3)
        ths = [make_thread((first + timedelta(days=random.randint(0, max(1, (last - first).days)))).isoformat())
               for _ in range(max(3, count // 4))]
        topic_threads[tid] = set(ths)
        nodes.append({"id": tid, "kind": "topic", "name": name, "emoji": em, "essence": ess, "count": count,
                      "span": (last - first).days, "first": first.isoformat(), "last": last.isoformat(),
                      "returns": returns, "invariance": round(min(.95, .25 + strength * .6), 3),
                      "invariant": strength > .75 and returns >= 3, "nthreads": len(ths), "weeks": weeks,
                      "samples": [], "grade": "solid", "threads": ths[:5],
                      "size": round(math.sqrt(count * ((last - first).days + 30)), 2)})
        lens_inv[tid] = cid
        lens_clu[tid] = CLUSTER_OF[cid]
        samples = []
        for l in labels:
            lid = f"l:{tid}:{l.replace(' ', '_')}"
            lw = {w: max(1, c // 2) for w, c in weeks.items() if random.random() < .6} or dict(list(weeks.items())[:1])
            nodes.append({"id": lid, "kind": "label", "parent": tid, "name": l, "count": sum(lw.values()), "weeks": lw,
                          "first": first.isoformat(), "last": last.isoformat(), "threads": random.sample(ths, min(3, len(ths))),
                          "size": round(math.sqrt(sum(lw.values()) * 40), 2)})
            for k in range(2):
                ty = random.choice(TYPES)
                text = random.choice(STEMS[ty]).format(l=l, L=l[0].upper() + l[1:])
                wk = random.choice(sorted(lw))
                th = random.choice(ths)
                nodes.append({"id": f"i:{lid}:{k}", "kind": "idea", "parent": lid, "name": text, "type": ty, "week": wk,
                              "time": threads[th]["started"], "thread": th, "verified": True, "size": 4})
                samples.append(text)
        nodes[[n["id"] for n in nodes].index(tid)]["samples"] = samples[:3]

# coined words (lexicon terms), each living mostly in one topic
TERMS = [("idea-objects", "🪨", "t_symbols_you_can_hold", "Ideas turned into things you can pick up and place."),
         ("the 4am club", "🌒", "t_sleep_energy", "The waking hour where worries get loud."),
         ("permission debt", "🧾", "t_pricing_your_work", "What you owe yourself every time you wait for a yes."),
         ("runway math", "🛫", "t_money_fear", "Counting months instead of choices."),
         ("studio weather", "🌦️", "t_home_studio", "How the room's mood changes the work."),
         ("thinking rooms", "🚪", "t_shared_worlds", "Spaces built for meeting your own thoughts."),
         ("small bets", "🎲", "t_experiments", "Cheap experiments that can fail without hurting."),
         ("spring crash", "🍂", "t_burnout_cycles", "The yearly collapse after an overfull winter."),
         ("carry forward", "🎒", "t_weekly_reflection", "The one thing chosen each week to keep."),
         ("scan-and-place", "📍", "t_capturing_places", "Capture a real room, then put ideas inside it."),
         ("rough-first", "✏️", "t_prototyping", "Make the ugly version before you plan the pretty one."),
         ("quiet hours", "🔕", "t_protected_mornings", "Time with no inputs at all."),
         ("dad voice", "📞", "t_you_and_your_father", "The inner critic that sounds like home."),
         ("context window", "🪟", "t_working_with_ai", "How much an AI can hold at once, and how much you can."),
         ("loci walk", "🚶", "t_memory_palaces", "Recalling by walking a remembered route.")]
ids = {n["id"] for n in nodes}
term_ids = []
for key, em, topic, definition in TERMS:
    if topic not in ids:
        continue
    tid = "w:" + key.replace(" ", "_")
    term_ids.append(tid)
    ths = random.sample(sorted(topic_threads[topic]), min(4, len(topic_threads[topic])))
    nodes.append({"id": tid, "kind": "term", "parent": topic, "key": key, "name": key, "emoji": em, "termkind": "coined",
                  "essence": definition, "count": random.randint(8, 60), "ai": random.randint(0, 20), "nthreads": len(ths),
                  "first": "2025-01-10", "last": "2026-10-01", "threads": ths, "size": 6})

topics = [n for n in nodes if n["kind"] == "topic"]
for i, a in enumerate(topics):  # co-occurrence: mostly within a theme, sometimes across
    for b in topics[i + 1:]:
        same = lens_inv[a["id"]] == lens_inv[b["id"]]
        if random.random() < (.35 if same else .05):
            w = random.randint(6, 30) if same else random.randint(3, 16)
            links.append({"a": a["id"], "b": b["id"], "kind": "cooccur", "why": f"{w} shared conversations", "w": w})
UNEXPECTED = [("t_sleep_energy", "t_pricing_your_work"), ("t_memory_palaces", "t_you_and_your_father"),
              ("t_game_design", "t_facilitation"), ("t_money_fear", "t_protected_mornings"),
              ("t_capturing_places", "t_personal_history"), ("t_burnout_cycles", "t_shipping"),
              ("t_language", "t_symbols_you_can_hold"), ("t_stillness", "t_creative_coding"),
              ("t_being_seen", "t_writing_it_down"), ("t_time_outside", "t_big_questions")]
for a, b in UNEXPECTED:
    if a in ids and b in ids:
        s = random.randint(9, 24)
        links.append({"a": a, "b": b, "kind": "unexpected", "w": round(s / 10, 2),
                      "why": f"{s} shared conversations ({random.randint(25, 45)}% of the smaller one), yet different themes"})
for t in term_ids:  # lexicon links between related coined words and topics
    others = random.sample([x for x in term_ids if x != t], 1)
    links.append({"a": t, "b": others[0], "kind": "lexicon", "why": "travels with", "w": 1})
    links.append({"a": t, "b": random.choice(topics)["id"], "kind": "lexicon", "why": "shared conversations", "w": .2})

out = {"generated": "demo", "range": {"first": START.isoformat(), "last": (START + timedelta(weeks=WEEKS - 1)).isoformat(),
                                      "weeks": [week_key(i) for i in range(WEEKS)]},
       "lenses": [{"name": "invariants", "label": "Themes", "kind": "invariants", "groups": [t[0] for t in THEMES],
                   "parent": lens_inv, "also": [["t_working_with_ai", "c_memory_outside"], ["t_spatial_design", "c_make_it_real"]],
                   "inferred": []},
                  {"name": "clusters", "label": "Clusters (co-occurrence)", "kind": "clusters", "groups": [c[0] for c in CLUSTERS],
                   "parent": lens_clu, "also": [], "inferred": []}],
       "nodes": nodes + [{"id": cid, "kind": "group", "lens": "clusters", "name": name, "emoji": em,
                          "essence": "Topics that keep coming up together (demo)."} for cid, em, name in CLUSTERS],
       "links": links, "threads": threads}
nodes[0]["essence"] = (f"A made-up person: {sum(t['count'] for t in topics):,} ideas from {len(threads):,} conversations, "
                      f"{out['range']['first'][:7]} → {out['range']['last'][:7]} (demo data)")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print(f"Demo written: {len(topics)} topics, {sum(n['kind'] == 'label' for n in nodes)} labels, "
      f"{sum(n['kind'] == 'idea' for n in nodes)} ideas, {len(term_ids)} terms, {len(links)} links → {OUT}")
