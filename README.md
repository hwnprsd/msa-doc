# msa-doc

A Claude Code skill that writes documents in one house style: Times New Roman throughout, laid out
like a Master Services Agreement (cover, Contents, Summary, numbered clauses, horizontal-rule tables,
black on white), but written as plain explanatory prose. Claude writes the markdown, the scripts build
a `.docx` with pandoc and upload it to your Google Drive as a Google Doc. Re-publishing updates the
same Doc, so the link stays stable.

Two skills ship together:

- `/msa-doc` writes the doc, builds it and publishes it to Google Docs.
- `/print-doc` does the same, then exports the Google Doc as PDF and prints it via CUPS.

## Install

### Option A: plugin (recommended)

In Claude Code:

```
/plugin marketplace add hwnprsd/msa-doc
/plugin install msa-doc@msa-doc
```

### Option B: plain skills folder

```bash
git clone https://github.com/hwnprsd/msa-doc.git
mkdir -p ~/.claude/skills
ln -s "$PWD/msa-doc/plugins/msa-doc/skills/msa-doc"   ~/.claude/skills/msa-doc
ln -s "$PWD/msa-doc/plugins/msa-doc/skills/print-doc" ~/.claude/skills/print-doc
```

## Dependencies

| Need | For | Install |
|---|---|---|
| pandoc | building the .docx (required) | `brew install pandoc` / `apt install pandoc` / `pacman -S pandoc` |
| Python 3.9+ libs | Google upload, diagram sizing | `pip install -r plugins/msa-doc/skills/msa-doc/scripts/requirements.txt` |
| Times New Roman, Roboto Mono | correct look in a local .docx viewer (Google Docs has both) | `ttf-ms-fonts` / `ttf-mscorefonts-installer`, Roboto Mono from Google Fonts |
| PlantUML | diagrams (optional) | `plantuml` on PATH, or `PLANTUML_JAR=/path/to/plantuml.jar` |
| CUPS `lp` | `/print-doc` only (optional) | already on macOS and most Linux desktops |

Check everything with:

```bash
python3 plugins/msa-doc/skills/msa-doc/scripts/docpub.py check
```

## Google Drive setup (once per person)

`build` works without this. `publish` and `print` need your own OAuth client:

1. In Google Cloud Console, create (or pick) a project and enable the **Google Drive API**.
2. Configure the OAuth consent screen (Internal if you are on Workspace, otherwise External and
   add yourself as a test user).
3. Create credentials: **OAuth client ID → Desktop app**. Download the JSON.
4. Save it as `~/.config/msa-doc/credentials.json` (or set `MSA_DOC_HOME` to another folder).
5. Run one publish yourself so the browser consent can open:

   ```bash
   python3 plugins/msa-doc/skills/msa-doc/scripts/docpub.py publish plugins/msa-doc/skills/msa-doc/examples/example.md
   ```

   This writes `token.json` next to `credentials.json`. After that Claude can publish on its own.

The scope is `drive.file`: the app can only see files it created, not the rest of your Drive.
Never commit `credentials.json` or `token.json`.

## Usage

Ask Claude for a doc ("write up the caching design as a doc", or `/msa-doc caching design`). It writes
the markdown, runs:

```bash
docpub.py publish "reports/My Doc.md"     # build + upload, prints the Doc link
docpub.py build   "reports/My Doc.md"     # .docx only
docpub.py print   "reports/My Doc.md"     # build + upload + print (A4, double-sided)
```

Flags: `--key K` reuse a cached Doc id, `--title T` rename, `--new` make a separate copy,
`--copies N`, `--simplex`, `--printer NAME`.

Uploading replaces the Google Doc body. If someone edited the Doc in Google Docs, copy those edits
back into the markdown before re-publishing.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `MSA_DOC_HOME` | `~/.config/msa-doc` | credentials, token and per-doc Drive id cache |
| `MSA_DOC_PRINTER` | system default printer | CUPS printer for `/print-doc` |
| `MSA_DOC_MEDIA` | `A4` | paper size for printing (e.g. `Letter`) |
| `PLANTUML_JAR` | none | path to plantuml.jar if `plantuml` isn't on PATH |

## Layout

```
.claude-plugin/marketplace.json
plugins/msa-doc/
  .claude-plugin/plugin.json
  skills/msa-doc/
    SKILL.md                 style + writing rules Claude follows
    scripts/docpub.py        build / publish / print / check
    scripts/tnr_doc.py       markdown → styled .docx (pandoc + XML rewrite)
    scripts/diagram.py       PlantUML render + DPI sizing
    scripts/reference-legal.docx
    assets/style.iuml        black-and-white PlantUML theme
    examples/example.md      a complete doc in the house skeleton
  skills/print-doc/SKILL.md
```
