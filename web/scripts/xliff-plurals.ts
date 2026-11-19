/**
 * @remarks
 *   `plural()` gives each form its own message id, `<base>.<category>`. Transifex
 *   only offers translators the strings in `en.xlf`, so the forms are grouped
 *   into its plural format:
 *
 *   ```xml
 *   <group id="<base>" restype="x-gettext-plurals">
 *   <trans-unit id="<base>[0]">…</trans-unit>
 *   <trans-unit id="<base>[1]">…</trans-unit>
 *   </group>
 *   ```
 *
 *   Transifex then asks each translator for exactly the forms their language
 *   has. Index `n` is the n-th category of the file's locale, in CLDR order,
 *   which is the order of `Intl.PluralRules#resolvedOptions().pluralCategories`.
 * @file Plural message support for lit-localize's XLIFF interchange.
 */

import type { Message, ProgramMessage } from "@lit/localize-tools/lib/messages.js";
import { RuntimeLitLocalizer } from "@lit/localize-tools/lib/modes/runtime.js";
import type { Locale } from "@lit/localize-tools/lib/types/locale.js";

/**
 * Every CLDR plural category, in CLDR order.
 */
export const PluralCategories = ["zero", "one", "two", "few", "many", "other"] as const;

export type PluralCategory = (typeof PluralCategories)[number];

const CategoryIDPattern = /^(.+)\.(zero|one|two|few|many|other)$/;
const IndexedIDPattern = /^(.+)\[(\d+)\]$/;

/**
 * The plural categories of a locale, in the order Transifex indexes them.
 */
export function pluralCategoriesOf(locale: string): PluralCategory[] {
    return new Intl.PluralRules(locale).resolvedOptions().pluralCategories as PluralCategory[];
}

/**
 * Split a plural form's message id into its base id and category.
 */
export function parsePluralID(id: string): [base: string, category: PluralCategory] | null {
    const match = CategoryIDPattern.exec(id);

    return match ? [match[1], match[2] as PluralCategory] : null;
}

/**
 * Collect the base ids of plural messages, i.e. those with an "other" form.
 */
function collectPluralBases(ids: Iterable<string>): Set<string> {
    const bases = new Set<string>();

    for (const id of ids) {
        const parsed = parsePluralID(id);

        if (parsed?.[1] === "other") {
            bases.add(parsed[0]);
        }
    }

    return bases;
}

type SourceMessages = ReturnType<RuntimeLitLocalizer["extractSourceMessages"]>;

type Translations = ReturnType<RuntimeLitLocalizer["readTranslationsSync"]>;

/**
 * A runtime-mode localizer aware of plural groups.
 *
 * - Every plural message gets a source message for every category. Categories the source code doesn't
 *   write use the "other" form's text, and fall back to it at runtime when untranslated.
 * - Translations indexed as `<base>[n]` are read back as `<base>.<category>`.
 */
export class PluralRuntimeLitLocalizer extends RuntimeLitLocalizer {
    #sourceMessages?: SourceMessages;
    #translations?: Translations;

    public override extractSourceMessages(): SourceMessages {
        if (this.#sourceMessages) return this.#sourceMessages;

        const extracted = super.extractSourceMessages();
        const sourceCategories = new Set<string>(pluralCategoriesOf(this.config.sourceLocale));

        for (const { name } of extracted.messages) {
            const category = parsePluralID(name)?.[1];

            if (category && !sourceCategories.has(category)) {
                throw new Error(
                    `Message "${name}" is a "${category}" form, which ${this.config.sourceLocale} doesn't have. ` +
                        "Translators supply it; use a numeric key for an exact count.",
                );
            }
        }

        const byName = new Map(extracted.messages.map((message) => [message.name, message]));
        const messages: ProgramMessage[] = [...extracted.messages];

        for (const base of collectPluralBases(byName.keys())) {
            const other = byName.get(`${base}.other`)!;

            for (const category of PluralCategories) {
                const name = `${base}.${category}`;

                if (!byName.has(name)) {
                    messages.push({ ...other, name });
                }
            }
        }

        this.#sourceMessages = { ...extracted, messages };

        return this.#sourceMessages;
    }

    public override readTranslationsSync(): Translations {
        if (this.#translations) return this.#translations;

        const read = super.readTranslationsSync();
        const translations = new Map<Locale, Message[]>();

        for (const [locale, messages] of read.translations) {
            const categories = pluralCategoriesOf(locale);
            const renamed: Message[] = [];

            for (const message of messages) {
                const match = IndexedIDPattern.exec(message.name);

                if (!match) {
                    renamed.push(message);

                    continue;
                }

                const category = categories[Number(match[2])];

                if (category) {
                    renamed.push({ ...message, name: `${match[1]}.${category}` });
                }
            }

            translations.set(locale, renamed);
        }

        this.#translations = { ...read, translations };

        return this.#translations;
    }
}

const TransUnitPattern = /<trans-unit id="([^"]+)">\n([\s\S]*?)<\/trans-unit>\n/g;
const TargetLanguagePattern = /target-language="([^"]+)"/;

/**
 * Rewrite the per-category units lit-localize writes into one Transifex plural
 * group per message, with the forms of the file's own locale.
 *
 * @param xml An XLIFF file as written by lit-localize.
 *
 * @returns The rewritten file.
 */
export function groupPluralUnits(xml: string): string {
    const locale = TargetLanguagePattern.exec(xml)?.[1];

    if (!locale) {
        throw new TypeError("XLIFF file has no target-language");
    }

    const units = new Map<string, string>();

    for (const [, id, body] of xml.matchAll(TransUnitPattern)) {
        units.set(id, body);
    }

    const bases = collectPluralBases(units.keys());

    if (!bases.size) return xml;

    const categories = pluralCategoriesOf(locale);

    return xml.replace(TransUnitPattern, (unit, id: string) => {
        const parsed = parsePluralID(id);

        if (!parsed || !bases.has(parsed[0])) return unit;

        const [base, category] = parsed;

        // The group takes the place of the "other" form, which every plural message has.
        if (category !== "other") return "";

        const forms = categories.map((formCategory, index) => {
            const body = (units.get(`${base}.${formCategory}`) ?? units.get(`${base}.other`)!)
                .replace(/^/gm, "  ")
                .trimEnd();

            return `  <trans-unit id="${base}[${index}]" xml:space="preserve">\n${body}\n  </trans-unit>\n`;
        });

        return `<group id="${base}" restype="x-gettext-plurals">\n${forms.join("")}</group>\n`;
    });
}
