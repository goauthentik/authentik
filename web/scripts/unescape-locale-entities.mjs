/// <reference types="node" />

/**
 * @file Locale module post-process pass. `@lit/localize-tools` 0.8.x runs an HTML escape on every
 *   text fragment it splices into a compiled message template, including `str`-tagged and untagged
 *   messages whose runtime value is a plain string. Any `<`/`>`/`&` in the translation gets baked
 *   in as `&lt;`/`&gt;`/`&amp;`, and any literal entity reference a translator typed (`&quot;`,
 *   `&lt;`, ...) round-trips through the escape as `&amp;quot;`/`&amp;lt;`/..., showing up to the
 *   user as visible entity text. The `html`-tagged messages need the escape — lit-html parses their
 *   static parts as HTML — so we leave those alone. Everything else gets decoded back to the
 *   characters the translator meant.
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

const TEMPLATE_TAGS = new Set(["str", "html"]);

const ENTITY_PATTERN = /&(?:lt|gt|quot|apos|amp);/g;
const DOUBLE_ENCODED_PATTERN = /&amp;(lt|gt|quot|apos|amp);/g;

/** @type {Record<string, string>} */
const ENTITY_TABLE = {
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&apos;": "'",
    "&amp;": "&",
};

/**
 * Decode the XML predefined entity refs. Repeats until stable so doubly-encoded forms like
 * `&amp;quot;` collapse to `"` in one call.
 *
 * Used for non-HTML templates: the result becomes raw text content in the DOM, so the entity
 * references have to disappear entirely.
 *
 * @param {string} input
 *
 * @returns {{ output: string; replacements: number }}
 */
function decodeXmlEntities(input) {
    let current = input;
    let replacements = 0;

    for (;;) {
        let local = 0;
        const next = current.replace(ENTITY_PATTERN, (match) => {
            local++;

            return ENTITY_TABLE[match];
        });

        if (local === 0) return { output: current, replacements };

        replacements += local;
        current = next;
    }
}

/**
 * Strip exactly one layer of `&amp;`-doubling from XML entity references.
 *
 * Used for `html`-tagged templates: lit-html parses the static parts as HTML, so a legitimate
 * `&gt;` must stay as `&gt;`, but a translator's `&amp;gt;` (which renders to a visible `&gt;`)
 * should collapse back to `&gt;` (which renders to `>`).
 *
 * @param {string} input
 *
 * @returns {{ output: string; replacements: number }}
 */
function undoubleHtmlEntities(input) {
    let replacements = 0;
    const output = input.replace(DOUBLE_ENCODED_PATTERN, (_match, name) => {
        replacements++;

        return `&${name};`;
    });

    return { output, replacements };
}

/**
 * Walks a compiled locale module and rewrites every non-`html` template literal so its body no
 * longer carries XML entity references.
 *
 * Does not parse the file as TypeScript; the emitted shape from `@lit/localize-tools` is regular
 * enough to scan character-by-character.
 *
 * @param {string} source
 *
 * @returns {{ output: string; replacements: number }}
 */
export function sanitizeLocaleModule(source) {
    let output = "";
    let cursor = 0;
    let replacements = 0;

    while (cursor < source.length) {
        const backtick = source.indexOf("`", cursor);

        if (backtick === -1) {
            output += source.slice(cursor);
            break;
        }

        // Walk back from the opening backtick to recover the tag identifier
        // (`str`, `html`, or none for a plain template literal).
        let tagStart = backtick;

        while (tagStart > 0 && /[A-Za-z_$]/.test(source[tagStart - 1])) {
            tagStart--;
        }

        const tag = source.slice(tagStart, backtick);
        const isTagged = TEMPLATE_TAGS.has(tag);
        const isHtml = tag === "html";

        // Emit everything up to and including the opening backtick.
        output += source.slice(cursor, backtick + 1);

        // Scan to the matching closing backtick, jumping over backslash
        // escapes and ${...} substitution holes.
        let end = backtick + 1;
        let depth = 0;

        while (end < source.length) {
            const ch = source[end];

            if (ch === "\\") {
                end += 2;
                continue;
            }

            if (depth === 0 && ch === "`") {
                break;
            }

            if (ch === "$" && source[end + 1] === "{") {
                depth++;
                end += 2;
                continue;
            }

            if (ch === "{" && depth > 0) {
                depth++;
                end++;
                continue;
            }

            if (ch === "}" && depth > 0) {
                depth--;
                end++;
                continue;
            }

            end++;
        }

        const body = source.slice(backtick + 1, end);

        if (isHtml) {
            const decoded = undoubleHtmlEntities(body);
            replacements += decoded.replacements;
            output += decoded.output;
        } else if (isTagged || tag === "") {
            const decoded = decodeXmlEntities(body);
            replacements += decoded.replacements;
            output += decoded.output;
        } else {
            output += body;
        }

        if (end < source.length) {
            output += "`";
            cursor = end + 1;
        } else {
            cursor = end;
        }
    }

    return { output, replacements };
}

/**
 * Run {@link sanitizeLocaleModule} over every `.ts` and `.js` file in the emitted locales directory.
 * Rewrites files in place when their contents change.
 *
 * @param {string} directory
 *
 * @returns {Promise<{ touched: number; replacements: number }>}
 */
export async function unescapeOverescapedLitTemplates(directory) {
    const entries = await fs.readdir(directory, { withFileTypes: true });

    let touched = 0;
    let replacements = 0;

    await Promise.all(
        entries.map(async (entry) => {
            if (!entry.isFile()) return;

            if (!entry.name.endsWith(".ts") && !entry.name.endsWith(".js")) return;

            const filePath = path.join(directory, entry.name);
            const original = await fs.readFile(filePath, "utf8");
            const { output, replacements: localReplacements } = sanitizeLocaleModule(original);

            if (output !== original) {
                await fs.writeFile(filePath, output, "utf8");
                touched++;
                replacements += localReplacements;
            }
        }),
    );

    return { touched, replacements };
}
