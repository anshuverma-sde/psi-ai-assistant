// Writes demo/external-site.local.html with the tokens from samples/.seed-output.json.
// Usage: node demo/fill-tokens.mjs [APP_URL]
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const seed = JSON.parse(readFileSync(join(here, "../samples/.seed-output.json"), "utf8"));
const appUrl = process.argv[2] ?? "http://localhost:3000";

const html = readFileSync(join(here, "external-site.html"), "utf8")
  .replace('var APP_URL = "http://localhost:3000";', `var APP_URL = "${appUrl}";`)
  .replace("PASTE_NORTHBRIDGE_TOKEN", seed["northbridge-university"].token)
  .replace("PASTE_ACME_TOKEN", seed["acme-corp-hr"].token);

writeFileSync(join(here, "external-site.local.html"), html);
console.log("Wrote demo/external-site.local.html — serve with: python3 -m http.server 5500 --directory demo");
