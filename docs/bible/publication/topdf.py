#!/usr/bin/env python3
"""Render the DOCX master to a press-quality PDF.

`soffice --convert-to pdf` does not resolve field-driven apparatus, so the
table of contents, the lists of tables and figures, and the index all export
empty. This drives LibreOffice over UNO instead: load, repaginate, update
every index and field, then export — so the PDF carries the same live
apparatus the DOCX does, resolved to real page numbers.
"""
import os, subprocess, sys, time, uno
from com.sun.star.beans import PropertyValue

SRC = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
PORT = 2202
PROFILE = 'file:///tmp/lo-uno-profile'


def prop(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p


def connect(timeout=90):
    ctx = uno.getComponentContext()
    resolver = ctx.ServiceManager.createInstanceWithContext(
        'com.sun.star.bridge.UnoUrlResolver', ctx)
    url = f'uno:socket,host=127.0.0.1,port={PORT};urp;StarOffice.ComponentContext'
    deadline = time.time() + timeout
    while True:
        try:
            return resolver.resolve(url)
        except Exception:
            if time.time() > deadline:
                raise
            time.sleep(1)


def main():
    soffice = subprocess.Popen([
        'soffice', '--headless', '--norestore', '--invisible', '--nologo',
        f'-env:UserInstallation={PROFILE}',
        f'--accept=socket,host=127.0.0.1,port={PORT};urp;',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        remote = connect()
        desktop = remote.ServiceManager.createInstanceWithContext(
            'com.sun.star.frame.Desktop', remote)

        doc = desktop.loadComponentFromURL(
            uno.systemPathToFileUrl(SRC), '_blank', 0,
            (prop('Hidden', True), prop('ReadOnly', False), prop('UpdateDocMode', 3)))

        # Repaginate first so that field results resolve against real pages,
        # then update indexes, then repaginate again because inserting a
        # populated contents list shifts every page number after it.
        doc.refresh()
        try:
            doc.getTextFields().refresh()
        except Exception:
            pass

        for _ in range(3):
            idxs = doc.getDocumentIndexes()
            for i in range(idxs.getCount()):
                idxs.getByIndex(i).update()
            doc.refresh()
            try:
                doc.getTextFields().refresh()
            except Exception:
                pass

        try:
            cursor = doc.getText().createTextCursor()
            pages = doc.getCurrentController().PageCount
            print(f'  pages after field update: {pages}')
        except Exception:
            pass

        doc.storeToURL(uno.systemPathToFileUrl(OUT), (
            prop('FilterName', 'writer_pdf_Export'),
            prop('FilterData', uno.Any('[]com.sun.star.beans.PropertyValue', (
                prop('UseTaggedPDF', True),        # accessible / structured
                prop('ExportBookmarks', True),     # navigation panel
                prop('ExportNotes', False),
                prop('SelectPdfVersion', 0),
                prop('Quality', 100),
                prop('ReduceImageResolution', False),
                prop('UseLosslessCompression', True),
                prop('ExportLinksRelativeFsys', False),
                prop('InitialView', 2),            # open with bookmarks panel
                prop('Magnification', 2),          # fit page
                prop('DisplayPDFDocumentTitle', True),
            ))),
        ))
        doc.close(False)
        print('  wrote', OUT)
    finally:
        try:
            desktop.terminate()
        except Exception:
            pass
        time.sleep(2)
        soffice.terminate()
        try:
            soffice.wait(timeout=20)
        except Exception:
            soffice.kill()


if __name__ == '__main__':
    main()
