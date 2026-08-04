#!/usr/bin/env python3
"""Embed the brand typefaces in the DOCX.

Without this, a recipient who does not have Inter installed sees Word's
substitute and the typography this document specifies is lost. OOXML embeds
fonts as "obfuscated" TTFs: the first 32 bytes are XORed with the 16-byte key
derived from the font's GUID.
"""
import os
import re
import shutil
import uuid
import zipfile

ROOT = "/home/user/Stromex.ai/publication"
DOCX = os.path.join(ROOT, "dist/SpaceTalk_Editorial_Bible_v1.0.docx")
FONTS = os.path.expanduser("~/.local/share/fonts")

# family → {style: filename}
EMBED = {
    "Inter": {
        "embedRegular": "Inter-Regular.ttf",
        "embedBold": "Inter-SemiBold.ttf",          # the document's bold weight
        "embedItalic": "Inter-Italic.ttf",
        "embedBoldItalic": "Inter-SemiBoldItalic.ttf",
    },
    "Inter Display": {
        "embedRegular": "InterDisplay-Regular.ttf",
        "embedBold": "InterDisplay-SemiBold.ttf",
    },
    "JetBrains Mono": {
        "embedRegular": "JetBrainsMono-Regular.ttf",
        "embedBold": "JetBrainsMono-Bold.ttf",
        "embedItalic": "JetBrainsMono-Italic.ttf",
    },
}

NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_FONT = "application/vnd.openxmlformats-officedocument.obfuscatedFont"


def obfuscate(data, guid):
    """XOR the first 32 bytes with the key derived from the font GUID."""
    hexs = guid.strip("{}").replace("-", "")
    key = bytes(int(hexs[i:i + 2], 16) for i in range(0, 32, 2))[::-1]
    out = bytearray(data)
    for i in range(min(32, len(out))):
        out[i] ^= key[i % 16]
    return bytes(out)


def main():
    tmp = os.path.join(ROOT, "build/_docx")
    shutil.rmtree(tmp, ignore_errors=True)
    with zipfile.ZipFile(DOCX) as z:
        names = z.namelist()
        z.extractall(tmp)

    font_rels, font_files, n = [], [], 0
    fonttable_entries = []

    for family, styles in EMBED.items():
        parts = []
        for tag, fname in styles.items():
            src = os.path.join(FONTS, fname)
            if not os.path.exists(src):
                print(f"  ! missing {fname}, skipping")
                continue
            n += 1
            guid = "{%s}" % str(uuid.UUID(int=n * 0x1111111111111111111111111111111 % (1 << 128))).upper()
            rid = f"rIdFont{n}"
            target = f"fonts/font{n}.odttf"
            with open(src, "rb") as fh:
                data = fh.read()
            os.makedirs(os.path.join(tmp, "word/fonts"), exist_ok=True)
            with open(os.path.join(tmp, "word", target), "wb") as fh:
                fh.write(obfuscate(data, guid))
            font_rels.append(
                f'<Relationship Id="{rid}" Type="{NS_R}/font" Target="{target}"/>')
            font_files.append(target)
            parts.append(f'<w:{tag} r:id="{rid}" w:fontKey="{guid}" w:subsetted="0"/>')
        if parts:
            fonttable_entries.append((family, "".join(parts)))

    # ---- fontTable.xml: attach the embed elements to each font entry
    ft_path = os.path.join(tmp, "word/fontTable.xml")
    ft = open(ft_path, encoding="utf-8").read()
    if "xmlns:r=" not in ft:
        ft = ft.replace("<w:fonts ", f'<w:fonts xmlns:r="{NS_R}" ', 1)
    ft = re.sub(r"(<w:fonts\b[^>]*?)/>", r"\1></w:fonts>", ft)      # self-closing root
    for family, embeds in fonttable_entries:
        pat = re.compile(r'(<w:font w:name="%s">)(.*?)(</w:font>)' % re.escape(family), re.S)
        if pat.search(ft):
            ft = pat.sub(lambda m: m.group(1) + m.group(2) + embeds + m.group(3), ft, count=1)
        else:
            ft = ft.replace("</w:fonts>", f'<w:font w:name="{family}">{embeds}</w:font></w:fonts>')
    open(ft_path, "w", encoding="utf-8").write(ft)

    # ---- fontTable rels
    rels_path = os.path.join(tmp, "word/_rels/fontTable.xml.rels")
    if os.path.exists(rels_path):
        rels = open(rels_path, encoding="utf-8").read()
        rels = re.sub(r"(<Relationships\b[^>]*?)/>", r"\1></Relationships>", rels)
        rels = rels.replace("</Relationships>", "".join(font_rels) + "</Relationships>")
    else:
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + "".join(font_rels) + "</Relationships>")
    os.makedirs(os.path.dirname(rels_path), exist_ok=True)
    open(rels_path, "w", encoding="utf-8").write(rels)

    # ---- content types
    ct_path = os.path.join(tmp, "[Content_Types].xml")
    ct = open(ct_path, encoding="utf-8").read()
    if 'Extension="odttf"' not in ct:
        ct = ct.replace("<Types ", "<Types ", 1).replace(
            "</Types>", f'<Default Extension="odttf" ContentType="{CT_FONT}"/></Types>')
    open(ct_path, "w", encoding="utf-8").write(ct)

    # ---- settings: tell Word the fonts are embedded and to save them on
    st_path = os.path.join(tmp, "word/settings.xml")
    st = open(st_path, encoding="utf-8").read()
    if "embedTrueTypeFonts" not in st:
        # CT_Settings is an ordered sequence: embedTrueTypeFonts must follow
        # displayBackgroundShape and precede evenAndOddHeaders.
        ins = "<w:embedTrueTypeFonts/><w:saveSubsetFonts w:val='false'/>"
        for anchor in ("<w:evenAndOddHeaders", "<w:updateFields", "<w:compat>"):
            if anchor in st:
                st = st.replace(anchor, ins + anchor, 1)
                break
        else:
            st = st.replace("</w:settings>", ins + "</w:settings>")
    open(st_path, "w", encoding="utf-8").write(st)

    # ---- unique bookmark ids
    doc_path = os.path.join(tmp, "word/document.xml")
    doc = open(doc_path, encoding="utf-8").read()
    counter = [0]
    stack = []

    def renumber(m):
        tag = m.group(0)
        if tag.startswith("<w:bookmarkStart"):
            counter[0] += 1
            stack.append(counter[0])
            return re.sub(r'w:id="\d+"', 'w:id="%d"' % counter[0], tag)
        n = stack.pop() if stack else 0
        return '<w:bookmarkEnd w:id="%d"/>' % n

    # one pass over both tags in document order, so every end keeps its start's id
    doc = re.sub(r"<w:bookmark(?:Start|End)[^>]*/>", renumber, doc)
    open(doc_path, "w", encoding="utf-8").write(doc)
    print(f"  bookmark ids: {counter[0]} made unique")

    # ---- repack, [Content_Types].xml first
    out = DOCX
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(tmp, "[Content_Types].xml"), "[Content_Types].xml")
        for root, _, files in os.walk(tmp):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, tmp).replace(os.sep, "/")
                if rel == "[Content_Types].xml":
                    continue
                z.write(full, rel)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"  embedded {len(font_files)} font files  ·  "
          f"docx now {os.path.getsize(out) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
