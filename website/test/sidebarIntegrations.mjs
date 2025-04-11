/**
 * @file Test suite for the sidebar configuration of the authentik integrations.
 *
 * @todo Enforce types.
 */
import FastGlob from "fast-glob";
import assert from "node:assert";
import test from "node:test";

import sidebar from "../sidebarsIntegrations.mjs";

const getSidebarItems = () => {
    /**
     * @type {any[]}
     */
    const allItems = [];
    /**
     *
     * @param {any} category
     */
    const mapper = (category) => {
        if (!category.items) {
            return;
        }

        category.items.forEach(
            /**
             *
             * @param {any} item
             */
            (item) => {
                if (typeof item === "string") {
                    allItems.push(item);
                } else {
                    mapper(item);
                }
            },
        );
    };

    sidebar.integrations.forEach(mapper);
    return allItems.sort();
};

test("ensure all services have a sidebar entry", (_t) => {
    // All services in the sidebar
    const services = getSidebarItems()
        .filter((entry) => entry.startsWith("services/"))
        .map((entry) => entry.replace("/index", ""))
        .map((entry) => entry.replace("services/", ""));
    const servicesFiles = FastGlob.sync("integrations/**/*.+(md|mdx)")
        .filter((entry) => entry.startsWith("integrations/services/"))
        .map((entry) => entry.replace("integrations/services/", ""))
        .map((entry) => entry.replace(/\/index\.mdx?/, ""))
        .filter((entry) => entry !== "index.mdx")
        .sort();
    servicesFiles.forEach((file, idx) => {
        assert.strictEqual(file, services[idx]);
    });
});

test("ensure all sources have a sidebar entry", (_t) => {
    // All sources in the sidebar
    const sources = getSidebarItems()
        .filter((entry) => entry.startsWith("sources/"))
        .map((entry) => entry.replace("/index", ""))
        .map((entry) => entry.replace("sources/", ""));
    const sourceFiles = FastGlob.sync("integrations/**/*.+(md|mdx)")
        .filter((entry) => entry.startsWith("integrations/sources/"))
        .map((entry) => entry.replace("integrations/sources/", ""))
        .map((entry) => entry.replace(/\/index\.mdx?/, ""))
        .map((entry) => entry.replace(".md", ""))
        .sort();

    sourceFiles.forEach((file, idx) => {
        assert.strictEqual(file, sources[idx]);
    });
});
