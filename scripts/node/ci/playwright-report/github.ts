import { COMMENT_MARKER } from "./render.ts";

import { ConsoleLogger } from "#logger";

const logger = ConsoleLogger.prefix("playwright-report");

interface IssueComment {
    id: number;
    body?: string;
}

/**
 * What it takes to write the run's comment as the workflow's token.
 */
export interface CommentOptions {
    body: string;
    /**
     * Base URL of the GitHub API, which differs on GitHub Enterprise Server.
     */
    apiURL: string;
    prNumber: string;
    repository: string;
    token: string;
}

type RequestOptions = Pick<CommentOptions, "apiURL" | "token">;

async function requestGitHub<T>(
    { apiURL, token }: RequestOptions,
    path: string,
    init?: RequestInit,
): Promise<T> {
    const response = await fetch(new URL(path, `${apiURL}/`), {
        ...init,
        headers: {
            "accept": "application/vnd.github+json",
            "authorization": `Bearer ${token}`,
            "content-type": "application/json",
            "x-github-api-version": "2022-11-28",
            ...init?.headers,
        },
    });

    if (!response.ok) {
        throw new Error(
            `GitHub API ${init?.method ?? "GET"} ${path} failed: ${response.status} ${response.statusText}`,
            { cause: new Error(await response.text()) },
        );
    }

    return response.json() as Promise<T>;
}

/**
 * Finds this script's existing comment on the pull request, if it has already commented.
 */
async function findMarkerComment(
    request: RequestOptions,
    repository: string,
    prNumber: string,
): Promise<number | null> {
    const perPage = 100;

    for (let page = 1; ; page++) {
        const comments = await requestGitHub<IssueComment[]>(
            request,
            `repos/${repository}/issues/${prNumber}/comments?per_page=${perPage}&page=${page}`,
        );
        const marked = comments.find((comment) => comment.body?.startsWith(COMMENT_MARKER));

        if (marked) return marked.id;
        if (comments.length < perPage) return null;
    }
}

/**
 * Updates this script's comment on the pull request, creating it on the first run.
 */
export async function upsertComment({
    apiURL,
    body,
    prNumber,
    repository,
    token,
}: CommentOptions): Promise<void> {
    const request: RequestOptions = { apiURL, token };
    const existing = await findMarkerComment(request, repository, prNumber);
    const path = existing
        ? `repos/${repository}/issues/comments/${existing}`
        : `repos/${repository}/issues/${prNumber}/comments`;

    await requestGitHub(request, path, {
        method: existing ? "PATCH" : "POST",
        body: JSON.stringify({ body }),
    });

    logger.info(existing ? `Updated comment ${existing}` : "Created the result comment");
}
