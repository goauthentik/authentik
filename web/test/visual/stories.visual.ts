import { readFileSync } from "node:fs";
import { join } from "node:path";

import { ColorSchemes, pinNondeterminism, skipWithoutBaseline } from "./capture.ts";
import { VisualEnvironment } from "./environment.ts";

import { expect, test } from "#e2e";

interface StoryIndexEntry {
    type: "story" | "docs";
    id: string;
    title: string;
    name: string;
    tags?: string[];
}

interface StoryIndex {
    entries: Record<string, StoryIndexEntry>;
}

function readStories(): StoryIndexEntry[] {
    const indexPath = join(VisualEnvironment.storybookDirectory, "index.json");

    let index: StoryIndex;

    try {
        index = JSON.parse(readFileSync(indexPath, "utf8"));
    } catch (cause) {
        throw new Error(
            `No Storybook index at ${indexPath}. Run \`pnpm run storybook:build\` first.`,
            { cause },
        );
    }

    return Object.values(index.entries).filter(
        (entry) => entry.type === "story" && entry.tags?.includes("test"),
    );
}

const stories = readStories();

for (const scheme of ColorSchemes) {
    test.describe(scheme, () => {
        test.use({ colorScheme: scheme });

        for (const story of stories) {
            test(`${story.title} › ${story.name}`, async ({
                page,
                navigator,
                baseURL,
            }, testInfo) => {
                const name = `${story.id}--${scheme}.png`;

                await pinNondeterminism(page, new URL(baseURL!).origin);
                await page.goto(`/iframe.html?id=${encodeURIComponent(story.id)}&viewMode=story`);

                const body = page.locator("body");

                await expect(body).toHaveClass(/sb-show-(main|errordisplay|nopreview)/);

                await expect(body, "Story renders without an error").not.toHaveClass(
                    /sb-show-errordisplay/,
                );

                await expect(
                    page.locator("html"),
                    `Document uses the ${scheme} theme`,
                ).toHaveAttribute("data-theme", scheme);

                await navigator.waitForRender();

                skipWithoutBaseline(testInfo, name);

                await expect(page).toHaveScreenshot(name, { fullPage: true });
            });
        }
    });
}
