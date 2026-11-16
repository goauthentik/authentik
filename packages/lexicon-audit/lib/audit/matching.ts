import { TIERS, type Tier } from "#constants";
import { sha256 } from "#hash";
import type { Allowlist } from "#lexicon/allowlist";
import type { LexiconEntry, LexiconIndex } from "#lexicon/database";
import type { TranslationEntry } from "#translation/shared";
import { entryKey, entryVariant } from "#translation/shared";
import { type Token, maskPlaceholders, tokenize } from "#translation/tokenize";

//#region Findings

export type MatchType = "exact" | "casefold";

/**
 * Which text of the unit matched: the translation, or the source string.
 */
export type Side = "target" | "source";

export interface Finding {
    fingerprint: string;
    side: Side;
    /**
     * Path relative to the working directory. For source findings, the first file the string
     * appeared in.
     */
    file: string;
    /**
     * Locale of the matched text.
     */
    locale: string;
    /**
     * Lexicon the match came from.
     */
    lexicon: string;
    key: string;
    variant: string;
    /**
     * 1-based line of the unit in {@linkcode file}.
     */
    line: number;
    tier: Tier;
    categoryHex: string;
    categoryBits: number;
    word: string;
    matchType: MatchType;
    /**
     * UTF-16 span of the match in {@linkcode source} or {@linkcode target}, per {@linkcode side}.
     */
    start: number;
    end: number;
    source: string;
    target: string;
}

/**
 * Where matches are collected: reported findings, and a count of allowlisted ones.
 */
export interface FindingSink {
    findings: Finding[];
    /**
     * Matches suppressed by the allowlist.
     */
    allowed: number;
}

//#endregion

//#region Matching

function matchesAt(
    tokens: Token[],
    index: number,
    text: string,
    entry: LexiconEntry,
    locale: string,
) {
    for (let offset = 1; offset < entry.tokens.length; offset++) {
        const previous = tokens[index + offset - 1];
        const token = tokens[index + offset];

        if (!previous || !token || token.norm !== entry.tokens[offset]) {
            return false;
        }

        const separator = text
            .slice(previous.end, token.start)
            .normalize("NFC")
            .toLocaleLowerCase(locale);

        if (separator !== entry.separators[offset - 1]) {
            return false;
        }
    }

    return true;
}

/**
 * Find whole-token lexicon matches in a translation unit.
 */
export function matchText(
    original: string,
    format: TranslationEntry["format"],
    locale: string,
    index: LexiconIndex,
): Array<{ entry: LexiconEntry; start: number; end: number; matchType: MatchType }> {
    const text = format === "po" ? maskPlaceholders(original) : original;
    const tokens = tokenize(text, locale);
    const matches: Array<{
        entry: LexiconEntry;
        start: number;
        end: number;
        matchType: MatchType;
    }> = [];

    tokens.forEach((token, i) => {
        // Entries differing only in case (`x`, `X`) can match the same span. Keep the best one.
        const best = new Map<number, (typeof matches)[number]>();

        for (const entry of index.get(token.norm) ?? []) {
            if (!matchesAt(tokens, i, text, entry, locale)) {
                continue;
            }

            const end = tokens[i + entry.tokens.length - 1]!.end;
            const exact =
                original.slice(token.start, end).normalize("NFC") === entry.word.normalize("NFC");

            if (entry.caseSensitive && !exact) {
                continue;
            }

            const candidate = {
                entry,
                start: token.start,
                end,
                matchType: exact ? "exact" : "casefold",
            } as const;
            const current = best.get(end);

            if (!current || rankMatch(candidate) < rankMatch(current)) {
                best.set(end, candidate);
            }
        }

        matches.push(...best.values());
    });

    return matches;
}

/**
 * Lower is better: exact before casefold, then the more severe tier, then lexicon order.
 */
function rankMatch({ entry, matchType }: { entry: LexiconEntry; matchType: MatchType }): number {
    return (matchType === "exact" ? 0 : 1) * 1e9 + TIERS.indexOf(entry.tier) * 1e8 + entry.id;
}

//#endregion

//#region Collecting

export function compareFindings(a: Finding, b: Finding): number {
    return (
        a.side.localeCompare(b.side, "en") ||
        a.locale.localeCompare(b.locale, "en") ||
        a.file.localeCompare(b.file, "en") ||
        a.line - b.line ||
        a.key.localeCompare(b.key, "en") ||
        a.variant.localeCompare(b.variant, "en") ||
        a.start - b.start ||
        a.tier.localeCompare(b.tier, "en") ||
        a.word.localeCompare(b.word, "en") ||
        a.categoryBits - b.categoryBits
    );
}

interface MatchContext {
    side: Side;
    file: string;
    locale: string;
    lexicon: string;
    unit: TranslationEntry;
    index: LexiconIndex;
}

export function collectFindings(
    context: MatchContext,
    result: FindingSink,
    allowlist?: Allowlist,
): void {
    const { side, file, locale, lexicon, unit, index } = context;
    const text = side === "target" ? unit.target : unit.source;
    const textHash = sha256(text);
    const seen = new Set<string>();

    for (const { entry, start, end, matchType } of matchText(text, unit.format, locale, index)) {
        if (allowlist?.has(locale, entry.word)) {
            result.allowed++;
            continue;
        }

        // Source strings repeat in every locale's file, so their identity uses the format
        // instead of the file. Otherwise one string would get a fingerprint per locale.
        const identity = JSON.stringify([
            side,
            side === "target" ? file : unit.format,
            locale,
            entryKey(unit),
            entryVariant(unit),
            textHash,
            entry.locale,
            entry.word,
            entry.tier,
            entry.categoryHex,
            start,
            end,
        ]);

        if (seen.has(identity)) {
            continue;
        }
        seen.add(identity);

        result.findings.push({
            fingerprint: sha256(identity),
            side,
            file,
            locale,
            lexicon,
            key: entryKey(unit),
            variant: entryVariant(unit),
            line: unit.line,
            tier: entry.tier,
            categoryHex: entry.categoryHex,
            categoryBits: entry.categoryBits,
            word: entry.word,
            matchType,
            start,
            end,
            source: unit.source,
            target: unit.target,
        });
    }
}

//#endregion
