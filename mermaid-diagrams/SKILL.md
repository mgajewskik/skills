---
name: mermaid-diagrams
description: Write Mermaid diagrams as fenced Markdown for GitHub. Use when the user mentions Mermaid, or asks for a flowchart, sequence, class, state, ER, Gantt, git graph, or other text diagram in a README, issue, pull request, discussion, or wiki. PlantUML requests belong to the plantuml skill.
---

# Mermaid diagrams

GitHub renders a fence whose info string is `mermaid` in Markdown files, issues, pull requests, discussions, and wikis. The deliverable is that fence. GitHub pins a Mermaid build behind upstream, so a diagram that renders on mermaid.live can still fail on GitHub. The version check GitHub documents is a fence whose body is `info`: <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams>.

## Steps

1. Choose a core keyword from the table below, or read the current syntax page for any other keyword.
   Done when the diagram's first line is a keyword from that table, or the keyword printed on the page you opened.

2. Write one fence into the Markdown file in scope. When no file is in scope, put the fence in the reply.
   Done when the info string is `mermaid`, the block holds one diagram, and a reader can follow that diagram in one glance. Split a larger idea into another fence.

3. Apply the GitHub rules before the fence is finished.
   Done when every rule that applies to this diagram is true of the fence.

4. When the user asks for an SVG, PNG, or PDF file, follow [references/export.md](references/export.md) after the fence is valid.
   Done when that file's completion criterion is met. Skip this step when the user did not ask for a file.

## Core keywords

| Need | First line |
| --- | --- |
| Process or decisions | `flowchart TD` or `flowchart LR` |
| Messages over time | `sequenceDiagram` |
| Types and relationships | `classDiagram` |
| States and transitions | `stateDiagram-v2` |
| Data model | `erDiagram` |
| Schedule | `gantt` |
| Commits and branches | `gitGraph` |
| Shares of a whole | `pie` |
| Topic hierarchy | `mindmap` |
| Dated events | `timeline` |
| Experience across steps | `journey` |
| Two-axis priority | `quadrantChart` |
| Requirements | `requirementDiagram` |

Use `flowchart TD` for a process and `flowchart LR` for a left-to-right pipeline. A mindmap is indented text, not arrows. A gantt chart sets `dateFormat` before its tasks. A journey score is an integer from 1 to 5. A participant or node id is one token; a visible name that contains spaces goes in a label or after `as`.

For C4, or for any keyword that is not in the table (including a keyword ending in `-beta`), read `https://mermaid.js.org/syntax/<name>.html` before writing. The stem is the docs file, for example `c4`, `architecture`, `sankey`, `xyChart`, `entityRelationshipDiagram`, `gitgraph`. Copy the declaration that page uses. If you have not seen GitHub's `info` version in this task, stay on the core table.

## GitHub rules

- Quote a label that contains parentheses, brackets, colons, commas, or slashes: `A["GET /users (v2)"]`.
- A label is plain text. A line break inside a quoted label is `<br/>`.
- The diagram contains structure and plain labels. GitHub draws the theme. A `click` line needs a security level GitHub does not grant, and GitHub loads no icon packs.
- Use classic shapes: `[]`, `()`, `{}`, `[[]]`, `[()]`, `(())`.
- A subgraph closes with `end`. A node id that would have been `end` is written `End`.
- Quote an ER relationship label that contains a space.
- When a node id starts with `o` or `x`, put a space before that id or capitalize it (`dev--- ops`, `dev---Ops`).
- An architecture diagram uses the built-in icons `cloud`, `database`, `disk`, `internet`, and `server`.

A comment is its own line and starts with `%%`.
