/**
 * @file Custom locale catalogs, managed by administrators and stored by the server.
 */

import { aki } from "#common/api/client";
import { globalAK } from "#common/global";
import { PseudoLanguageTag } from "#common/ui/locale/definitions";

import { ConsoleLogger } from "#logger/browser";

import { AdminApi } from "@goauthentik/api";

import { type LocaleModule, str, type StrResult } from "@lit/localize";
import { generateMsgId } from "@lit/localize/internal/id-generation.js";

const logger = ConsoleLogger.prefix("locale/custom");

type Templates = LocaleModule["templates"];

/**
 * Lit Localize's placeholder for the n-th expression of a template, e.g. `Hello ${0}`.
 */
const PlaceholderPattern = /\$\{(\d+)\}/g;

/**
 * Splits a message into its literal strings and the indices of its placeholders.
 */
function splitPlaceholders(message: string): [strings: string[], values: number[]] {
    const strings: string[] = [];
    const values: number[] = [];

    let lastIndex = 0;

    for (const match of message.matchAll(PlaceholderPattern)) {
        strings.push(message.slice(lastIndex, match.index));
        values.push(parseInt(match[1], 10));
        lastIndex = match.index + match[0].length;
    }

    strings.push(message.slice(lastIndex));

    return [strings, values];
}

/**
 * Converts a custom translation to a Lit Localize template.
 *
 * Placeholders such as `${0}` refer to the expressions of the source template,
 * which allows translations to reorder them.
 */
export function parseTranslation(translation: string): string | StrResult {
    const [strings, values] = splitPlaceholders(translation);

    if (!values.length) return translation;

    return str(Object.assign(strings, { raw: strings }), ...values);
}

/**
 * Converts custom messages to Lit Localize templates.
 *
 * Messages may be keyed by either a message ID, or by the English source string
 * (with `${0}`-style placeholders for expressions), which is converted to the
 * ID Lit Localize generates for it. The runtime checks both for every message.
 */
export function createCustomTemplates(messages: Record<string, string>): Templates {
    const templates: Templates = {};

    for (const [key, translation] of Object.entries(messages)) {
        const template = parseTranslation(translation);
        const [strings] = splitPlaceholders(key);

        templates[generateMsgId(strings, false)] = template;
        templates[key] = template;
    }

    return templates;
}

/**
 * Fetches the custom templates applicable to the given locale.
 *
 * The server embeds the custom messages for the initial locale into the page,
 * so only switching to another locale requires a request.
 * Failing to do so is not fatal, the built-in translations are used instead.
 */
export async function loadCustomTemplates(locale: string): Promise<Templates> {
    if (locale === PseudoLanguageTag) return {};

    const { locale: initialLocale, localeCatalog } = globalAK();

    if (localeCatalog && locale === initialLocale) {
        return createCustomTemplates(localeCatalog.messages);
    }

    try {
        const { messages } = await aki(AdminApi).adminLocaleCatalogsResolveRetrieve({ locale });

        return createCustomTemplates(messages);
    } catch (error) {
        logger.warn(`Failed to load custom catalogs for "${locale}"`, error);

        return {};
    }
}
