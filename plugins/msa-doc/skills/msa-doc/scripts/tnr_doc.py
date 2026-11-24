#!/usr/bin/env python3
"""Markdown -> .docx in the house MSA layout, Times New Roman throughout, for Google Docs import.

Derived from mm_docx.py: same clause numbering, ruled headings and horizontal-ruled tables,
but every run (headings, tables, cover) is Times New Roman; fenced code blocks are Roboto Mono in a grey box.
The markdown must open with:  # Title / product / subtitle / date line / status line
Usage: tnr_doc.py SRC.md OUT.docx
"""
import os, re, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 9638
TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman"/>'
BREAK_BEFORE = ("Overview", "Summary")
BORDERS = ('<w:tblBorders><w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
           '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
           '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/></w:tblBorders>')
HEAD_RUN = f'<w:rPr>{TNR}<w:b/><w:sz w:val="20"/></w:rPr>'
HEAD_CELL = '<w:tcBorders><w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/></w:tcBorders>'
COVER_END = "<!--cover-end-->"
BAR = ('<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="3" w:color="000000"/></w:pBdr>'
       '<w:spacing w:before="320" w:after="140"/>')
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def run(text, size, bold=False, caps=False):
    return (f'<w:r><w:rPr>{TNR}{"<w:b/>" if bold else ""}{"<w:caps/>" if caps else ""}<w:color w:val="000000"/>'
            f'<w:sz w:val="{size}"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>')


def para(body, before=0, after=0):
    return f'<w:p><w:pPr><w:spacing w:before="{before}" w:after="{after}"/><w:jc w:val="left"/></w:pPr>{body}</w:p>'


def cover(lines):
    title, product, subtitle, date, note = lines
    rule = ('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="12" w:space="1" w:color="000000"/></w:pBdr>'
            '<w:spacing w:before="0" w:after="240"/></w:pPr></w:p>')
    return (para(run(product, 72, True), 300, 60) + para(run(title, 32, True, True), 0, 120)
            + para(run(subtitle, 24), 0, 240) + rule
            + para(run(date, 18, caps=True), 0, 60) + para(run(note, 18, caps=True), 0, 360))


