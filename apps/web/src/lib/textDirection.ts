// Audit finding: the backend supports a full Arabic conversation mode and
// bilingual books, but the frontend never set `dir="rtl"` or switched to the
// Arabic font stack anywhere — Arabic replies would render left-to-right in
// a Latin font, which is a real functional break for the "Arabic-English
// Assistant" MVP module, not a cosmetic one. Detection is based on the
// actual text (not the conversation `mode`) because a message can contain
// Arabic regardless of which mode it was sent in.
const ARABIC_RANGE = /[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]/;

/** True when a meaningful share of the text's letters are Arabic script. */
export function isArabicText(text: string): boolean {
  const letters = text.replace(/[^\p{L}]/gu, "");
  if (letters.length < 4) return false;
  const arabicLetters = letters.match(new RegExp(ARABIC_RANGE, "gu"))?.length ?? 0;
  return arabicLetters / letters.length > 0.4;
}
