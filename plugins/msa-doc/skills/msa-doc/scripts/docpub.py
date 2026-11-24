#!/usr/bin/env python3
"""Build a house-style (Times New Roman, MSA layout) doc, upload it to Google Docs, and optionally print it.

    docpub.py build   SRC.md [--out OUT.docx]
    docpub.py publish SRC.md [--title T] [--key K] [--new]
    docpub.py print   SRC.md|SRC.docx [--title T] [--key K] [--new] [--copies N] [--simplex] [--printer P]
    docpub.py check   (report missing dependencies / credentials)

Config lives in $MSA_DOC_HOME (default ~/.config/msa-doc):
    credentials.json   your Google OAuth "Desktop app" client (you create this; never commit it)
    token.json         written after the first browser consent
    .gdoc_id_<key>     cached Drive file id per document, so re-runs update the same Doc
print exports the uploaded Google Doc as PDF (what you see in Docs is what prints) and sends it to CUPS.
"""
import argparse, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser(os.environ.get("MSA_DOC_HOME", "~/.config/msa-doc"))
CREDENTIALS = os.path.join(HOME, "credentials.json")
TOKEN = os.path.join(HOME, "token.json")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
GDOC = "application/vnd.google-apps.document"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def md_title(src):
    """Google Doc title: '<product> - <Title>' from the cover lines, else the file name."""
    if src.endswith(".md"):
        lines = [l.strip() for l in open(src, encoding="utf-8") if l.strip()]
        if lines and lines[0].startswith("# ") and len(lines) > 1:
            return f"{lines[1]} - {lines[0][2:].strip()}"
    return os.path.splitext(os.path.basename(src))[0]


def build(src, out):
    subprocess.run([sys.executable, os.path.join(HERE, "tnr_doc.py"), src, out], check=True)
    return out


def drive():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build as gbuild
    except ImportError:
        sys.exit("Missing Google libraries: pip install -r " + os.path.join(HERE, "requirements.txt"))
    os.makedirs(HOME, exist_ok=True)
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if os.path.exists(TOKEN) else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS):
                sys.exit(f"Missing {CREDENTIALS}: create a Google OAuth Desktop client (see README) and save it there.")
            creds = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES).run_local_server(port=0)
        with open(TOKEN, "w") as fh:
            fh.write(creds.to_json())
        os.chmod(TOKEN, 0o600)
    return gbuild("drive", "v3", credentials=creds)


def upload(svc, docx, title, key, new=False):
    from googleapiclient.http import MediaFileUpload
    cache = os.path.join(HOME, f".gdoc_id_{key}")
    media = MediaFileUpload(docx, mimetype=DOCX, resumable=True)
    fid = None if new or not os.path.exists(cache) else open(cache).read().strip()
    if fid:
        doc = svc.files().update(fileId=fid, media_body=media, fields="id,webViewLink").execute()
        action = "Updated"
    else:
        doc = svc.files().create(body={"name": title, "mimeType": GDOC}, media_body=media,
                                 fields="id,webViewLink").execute()
        action = "Created"
    open(cache, "w").write(doc["id"])
    print(f"{action}: {doc['webViewLink']}  (cache {os.path.basename(cache)})")
    return doc["id"]


def export_pdf(svc, fid, out):
    data = svc.files().export(fileId=fid, mimeType="application/pdf").execute()
    open(out, "wb").write(data)
    return out


def send_to_printer(pdf, printer, copies, simplex):
    if not shutil.which("lp"):
        sys.exit("No `lp` command (CUPS). PDF is at " + pdf)
    sides = "one-sided" if simplex else "two-sided-long-edge"
    media = os.environ.get("MSA_DOC_MEDIA", "A4")
    cmd = ["lp"] + (["-d", printer] if printer else []) + [
        "-n", str(copies), "-o", f"sides={sides}", "-o", f"media={media}",
        "-o", "fit-to-page", "-t", os.path.basename(pdf), pdf]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("Print failed: " + (r.stderr or r.stdout).strip())
    print("Printed:", r.stdout.strip())


def check():
    ok = True
    def line(good, msg):
        nonlocal ok
        ok &= good
        print(("ok    " if good else "MISSING ") + msg)
    line(bool(shutil.which("pandoc")), "pandoc (required for build)")
    try:
        import googleapiclient, google_auth_oauthlib  # noqa: F401
        line(True, "Google API Python libraries")
    except ImportError:
        line(False, "Google API Python libraries: pip install -r " + os.path.join(HERE, "requirements.txt"))
    line(os.path.exists(CREDENTIALS), f"OAuth client at {CREDENTIALS} (needed for publish/print)")
    print(("ok    " if os.path.exists(TOKEN) else "info  ") + f"token at {TOKEN} "
          + ("" if os.path.exists(TOKEN) else "(created on first publish via browser consent)"))
    has_puml = bool(shutil.which("plantuml") or os.environ.get("PLANTUML_JAR"))
    print(("ok    " if has_puml else "info  ") + "PlantUML (optional, for diagrams: `plantuml` on PATH or PLANTUML_JAR)")
    print(("ok    " if shutil.which("lp") else "info  ") + "CUPS `lp` (optional, for print)")
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "publish", "print", "check"])
    ap.add_argument("src", nargs="?")
    ap.add_argument("--out", help="build: where to write the .docx (default: next to SRC)")
    ap.add_argument("--title", help="Google Doc name (default: '<product> - <Title>')")
    ap.add_argument("--key", help="cache key for .gdoc_id_<key> (default: slug of the file name)")
    ap.add_argument("--new", action="store_true", help="create a fresh Doc instead of updating the cached one")
    ap.add_argument("--copies", type=int, default=1)
    ap.add_argument("--simplex", action="store_true", help="print one-sided (default is double-sided)")
    ap.add_argument("--printer", default=os.environ.get("MSA_DOC_PRINTER"),
                    help="CUPS printer name (default: $MSA_DOC_PRINTER, else the system default printer)")
    a = ap.parse_args()

    if a.cmd == "check":
        check()
    if not a.src:
        ap.error("src is required")
    src = os.path.abspath(a.src)
    if not os.path.exists(src):
        sys.exit("Not found: " + src)
    base = os.path.splitext(src)[0]
    key = a.key or slug(os.path.basename(base))
    title = a.title or md_title(src)

    docx = src if src.endswith(".docx") else build(src, a.out or base + ".docx")
    if a.cmd == "build":
        return

    svc = drive()
    fid = upload(svc, docx, title, key, a.new)
    if a.cmd == "print":
        pdf = export_pdf(svc, fid, base + ".pdf")
        print("PDF:", pdf)
        send_to_printer(pdf, a.printer, a.copies, a.simplex)


if __name__ == "__main__":
    main()
