import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

import type { Finding } from "#audit/matching";
import type { ScanResult } from "#audit/scan";
import { SCHEMA_VERSION, TIERS, type Tier } from "#constants";
import { NORMALIZATION } from "#translation/tokenize";

export interface ReportContext {
    result: ScanResult;
    tiers: readonly Tier[];
    generatedAt: string;
}

//#region JSONL

export function renderJSONL({ result, generatedAt }: ReportContext): string {
    const metadata = {
        type: "metadata",
        schemaVersion: SCHEMA_VERSION,
        normalization: NORMALIZATION,
        generatedAt,
    };

    const lines = [
        metadata,
        ...result.findings.map((finding) => ({ type: "finding", ...finding })),
    ];

    return lines.map((line) => JSON.stringify(line)).join("\n") + "\n";
}

//#endregion

//#region Markdown rendering

const MARK_OPEN = "⟦";
const MARK_CLOSE = "⟧";

const TRIAGE = `## How to triage

The lexicon flags words, not meanings. Many matches are ordinary vocabulary that the lexicon
marks because of a secondary sense. Read each match in context and decide:

- **false positive**: legitimate use, e.g. a technical term or a word with an innocent primary sense.
- **accepted**: the text is a real problem and needs rewording.
- **needs context**: can't tell without knowing where the string appears in the UI.

Where to fix a real problem:

- **Translations** are synced from Transifex. Don't edit \`web/xliff/*.xlf\` or
  \`locale/*/LC_MESSAGES/*.po\` by hand: the next sync overwrites them. Fix the string in
  Transifex for that locale.
- **Source strings** (English) come from the code. Find the string with the unit key and fix it
  there, then re-extract with \`make i18n-extract\`.

How to read a finding:

- The match is marked ${MARK_OPEN}like this${MARK_CLOSE} inside the text.
- Locations are \`file:line\` of the unit. In XLIFF the key is the \`<trans-unit id>\`; in PO it is
  the \`msgid\`, prefixed with its \`msgctxt\` and U+0004 when there is one.
- \`casefold\` means the match differs from the lexicon entry only by case or Unicode
  normalization; \`exact\` means it is identical.
- Compound words split on hyphens and apostrophes, so a match can be one part of a compound.
`;

function fence(text: string): string {
    let ticks = "```";

    while (text.includes(ticks)) {
        ticks += "`";
    }

    return `${ticks}text\n${text}\n${ticks}`;
}

function inlineCode(text: string): string {
    const single = text.replaceAll("\n", "\\n");
    const ticks = single.includes("`") ? "``" : "`";
    const pad = single.startsWith("`") || single.endsWith("`") ? " " : "";

    return `${ticks}${pad}${single}${pad}${ticks}`;
}

function markMatch(text: string, start: number, end: number): string {
    return text.slice(0, start) + MARK_OPEN + text.slice(start, end) + MARK_CLOSE + text.slice(end);
}

function groupBy<T, K>(items: readonly T[], key: (item: T) => K): Map<K, T[]> {
    const groups = new Map<K, T[]>();

    for (const item of items) {
        const k = key(item);
        const group = groups.get(k);

        if (group) {
            group.push(item);
        } else {
            groups.set(k, [item]);
        }
    }

    return groups;
}

function renderWord(word: string, findings: Finding[]): string[] {
    const matchTypes = [...new Set(findings.map((f) => f.matchType))].sort().join(", ");
    const lines = [
        `### ${inlineCode(word)}: ${findings.length} ${findings.length === 1 ? "match" : "matches"} (${matchTypes})`,
        "",
    ];

    // The same text often appears in several files or units. Show it once with every location.
    const byText = groupBy(findings, (f) => {
        const text = f.side === "target" ? f.target : f.source;

        return markMatch(text, f.start, f.end);
    });

    for (const [marked, occurrences] of byText) {
        const first = occurrences[0]!;

        lines.push("- Locations:");

        for (const f of occurrences) {
            const variant = f.variant ? `, variant ${inlineCode(f.variant)}` : "";

            lines.push(
                `    - \`${f.file}:${f.line}\`, key ${inlineCode(f.key)}${variant}, fingerprint \`${f.fingerprint.slice(0, 12)}\``,
            );
        }

        if (first.side === "target") {
            lines.push(
                "- Source:",
                "",
                indent(fence(first.source)),
                "",
                "- Target:",
                "",
                indent(fence(marked)),
                "",
            );
        } else {
            lines.push("- Source:", "", indent(fence(marked)), "");
        }
    }

    return lines;
}

