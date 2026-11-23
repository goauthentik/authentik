#!/usr/bin/env node

/**
 * @file Post-process script for handling TypeScript files in the src directory.
 */

import { glob, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

/** The package root, i.e. the parent of this script's directory. */
const PackageRoot = resolve(import.meta.dirname, "..");

const UV_THREADPOOL_DEFAULT = 4;
const UV_THREADPOOL_MAX = 1024;

/**
 * Libuv's threadpool size: the real ceiling on concurrent filesystem calls in Node.
 */
export function fsConcurrency(): number {
    const raw = process.env.UV_THREADPOOL_SIZE;

    if (!raw) return UV_THREADPOOL_DEFAULT;

    const parsed = Number.parseInt(raw, 10);

    if (Number.isNaN(parsed) || parsed === 0) return 1;

    return parsed < 0 || parsed > UV_THREADPOOL_MAX ? UV_THREADPOOL_MAX : parsed;
}

/**
 * The blanket linter suppressions OpenAPI Generator stamps onto every emitted file.
 *
 * They're hard-coded in the upstream `typescript-fetch` mustache templates, so rather than fork the
 * template set we strip them here. Without this, `oxlint` skips the generated client entirely and
 * its unused-import fixer never runs.
 */
const SuppressionPattern = /^(?:\/\* (?:tslint:disable|eslint-disable) \*\/\r?\n)+/;

/**
 * Removes the generator's blanket linter suppressions from a file's leading comments.
 *
 * @returns The rewritten source, or `null` when the file needs no change.
 */
export function stripSuppressions(source: string): string | null {
    const next = source.replace(SuppressionPattern, "");

    return next === source ? null : next;
}

/**
 * Applies every post-processing pass to a single file.
 *
 * @returns Whether the file was rewritten.
 */
async function postProcessFile(file: string): Promise<boolean> {
    const source = await readFile(join(PackageRoot, file), "utf-8");
    const next = stripSuppressions(source);

    if (next === null) return false;

    await writeFile(join(PackageRoot, file), next, "utf-8");

    return true;
}

async function postProcess(): Promise<void> {
    // Anchored to the package root rather than the caller's working directory, so running this
    // from anywhere can't silently match nothing and report success.
    const files = glob("src/**/*.ts", { cwd: PackageRoot });
    const batchSize = fsConcurrency();

    let batch: string[] = [];
    let rewritten = 0;
    let visited = 0;

    const drain = async (): Promise<void> => {
        const results = await Promise.all(batch.map(postProcessFile));

        visited += results.length;
        rewritten += results.filter(Boolean).length;

        batch = [];
    };

    for await (const file of files) {
        batch.push(file);

        if (batch.length >= batchSize) await drain();
    }

    if (batch.length) await drain();

    console.log(`Post-processed ${visited} files (${rewritten} rewritten).`);
}

await postProcess();
