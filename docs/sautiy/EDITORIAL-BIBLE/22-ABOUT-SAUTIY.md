# Chapter 22 — About SAUTIY

---

## 22.1 The Product

**SAUTIY™** — from *ṣawtī* (صَوْتِي), "my voice".

SAUTIY™ is engineered to deliver an elegant, dependable and professional mobile audio production
experience with intuitive workflows, premium design, and high-quality recording, editing and
publishing capabilities for creators, educators, reciters, lecturers, broadcasters and
podcasters.

## 22.2 Developed By

**Imam Ahmad Sulaimiy**
Senior Software Engineer, Product Architect & Founder

## 22.3 What The About Screen Says

The About screen is one of only two full destinations in the product (chapter 4.1.2). It shows,
in this order and nothing else:

1. The Aperture, at rest.
2. **SAUTIY™**, and the version.
3. The developer's name and title.
4. The About paragraph above.
5. **The privacy statement**, given its own weight:

   > SAUTIY has no internet permission. Nothing you record can leave this device unless you
   > export or share it yourself.

6. Third-party notices — the four bundled typefaces and their licences.
7. Nothing else. No links to rate, no social accounts, no newsletter, no support chat.

## 22.4 Versioning

`MAJOR.MINOR.PATCH`.

| Increment | When |
|---|---|
| **MAJOR** | A constitutional amendment — a change to chapter 1, or to the one-canvas law |
| **MINOR** | A new capability that fits within the existing chapters |
| **PATCH** | A fix that changes no documented behaviour |

The version and the Editorial Bible move together. A release that changes behaviour without
changing a chapter has diverged from its own constitution.

## 22.5 Licensing

The SAUTIY source in this repository is the property of its author. The bundled typefaces —
Archivo, Fraunces, Amiri and Cairo — are licensed under the **SIL Open Font Licence 1.1**, which
permits their inclusion in an application. Full notices are in
`apps/sautiy/THIRD-PARTY-NOTICES.md`.

The entire audio engine — capture, DSP, timeline, WAV, FLAC — is original work in this
repository. SAUTIY ships no third-party audio code.

## 22.6 Acknowledgements

- The **Audio EQ Cookbook** filter designs, which are the basis of every biquad in the product.
- **ITU-R BS.1770-4** and **EBU R128**, implemented to specification because they are the
  numbers a broadcaster is held to.
- **Schroeder** and **Moorer**, for a reverb topology that is controllable rather than merely
  convincing.
- The **Xiph.Org Foundation**, for a FLAC specification clear enough to implement from.
- The five people of chapter 3.1 — Ustadh Bilal, Dr Aisha, Tunde, Mariam and Yusuf — who are
  composites, and who every design decision in this product was checked against.

## 22.7 The Standard

> Do not stop until every implemented screen, interaction and workflow achieves a standard that
> would be credible as a flagship Android application. Every design decision must simplify the
> user's work while preserving professional capability.

That instruction is the reason this Bible exists, and the reason each of its chapters is
executable rather than aspirational. Where the product falls short of it, the shortfall is
recorded in `docs/sautiy/IMPLEMENTATION-LEDGER.md` in plain terms — because the one thing that
would make all of this worthless is a document that claims more than the code does.

---

**SAUTIY™** — my voice.
