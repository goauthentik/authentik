/**
 * @remarks
 *   Fills the strings a locale's catalogs are missing, for shipping a language whose
 *   Transifex catalogs lag behind the source. `export` writes the missing web and
 *   backend strings as JSON batches, someone translates them into `out*.json`, and
 *   `merge` writes them back. `merge --corrections` applies a review's
 *   `corrections.json` over existing translations.
 *   Web placeholders are written as `{{n}}`, the n-th placeholder of the source
 *   message. Backend plurals are an array with one string per form of the locale.
 *
 *   ```sh
 *   node scripts/fill-locale.ts export <tag> <workdir> [batches]
 *   node scripts/fill-locale.ts merge <tag> <workdir> [--check] [--corrections]
 *   ```
 * @file Fill a locale's missing web and backend translations.
 */

import { execFileSync } from "node:child_process";
import * as fs from "node:fs/promises";
import path from "node:path";

import {
    groupPluralUnits,
    pluralCategoriesOf,
    parsePluralID,
    PluralRuntimeLitLocalizer,
    ungroupPluralUnits,
} from "./xliff-plurals.ts";

import { ConsoleLogger } from "#logger/node";
import { PackageRoot } from "#paths/node";

import { readPO, readPOBlocks } from "@goauthentik/lexicon-audit/translation/po";
import { entryKey } from "@goauthentik/lexicon-audit/translation/shared";

import { readConfigFileAndWriteSchema } from "@lit/localize-tools/lib/config.js";
import type { Message, Placeholder } from "@lit/localize-tools/lib/messages.js";
import { validateLocalizedPlaceholders } from "@lit/localize-tools/lib/messages.js";
import type { Locale } from "@lit/localize-tools/lib/types/locale.js";

const logger = ConsoleLogger.child({ name: "Locales" });

//#region Types

interface BatchItem {
    key: string;
    source: string;
    /** Backend plural source, when the entry has one. */
    plural?: string;
    /** Number of backend plural forms the locale has. */
    forms?: number;
}

type Translation = string | string[];

interface Correction {
    old: Translation;
    new: Translation;
    why: string;
}

//#endregion

//#region Web (XLIFF)

class FillLocalizer extends PluralRuntimeLitLocalizer {
    public extra: Message[] = [];

    public override readTranslationsSync() {
        const read = super.readTranslationsSync();
        const [locale] = this.config.targetLocales;
        const byName = new Map((read.translations.get(locale) ?? []).map((m) => [m.name, m]));

        for (const message of this.extra) byName.set(message.name, message);

        read.translations.set(locale, [...byName.values()]);

        return read;
    }
}

function createLocalizer(tag: string): FillLocalizer {
    const config = readConfigFileAndWriteSchema(path.join(PackageRoot, "lit-localize.json"));

    if (config.interchange.format !== "xliff" || config.output.mode !== "runtime") {
        throw new Error("Expected XLIFF interchange and runtime output");
    }

    return new FillLocalizer({
        ...config,
        targetLocales: [tag as Locale],
        interchange: config.interchange,
        output: config.output,
    });
}

function toText(contents: Message["contents"]): string {
    let index = 0;

    return contents.map((part) => (typeof part === "string" ? part : `{{${index++}}}`)).join("");
}

function fromText(text: string, source: Message["contents"]): Message["contents"] {
    const placeholders = source.filter((part): part is Placeholder => typeof part !== "string");

    return text
        .split(/(\{\{\d+\}\})/)
        .filter(Boolean)
        .map((part) => {
            const match = /^\{\{(\d+)\}\}$/.exec(part);

            return match ? placeholders[Number(match[1])] : part;
        });
}

function missingWebMessages(localizer: FillLocalizer, tag: string): BatchItem[] {
    const categories = new Set<string>(pluralCategoriesOf(tag));

    const translated = new Set(
        (localizer.readTranslationsSync().translations.get(tag as Locale) ?? []).map((m) => m.name),
    );

    return localizer
        .extractSourceMessages()
        .messages.filter(({ name, contents }) => {
            const category = parsePluralID(name)?.[1];

            if (category && !categories.has(category)) return false;

            return !translated.has(name) && toText(contents).trim();
        })
        .map(({ name, contents }) => ({ key: `web:${name}`, source: toText(contents) }));
}

