/**
 * @file Symmetric GnuPG encryption of the lexicon database, so it can be committed and unlocked
 *   in CI with a passphrase secret.
 */

import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { openLexicon } from "#lexicon/database";
import { LexiconError } from "#lexicon/errors";

/**
 * Run `gpg` with the passphrase on stdin and a throwaway home directory, so the passphrase never
 * appears in the process list or the user's agent cache.
 */
async function gpg(args: string[], passphrase: string): Promise<void> {
    const home = await mkdtemp(join(tmpdir(), "lexicon-audit-gnupg-"));

    try {
        await new Promise<void>((resolve, reject) => {
            const child = spawn(
                "gpg",
                [
                    "--homedir",
                    home,
                    "--batch",
                    "--yes",
                    "--quiet",
                    "--no-symkey-cache",
                    "--pinentry-mode",
                    "loopback",
                    "--passphrase-fd",
                    "0",
                    ...args,
                ],
                { stdio: ["pipe", "ignore", "pipe"] },
            );
            let stderr = "";

            child.stderr.setEncoding("utf8").on("data", (chunk: string) => (stderr += chunk));
            child.on("error", (error: NodeJS.ErrnoException) =>
                reject(
                    error.code === "ENOENT"
                        ? new LexiconError("gpg is not installed or not on PATH.")
                        : error,
                ),
            );
            child.on("close", (code) =>
                code === 0
                    ? resolve()
                    : reject(new LexiconError(`gpg exited with status ${code}: ${stderr.trim()}`)),
            );
            child.stdin.end(passphrase);
        });
    } finally {
        await rm(home, { recursive: true, force: true });
    }
}

/**
 * Check that a database opens and has the current schema.
 */
function verify(databasePath: string): void {
    using _db = openLexicon(databasePath);
}

/**
 * Encrypt a lexicon database with AES-256.
 */
export async function sealLexicon(
    databasePath: string,
    sealedPath: string,
    passphrase: string,
): Promise<void> {
    verify(databasePath);

    await gpg(
        ["--symmetric", "--cipher-algo", "AES256", "--output", sealedPath, databasePath],
        passphrase,
    );
}

/**
 * Decrypt a sealed lexicon database, removing the output if it isn't a usable lexicon.
 */
export async function unsealLexicon(
    sealedPath: string,
    databasePath: string,
    passphrase: string,
): Promise<void> {
    try {
        await gpg(["--decrypt", "--output", databasePath, sealedPath], passphrase);
        verify(databasePath);
    } catch (error) {
        await rm(databasePath, { force: true });
        throw error;
    }
}
