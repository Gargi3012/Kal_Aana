import { useEffect, useState } from "react";

export type Language = "en" | "hi";

const STORAGE_KEY = "kalaana_lang";

const TRANSLATIONS = {
  en: {
    // Nav
    ask: "Ask",
    map: "Map",
    offices: "Offices",
    method: "Method",
    find_office: "Find an office",
    menu: "Menu",
    close: "Close",
    pages: "Pages",
    loading_offices: "Loading offices…",
    search_placeholder: "Find an office: HR-26, Gurugram, Faridabad…",
    search_empty_title: "No office matches.",
    search_empty_hint: "Try a code like HR-26, or a district name.",

    // Hero
    hero_greeting_1: "Ram Ram,",
    hero_greeting_2: "Haryana",
    hero_tagline: "Stuck at a government office? Start here.",
    hero_placeholder: "e.g. Applied for learner's licence at RTA Gurugram 3 weeks ago",
    hero_badge: "Haryana Public Services",

    // Map
    map_heading: "What Google Maps shows for each Haryana office.",
    map_district_filter: "District",
    map_all_districts: "All Districts",
    map_all_offices: "All Offices",
    map_call_office: "Call Office",
    map_verified_landline: "Verified Landline",
    map_not_verified: "Contact number not verified",
    map_no_phone: "No phone listed",
    map_open_office: "Open the office",
    map_ask_about_it: "Ask about it",

    // Legal & Stat
    law_name: "Haryana Right to Service Act, 2014",
    charter_name: "Passport Seva Citizen's Charter",
    statutory_timelines: "Statutory Timelines",
    commission_name: "Haryana Right to Service Commission",

    // Language Toggle
    switch_language: "हिन्दी",
    current_lang: "English",
  },
  hi: {
    // Nav
    ask: "पूछें",
    map: "मानचित्र",
    offices: "कार्यालय",
    method: "कार्यप्रणाली",
    find_office: "कार्यालय खोजें",
    menu: "मेनू",
    close: "बंद करें",
    pages: "पृष्ठ",
    loading_offices: "कार्यालय लोड हो रहे हैं…",
    search_placeholder: "कार्यालय खोजें: HR-26, गुरुग्राम, फरीदाबाद…",
    search_empty_title: "कोई कार्यालय नहीं मिला।",
    search_empty_hint: "HR-26 जैसा कोड या ज़िले का नाम लिखकर देखें।",

    // Hero
    hero_greeting_1: "राम राम,",
    hero_greeting_2: "हरियाणा",
    hero_tagline: "सरकारी कार्यालय में काम अटका है? यहाँ से शुरुआत करें।",
    hero_placeholder: "उदा. RTA गुरुग्राम में 3 हफ़्ते पहले लर्निंग लाइसेंस दिया था",
    hero_badge: "हरियाणा जनसेवा मंच",

    // Map
    map_heading: "गूगल मैप्स हरियाणा के सरकारी दफ़्तरों के बारे में क्या दिखाता है।",
    map_district_filter: "ज़िला",
    map_all_districts: "सभी ज़िले",
    map_all_offices: "सभी कार्यालय",
    map_call_office: "कॉल करें",
    map_verified_landline: "सत्यापित लैंडलाइन",
    map_not_verified: "फ़ोन नंबर सत्यापित नहीं",
    map_no_phone: "फ़ोन नंबर उपलब्ध नहीं",
    map_open_office: "कार्यालय विवरण देखें",
    map_ask_about_it: "इसके बारे में पूछें",

    // Legal & Stat
    law_name: "हरियाणा सेवा का अधिकार अधिनियम, 2014",
    charter_name: "पासपोर्ट सेवा नागरिक चार्टर",
    statutory_timelines: "कानूनी समय सीमा",
    commission_name: "हरियाणा सेवा का अधिकार आयोग (HRTSC)",

    // Language Toggle
    switch_language: "English",
    current_lang: "हिन्दी",
  },
} as const;

export type TranslationKey = keyof typeof TRANSLATIONS.en;

let currentLang: Language = (typeof localStorage !== "undefined" && (localStorage.getItem(STORAGE_KEY) as Language)) || "en";
const listeners = new Set<(lang: Language) => void>();

export function getLanguage(): Language {
  return currentLang;
}

export function setLanguage(lang: Language) {
  currentLang = lang;
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(STORAGE_KEY, lang);
  }
  document.documentElement.lang = lang;
  listeners.forEach((fn) => fn(lang));
}

export function useLanguage() {
  const [lang, setLangState] = useState<Language>(getLanguage);

  useEffect(() => {
    const handler = (l: Language) => setLangState(l);
    listeners.add(handler);
    return () => {
      listeners.delete(handler);
    };
  }, []);

  const t = (key: TranslationKey): string => {
    return TRANSLATIONS[lang]?.[key] ?? TRANSLATIONS.en[key] ?? key;
  };

  const toggleLang = () => {
    setLanguage(lang === "en" ? "hi" : "en");
  };

  return { lang, setLanguage, toggleLang, t };
}
