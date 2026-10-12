import { staticMessages } from "./static-translations.js";

export const supportedLanguages = ["en", "zh-Hant"];
export const languageStorageKey = "hk-minibus-language";
let currentLanguage = "en";

export function resolveLanguage(query, stored) {
  return [query, stored].find((value) => supportedLanguages.includes(value)) ?? "en";
}

export const getLanguage = () => currentLanguage;

export function applyStaticLanguage(language, root = document) {
  const messages = staticMessages[language];
  const read = (key) => messages[key] ?? staticMessages.en[key];
  root.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = read(element.dataset.i18n);
  });
  root.querySelectorAll("[data-i18n-html]").forEach((element) => {
    element.innerHTML = read(element.dataset.i18nHtml);
  });
  root.querySelectorAll("[data-i18n-attr]").forEach((element) => {
    for (const pair of element.dataset.i18nAttr.split(/\s+/)) {
      const separator = pair.indexOf(":");
      element.setAttribute(pair.slice(0, separator), read(pair.slice(separator + 1)));
    }
  });
  root.documentElement.lang = language;
  root.querySelectorAll("[data-language]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.language === language));
  });
}

export function initializeLanguage(onChange) {
  let stored;
  try { stored = localStorage.getItem(languageStorageKey); } catch { /* Storage is optional. */ }
  currentLanguage = resolveLanguage(new URL(location.href).searchParams.get("lang"), stored);
  applyStaticLanguage(currentLanguage);
  document.querySelectorAll("[data-language]").forEach((button) => {
    button.addEventListener("click", () => {
      const next = button.dataset.language;
      if (!supportedLanguages.includes(next) || next === currentLanguage) return;
      currentLanguage = next;
      applyStaticLanguage(next);
      try { localStorage.setItem(languageStorageKey, next); } catch { /* Storage is optional. */ }
      const url = new URL(location.href);
      url.searchParams.set("lang", next);
      history.replaceState(history.state, "", url);
      onChange(next);
    });
  });
}
