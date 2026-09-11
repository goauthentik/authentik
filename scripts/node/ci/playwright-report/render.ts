import {
    collectFailures,
    type Failure,
    type JSONReport,
    type JSONReportError,
    stripANSI,
} from "./report.ts";

/**
 * The workflow run a report was produced by, which is what its links point at.
 */
export interface RunContext {
    serverURL: string;
    repository: string;
    runID: string;
    runAttempt: string;
    /**
     * Download URL of the uploaded HTML report. Null when the run produced none.
     */
    artifactURL: string | null;
}

/**
 * Identifies the comment this script owns, so repeated runs update one comment instead of
 * stacking a new one onto the pull request for every push.
 */
export const COMMENT_MARKER = "<!-- playwright-result -->";

const COMMENT_FAILURE_LIMIT = 10;
const ERROR_MESSAGE_LIMIT = 4_000;
const MISSING_REPORT_NOTE =
    "The job did not produce a Playwright JSON report. The suite likely crashed before the reporter wrote its output — see the workflow run for setup-step failures.";

function formatStatus(report: JSONReport | null): string {
    if (!report) return "⚠️ No results produced";
    if (report.errors.length || report.stats.unexpected > 0) return "❌ Failed";
    if (report.stats.flaky > 0) return "⚠️ Passed with flakes";

    return "✅ Passed";
}

function formatCounts({ expected, unexpected, flaky, skipped }: JSONReport["stats"]): string {
    return [
        "| Result | Count |",
        "|---|---|",
        `| ✅ Passed | ${expected} |`,
        `| ❌ Failed | ${unexpected} |`,
        `| ⚠️ Flaky | ${flaky} |`,
        `| ⏭️ Skipped | ${skipped} |`,
    ].join("\n");
}

function formatLinks(run: RunContext | null, { verbose }: { verbose: boolean }): string | null {
    // Run outside a workflow there is nothing to link to, and the report is already on disk.
    if (!run) return null;

    const { artifactURL, repository, runAttempt, runID, serverURL } = run;

    const runURL = [serverURL, repository, "actions/runs", runID, "attempts", runAttempt].join("/");

    if (!artifactURL) return `[Workflow run](${runURL}) — no HTML report was produced.`;

    const showReport = [
        "```shell",
        `gh run download ${runID} -n playwright-report -D playwright-report`,
        "npx playwright show-report playwright-report",
        "```",
    ].join("\n");

    if (!verbose) {
        return `[Download the HTML report](${artifactURL}) · [Workflow run](${runURL})\n\n${showReport}`;
    }

    return [
        `[Download the HTML report](${artifactURL}) — \`index.html\` opens straight from disk.`,
        "For trace replay, serve it:",
        "",
        showReport,
        "",
        "Individual traces from the `playwright-traces` artifact can also be dropped onto",
        "<https://trace.playwright.dev> — it runs client-side, nothing is uploaded.",
    ].join("\n");
}

function formatErrors(errors: string[]): string {
    if (!errors.length) return "No error message was recorded for this failure.";

    const joined = errors.join("\n\n");

    if (joined.length <= ERROR_MESSAGE_LIMIT) return joined;

    return `${joined.slice(0, ERROR_MESSAGE_LIMIT)}\n\n… truncated. The full error is in the HTML report.`;
}

function escapeHTML(input: string): string {
    return input.replace(
        /[&<>"']/g,
        (character) =>
            ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;",
            })[character] ?? character,
    );
}

function displayText(input: string): string {
    return escapeHTML(input.replace(/[\r\n]+/g, "↵"));
}

function formatErrorBlock(errors: string[]): string {
    return `<pre>${escapeHTML(formatErrors(errors))}</pre>`;
}

function formatReportErrors(errors: JSONReportError[]): string[] {
    return errors.flatMap(({ message }) => (message ? [stripANSI(message)] : []));
}

function formatFailure(failure: Failure): string {
    return [
        `<details><summary><code>${displayText(failure.location)}</code> › ${displayText(failure.title)}</summary>`,
        "",
        formatErrorBlock(failure.errors),
        "",
        "</details>",
    ].join("\n");
}

function formatFailureList(failures: Failure[]): string {
    const listed = failures
        .slice(0, COMMENT_FAILURE_LIMIT)
        .map(
            (failure) =>
                `- <code>${displayText(failure.location)}</code> › ${displayText(failure.title)}`,
        );

    if (failures.length > listed.length) {
        listed.push("", `_…and ${failures.length - listed.length} more._`);
    }

    return listed.join("\n");
}

function join(sections: Array<string | null>): string {
    return sections.filter((section) => section !== null).join("\n\n");
}

function formatReport(
    report: JSONReport | null,
    run: RunContext | null,
    { comment, verbose }: { comment: boolean; verbose: boolean },
): string {
    const sections: Array<string | null> = [
        ...(comment ? [COMMENT_MARKER] : []),
        `## Playwright e2e — ${formatStatus(report)}`,
    ];

    if (!report) {
        sections.push(MISSING_REPORT_NOTE, formatLinks(run, { verbose }));
        return join(sections);
    }

    sections.push(formatCounts(report.stats));

    const runnerErrors = formatReportErrors(report.errors);

    if (runnerErrors.length) sections.push("### Runner errors", formatErrorBlock(runnerErrors));

    const failures = collectFailures(report.suites);

    if (failures.length) {
        sections.push(
            "### Failures",
            comment ? formatFailureList(failures) : failures.map(formatFailure).join("\n\n"),
        );
    }

    sections.push(formatLinks(run, { verbose }));
    return join(sections);
}

export function formatSummary(report: JSONReport | null, run: RunContext | null): string {
    return formatReport(report, run, { comment: false, verbose: true });
}

export function formatComment(report: JSONReport | null, run: RunContext | null): string {
    return formatReport(report, run, { comment: true, verbose: false });
}
