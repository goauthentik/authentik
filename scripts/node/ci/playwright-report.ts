#!/usr/bin/env node
/**
 * @file Renders a Playwright run's JSON report into GitHub's reviewer-facing surfaces.
 *
 * Usage:
 *   playwright-report [path/to/results.json]
 *
 * Every input has a flag, and each one falls back to the variable a workflow runner sets:
 *
 *   --report         The JSON report to render            (positional)
 *   --summary        File the job summary is appended to  (GITHUB_STEP_SUMMARY)
 *   --pr             Pull request to comment on           (PR_NUMBER)
 *   --repository     owner/name                           (GITHUB_REPOSITORY)
 *   --run-id         Workflow run the report came from    (GITHUB_RUN_ID)
 *   --run-attempt    Attempt within that run              (GITHUB_RUN_ATTEMPT)
 *   --artifact-url   Download URL of the HTML report      (REPORT_ARTIFACT_URL)
 *   --server-url     GitHub's web origin                  (GITHUB_SERVER_URL)
 *   --api-url        GitHub's API origin                  (GITHUB_API_URL)
 *
 * `GITHUB_TOKEN` deliberately has no flag: anything in `argv` is readable by every other
 * process on the machine. Without a pull request to comment on, no token is needed.
 */

import { appendFile } from "node:fs/promises";

import { reportAndExit } from "../utils/commands.ts";
import { upsertComment } from "./playwright-report/github.ts";
import { parseOptions } from "./playwright-report/options.ts";
import { formatComment, formatSummary } from "./playwright-report/render.ts";
import { readReport } from "./playwright-report/report.ts";

import { ConsoleLogger } from "#logger";

const logger = ConsoleLogger.prefix("playwright-report");

async function main(): Promise<void> {
    const { comment, reportPath, run, summaryPath } = parseOptions();
    const report = await readReport(reportPath);

    if (!report) logger.warn(`No report at ${reportPath}`);

    const summary = formatSummary(report, run);

    if (summaryPath) {
        await appendFile(summaryPath, `${summary}\n`, "utf-8");
        logger.info("Wrote the job summary.");
    } else {
        // Outside a runner there is nowhere to append to, so the summary is the output.
        process.stdout.write(`${summary}\n`);
    }

    if (!comment) {
        logger.info("No pull request to comment on; skipping the comment.");
        return;
    }

    await upsertComment({ ...comment, body: formatComment(report, run) });
}

main()
    .then(() => process.exit(0))
    .catch((error) => reportAndExit(error, logger));
