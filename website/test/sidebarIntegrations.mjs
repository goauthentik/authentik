import test from "node:test";
import assert from "node:assert";
import sidebar from "../sidebarsIntegrations.js";
import glob from "glob";

const getSidebarItems = () => {
    const allItems = [];
    const mapper = (category) => {
        if (!category.items) {
            return;
        }
        category.items.forEach((item) => {
            if (item.constructor === String) {
                allItems.push(item);
            } else {
                mapper(item);
            }
        });
    };
    sidebar.integrations.forEach(mapper);
    return allItems.sort();
};

test("ensure all services have a sidebar entry", (t) => {
    // All services in the sidebar
    const services = getSidebarItems()
        .filter((entry) => entry.startsWith("services/"))
        .map((entry) => entry.replace("/index", ""))
        .map((entry) => entry.replace("services/", ""));
    const servicesFiles = glob
        .sync("integrations/**/*.+(md|mdx)")
        .filter((entry) => entry.startsWith("integrations/services/"))
        .map((entry) => entry.replace("integrations/services/", ""))
        .map((entry) => entry.replace(/\/index\.mdx?/, ""))
        .filter((entry) => entry !== "index.mdx")
        .sort();
    servicesFiles.forEach((file, idx) => {
        assert.strictEqual(file, services[idx]);
    });
});

test("ensure all sources have a sidebar entry", (t) => {
    // All sources in the sidebar
    const sources = getSidebarItems()
        .filter((entry) => entry.startsWith("sources/"))
        .map((entry) => entry.replace("/index", ""))
        .map((entry) => entry.replace("sources/", ""));
    const sourceFiles = glob
        .sync("integrations/**/*.+(md|mdx)")
        .filter((entry) => entry.startsWith("integrations/sources/"))
        .map((entry) => entry.replace("integrations/sources/", ""))
        .map((entry) => entry.replace(/\/index\.mdx?/, ""))
        .map((entry) => entry.replace(".md", ""))
        .sort();
    sourceFiles.forEach((file, idx) => {
        assert.strictEqual(file, sources[idx]);
    });
});
