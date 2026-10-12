import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { staticMessages } from "../src/static-translations.js";
import { annualMessages, annualText } from "../src/annual-translations.js";
import { resolveLanguage, initializeLanguage, getLanguage, languageStorageKey } from "../src/i18n.js";

const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");

test("explicit supported URL language takes precedence, with stored preference and English fallbacks", () => {
  assert.equal(resolveLanguage("en", "zh-Hant"), "en");
  assert.equal(resolveLanguage("zh-Hant", "en"), "zh-Hant");
  assert.equal(resolveLanguage(null, "zh-Hant"), "zh-Hant");
  assert.equal(resolveLanguage("unsupported", "en"), "en");
  assert.equal(resolveLanguage("<script>", "unsupported"), "en");
  assert.equal(resolveLanguage(null, null), "en");
});

test("every static annotation has a complete English and Traditional Chinese translation", () => {
  const keys = [...html.matchAll(/data-i18n(?:-html)?="([^"]+)"/g)].map((match) => match[1]);
  for (const match of html.matchAll(/data-i18n-attr="([^"]+)"/g)) {
    keys.push(...match[1].split(/\s+/).map((pair) => pair.slice(pair.indexOf(":") + 1)));
  }
  assert.equal(keys.length, new Set(keys).size);
  assert.deepEqual(new Set(keys), new Set(Object.keys(staticMessages.en)));
  assert.deepEqual(Object.keys(staticMessages.en).sort(), Object.keys(staticMessages["zh-Hant"]).sort());
  for (const key of keys) {
    assert.ok(staticMessages.en[key].trim(), key);
    assert.ok(staticMessages["zh-Hant"][key].trim(), key);
  }
});

test("trusted static HTML translations never replace controls, chart nodes or live numerical bindings", () => {
  for (const key of [...html.matchAll(/data-i18n-html="([^"]+)"/g)].map((match) => match[1])) {
    for (const language of ["en", "zh-Hant"]) {
      assert.doesNotMatch(staticMessages[language][key], /<(?:input|select|button|canvas|svg|table|details)\b|\bid=|\bdata-(?:kpi|value|recovery|composition|fleet)\b|\bon\w+=|<script/i, `${language}:${key}`);
    }
  }
});

test("annual runtime translations preserve interpolation and qualify estimated RMB in both languages", () => {
  assert.deepEqual(Object.keys(annualMessages.en).sort(), Object.keys(annualMessages["zh-Hant"]).sort());
  assert.equal(annualText("volumeValue", "en", { value: "123.45" }), "123.45 million");
  assert.equal(annualText("volumeValue", "zh-Hant", { value: "123.45" }), "123.45 百萬旅次");
  assert.match(annualText("rmb", "en"), /estimated/);
  assert.match(annualText("rmb", "zh-Hant"), /估算/);
  assert.match(annualText("indexDescription", "zh-Hant"), /2015.*100/);
  assert.match(annualText("chartUnavailable", "zh-Hant"), /無法使用/);
});

function withBrowser({ stored, storageFails = false, url }, run) {
  const names = ["document", "localStorage", "location", "history"];
  const previous = names.map((name) => Object.getOwnPropertyDescriptor(globalThis, name));
  const events = new Map();
  const buttons = ["en", "zh-Hant"].map((language) => ({
    dataset: { language }, attributes: {},
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener(name, callback) { events.set(`${language}:${name}`, callback); },
  }));
  const label = { dataset: { i18n: "static.language" }, textContent: "" };
  const writes = [];
  const replacementUrls = [];
  globalThis.document = {
    documentElement: { lang: "en" },
    querySelectorAll(selector) {
      return selector === "[data-language]" ? buttons : selector === "[data-i18n]" ? [label] : [];
    },
  };
  globalThis.localStorage = {
    getItem(key) { assert.equal(key, languageStorageKey); if (storageFails) throw new Error("Blocked"); return stored; },
    setItem(key, value) { if (storageFails) throw new Error("Blocked"); writes.push([key, value]); },
  };
  globalThis.location = { href: url };
  globalThis.history = { state: { preserved: true }, replaceState(state, _, next) { assert.deepEqual(state, { preserved: true }); replacementUrls.push(new URL(next)); } };
  try { run({ events, buttons, label, writes, replacementUrls }); }
  finally { names.forEach((name, index) => previous[index] ? Object.defineProperty(globalThis, name, previous[index]) : delete globalThis[name]); }
}

test("language toggle updates accessible state, remembers choice and preserves other URL state", () => {
  withBrowser({ stored: "zh-Hant", url: "https://example.com/research/?lang=en&year=2019#fleet" }, ({ events, buttons, label, writes, replacementUrls }) => {
    const changed = [];
    initializeLanguage((language) => changed.push(language));
    assert.equal(getLanguage(), "en");
    events.get("zh-Hant:click")();
    assert.equal(document.documentElement.lang, "zh-Hant");
    assert.equal(label.textContent, staticMessages["zh-Hant"]["static.language"]);
    assert.deepEqual(buttons.map((button) => button.attributes["aria-pressed"]), ["false", "true"]);
    assert.deepEqual(writes, [[languageStorageKey, "zh-Hant"]]);
    assert.equal(replacementUrls[0].searchParams.get("year"), "2019");
    assert.equal(replacementUrls[0].searchParams.get("lang"), "zh-Hant");
    assert.equal(replacementUrls[0].hash, "#fleet");
    events.get("zh-Hant:click")();
    assert.deepEqual(changed, ["zh-Hant"]);
    events.get("en:click")();
    assert.equal(getLanguage(), "en");
    assert.deepEqual(changed, ["zh-Hant", "en"]);
  });
});

test("language selection still works when browser storage is unavailable", () => {
  withBrowser({ storageFails: true, url: "https://example.com/research/" }, ({ events }) => {
    let changed;
    initializeLanguage((language) => { changed = language; });
    assert.equal(getLanguage(), "en");
    events.get("zh-Hant:click")();
    assert.equal(changed, "zh-Hant");
    assert.equal(document.documentElement.lang, "zh-Hant");
  });
});
