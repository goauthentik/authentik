"use strict";
/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
Object.defineProperty(exports, "__esModule", { value: true });
const _1 = require(".");
// npx jest packages/docusaurus-plugin-openapi/src/sidebars/sidebars.test.ts --watch
function isCategory(item) {
    return item.type === "category";
}
function isLink(item) {
    return item.type === "link";
}
describe("sidebars", () => {
    const getOpts = () => ({
        contentPath: "",
        sidebarCollapsible: true,
        sidebarCollapsed: true,
    });
    const getIntro = (overrides = {}) => ({
        type: "info",
        id: "introduction",
        title: "Introduction",
        description: "Sample description.",
        slug: "/introduction",
        frontMatter: {},
        info: {
            title: "YAML Example",
            version: "1.0.0",
            description: "Sample description.",
        },
        source: "@site/examples/openapi.yaml",
        sourceDirName: ".",
        permalink: "/yaml/introduction",
        next: {
            title: "Hello World",
            permalink: "/yaml/hello-world",
        },
        ...overrides,
    });
    describe("Single Spec - YAML", () => {
        it("base case - single spec with untagged routes should render flat with a default category", async () => {
            const input = [
                getIntro(),
                {
                    type: "api",
                    id: "hello-world",
                    title: "Hello World",
                    api: {
                        tags: [],
                    },
                    source: "@site/examples/openapi.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/hello-world",
                },
            ];
            const output = await (0, _1.generateSidebar)(input, getOpts());
            // console.log(JSON.stringify(output, null, 2));
            // intro.md
            const info = output.find((x) => x.type === "link" && x.docId === "introduction");
            expect(info === null || info === void 0 ? void 0 : info.type).toBe("link");
            expect(info === null || info === void 0 ? void 0 : info.label).toBe("Introduction");
            expect(info === null || info === void 0 ? void 0 : info.href).toBe("/yaml/introduction");
            const category = output.find(isCategory);
            expect(category === null || category === void 0 ? void 0 : category.label).toBe("API");
            const api = category === null || category === void 0 ? void 0 : category.items.find(isLink);
            expect(api === null || api === void 0 ? void 0 : api.label).toBe("Hello World");
            expect(api === null || api === void 0 ? void 0 : api.docId).toBe("hello-world");
        });
        it("single spec tags case - should render root level categories per tag", async () => {
            var _a;
            const input = [
                getIntro(),
                {
                    type: "api",
                    id: "hello-world",
                    title: "Hello World",
                    api: {
                        tags: ["stuff"],
                    },
                    source: "@site/examples/openapi.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/hello-world",
                },
            ];
            const output = await (0, _1.generateSidebar)(input, getOpts());
            // console.log(JSON.stringify(output, null, 2));
            // intro.md
            const info = output.find((x) => x.type === "link" && x.docId === "introduction");
            expect(info === null || info === void 0 ? void 0 : info.type).toBe("link");
            expect(info === null || info === void 0 ? void 0 : info.label).toBe("Introduction");
            expect(info === null || info === void 0 ? void 0 : info.href).toBe("/yaml/introduction");
            // swagger rendering
            const api = output.find((x) => x.type === "category");
            expect(api === null || api === void 0 ? void 0 : api.label).toBe("stuff");
            expect(api === null || api === void 0 ? void 0 : api.items).toBeInstanceOf(Array);
            expect(api === null || api === void 0 ? void 0 : api.items).toHaveLength(1);
            const [helloWorld] = (_a = api === null || api === void 0 ? void 0 : api.items) !== null && _a !== void 0 ? _a : [];
            expect(helloWorld.type).toBe("link");
            expect(helloWorld.label).toBe("Hello World");
        });
    });
    describe("Multi Spec", () => {
        it("should leverage the info.title if provided for spec name @ root category", async () => {
            const input = [
                {
                    type: "api",
                    id: "cats",
                    title: "Cats",
                    api: {
                        info: { title: "Cats" },
                        tags: [],
                    },
                    source: "@site/examples/cats.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/cats",
                },
                {
                    type: "api",
                    id: "dogs",
                    title: "Dogs",
                    api: {
                        info: { title: "Dogs" },
                        tags: [],
                    },
                    source: "@site/examples/dogs.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/dogs",
                },
            ];
            const output = (await (0, _1.generateSidebar)(input, getOpts()));
            // console.log(JSON.stringify(output, null, 2));
            expect(output).toHaveLength(2);
            const [cats, dogs] = output;
            expect(cats.type).toBe("category");
            expect(cats.items).toHaveLength(1);
            // Check that the category has been squashed
            const [catLink] = cats.items;
            expect(catLink.type).toBe("link");
            expect(dogs.type).toBe("category");
            expect(dogs.items).toHaveLength(1);
            expect(dogs.label).toBe("Dogs");
        });
        it("empty title should render the filename.", async () => {
            const input = [
                {
                    type: "api",
                    id: "cats",
                    title: "Cats",
                    api: {
                        info: { title: "Cats" },
                        tags: [],
                    },
                    source: "@site/examples/cats.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/cats",
                },
                {
                    type: "api",
                    id: "dogs",
                    title: "List Dogs",
                    api: {
                        info: { title: "" },
                        tags: [],
                    },
                    source: "@site/examples/dogs.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/dogs",
                },
                {
                    type: "api",
                    id: "dogs-id",
                    title: "Dog By Id",
                    api: {
                        info: { title: "" },
                        tags: [],
                    },
                    source: "@site/examples/dogs.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/dogs-id",
                },
            ];
            const output = (await (0, _1.generateSidebar)(input, getOpts()));
            // console.log(JSON.stringify(output, null, 2));
            const [cats, dogsSpec] = output;
            expect(cats.items).toHaveLength(1);
            expect(dogsSpec.type).toBe("category");
            expect(dogsSpec.items).toHaveLength(2);
            expect(dogsSpec.label).toBe("dogs");
            const [dogsItem] = dogsSpec.items;
            expect(dogsItem.label).toBe("List Dogs");
        });
        it("multi spec, multi tag", async () => {
            var _a, _b, _c, _d;
            const input = [
                {
                    type: "api",
                    id: "tails",
                    title: "List Tails",
                    api: {
                        info: { title: "Cats" },
                        tags: ["Tails"],
                    },
                    source: "@site/examples/cats.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/tails",
                },
                {
                    type: "api",
                    id: "tails-by-id",
                    title: "Tails By Id",
                    api: {
                        info: { title: "Cats" },
                        tags: ["Tails"],
                    },
                    source: "@site/examples/cats.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/tails-by-id",
                },
                {
                    type: "api",
                    id: "whiskers",
                    title: "List whiskers",
                    api: {
                        info: { title: "Cats" },
                        tags: ["Whiskers"],
                    },
                    source: "@site/examples/cats.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/whiskers",
                },
                {
                    type: "api",
                    id: "dogs",
                    title: "List Dogs",
                    api: {
                        info: { title: "Dogs" },
                        tags: ["Doggos"],
                    },
                    source: "@site/examples/dogs.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/dogs",
                },
                {
                    type: "api",
                    id: "dogs-id",
                    title: "Dogs By Id",
                    api: {
                        info: { title: "Dogs" },
                        tags: ["Doggos"],
                    },
                    source: "@site/examples/dogs.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/dogs-id",
                },
                {
                    type: "api",
                    id: "toys",
                    title: "Toys",
                    api: {
                        info: { title: "Dogs" },
                        tags: ["Toys"],
                    },
                    source: "@site/examples/dogs.yaml",
                    sourceDirName: ".",
                    permalink: "/yaml/toys",
                },
            ];
            const output = (await (0, _1.generateSidebar)(input, getOpts()));
            // console.log(JSON.stringify(output, null, 2));
            const [cats, dogs] = output;
            expect(cats.type).toBe("category");
            expect(cats.items).toHaveLength(2);
            const [tails, whiskers] = (cats.items || []).filter(isCategory);
            expect(tails.type).toBe("category");
            expect(whiskers.type).toBe("category");
            expect(tails.items).toHaveLength(2);
            expect(whiskers.items).toHaveLength(1);
            expect((_a = tails.items) === null || _a === void 0 ? void 0 : _a[0].type).toBe("link");
            expect((_b = whiskers.items) === null || _b === void 0 ? void 0 : _b[0].type).toBe("link");
            expect((_c = tails.items) === null || _c === void 0 ? void 0 : _c[0].label).toBe("List Tails");
            expect((_d = whiskers.items) === null || _d === void 0 ? void 0 : _d[0].label).toBe("List whiskers");
            expect(dogs.type).toBe("category");
            expect(dogs.items).toHaveLength(2);
            expect(dogs.label).toBe("Dogs");
            const [doggos, toys] = (dogs.items || []);
            expect(doggos.type).toBe("category");
            expect(toys.type).toBe("category");
            expect(doggos.items).toHaveLength(2);
            expect(toys.items).toHaveLength(1);
        });
        it("child folders", async () => {
            const input = [
                {
                    type: "api",
                    id: "cats",
                    title: "Cats",
                    api: {
                        info: { title: "Cat Store" },
                        tags: ["Cats"],
                    },
                    source: "@site/examples/animals/pets/cats.yaml",
                    sourceDirName: "animals/pets",
                    permalink: "/yaml/cats",
                },
                {
                    type: "api",
                    id: "burgers",
                    title: "Burgers",
                    api: {
                        info: { title: "Burger Store" },
                        tags: ["Burgers"],
                    },
                    source: "@site/examples/food/fast/burgers.yaml",
                    sourceDirName: "food/fast",
                    permalink: "/yaml/burgers",
                },
            ];
            const output = await (0, _1.generateSidebar)(input, getOpts());
            expect(output).toBeTruthy();
            // console.log(JSON.stringify(output, null, 2));
            // console.log(output);
            const [animals, foods] = output;
            expect(animals.type).toBe("category");
            expect(foods.type).toBe("category");
            /*
              animals
                pets <-- should not exist
                  Cat Store
                    cats
              Foods
                Buger Store <-- should not exist
                  Burger Example  <-- should be called "Burger Store"
                    burgers
            */
            output.filter(isCategory).forEach((category) => {
                // console.log(category.label);
                expect(category.items[0].type).toBe("category");
                category.items.filter(isCategory).forEach((subCategory) => {
                    expect(subCategory.items[0].type).toBe("category");
                    subCategory.items.filter(isCategory).forEach((groupCategory) => {
                        expect(groupCategory.items[0].type).toBe("link");
                    });
                });
            });
        });
        it("child folders with no paths", async () => {
            const input = [
                getIntro({
                    source: "@site/examples/foods/foods.yaml",
                    sourceDirName: "foods",
                }),
                getIntro({
                    source: "@site/examples/animals/animals.yaml",
                    sourceDirName: "animals",
                }),
            ];
            const output = await (0, _1.generateSidebar)(input, getOpts());
            expect(output).toBeTruthy();
            expect(output[0].type).toBe("category");
        });
    });
});
