import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { collectSearchRecords } from "./node.mjs";

/**
 * @import { SearchSite } from "./common.mjs";
 */

/**
 * A website directory with two sites, each holding the page shapes whose URLs differ from their
 * file paths.
 *
 * @param {string} root
 */
function writeSites(root) {
    /** @type {[path: string, content: string][]} */
    const files = [
        ["docs/index.mdx", "---\ntitle: Welcome\n---\n\nThe front page.\n"],
        ["docs/core/terminology.mdx", "# Terminology\n\nA flow is a sequence of stages.\n"],
        ["docs/core/settings/settings.mdx", "# Settings\n\nServed at the folder's URL.\n"],
        ["docs/core/moved.mdx", "---\nslug: /core/renamed/\n---\n\n# Moved\n\nSlugged.\n"],
        ["docs/core/draft.mdx", "---\ndraft: true\n---\n\n# Draft\n\nNot built.\n"],
        ["docs/core/hidden.mdx", "---\nunlisted: true\n---\n\n# Hidden\n\nNot indexed.\n"],
        ["docs/core/_partial.mdx", "Partial text.\n"],
        ["integrations/monitoring/grafana/index.mdx", "# Grafana\n\nDashboards.\n"],
    ];

    for (const [path, content] of files) {
        mkdirSync(join(root, path, ".."), { recursive: true });
        writeFileSync(join(root, path), content);
    }
}

/** @type {SearchSite[]} */
const SITES = [
    {
        id: "docs",
        label: "Documentation",
        directory: "docs",
        url: "https://docs.example",
        routeBasePath: "/",
        categories: [
            ["index", "Overview"],
            ["core", "Core Concepts"],
        ],
    },
    {
        id: "integrations",
        label: "Integrations",
        directory: "integrations",
        url: "https://integrations.example",
        routeBasePath: "/",
        categories: [["monitoring", "Monitoring"]],
    },
];

test("collectSearchRecords resolves URLs as Docusaurus routes the pages", () => {
    const root = mkdtempSync(join(tmpdir(), "ak-search-site-"));

    try {
        writeSites(root);

        const report = collectSearchRecords({
            websiteDir: root,
            sites: SITES,
            currentSite: "docs",
        });

        assert.deepEqual(report.currentURLs.toSorted(), [
            "/",
            "/core/renamed/",
            "/core/settings/",
            "/core/terminology/",
        ]);
        assert.deepEqual(
            report.sites.map((site) => [site.id, site.pages]),
            [
                ["docs", 4],
                ["integrations", 1],
            ],
        );
    } finally {
        rmSync(root, { recursive: true, force: true });
    }
});

test("collectSearchRecords stores the current site's URLs relative and the others' absolute", () => {
    const root = mkdtempSync(join(tmpdir(), "ak-search-site-"));

    try {
        writeSites(root);

        const { records } = collectSearchRecords({
            websiteDir: root,
            sites: SITES,
            currentSite: "docs",
        });

        const grafana = records.find((record) => record.site === "Integrations");
        const welcome = records.find((record) => record.url === "/");

        assert.equal(grafana?.url, "https://integrations.example/monitoring/grafana/");
        assert.deepEqual(grafana?.hierarchy.slice(0, 2), ["Monitoring", "Grafana"]);
        assert.deepEqual(welcome?.hierarchy.slice(0, 2), ["Overview", "Welcome"]);
        assert.equal(welcome?.content, "The front page.");

        const everyAbsolute = collectSearchRecords({ websiteDir: root, sites: SITES }).records;

        assert.ok(everyAbsolute.every((record) => record.url.startsWith("https://")));
    } finally {
        rmSync(root, { recursive: true, force: true });
    }
});
