/**
 * @file Counts-only scan summary for the terminal.
 */

import type { Finding } from "#audit/matching";
import type { ScanResult } from "#audit/scan";
import type { Tier } from "#constants";

export function formatCounts(findings: readonly Finding[]): string {
    const counts = new Map<Tier, number>();

    for (const { tier } of findings) {
        counts.set(tier, (counts.get(tier) ?? 0) + 1);
    }

    return [...counts].map(([tier, count]) => `${tier} ${count}`).join(", ") || "no findings";
}

/**
 * Print scan counts to stderr. Never prints matched words or translation text.
 */
export function printScanSummary(result: ScanResult): void {
    const byLocale = new Map<
        string,
        { files: number; units: number; lexicon: string; match: string }
    >();
    const uncovered = new Set<string>();

    for (const file of result.files) {
        if (!file.lexicon) {
            uncovered.add(file.locale);
            continue;
        }

        const entry = byLocale.get(file.locale) ?? {
            files: 0,
            units: 0,
            lexicon: file.lexicon.lexicon,
            match: file.lexicon.match,
        };

        entry.files++;
        entry.units += file.units;
        byLocale.set(file.locale, entry);
    }

    const units = result.files.reduce((sum, file) => sum + file.units, 0);

    console.error(`Scanned ${result.files.length} files, ${units} translated units.`);

    for (const [locale, { files, units, lexicon, match }] of [...byLocale].sort(([a], [b]) =>
        a.localeCompare(b),
    )) {
        const findings = result.findings.filter((f) => f.side === "target" && f.locale === locale);
        const via = match === "exact" ? "" : ` (lexicon ${lexicon}, ${match})`;

        console.error(
            `  ${locale.padEnd(8)} ${files} files, ${units} units${via}: ${formatCounts(findings)}`,
        );
    }

    if (uncovered.size) {
        console.error(`No lexicon for: ${[...uncovered].sort().join(", ")}`);
    }

    if (result.sourceLexicon) {
        const findings = result.findings.filter((f) => f.side === "source");
        const { lexicon, match } = result.sourceLexicon;
        const via = match === "exact" ? "" : ` (${match})`;

        console.error(
            `Source strings: ${result.sourceUnits} distinct, lexicon ${lexicon}${via}: ${formatCounts(findings)}`,
        );
    }

    const allowed = result.allowed ? ` (${result.allowed} more skipped by the allowlist)` : "";

    console.error(`${result.findings.length} findings${allowed}.`);
}
