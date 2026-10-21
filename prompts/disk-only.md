# Poincaré disk only (advanced)

For people who already have their own material (a notes vault, an existing topic list, their own chat pipeline) and just want the disk as a compass over it. Copy `reference/disk.html` and `docs/hierarchy-format.md` from this repo into your project, open Claude Code there, and paste:

```text
I want a Poincaré-disk "compass" over my own ideas. In this folder: disk.html (a finished viewer that reads
data/hierarchy.json) and hierarchy-format.md (that file's format). My material is: <describe it, e.g. "an
Obsidian vault in ./vault", "topics.csv with one row per topic and a notes/ folder", "my own data/atoms.jsonl">.

1. Look at my material and propose the tree before writing code: what the centre is ("you"), what the 3–7 groups
   are, what counts as a topic, and what sits under each topic (sub-topics, then individual ideas or notes). Use
   plain Python for everything you can count; ask before using any model, and say how many calls it would take.
2. Write build_hierarchy.py (plain Python, no dependencies) that writes data/hierarchy.json in exactly that format:
   - topic size from volume × time span, with "weeks" counts, so big long-lived topics take the centre;
   - topics no group names get filed under the group whose topics they share the most sources with ("inferred");
   - links: co-occurrence (shared sources), and "unexpected" pairs, meaning high overlap but no direct link and
     different groups (at most 3 per node);
   - a second lens ("clusters") from plain-Python community detection on the co-occurrence graph.
3. Serve the folder (python -m http.server 8000), open http://localhost:8000/disk.html, click into a few nodes,
   and fix anything in the data that looks wrong (empty groups, one group swallowing everything, a hub node
   collecting every unexpected link).
4. Tell me the 5 most surprising unexpected links, and how to rebuild when my material changes.
```

The reference `hierarchy.py` shows one way to do step 2 for AI-chat data. It isn't standalone; read it for the logic.
