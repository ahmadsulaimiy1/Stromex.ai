/* Typographic and colour constants for the SpaceTalk Editorial Bible.
   Every value traces to 02-VISUAL-DESIGN-SYSTEM.md. Nothing here is invented. */

const C = {
  orbit50: 'EEF2FF', orbit100: 'DDE4FF', orbit200: 'BCC9FF', orbit300: '92A7FF',
  orbit400: '6681FB', orbit500: '3F5EF0', orbit600: '2E48D8', orbit700: '2438AE',
  orbit800: '1E2F8A', orbit900: '1A2769', orbit950: '10173F',
  aurora050: 'E6FAF6', aurora300: '5FE3CE', aurora500: '12B39B', aurora700: '0A7466',
  aurora800: '08594E', aurora950: '062F2A',
  void0: 'FFFFFF', void25: 'FAFBFD', void50: 'F4F6FA', void100: 'E9EDF4',
  void200: 'D7DDE8', void300: 'B4BCCB', void400: '8B94A6', void500: '676F80',
  void600: '4C5464', void700: '363D4B', void800: '232935', void850: '1A1F29',
  void900: '12161E', void950: '0A0D13',
  success: '08602F', successS: 'E8F7EE',
  warning: 'B45309', warningS: 'FEF4E6',
  danger: 'C0271B', dangerS: 'FDECEA',
};

const F = {
  ui: 'Inter',
  display: 'Inter Display',
  mono: 'JetBrains Mono',
};

// US Letter, in DXA (1440 per inch)
const PAGE = {
  w: 12240, h: 15840,
  top: 1180, bottom: 1180, left: 1584, right: 1584,
  header: 680, footer: 680,
};
PAGE.content = PAGE.w - PAGE.left - PAGE.right;   // 9072 dxa = 6.30 in

module.exports = { C, F, PAGE };
