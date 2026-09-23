import { arch, platform } from "node:os";
import { resolve } from "node:path";

import { PackageRoot } from "#paths/node";

export type VisualSuite = "storybook" | "pages";

export const VisualSuites = ["storybook", "pages"] as const satisfies VisualSuite[];

export const VisualStoreRoot = resolve(PackageRoot, ".visual");

export const PlatformKey = `${platform()}-${arch()}`;

export function commitDirectory(commit: string): string {
    return resolve(VisualStoreRoot, commit, PlatformKey);
}

export function suiteDirectory(commit: string, suite: VisualSuite): string {
    return resolve(commitDirectory(commit), suite);
}

export function reportDirectory(suite: string): string {
    return resolve(VisualStoreRoot, "report", suite);
}

export function outputDirectory(suite: string): string {
    return resolve(PackageRoot, "test-results", "visual", suite);
}

export const ViewportSize = {
    Desktop: { width: 1280, height: 800 },
} as const;

// Admin screens show subpixel layout drift between loads.
export const MaxDiffPixelRatio = {
    Storybook: 0,
    Pages: 0.01,
} as const;

export const VisualEnvironment = {
    suite: process.env.AK_VISUAL_SUITE || "local",
    baselineDirectory: process.env.AK_VISUAL_BASELINE_DIR || commitDirectory("local"),
    storybookDirectory:
        process.env.AK_VISUAL_STORYBOOK_DIR || resolve(PackageRoot, "storybook-static"),
    storybookPort: Number(process.env.AK_VISUAL_STORYBOOK_PORT || 6007),
    pageURL: process.env.AK_TEST_RUNNER_PAGE_URL || "http://localhost:9000",
} as const;
