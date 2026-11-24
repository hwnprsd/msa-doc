---
name: print-doc
description: Print a house-style (msa-doc) document on a CUPS printer while uploading/updating it in Google Drive. Use when the user says /print-doc, "print this doc", or asks to print a report.
argument-hint: "<path/to/doc.md or .docx> [copies] [single-sided]"
---

# Print a doc (and upload it to Drive)

The user invoked this to print — do it without asking for confirmation.

The scripts live in the sibling `msa-doc` skill: `MSA_DIR` below means `../msa-doc` relative to this
skill's base directory. Use its absolute path.

1. Work out the source file from the arguments. If none was given, use the doc most recently
   written or discussed in this session; if there isn't one, ask which file.
   - A `.md` must follow the msa-doc skeleton (`MSA_DIR/SKILL.md`). If it doesn't, say so rather
     than printing something broken.
2. Run:

   ```bash
   python3 MSA_DIR/scripts/docpub.py print "<file>" [--copies N] [--simplex] [--printer NAME]
   ```

   This builds the .docx, uploads it to Google Docs (updating the cached Doc for that file if one
   exists), exports that Google Doc as PDF next to the source, and sends the PDF to CUPS:
   double-sided long-edge by default, paper size `$MSA_DOC_MEDIA` (default A4). Pass `--simplex`
   if the user says single-sided, `--copies N` for more copies, `--key K` to reuse an existing
   `.gdoc_id_<K>` cache.
3. Report the Doc link and the CUPS job id from the output. If `lp` failed, show its error and
   check `lpstat -p -o` (printer offline, stuck job). Don't retry more than once.

Printer: `--printer`, else `$MSA_DOC_PRINTER`, else the system default printer (`lpstat -d`).
Never print or copy `credentials.json` or `token.json`.
