/**
 * @file Version comparison for `engines` and `packageManager` checks. No imports, so code that
 *   runs before `pnpm install`, such as dev-mcp's setup mode, can use it.
 */

/**
 * Compares two semantic version strings (e.g., "14.17.0").
 *
 * A missing part counts as zero, so "24" and "24.0.0" compare equal.
 *
 * @param a The first version string.
 * @param b The second version string.
 */
export function compareVersions(a: string, b: string): number {
    const pa = a.split(".").map(Number);
    const pb = b.split(".").map(Number);

    for (let i = 0; i < 3; i++) {
        const left = pa[i] ?? 0;
        const right = pb[i] ?? 0;

        if (left > right) return 1;

        if (left < right) return -1;
    }

    return 0;
}

/**
 * Checks a version against a range of `||`-separated comparators.
 *
 * Supports `>=1.2.3`, `^1.2.3`, and exact versions; missing parts count as zero.
 */
export function satisfiesRange(version: string, range: string): boolean {
    return range.split("||").some((part) => {
        const comparator = part.trim();

        if (comparator.startsWith(">=")) {
            return compareVersions(version, comparator.slice(2)) >= 0;
        }

        if (comparator.startsWith("^")) {
            const required = comparator.slice(1);

            return (
                version.split(".")[0] === required.split(".")[0] &&
                compareVersions(version, required) >= 0
            );
        }

        return compareVersions(version, comparator) === 0;
    });
}
