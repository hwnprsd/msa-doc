---
name: msa-doc
description: Write any document (report, proposal, design doc, explainer, Q&A, plan) in the house style — Times New Roman throughout, MSA-style numbered clauses, cover + Contents + Summary, horizontal-rule tables, black on white — build it to .docx and upload it to Google Drive as a Google Doc. Use whenever the user asks for a doc, writeup, report or proposal, or says /msa-doc. For printing, see /print-doc.
argument-hint: "[topic or path/to/doc.md]"
---

# House document style (MSA layout, Times New Roman)

Every doc looks the same: Times New Roman, laid out like a Master Services Agreement, but written
as a plain **explanatory** document — never as a contract.

Pipeline: write markdown → `scripts/docpub.py publish` → .docx built next to the .md and uploaded
to Google Docs (re-runs update the same Doc).

In the commands below, `SKILL_DIR` means the directory this SKILL.md lives in (the "Base directory
for this skill" shown when the skill loads). Always use its absolute path.

First use on a machine: run `python3 SKILL_DIR/scripts/docpub.py check`. If something required is
missing, tell the user what to install (see the repo README) rather than working around it.
`build` only needs pandoc; `publish` and `print` also need Google credentials.

## 1. Markdown skeleton (required exactly)

The builder reads the first five non-blank lines as the cover. Then a two-column Contents table,
then `## Summary`. A full example is in `SKILL_DIR/examples/example.md`.

```markdown
# Document Title

product-or-org-name

One-line Subtitle Saying What This Covers

Values as of 16 November 2026

Internal working document.

| Contents | |
|---|---|
| Summary | 5. Costs |
| 1. Key Terms | 6. Risks and Open Items |
| 2. How It Works | |
| 3. ... | |
| 4. ... | |

## Summary

Two or three sentences stating the point directly.

| Item | Design |
|---|---|
| What it is | ... |
| Main risk | ... |

## 1. Key Terms

1.1 **Terms used.**

“**Vault**” means the single pool of funds that quotes the markets.

“**Period**” means one day.

## 2. How It Works

2.1 **Deposit.** Body text in plain sentences.

(a) **First point.** Sub-clause text.

(b) **Second point.** Sub-clause text.

![](/absolute/path/to/diagrams/name.png)

Figure 1. Caption sentence.

## 6. Risks and Open Items

6.1 **Risks.**

(a) **Name.** What could go wrong and how it is limited.

6.2 **Open items.**

(a) Decision or measurement still needed.
```

Fill the Contents table down the left column first, then the right; keep both columns balanced.

## 2. Formatting rules the builder relies on

- Clauses start a paragraph with `N.N ` (e.g. `2.3 `), then a **bold lead-in.** — they get a hanging indent.
- Sub-clauses start with `(a) `, `(b) ` … — deeper hanging indent.
- `(A) `, `(B) ` paragraphs are allowed in an intro section (same indent as clauses).
- Definitions start with a curly quote: `“**Term**” means …` — indented.
- Headings are `## N. Title` (only `##`; `## Summary` / `## Overview` start a new page).
- Tables: normal GFM pipe tables; first row is the header. Rendered with horizontal rules only.
- Code: fenced blocks render in Roboto Mono in a grey box; inline `code` is Roboto Mono. Everything else is TNR.
- Images: absolute paths only, followed by a `Figure N. …` line.
- Use curly quotes (“ ” ’) in prose.

## 3. Writing rules (strict)

- It is an explanatory document, **not a contract**. Never use "Schedule", "Background", "Recitals",
  "Definitions and Interpretation", "Whereas", or "this is not a contract" disclaimers.
- Use plain headings: Summary, Key Terms, How It Works, Costs, Risks and Open Items, etc.
- Open with a short Summary (a sentence or two plus an Item/Detail table). Write directly.
- No "Sources" or "Calculations" section at the end. Put formulas inline; keep references only
  when asked, e.g. as an in-body comparison table.
- Usually end with "Risks and Open Items".
- Plain black on white. No colour, no emoji.

## 4. Diagrams (optional)

PlantUML, black and white, Liberation Serif. Start each `.puml` with
`!include SKILL_DIR/assets/style.iuml` (absolute path). Render and size in one step:

```bash
python3 SKILL_DIR/scripts/diagram.py diagrams/foo.puml diagrams/bar.puml
```

This renders PNGs next to the .puml files and sets their DPI so each fits within 6.3 × 4.6 in
(pandoc sizes images by DPI). Keep sequence diagrams to 4–5 participants so the text stays legible.

## 5. Build and upload

Write the `.md` where the project keeps docs (e.g. `docs/` or `reports/`), then:

```bash
python3 SKILL_DIR/scripts/docpub.py publish "reports/My Doc.md"
```

- Builds `reports/My Doc.docx` and uploads it as a Google Doc named `<product> - <Title>`.
- Caches the Drive id in `$MSA_DOC_HOME/.gdoc_id_<key>` (default `~/.config/msa-doc`; key defaults
  to a slug of the file name), so re-running updates the same Doc and keeps its URL. Use `--key`
  to reuse an existing cache, `--title` to rename, `--new` for a separate copy.
- `build` instead of `publish` only makes the .docx (no Google account needed).
- Uploading **replaces** the Doc body. If the user has edited it in Google Docs, bring those edits
  back into the markdown first.

Give the user the Doc link printed by the script.

## 6. Safety

- Credentials live in `$MSA_DOC_HOME/credentials.json` and `token.json`. Never print, copy or commit
  them. The scope is `drive.file` (only files this app created).
- If there is no token yet, or it is expired/revoked, the consent flow needs a browser. Ask the user
  to run it themselves, e.g. in Claude Code: `! python3 SKILL_DIR/scripts/docpub.py publish <file>`.
