import { readFile } from "node:fs/promises";

export interface JSONReport {
    stats: JSONReportStats;
    suites: JSONReportSuite[];
    errors: JSONReportError[];
}

export interface JSONReportStats {
    expected: number;
    unexpected: number;
    flaky: number;
    skipped: number;
}

export interface JSONReportError {
    message?: string;
}

interface JSONReportSuite {
    title: string;
    specs?: JSONReportSpec[];
    suites?: JSONReportSuite[];
}

interface JSONReportSpec {
    title: string;
    file: string;
    line: number;
    ok: boolean;
    tests: JSONReportTest[];
}

interface JSONReportTest {
    results: JSONReportResult[];
}

interface JSONReportResult {
    error?: JSONReportError;
    errors?: JSONReportError[];
}

export interface Failure {
    location: string;
    title: string;
    errors: string[];
}

/**
 * Reads the JSON report, returning null when the run never produced one.
 *
 * @throws {Error} If the report exists but cannot be read or parsed.
 */
export async function readReport(reportPath: string): Promise<JSONReport | null> {
    const source = await readFile(reportPath, "utf-8").catch((cause: NodeJS.ErrnoException) => {
        if (cause.code === "ENOENT") return null;

        throw new Error(`Could not read ${reportPath}`, { cause });
    });

    if (source === null) return null;

    try {
        return JSON.parse(source) as JSONReport;
    } catch (cause) {
        throw new Error(`Could not parse ${reportPath}`, { cause });
    }
}

/**
 * Walks the suite tree and flattens every failing spec, carrying down the `describe` titles.
 */
export function collectFailures(
    suites: JSONReportSuite[],
    ancestors: string[] = [],
    depth = 0,
): Failure[] {
    const failures: Failure[] = [];

    for (const suite of suites) {
        // The outermost suite is the file, whose title is already in `location`.
        const titlePath = depth === 0 ? ancestors : [...ancestors, suite.title];

        for (const spec of suite.specs ?? []) {
            if (spec.ok) continue;

            const errors = spec.tests.flatMap((test) => {
                const result = test.results.at(-1);

                return result?.errors?.length ? result.errors : result?.error ? [result.error] : [];
            });

            failures.push({
                location: `${spec.file}:${spec.line}`,
                title: [...titlePath, spec.title].join(" › "),
                errors: errors.flatMap(({ message }) => (message ? [stripANSI(message)] : [])),
            });
        }

        failures.push(...collectFailures(suite.suites ?? [], titlePath, depth + 1));
    }

    return failures;
}

export function stripANSI(input: string): string {
    return input.replace(/\u001B\[[0-9;]*m/g, "");
}
