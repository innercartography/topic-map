# `hierarchy.json`: the disk's data format

The disk viewer (`reference/disk.html`) reads one file, `data/hierarchy.json`. Anything that writes this format can be explored on the disk: an AI-chat pipeline, a notes vault, a reading log. `reference/make_demo.py` writes a complete example.

```jsonc
{
  "generated": "2026-10-20T12:00:00",          // "demo" hides links to conversations and the lexicon
  "range": { "first": "2024-11-04", "last": "2026-10-26",
             "weeks": ["2024-W45", "2024-W46", "..."] },   // every ISO week in range, oldest first (time windows use the last 12 / 4)

  "lenses": [                                   // ways of arranging the top of the tree; the first is the default
    { "name": "invariants",                     // id, also used in the URL: disk.html#invariants/<node id>
      "label": "Themes",                        // button text (anything after " (" is dropped)
      "kind": "invariants",                     // invariants | clusters | ontology
      "groups": ["c_make_it_real", "..."],      // the group nodes, children of "you"
      "parent": { "t_prototyping": "c_make_it_real" },   // every topic → its one group in the tree
      "also": [["t_working_with_ai", "c_memory_outside"]], // extra memberships, drawn as dotted "also under" links
      "inferred": ["t_reading"] }               // topics this lens didn't name; filed by shared conversations
  ],

  "nodes": [
    { "id": "you", "kind": "root", "name": "you", "emoji": "✶", "essence": "one line about the whole archive" },

    { "id": "c_make_it_real", "kind": "group", "lens": "invariants", "name": "Make It Real", "emoji": "🛠️",
      "essence": "one sentence", "question": "the open question it keeps asking" },

    { "id": "t_prototyping", "kind": "topic", "name": "Prototyping", "emoji": "🧱", "essence": "one line",
      "count": 120,                             // ideas
      "span": 540,                              // days from first to last  (topic size = √(count × (span + 30)))
      "first": "2025-01-06", "last": "2026-06-30",
      "weeks": { "2025-W02": 3, "2025-W03": 1 },// ideas per ISO week (sparklines and time windows)
      "returns": 6,                             // came back after 2+ weeks away
      "invariance": 0.81, "invariant": true,    // gold ring when true
      "nthreads": 31, "threads": ["conv-id", "..."],   // top conversations for the side panel
      "samples": ["a quote in your own words", "..."], "grade": "solid" },

    { "id": "l:t_prototyping:mvp_scope", "kind": "label", "parent": "t_prototyping", "name": "MVP scope",
      "count": 14, "weeks": { "2025-W02": 1 }, "first": "...", "last": "...", "threads": ["..."] },

    { "id": "i:...", "kind": "idea", "parent": "l:t_prototyping:mvp_scope", "name": "the idea, in your words",
      "type": "question", "week": "2025-W02", "time": "2025-01-08", "thread": "conv-id", "verified": true },

    { "id": "w:small_bets", "kind": "term", "parent": "t_experiments", "key": "small bets", "name": "small bets",
      "emoji": "🎲", "termkind": "coined", "essence": "a definition", "count": 22, "ai": 4,
      "nthreads": 9, "first": "...", "last": "...", "threads": ["..."] }
  ],

  "links": [                                    // cross-links that aren't parent/child
    { "a": "t_prototyping", "b": "t_shipping", "kind": "cooccur", "w": 18, "why": "18 shared conversations" },
    { "a": "t_sleep_energy", "b": "t_pricing_your_work", "kind": "unexpected", "w": 1.7,
      "why": "17 shared conversations (31% of the smaller one), yet different themes" },
    { "a": "w:small_bets", "b": "w:rough_first", "kind": "lexicon", "w": 1, "why": "travels with" }
  ],

  "threads": { "conv-id": { "title": "Planning the week", "emoji": "💬", "started": "2025-01-08" } }
}
```

## Notes

- **Kinds:** `root` (exactly one, id `you`), `group`, `topic`, `label`, `idea` and `term`. Topics find their parent through the active lens; every other non-root node has a fixed `parent`.
- **Required fields:** every node needs `id`, `kind` and `name`, and non-topic nodes need `parent`. Topics also need `count`, `span` and `weeks`, and labels need `count` and `weeks`; these drive sizes and time windows. Everything else is optional and only fills the side panel.
- **Co-occurrence links** are drawn only for the strongest pairs (`w` ≥ 18) until you hover or focus a node, when its 10 strongest show. Tune this in `draw()` if your weights run smaller.
- **Size:** about 3,000 nodes and 2,000 links stay smooth (a frame takes ~15 ms in software rendering).
