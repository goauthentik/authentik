/**
 * @file Capture helpers for the visual specs.
 */

import { existsSync } from "node:fs";

import { type Page, type TestInfo } from "@playwright/test";

export const ColorSchemes = ["light", "dark"] as const;

const FixedTime = new Date("2026-01-15T12:00:00Z");

/**
 * Fix the clock and `Math.random`, and block requests to other origins.
 */
export async function pinNondeterminism(page: Page, origin: string): Promise<void> {
    await page.route(
        (url) => url.origin !== origin,
        (route) => route.abort("blockedbyclient"),
    );

    await page.clock.setFixedTime(FixedTime);

    await page.addInitScript(() => {
        let seed = 0x2f6b;

        Math.random = () => {
            seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;

            return seed / 2 ** 32;
        };
    });
}

/**
 * Skip screenshots that have no baseline yet.
 */
export function skipWithoutBaseline(testInfo: TestInfo, name: string): void {
    if (testInfo.config.updateSnapshots !== "none") return;

    if (existsSync(testInfo.snapshotPath(name, { kind: "screenshot" }))) return;

    testInfo.annotations.push({ type: "new", description: `No baseline for ${name}` });
    testInfo.skip(true, "New since the baseline");
}