function indent(text: string): string {
    return text
        .split("\n")
        .map((line) => (line ? `    ${line}` : line))
        .join("\n");
}

function renderCategories(findings: Finding[]): string[] {
    const lines: string[] = [];
    const tierOrder = (tier: Tier) => TIERS.indexOf(tier);

    const categories = [...groupBy(findings, (f) => `${f.tier}\0${f.categoryHex}`).values()].sort(
        (a, b) =>
            tierOrder(a[0]!.tier) - tierOrder(b[0]!.tier) ||
            a[0]!.categoryBits - b[0]!.categoryBits,
    );

    for (const group of categories) {
        const { tier, categoryHex } = group[0]!;

        lines.push(`## ${tier}, category \`${categoryHex}\``, "");

        const words = [...groupBy(group, (f) => f.word)].sort(
            ([a, x], [b, y]) => y.length - x.length || a.localeCompare(b),
        );

        for (const [word, wordFindings] of words) {
            lines.push(...renderWord(word, wordFindings));
        }
    }

    return lines;
}

function renderFile(
    title: string,
    intro: string,
    findings: Finding[],
    context: ReportContext,
): string {
    const lines = [
        `# ${title}`,
        "",
        intro,
        "",
        `Generated ${context.generatedAt}. Tiers: ${context.tiers.join(", ")}. Normalization: ${NORMALIZATION}.`,
        "",
        "Findings are grouped by lexicon tier and category, then by matched word. Categories are the",
        "lexicon's topic bits; their meaning varies by locale, so treat them as grouping labels.",
        "",
        TRIAGE,
        ...renderCategories(findings),
    ];

    return lines.join("\n").trimEnd() + "\n";
}

function via(locale: string, lexicon: string): string {
    return lexicon === locale ? "" : `, using the ${lexicon} lexicon`;
}

//#endregion

//#region Writing reports

/**
 * Write one Markdown file per locale, one for source strings, and an index.
 *
 * @returns The written file names, relative to `directory`.
 */
export async function writeMarkdownReports(
    directory: string,
    context: ReportContext,
): Promise<string[]> {
    await mkdir(directory, { recursive: true });

    const { result } = context;
    const targets = result.findings.filter((f) => f.side === "target");
    const sources = result.findings.filter((f) => f.side === "source");
    const files: Array<{ name: string; title: string; count: number; content: string }> = [];

    for (const [locale, findings] of [...groupBy(targets, (f) => f.locale)].sort(([a], [b]) =>
        a.localeCompare(b),
    )) {
        files.push({
            name: `${locale}.md`,
            title: `${locale} translations`,
            count: findings.length,
            content: renderFile(
                `${locale} lexicon findings`,
                `${findings.length} findings in ${locale} translations${via(locale, findings[0]!.lexicon)}.`,
                findings,
                context,
            ),
        });
    }

    if (sources.length) {
        const { locale, lexicon } = sources[0]!;

        files.push({
            name: `source-${locale}.md`,
            title: `Source strings (${locale})`,
            count: sources.length,
            content: renderFile(
                `Source string lexicon findings (${locale})`,
                `${sources.length} findings in source strings${via(locale, lexicon)}. Each distinct string is listed once; its location is the first file it appeared in.`,
                sources,
                context,
            ),
        });
    }

    const index = [
        "# Lexicon audit findings",
        "",
        `Generated ${context.generatedAt}. ${result.findings.length} findings.`,
        "",
        ...(files.length
            ? ["| File | Scope | Findings |", "| --- | --- | --- |"]
            : ["No findings."]),
        ...files.map(({ name, title, count }) => `| [${name}](${name}) | ${title} | ${count} |`),
    ];

    files.push({ name: "index.md", title: "", count: 0, content: index.join("\n") + "\n" });

    for (const { name, content } of files) {
        await writeFile(join(directory, name), content);
    }

    return files.map(({ name }) => name);
}

//#endregion
