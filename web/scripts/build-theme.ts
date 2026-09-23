/**
 * @file Build `@goauthentik/theme` and copy its stylesheet into the web styles.
 *   The copy is committed so building web doesn't need the theme's dependencies.
 *   Pass `--check` to fail when the committed copy is out of date.
 * @runtime node
 */

import { execFileSync } from "node:child_process";
import * as fs from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";

import { ConsoleLogger } from "#logger/node";
import { PackageRoot } from "#paths/node";

import { MonoRepoRoot } from "@goauthentik/core/paths/node";

const logger = ConsoleLogger.child({ name: "Theme" });

const ThemeRoot = resolve(MonoRepoRoot, "packages", "theme");
const Source = resolve(ThemeRoot, "dist", "index.css");

const Destination = resolve(
    PackageRoot,
    "src",
    "styles",
    "global",
    "theme",
    "generated",
    "theme.css",
);

const DestinationLabel = relative(PackageRoot, Destination);

execFileSync("pnpm", ["run", "build"], { cwd: ThemeRoot, stdio: "inherit" });

const generated = await fs.readFile(Source, "utf8");

if (process.argv.includes("--check")) {
    const committed = await fs.readFile(Destination, "utf8").catch(() => null);

    if (committed !== generated) {
        logger.error(`${DestinationLabel} is out of date. Run \`pnpm run build:theme\`.`);
        process.exit(1);
    }

    logger.info(`${DestinationLabel} is up to date`);
} else {
    await fs.mkdir(dirname(Destination), { recursive: true });
    await fs.writeFile(Destination, generated);

    logger.info(`Wrote ${DestinationLabel}`);
}
