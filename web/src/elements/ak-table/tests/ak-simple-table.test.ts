import "#elements/ak-table/ak-simple-table";

import { nutritionDbUSDA } from "../stories/sample_nutrition_db.js";

import { render } from "#elements/tests/utils";

import { $, browser } from "@wdio/globals";
import { expect } from "expect-webdriverio";
import { slug } from "github-slugger";
import { ChainablePromiseElement } from "webdriverio";

import { html } from "lit";

const columns = ["Name", "Calories", "Protein", "Fiber", "Sugar"];
const content = nutritionDbUSDA.map(({ name, calories, sugar, fiber, protein }) => ({
    key: slug(name),
    content: [name, calories, protein, fiber, sugar].map((a) => html`${a}`),
}));

describe("Simple Table", () => {
    let table: ChainablePromiseElement;

    beforeEach(async () => {
        render(html`<ak-simple-table .content=${content} .columns=${columns}> </ak-simple-table>`);
        table = $("ak-simple-table").$(">>>table");
    });

    it("it should render a simple table", async () => {
        await expect(table).resolves.toBeDisplayed();
    });

    it("the table should have as many entries as the data source", async () => {
        const tbody = table.$(">>>tbody");
        const rows = tbody.$$(">>>tr");

        await expect(rows.length).resolves.toBe(content.length);
    });

    afterEach(() =>
        browser.execute(() => {
            document.body.querySelector("ak-simple-table")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        }),
    );
});
