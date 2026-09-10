/**
 * @file Resolves everything the renderer and the GitHub client need, in one place.
 *
 * This is the only module that reads the environment. Every value also has a flag, so a run
 * can be reproduced locally without impersonating a runner, and the modules downstream take
 * plain arguments instead of reaching for globals they cannot be tested without.
 */

import { resolve } from "node:path";
import { parseArgs } from "node:util";

import type { CommentOptions } from "./github.ts";
import type { RunContext } from "./render.ts";

const DEFAULT_REPORT_PATH = "web/playwright-report/results.json";
const DEFAULT_API_URL = "https://api.github.com";
const DEFAULT_SERVER_URL = "https://github.com";

export interface Options {
    /**
     * The Playwright JSON report to render.
     */
    reportPath: string;
    /**
     * File the job summary is appended to. Null prints it to stdout instead, which is what a
     * local run wants.
     */
    summaryPath: string | null;
    /**
     * Where the run lives, for the links a rendered report ends with. Null outside a workflow,
     * where there is no run to link to.
     */
    run: RunContext | null;
    /**
     * The pull request comment to write. Null when there is no pull request to comment on,
     * which is the case for pushes and for fork pull requests.
     */
    comment: Omit<CommentOptions, "body"> | null;
}

/**
 * Returns the first argument that was actually given.
 *
 * GitHub Actions renders an unmatched expression as an empty string rather than leaving the
 * variable unset, so `??` would accept `PR_NUMBER=""` as an answer.
 */
function coalesce(...values: Array<string | undefined>): string | null {
    return values.find((value) => value) ?? null;
}

/**
 * Parses `process.argv`, falling back to the variables a workflow runner provides.
 *
 * @throws {TypeError} If an unknown flag is passed.
 * @throws {Error} If a pull request was named without a token to comment with.
 */
export function parseOptions(): Options {
    const { values, positionals } = parseArgs({
        allowPositionals: true,
        options: {
            "report": { type: "string" },
            "summary": { type: "string" },
            "pr": { type: "string" },
            "repository": { type: "string" },
            "server-url": { type: "string" },
            "api-url": { type: "string" },
            "run-id": { type: "string" },
            "run-attempt": { type: "string" },
            "artifact-url": { type: "string" },
        },
    });

    const {
        GITHUB_API_URL,
        GITHUB_REPOSITORY,
        GITHUB_RUN_ATTEMPT,
        GITHUB_RUN_ID,
        GITHUB_SERVER_URL,
        GITHUB_STEP_SUMMARY,
        GITHUB_TOKEN,
        PR_NUMBER,
        REPORT_ARTIFACT_URL,
    } = process.env;

    const repository = coalesce(values.repository, GITHUB_REPOSITORY);
    const runID = coalesce(values["run-id"], GITHUB_RUN_ID);
    const prNumber = coalesce(values.pr, PR_NUMBER);
    const apiURL = coalesce(values["api-url"], GITHUB_API_URL) ?? DEFAULT_API_URL;

    // The token is deliberately environment-only: anything in `argv` is readable by every
    // other process on the machine.
    const token = coalesce(GITHUB_TOKEN);

    if (prNumber && !token) {
        throw new Error("A pull request was given to comment on, but GITHUB_TOKEN is unset.");
    }

    return {
        reportPath: resolve(
            process.cwd(),
            coalesce(values.report, positionals[0]) ?? DEFAULT_REPORT_PATH,
        ),
        summaryPath: coalesce(values.summary, GITHUB_STEP_SUMMARY),
        run:
            runID && repository
                ? {
                      artifactURL: coalesce(values["artifact-url"], REPORT_ARTIFACT_URL),
                      repository,
                      runAttempt: coalesce(values["run-attempt"], GITHUB_RUN_ATTEMPT) ?? "1",
                      runID,
                      serverURL:
                          coalesce(values["server-url"], GITHUB_SERVER_URL) ?? DEFAULT_SERVER_URL,
                  }
                : null,
        comment: prNumber && repository && token ? { apiURL, prNumber, repository, token } : null,
    };
}
