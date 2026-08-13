'use strict';
/* The design tokens of the printed edition.
   Derived from Volume I, Chapter 10 (Brand, Identity & the Logo Decision). */

const A4_W = 11906, A4_H = 16838;           // DXA (twentieths of a point)
const M = { top: 1300, bottom: 1240, left: 1580, right: 1400, header: 720, footer: 680 };

module.exports = {
  page: {
    width: A4_W,
    height: A4_H,
    margin: M,
    contentWidth: A4_W - M.left - M.right,   // 8926
  },

  // Volume I §10.2 — Fraunces is the editorial/imprint voice, Archivo the
  // body and UI face. This is a publication, so a serif carries display.
  //
  // BRAND=1 sets the true brand faces. They require Archivo and Fraunces to be
  // installed in the rendering environment; where they are not, the renderer
  // silently substitutes and the result is worse than a deliberate stand-in.
  // The default set below is chosen to render identically everywhere.
  font: process.env.BRAND === '1'
    ? { display: 'Fraunces', body: 'Archivo', ui: 'Archivo', mono: 'DejaVu Sans Mono', arabic: 'Amiri' }
    : { display: 'DejaVu Serif', body: 'Liberation Serif', ui: 'DejaVu Sans', mono: 'DejaVu Sans Mono', arabic: 'Amiri' },

  // Leading for a given size (docx half-points) at a chosen factor.
  // Large display text needs a factor near 1; body text near 1.45.
  lead: (halfPoints, factor) => Math.round(halfPoints * 10 * factor),

  color: {
    obsidian: '05070A',
    ink: '0D1117',
    ink2: '38414D',
    graphite: '6B7480',
    rule: 'C9CFD9',
    ruleSoft: 'E2E6EC',
    zebra: 'F5F7FA',
    sunk: 'F2F4F8',
    accent: '1B6EF3',
    depth: '0B3C91',
    brass: 'C9A227',
    brassInk: '8A6D12',
    paper: 'FFFFFF',
  },

  // 1pt = 2 half-points in docx sizing
  size: {
    coverTitle: 96,
    coverSub: 26,
    volumeNumeral: 170,
    volumeTitle: 60,
    title: 56,
    h1: 34,
    h2: 25,
    h3: 20,
    h4: 18,
    body: 21,
    small: 18,
    caption: 16,
    micro: 14,
  },
};
