/**
 * @file Select an installed Node.js version that satisfies `engines.node`, if available.
 */

import { existsSync, readFileSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { delimiter, join } from "node:path";

import { ROOT } from "#dev/lib/git";
import { compareVersions, satisfiesRange } from "#dev/lib/versions";

export interface NodeChoice {
    /** The active Node, without the `v`. */
    current: string;
    /** `engines.node` from the root package.json, or null when it sets none. */
    range: string | null;
    /** Whether the active Node fits the range. */
    ok: boolean;
    /** An nvm-installed Node that fits, when the active one doesn't. */
    switchTo: { version: string; bin: string } | null;
    /** What to do when no installed version fits. */
    hint: string | null;
}

export interface ChooseOptions {
    current?: string;
    range?: string | null;
    nvmDir?: string;
}

export function requiredNodeRange(): string | null {
    const pkg = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8")) as {
        engines?: { node?: string };
    };

    return pkg.engines?.node ?? null;
}

export function nvmDir(): string {
    return process.env.NVM_DIR || join(homedir(), ".nvm");
}

/**
 * Versions nvm has installed, newest first, each with its `bin` directory.
 */
export function nvmVersions(dir = nvmDir()): { version: string; bin: string }[] {
    const root = join(dir, "versions", "node");

    if (!existsSync(root)) return [];

    return readdirSync(root)
        .filter((name) => /^v\d+\.\d+\.\d+$/.test(name))
        .map((name) => ({ version: name.slice(1), bin: join(root, name, "bin") }))
        .filter(({ bin }) => existsSync(join(bin, "node")))
        .sort((a, b) => compareVersions(b.version, a.version));
}

/**
 * The newest major the range allows, for an `nvm install` suggestion.
 */
function suggestedMajor(range: string): string | null {
    const majors = range
        .split("||")
        .map((part) => /\d+/.exec(part)?.[0])
        .filter((major): major is string => Boolean(major))
        .map(Number);

    return majors.length ? String(Math.max(...majors)) : null;
}

export function chooseNode(options: ChooseOptions = {}): NodeChoice {
    const current = options.current ?? process.versions.node;
    const range = options.range === undefined ? requiredNodeRange() : options.range;

    if (!range || satisfiesRange(current, range)) {
        return { current, range, ok: true, switchTo: null, hint: null };
    }

    const dir = options.nvmDir ?? nvmDir();
    const switchTo = nvmVersions(dir).find(({ version }) => satisfiesRange(version, range));

    if (switchTo) return { current, range, ok: false, switchTo, hint: null };

    const major = suggestedMajor(range);
    const hasNvm = existsSync(join(dir, "nvm.sh"));

    const hint =
        hasNvm && major
            ? `No nvm-installed Node fits. Ask the person, then run \`. "${dir}/nvm.sh" && ` +
              `nvm install ${major}\` (downloads Node).`
            : `Install a Node.js that fits ${range}, then start the server again.`;

    return { current, range, ok: false, switchTo: null, hint };
}

/** One line on the active Node, and what setup mode does about it. */
export function describeNode(choice: NodeChoice): string {
    if (choice.ok) return `Node ${choice.current}: ok.`;

    const head = `Node ${choice.current} doesn't satisfy ${choice.range}.`;

    if (choice.switchTo) {
        return (
            `${head} akdev_install and the full server use nvm's ${choice.switchTo.version}. ` +
            `In your own shell, run \`. "${nvmDir()}/nvm.sh" && nvm use ` +
            `${choice.switchTo.version}\` before make or pnpm commands.`
        );
    }

    return `${head} ${choice.hint}`;
}

/** `env` with the chosen Node first on PATH. Global tools like pnpm then run under it too. */
export function withNode(env: NodeJS.ProcessEnv, choice: NodeChoice): NodeJS.ProcessEnv {
    if (!choice.switchTo) return env;

    return { ...env, PATH: [choice.switchTo.bin, env.PATH].filter(Boolean).join(delimiter) };
}

/** The node binary to start child servers with. */
export function nodeBinary(choice: NodeChoice): string {
    return choice.switchTo ? join(choice.switchTo.bin, "node") : process.execPath;
}