async function writeWeb(
    localizer: FillLocalizer,
    tag: string,
    translations: Map<string, Translation>,
) {
    const sources = new Map(localizer.extractSourceMessages().messages.map((m) => [m.name, m]));

    for (const [key, value] of translations) {
        if (!key.startsWith("web:") || typeof value !== "string") continue;

        const source = sources.get(key.slice(4));

        if (source)
            localizer.extra.push({ name: source.name, contents: fromText(value, source.contents) });
    }

    const errors = validateLocalizedPlaceholders(
        [...sources.values()],
        new Map([[tag as Locale, localizer.extra]]),
    );

    if (errors.length) throw new Error(errors.join("\n"));

    const filePath = path.join(PackageRoot, "xliff", `${tag}.xlf`);

    // Read the existing translations while the plural groups are intact.
    localizer.readTranslationsSync();
    await fs.writeFile(filePath, ungroupPluralUnits(await fs.readFile(filePath, "utf8")), "utf8");
    await localizer.writeInterchangeFiles();
    await fs.writeFile(filePath, groupPluralUnits(await fs.readFile(filePath, "utf8")), "utf8");
}

//#endregion

//#region Backend (PO)

const POLineWidth = 78;

/**
 * Render a PO field the way Transifex wraps it: at most 78 columns, breaking
 * after spaces, hyphens between letters, and newlines.
 */
function renderPOField(keyword: string, text: string): string[] {
    const escaped = JSON.stringify(text).slice(1, -1);
    const single = `${keyword} "${escaped}"`;

    const multiline = escaped.slice(0, -2).includes("\\n");

    if (single.length <= POLineWidth && !multiline) return [single];

    // Text with line breaks is split at them only.
    if (multiline) {
        return [`${keyword} ""`, ...escaped.split(/(?<=\\n)/).map((line) => `"${line}"`)];
    }

    const tokens = escaped
        .split(/(\\n|\s+)/)
        .flatMap((token) => token.split(/(?<=\p{L}-)(?=\p{L})/u))
        .filter(Boolean);

    const lines = [`${keyword} ""`];
    let line = "";

    for (const token of tokens) {
        if (line && `"${line}${token}"`.length > POLineWidth) {
            lines.push(`"${line}"`);
            line = "";
        }

        line += token;

        if (token.endsWith("\\n")) {
            lines.push(`"${line}"`);
            line = "";
        }
    }

    if (line) lines.push(`"${line}"`);

    return lines;
}

function poPath(tag: string): string {
    // Django's to_locale() for every tag in locales.yaml.
    return path.join(
        PackageRoot,
        "..",
        "locale",
        tag.replace("-", "_"),
        "LC_MESSAGES",
        "django.po",
    );
}

interface POEntryForms {
    key: string;
    source: string;
    plural?: string;
    /** 1-based line where the entry's block starts. */
    line: number;
    targets: string[];
}

/**
 * Collect a PO file's entries, one per message with all its plural forms.
 */
async function readPOEntries(filePath: string): Promise<POEntryForms[]> {
    const entries = new Map<string, POEntryForms>();

    for await (const entry of readPO(filePath)) {
        const key = `po:${entryKey(entry)}`;
        const existing = entries.get(key);

        if (existing) {
            existing.targets.push(entry.target);
            existing.plural ??= entry.source;
        } else {
            entries.set(key, {
                key,
                source: entry.source,
                line: entry.line,
                targets: [entry.target],
            });
        }
    }

    return [...entries.values()];
}

async function missingPOEntries(tag: string): Promise<BatchItem[]> {
    const entries = await readPOEntries(poPath(tag));

    return entries
        .filter((entry) => entry.targets.every((target) => !target))
        .map(({ key, source, plural, targets }) =>
            plural ? { key, source, plural, forms: targets.length } : { key, source },
        );
}

async function writePO(tag: string, translations: Map<string, Translation>): Promise<number> {
    const filePath = poPath(tag);
    const entries = new Map((await readPOEntries(filePath)).map((entry) => [entry.line, entry]));
    const lines = (await fs.readFile(filePath, "utf8")).split("\n");
    const edits: { start: number; end: number; replacement: string[] }[] = [];

    for await (const block of readPOBlocks(filePath)) {
        const entry = entries.get(block.line);
        const value = entry && translations.get(entry.key);

        if (value === undefined) continue;

        const blockLines = block.text.split("\n");
        // msgstr is the last field of an entry.
        const offset = blockLines.findIndex((line) => line.startsWith("msgstr"));

        edits.push({
            start: block.line - 1 + offset,
            end: block.line - 1 + blockLines.length,
            replacement: Array.isArray(value)
                ? value.flatMap((form, index) => renderPOField(`msgstr[${index}]`, form))
                : renderPOField("msgstr", value),
        });
    }

    // Bottom-up, so earlier line numbers stay valid.
    for (const { start, end, replacement } of edits.toReversed()) {
        lines.splice(start, end - start, ...replacement);
    }

    if (edits.length) {
        await fs.writeFile(filePath, lines.join("\n"), "utf8");

        execFileSync(
            "uv",
            [
                "run",
                "--no-sync",
                "python",
                "-m",
                "manage",
                "compilemessages",
                "-l",
                tag.replace("-", "_"),
            ],
            { cwd: path.join(PackageRoot, ".."), stdio: "inherit" },
        );
    }

    return edits.length;
}

