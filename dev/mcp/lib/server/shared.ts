/**
 * @file Shared pieces of the MCP tool definitions.
 */

import * as jobs from "#dev-mcp/results/jobs";
import type { Progress } from "#dev-mcp/results/progress";
import type { Result } from "#dev-mcp/results/result";

import type { ServerContext, ToolAnnotations } from "@modelcontextprotocol/server";

export const READ_ONLY: ToolAnnotations = {
    readOnlyHint: true,
    destructiveHint: false,
    openWorldHint: false,
};

export const WRITES_TREE: ToolAnnotations = {
    readOnlyHint: false,
    destructiveHint: false,
    openWorldHint: false,
};

/** A tool result with the same data as text and as structured content. */
export function reply(data: object) {
    const structured = JSON.parse(JSON.stringify(data)) as Record<string, unknown>;

    return {
        content: [{ type: "text" as const, text: JSON.stringify(structured, null, 2) }],
        structuredContent: structured,
    };
}

/** Tool description text for a tool that runs through {@linkcode runJob}. */
export const JOB_NOTE =
    "When the client sends a progress token, the call reports each step as progress and " +
    "returns the finished result; otherwise it returns a jobId to poll with akdev_job. Either " +
    "way the run is a job, and the first progress message names it, so a call that times out " +
    "can be picked up with akdev_job.";

/** Run `fn` as a job, reporting progress when the client supports it. */
export async function runJob(
    ctx: ServerContext,
    tool: string,
    storeAs: string,
    fn: (progress: Progress) => Promise<Result>,
) {
    const token = ctx.mcpReq._meta?.progressToken;

    const progress: Progress = (done, total, message) => {
        if (token === undefined) return;

        // No total until the work knows its steps: a bar of 0 of 0 means nothing.
        const params = { progressToken: token, progress: done, total: total || undefined, message };

        // The client may have gone; the job carries on and keeps its result.
        ctx.mcpReq.notify({ method: "notifications/progress", params }).catch(() => {});
    };

    const job = jobs.start(tool, storeAs, () => fn(progress));

    if (token === undefined) {
        return reply(job);
    }

    // Before any step reports, so even a step that never finishes leaves the jobId behind.
    progress(0, 0, `job ${job.jobId} started`);

    return reply((await jobs.wait(job.jobId)) ?? job);
}
