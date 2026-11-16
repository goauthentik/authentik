import { createReadStream } from "node:fs";
import { glob, lstat, realpath } from "node:fs/promises";
import { isAbsolute, join, relative, resolve } from "node:path";
import { type Interface, createInterface } from "node:readline";

/**
 * Find files under a root, sorted, skipping symlinks that resolve outside of it.
 *
 * @returns Absolute paths under `root` as given, not with symlinks resolved, so that paths
 *   reported relative to the working directory stay short.
 */
export async function findFiles(root: string, patterns: string[]): Promise<string[]> {
    const absoluteRoot = resolve(root);
    const realRoot = await realpath(absoluteRoot);
    const matches = new Set<string>();

    for await (const entry of glob(patterns, { cwd: absoluteRoot })) {
        const absolutePath = join(absoluteRoot, entry);
        const stats = await lstat(absolutePath);

        if (stats.isSymbolicLink()) {
            const fromRoot = relative(realRoot, await realpath(absolutePath));

            if (fromRoot.startsWith("..") || isAbsolute(fromRoot)) {
                continue;
            }
        } else if (!stats.isFile()) {
            continue;
        }

        matches.add(absolutePath);
    }

    return [...matches].sort();
}

/**
 * Read a UTF-8 file line by line. Dispose to close the reader and its stream.
 */
export function openLines(filePath: string): Disposable & { lines: Interface } {
    const stack = new DisposableStack();
    // Destroy rather than async-dispose the stream: async disposal rejects again after a read
    // error, hiding it behind a SuppressedError.
    const stream = stack.adopt(createReadStream(filePath, { encoding: "utf8" }), (s) =>
        s.destroy(),
    );
    const lines = stack.use(createInterface({ input: stream, crlfDelay: Infinity }));

    return { lines, [Symbol.dispose]: () => stack.dispose() };
}