//#endregion

//#region Validation

const PlaceholderPattern = /\{\{\d+\}\}|%\(\w+\)[sd]|%[sd]|\{\w+\}|<[^>]+>/g;

function placeholdersOf(text: string): string {
    return (text.match(PlaceholderPattern) ?? []).toSorted().join(" ");
}

function validate(
    items: Map<string, BatchItem>,
    translations: Map<string, Translation>,
    complete: boolean,
): string[] {
    const problems: string[] = [];

    for (const [key, item] of items) {
        const value = translations.get(key);

        if (value === undefined) {
            if (complete) problems.push(`${key}: missing`);

            continue;
        }

        if (item.plural) {
            if (!Array.isArray(value) || value.length !== item.forms) {
                problems.push(`${key}: expected ${item.forms} plural forms`);
            }

            continue;
        }

        if (typeof value !== "string" || placeholdersOf(value) !== placeholdersOf(item.source)) {
            problems.push(`${key}: placeholders differ from the source`);
        }
    }

    for (const key of translations.keys()) {
        if (!items.has(key)) problems.push(`${key}: not in any batch`);
    }

    return problems;
}

//#endregion

//#region Commands

async function readJSONFiles<T>(dir: string, pattern: RegExp): Promise<T[]> {
    const names = (await fs.readdir(dir)).filter((name) => pattern.test(name)).toSorted();

    return Promise.all(
        names.map(async (name) => JSON.parse(await fs.readFile(path.join(dir, name), "utf8"))),
    );
}

async function exportCommand(tag: string, dir: string, batches: number) {
    const items = [
        ...missingWebMessages(createLocalizer(tag), tag),
        ...(await missingPOEntries(tag)),
    ];

    const size = Math.max(1, Math.ceil(items.length / batches));

    await fs.mkdir(dir, { recursive: true });

    for (let index = 0; index * size < items.length; index++) {
        const batch = items.slice(index * size, (index + 1) * size);

        await fs.writeFile(path.join(dir, `batch${index}.json`), JSON.stringify(batch, null, 1));
    }

    logger.info(`${items.length} missing strings in batches of ${size}`);
}

async function mergeCommand(tag: string, dir: string, check: boolean, corrections: boolean) {
    const items = new Map(
        (await readJSONFiles<BatchItem[]>(dir, /^batch\d+\.json$/)).flat().map((i) => [i.key, i]),
    );

    const translations = new Map<string, Translation>(
        corrections
            ? Object.entries(
                  (
                      await readJSONFiles<Record<string, Correction>>(dir, /^corrections\.json$/)
                  )[0] ?? {},
              ).map(([key, fix]) => [key, fix.new])
            : (await readJSONFiles<Record<string, Translation>>(dir, /^out\d+\.json$/)).flatMap(
                  Object.entries,
              ),
    );

    const problems = validate(items, translations, !corrections);

    if (problems.length) {
        for (const problem of problems) logger.error(problem);
        process.exit(1);
    }

    if (check) {
        logger.info(`${translations.size} translations are valid`);

        return;
    }

    await writeWeb(createLocalizer(tag), tag, translations);
    const po = await writePO(tag, translations);

    logger.info(`Wrote ${translations.size - po} web and ${po} backend translations`);
}

const [command, tag, dir, ...rest] = process.argv.slice(2);

if (!tag || !dir) {
    logger.error(
        "Usage: fill-locale.ts <export|merge> <tag> <workdir> [batches | --check --corrections]",
    );

    process.exit(1);
}

switch (command) {
    case "export":
        await exportCommand(tag, path.resolve(dir), Number(rest[0] ?? 4));
        break;
    case "merge":
        await mergeCommand(
            tag,
            path.resolve(dir),
            rest.includes("--check"),
            rest.includes("--corrections"),
        );
        break;
    default:
        logger.error(`Unknown command: ${command}`);
        process.exit(1);
}

//#endregion
