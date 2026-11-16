export interface Token {
    /**
     * Normalized form: NFC, then locale-aware lowercase.
     */
    norm: string;
    /**
     * UTF-16 offset of the token in the original text.
     */
    start: number;
    end: number;
}

/**
 * Normalization rules, recorded in report metadata.
 */
export const NORMALIZATION = "Intl.Segmenter(word) tokens; NFC; toLocaleLowerCase(locale)";

const segmenters = new Map<string, Intl.Segmenter>();

function segmenterFor(locale: string): Intl.Segmenter {
    let segmenter = segmenters.get(locale);

    if (!segmenter) {
        segmenter = new Intl.Segmenter(locale, { granularity: "word" });
        segmenters.set(locale, segmenter);
    }

    return segmenter;
}

export function normalize(text: string, locale: string): string {
    return text.normalize("NFC").toLocaleLowerCase(locale);
}

/**
 * Split text into word tokens, keeping offsets into the original string.
 */
export function tokenize(text: string, locale: string): Token[] {
    const tokens: Token[] = [];

    for (const segment of segmenterFor(locale).segment(text)) {
        if (!segment.isWordLike) {
            continue;
        }

        tokens.push({
            norm: normalize(segment.segment, locale),
            start: segment.index,
            end: segment.index + segment.segment.length,
        });
    }

    return tokens;
}

/**
 * Blank out format placeholders so their identifiers aren't scanned as words.
 *
 * Covers Python `%(name)s` and brace `{name}` placeholders. Offsets are preserved.
 */
export function maskPlaceholders(text: string): string {
    const out = text.split("");

    for (let i = 0; i < text.length; i++) {
        let closer: string | null = null;

        if (text[i] === "{") {
            closer = "}";
        } else if (text[i] === "%" && text[i + 1] === "(") {
            closer = ")";
        }

        if (!closer) {
            continue;
        }

        const end = text.indexOf(closer, i + 1);
        const span = end === -1 ? "" : text.slice(i + 1, end);

        if (end === -1 || span.includes("{") || span.includes("\n")) {
            continue;
        }

        // Include the `%(name)s` conversion character.
        const last = closer === ")" && end + 1 < text.length ? end + 1 : end;

        out.fill(" ", i, last + 1);
        i = last;
    }

    return out.join("");
}
