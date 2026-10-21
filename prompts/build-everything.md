# The one-shot prompt

Open a terminal in your `topic-map` folder (the one with `inbox/` inside it), start `claude`, and paste everything in the block below. See the [README](../README.md) for how to prepare.

```text
Build me a personal "Topic Map": a local tool that reads my AI chat exports and shows me the topics I keep
circling, how they change over time, and the deeper themes underneath. The exports are the zip files in ./inbox
(ChatGPT, Claude, maybe Gemini); their names don't say which is which. Build the whole thing end to end in this
folder. Work on your own and only stop at the two checkpoints marked ⏸.

GROUND RULES
- Plain Python and plain HTML/JS. No frameworks, no build step, no database server (SQLite is fine).
- Everything stays on this computer. The viewer is a small local server on 127.0.0.1:8765. If that port is busy,
  say so and use another (`serve --port`). On Windows, turn off HTTPServer's allow_reuse_address, or a second
  server silently shares the busy port.
- Reading conversations: use the local Ollama model qwen3:14b (http://127.0.0.1:11434, JSON output via a schema
  in the "format" field, thinking off with "think": false). Full conversations never leave this machine.
- Judgement work (naming topics, finding the deeper themes): do it yourself in this Claude Code session, from
  compact files you generate (labels, counts, short sample quotes). Never call a paid API. You do this once; after
  that `all` must run without you: new labels go to the closest existing topic (listed in topics.json for me to
  check) and new topics to the closest theme.
- Each step is a command, `python -m topicmap <step>`, is resumable, and caches its results, so re-running skips
  finished work. Add `python -m topicmap all` to run the chain, so I can update the map when I add new exports.
- Write a README that explains every step, which model it uses, and how to update.

STEPS
1. ingest: unzip and parse every export into data/threads.jsonl (id, source, title, start and last-update time,
   and messages with role me/ai, time, text). Recognise each source by its content, not its file name: ChatGPT
   and Claude both ship a conversations.json. ChatGPT's is a tree ("mapping"): follow the branch that ends at
   current_node, keep only the text parts of user and assistant messages, and skip hidden messages and custom
   instructions (content_type user_editable_context). Claude's lists chat_messages (sender human/assistant); the
   words are in "text" or, in newer exports, in the text blocks of "content". Gemini's Takeout "My Activity"
   (MyActivity.json, or MyActivity.html if it arrived as HTML) has one entry per prompt and no conversation ids:
   keep entries whose title starts with "Prompted", and group entries less than 30 minutes apart into one
   conversation. Skip empty conversations. Print counts per source.
2. index: a SQLite FTS5 index of every message, plus `python -m topicmap search "phrase"`.
3. extract: for each conversation, ask the local model for MY ideas only, not the AI's. Each idea has a type
   (question, claim, idea, plan, worry, insight, desire, decision), 1–3 short labels, a weight from 1 to 3, and a
   verbatim quote of my own words. Send only my messages (trim very long pasted ones) so it fits an 8K context.
   Then check every quote against my original message in Python; mark quotes that aren't found as unverified and
   never show them as evidence. Append to data/atoms.jsonl as it goes.
   ⏸ CHECKPOINT 1: run extract on 10 conversations. Show me 10 sample ideas with their quotes, the share of quotes
   verified, and the seconds per conversation, and estimate the full run time. After my OK, start the full run in
   the background, tell me it can be stopped and resumed, and keep building the rest with the ideas found so far.
4. topics: fold the labels into topics: 80–150 for an archive of 1,000+ conversations, fewer for a small one
   (roughly one per 4–6 distinct labels). Merge near-duplicate labels in Python first, then you name the
   topics: one emoji each, a 1–4 word name, and a one-line essence written to me ("you…"). Save data/topics.json
   with a label → topic map that I can hand-edit.
5. analyze: plain statistics per topic: idea count, first and last date, span, active weeks, "returns" (coming
   back after 2+ weeks away), sources. An invariance score that weighs returns and span most, then steady
   recurrence, then a little volume. Co-occurrence edges between topics that share conversations.
   Write data/map.json.
6. themes: read a timeline sample (a few quotes per topic, spread across its span) and write 3–7 deeper themes:
   what persists underneath the changing topics. Each gets a name, an emoji, a one-sentence essence, the open
   question it keeps asking, its topics, and 2–4 claims that cite idea ids. Most topics won't be named by any
   theme: file each one under the theme whose topics it shares the most conversations with, marked "inferred".
   A topic that shares no conversation with any theme goes under a "Loose threads" group rather than a guess.
7. hierarchy: plain Python, writes data/hierarchy.json, a tree me → themes → topics → each topic's top labels →
   2 best ideas per label. Add cross-links: co-occurrence, and "unexpected" links, which are pairs of topics that
   share an unusually large share of their conversations but sit under different themes (at most 3 per topic).
   Rebuild it whenever analyze runs.

THE VIEWER (`python -m topicmap serve`, dark theme)
- / : a main page with a constellation of topic emoji sized by idea count (recurring topics get a gold ring), a
  returns grid (topics × weeks, gold dot = came back after a break), a searchable ideas list, and a conversation
  reader. Window buttons: all time / 12 weeks / 4 weeks, counted back from my latest conversation, not today.
- /disk : the centrepiece, a Poincaré-disk view of the hierarchy (canvas + d3 v7 from cdnjs).
  · Each theme gets a sector around me. Pack its topics biggest first (size = ideas × span), each taking the free
    spot nearest the centre, so the big long-lived topics hold the middle. Below the topics, lay out a hyperbolic
    tree: children get slices of the parent's wedge, pushed outward until they have room. On-screen size is
    size × (1 − |z|²), so things shrink toward the rim.
  · Clicking any node runs a Möbius transform that glides it to the centre along the geodesic, so its neighbourhood
    opens up. Drag to slide the disk, scroll to zoom, Esc returns to me.
  · Draw links as geodesic arcs (circles that meet the rim at right angles): tree, co-occurrence, and dashed gold
    "unexpected" links, each kind toggleable. Hover shows the name and its numbers. A side panel shows the topic,
    its quotes, what it connects to and why, and links to its conversations. While something is focused, dim
    everything not related to it.
  · Lens buttons: themes | clusters (plain-Python communities of co-occurring topics). The same window buttons.
    A search box that jumps to any node.
  · Performance: never use canvas clip() (mask the rim with a CSS radial-gradient overlay instead), batch strokes
    by style, and draw each emoji once to a small offscreen canvas and reuse it with drawImage. Keep a frame under
    ~16 ms with ~3,000 nodes.

⏸ CHECKPOINT 2 (the end): start the server and open http://127.0.0.1:8765/disk. If you can drive a browser, click a
few nodes and switch lens and window, and fix anything broken. Then give me a short tour: my 10 biggest topics, my
themes, the 5 most surprising "unexpected" links, and how to update the map when I add new exports.
```
