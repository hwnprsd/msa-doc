# Document Pipeline

Example Co

How a Markdown File Becomes a House-Style Google Doc

Values as of 24 November 2026

Internal working document.

| Contents | |
|---|---|
| Summary | 3. Costs |
| 1. Key Terms | 4. Risks and Open Items |
| 2. How It Works | |

## Summary

Docs are written in markdown, built to .docx with pandoc, restyled to the house layout, and uploaded to Google Drive as an editable Google Doc. Re-running the build updates the same Doc, so its link never changes.

| Item | Detail |
|---|---|
| Input | One markdown file in the house skeleton |
| Output | A .docx next to the source and a Google Doc |
| Main risk | Uploading overwrites edits made directly in Google Docs |

## 1. Key Terms

1.1 **Terms used.**

“**Builder**” means the script that turns markdown into a styled .docx.

“**Cache key**” means the name under which the Google Drive file id is stored.

## 2. How It Works

2.1 **Build.** The builder runs pandoc with a reference document, then rewrites the Word XML so every run is Times New Roman, clauses get hanging indents and tables keep only horizontal rules.

(a) **Clauses.** A paragraph that starts with `2.1` is indented as a clause.

(b) **Sub-clauses.** A paragraph that starts with `(a)` is indented one level deeper.

2.2 **Upload.** The publisher sends the .docx to Google Drive, which converts it to a Google Doc. The file id is cached locally:

```bash
python3 scripts/docpub.py publish "reports/My Doc.md"
```

## 3. Costs

3.1 **Running cost.** None. The Drive API is free at this volume and the build runs locally.

## 4. Risks and Open Items

4.1 **Risks.**

(a) **Lost edits.** Uploading replaces the Doc body. Copy any edits made in Google Docs back into the markdown before re-publishing.

4.2 **Open items.**

(a) Decide where the team keeps its source markdown.
