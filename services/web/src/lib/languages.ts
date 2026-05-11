// ISO 639 code → English language name for the languages exposed in the
// voice-input dropdown. Single source of truth for routes that bake the
// language name into LLM prompts (chat/route.ts, voice/summarize/route.ts).
export const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  hi: "Hindi",
  bn: "Bengali",
  ta: "Tamil",
  te: "Telugu",
  mr: "Marathi",
  gu: "Gujarati",
  kn: "Kannada",
  ml: "Malayalam",
  pa: "Punjabi",
  as: "Assamese",
  ne: "Nepali",
  sa: "Sanskrit",
  he: "Hebrew",
};

export function languageName(code: string | undefined | null): string {
  if (!code) return "English";
  return LANGUAGE_NAMES[code] ?? "English";
}

// Block of prompt text — shared by the chat system prompt and the
// voice-summarize prompt — that pins down what the LLM must NOT change when
// translating defence/S1000D content into another language. The categories
// match what technicians have to recognize on paper: acronyms, NSNs, part
// numbers, units, and proper nouns. Worded as an OVERRIDE so the model knows
// it beats the "respond in {lang}" rule.
export const IDENTIFIER_PRESERVATION_RULES = `IDENTIFIERS — DO NOT MODIFY (overrides the language rule above):
The following tokens MUST appear in the output exactly as written in the input — same characters, same case, original Latin script — and must NOT be translated, transliterated, expanded, lowercased, or pluralized:
  • ALL-CAPS abbreviations of 2 or more letters (CALM, NBC, ECM, IFF, NSN, GPS, RPM, PSI, USB, LED, HUD, FCS, MRO).
  • Mixed-case alphanumeric designations (M16, F-22, T-72, AC/DC, 4WD, Mk-3, IPv6).
  • Roman numerals (I, II, III, IV, V).
  • Part numbers, NSNs, drawing numbers, software versions, fastener sizes.
  • Unit symbols (kg, mm, cm, °C, °F, dBA, V, A, Hz, Nm, ft·lb).
  • Proper nouns and brand names.

NEVER expand acronyms (CALM stays "CALM", NOT "Combat Active Landing Mark" or any translation of that phrase). NEVER transliterate them into the target script. NEVER translate them.

Worked example — input: "Reduce RPM to 800 and engage ECM, then inspect NSN 1234-56-7890123 every 100 hours."
  Translate ONLY the verbs and connecting words ("Reduce", "and engage", "then inspect", "every", "hours") into the target language. Keep RPM, ECM, NSN, 1234-56-7890123, 800, and 100 exactly as written.`;
