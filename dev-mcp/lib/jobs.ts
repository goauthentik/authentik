/**
 * @file Long-running tool calls run in the background; the agent polls `akdev_job` for the
 *   result. Jobs live in memory and are dropped when the server exits.
 */

import { randomUUID } from "node:crypto";

import type { Result, ResultData } from "#dev-mcp/result";
import { save } from "#dev-mcp/store";

export interface JobState {
    jobId: string;
    tool: string;
    state: "running" | "done" | "failed";
    seconds: number;
    result: ResultData | null;
    error: string | null;
}

interface Job {
    id: string;
    tool: string;
    started: number;
    finished: number | null;
    result: Result | null;
    error: string | null;
}

const registry = new Map<string, Job>();

function view(job: Job): JobState {
    return {
        jobId: job.id,
        tool: job.tool,
        state: job.error ? "failed" : job.result ? "done" : "running",
        seconds: Math.round(((job.finished ?? Date.now()) - job.started) / 100) / 10,
        result: job.result ? job.result.toJSON() : null,
        error: job.error,
    };
}

/** Start `fn` in the background, saving its result to the store under `storeAs`. */
export function start(tool: string, storeAs: string, fn: () => Promise<Result>): JobState {
    const job: Job = {
        id: randomUUID().slice(0, 8),
        tool,
        started: Date.now(),
        finished: null,
        result: null,
        error: null,
    };
    registry.set(job.id, job);
    fn().then(
        (result) => {
            save(storeAs, result);
            job.result = result;
            job.finished = Date.now();
        },
        (error: unknown) => {
            job.error = error instanceof Error ? (error.stack ?? error.message) : String(error);
            job.finished = Date.now();
        },
    );
    return view(job);
}

export function get(id: string): JobState | null {
    const job = registry.get(id);
    return job ? view(job) : null;
}