def fix_table(m):
    tbl = m.group(0)
    rows = re.findall(r"<w:tr>.*?</w:tr>", tbl, flags=re.S)
    cells = lambda r: ["".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)", c))
                       for c in re.findall(r"<w:tc>.*?</w:tc>", r, flags=re.S)]
    columns = list(zip(*map(cells, rows)))
    floor = [260 + 105 * min(16, max(len(w) for c in col for w in c.split() or [""])) for col in columns]
    want = [max(1, min(60, max(len(c) for c in col))) for col in columns]
    spare = max(0, PAGE - sum(floor))
    widths = [f + spare * w // sum(want) for f, w in zip(floor, want)]
    widths = [w * PAGE // sum(widths) for w in widths]
    tbl = re.sub(r"<w:tblGrid>.*?</w:tblGrid>",
                 "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>",
                 tbl, flags=re.S)
    tbl = re.sub(r"<w:tblW [^>]*/>", f'<w:tblW w:type="dxa" w:w="{PAGE}"/>' + BORDERS, tbl, count=1)
    tbl = re.sub(r"<w:tblLook [^>]*/>", '<w:tblLayout w:type="fixed"/>', tbl, count=1)
    for row in rows:
        head = "<w:tblHeader" in row
        it = iter(widths)
        new = re.sub(r"<w:tcPr ?/>", lambda _: f'<w:tcPr><w:tcW w:w="{next(it)}" w:type="dxa"/>'
                     + (HEAD_CELL if head else "") + "</w:tcPr>", row)
        if head:
            new = re.sub(r"<w:r>(<w:rPr>.*?</w:rPr>)?<w:t", f"<w:r>{HEAD_RUN}<w:t", new, flags=re.S)
        new = re.sub(r'(<w:pStyle w:val="Compact" ?/>)', r'\1<w:jc w:val="left"/>', new)
        tbl = tbl.replace(row, new, 1)
    return tbl


def add_ppr(p, frag):
    if "<w:pPr>" in p:
        m = re.search(r"<w:pPr>(<w:pStyle [^>]*/>)?", p)
        return p[:m.end()] + frag + p[m.end():]
    return re.sub(r"(<w:p\b[^>]*>)", r"\1<w:pPr>" + frag + "</w:pPr>", p, count=1)


def split_number(p, marker):
    p = re.sub(r'(<w:t(?: [^>]*)?>)' + re.escape(marker) + r' ',
               lambda m: f'{m.group(1)}{marker}</w:t><w:tab/><w:t xml:space="preserve">', p, count=1)
    p = re.sub(re.escape(marker) + r'</w:t></w:r><w:r><w:t xml:space="preserve"> </w:t></w:r>',
               lambda _: marker + "</w:t><w:tab/></w:r>", p, count=1)
    return p.replace('<w:t xml:space="preserve"></w:t>', "")


def fix_para(m):
    p = m.group(0)
    text = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)", p))
    style = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    style = style.group(1) if style else ""
    if style.startswith("Heading"):
        p = re.sub(r"<w:r>(<w:rPr>.*?</w:rPr>)?<w:t", f'<w:r><w:rPr>{TNR}<w:b/><w:caps/><w:sz w:val="24"/></w:rPr><w:t', p, flags=re.S)
        return add_ppr(p, ("<w:pageBreakBefore/>" if text.startswith(BREAK_BEFORE) else "") + BAR)
    if text.startswith("Figure ") or "<w:drawing>" in p:
        return add_ppr(p, '<w:keepNext/><w:jc w:val="center"/>' if "<w:drawing>" in p else '<w:jc w:val="center"/>')
    clause = re.match(r"(\d+\.\d+) ", text)
    sub = re.match(r"(\([a-z]\)) ", text)
    recital = re.match(r"(\([A-Z]\)) ", text)
    if clause or recital:
        mark = (clause or recital).group(1)
        return add_ppr(split_number(p, mark), '<w:ind w:left="720" w:hanging="720"/>')
    if sub:
        return add_ppr(split_number(p, sub.group(1)), '<w:ind w:left="1287" w:hanging="567"/>')
    if text.startswith("“"):
        return add_ppr(p, '<w:ind w:left="720"/>')
    return p


def fix_document(xml, lines):
    xml = re.sub(r"(<w:body>).*?" + re.escape(esc(lines[4])) + r"</w:t></w:r></w:p>", lambda m: m.group(1) + cover(lines) + COVER_END,
                 xml, count=1, flags=re.S)
    head, body = xml.split(COVER_END, 1)
    parts = re.split(r"(<w:tbl>.*?</w:tbl>)", body, flags=re.S)
    for i, part in enumerate(parts):
        if part.startswith("<w:tbl>"):
            parts[i] = re.sub(r"<w:tbl>.*?</w:tbl>", fix_table, part, flags=re.S)
        else:
            parts[i] = re.sub(r"<w:p\b[^>]*>.*?</w:p>", fix_para, part, flags=re.S)
            if i:
                parts[i] = re.sub(r"<w:p\b[^>]*>.*?</w:p>",
                                  lambda m: add_ppr(m.group(0), '<w:spacing w:before="180" w:after="120"/>'),
                                  parts[i], count=1, flags=re.S)
            if i + 1 < len(parts):
                ps = list(re.finditer(r"<w:p\b[^>]*>.*?</w:p>", parts[i], flags=re.S))
                if ps:
                    mm = ps[-1]
                    parts[i] = parts[i][:mm.start()] + add_ppr(mm.group(0), "<w:keepNext/>") + parts[i][mm.end():]
    return fix_code(all_tnr(head + "".join(parts)))


MONO = '<w:rFonts w:ascii="Roboto Mono" w:hAnsi="Roboto Mono" w:cs="Roboto Mono" w:eastAsia="Roboto Mono"/>'
CODE_PPR = ('<w:keepLines/><w:pBdr>' + "".join(
    f'<w:{side} w:val="single" w:sz="4" w:space="6" w:color="D0D7DE"/>' for side in ("top", "left", "bottom", "right"))
    + '</w:pBdr><w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/>'
    '<w:spacing w:before="160" w:after="200" w:line="264" w:lineRule="auto"/><w:ind w:left="144" w:right="144"/><w:jc w:val="left"/>')


def fix_code(xml):
    """Fenced code blocks: monospace 9 pt in a light grey box with a thin border."""
    def one(m):
        p = m.group(0)
        p = re.sub(r'<w:pPr>.*?</w:pPr>', '<w:pPr><w:pStyle w:val="SourceCode"/>' + CODE_PPR + '</w:pPr>', p, count=1, flags=re.S)
        p = re.sub(r"<w:rFonts [^>]*/>", "", p)
        p = re.sub(r"<w:szCs? [^>]*/>", "", p)
        p = re.sub(r"<w:rPr>(<w:rStyle [^>]*/>)?", lambda r: "<w:rPr>" + (r.group(1) or "") + MONO, p)
        p = p.replace("</w:rPr>", '<w:sz w:val="17"/></w:rPr>')
        return p.replace("<w:r><w:t", f'<w:r><w:rPr>{MONO}<w:sz w:val="17"/></w:rPr><w:t')
    xml = re.sub(r'<w:p\b[^>]*><w:pPr><w:pStyle w:val="SourceCode" ?/>.*?</w:p>', one, xml, flags=re.S)
    return xml


def all_tnr(xml):
    xml = re.sub(r"<w:rFonts [^>]*/>", TNR, xml)
    return xml


def fix_styles(xml):
    def style(sid, fn):
        nonlocal xml
        xml = re.sub(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid, lambda m: fn(m.group(0)), xml, flags=re.S)
    style("Hyperlink", lambda s: re.sub(r"<w:rPr>.*?</w:rPr>", '<w:rPr><w:color w:val="000000"/><w:u w:val="single"/></w:rPr>', s, flags=re.S))
    style("Compact", lambda s: s.replace("</w:pPr>", '</w:pPr><w:rPr><w:sz w:val="20"/></w:rPr>'))
    xml = all_tnr(xml)
    # inline code (pandoc's VerbatimChar): monospace, a touch smaller than the text
    style("VerbatimChar", lambda s: re.sub(r"<w:rPr>.*?</w:rPr>", f'<w:rPr>{MONO}<w:sz w:val="19"/></w:rPr>', s, flags=re.S))
    # headings: black, no theme colour
    xml = re.sub(r'<w:color w:val="[0-9A-Fa-f]{6}"( w:themeColor="[^"]+")?[^>]*/>', '<w:color w:val="000000"/>', xml)
    return xml


def fix_theme(xml):
    return re.sub(r'(<a:(?:latin|ea|cs) typeface=")[^"]*(")', r'\1Times New Roman\2', xml)


src, out = sys.argv[1:3]
md = open(src, encoding="utf-8").read().splitlines()
heads = [l for l in md if l.strip()][:5]
lines = [heads[0].lstrip("# ").strip(), heads[1], heads[2], heads[3], heads[4]]
subprocess.run(["pandoc", src, "-f", "gfm", "-t", "docx",
                "--reference-doc", os.path.join(HERE, "reference-legal.docx"), "-o", out], check=True)
tmp = out + ".tmp"
with zipfile.ZipFile(out) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/document.xml":
            data = fix_document(data.decode("utf-8"), lines).encode("utf-8")
        elif item.filename.startswith(("word/footer", "word/header")):
            data = all_tnr(re.sub(r'<w:color w:val="[^"]+"[^>]*/>', '<w:color w:val="000000"/>', data.decode("utf-8"))).encode("utf-8")
        elif item.filename == "word/styles.xml":
            data = fix_styles(data.decode("utf-8")).encode("utf-8")
        elif item.filename.startswith("word/theme/"):
            data = fix_theme(data.decode("utf-8")).encode("utf-8")
        zout.writestr(item, data)
os.replace(tmp, out)
print("built", out)
