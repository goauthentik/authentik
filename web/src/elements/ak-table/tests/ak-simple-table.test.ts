import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser } from "@wdio/globals";
import { expect } from "expect-webdriverio";
import { slug } from "github-slugger";

import { html } from "lit";

import "../ak-simple-table.js";
import { nutritionDbUSDA } from "../stories/sample_nutrition_db.js";

const columns = ["Name", "Calories", "Protein", "Fiber", "Sugar"];
const content = nutritionDbUSDA.map(({ name, calories, sugar, fiber, protein }) => ({
    key: slug(name),
    content: [name, calories, protein, fiber, sugar].map((a) => html`${a}`),
}));

describe("Simple Table", () => {
    let table: WebdriverIO.Element;

    beforeEach(async () => {
        await render(
            html`<ak-simple-table .content=${content} .columns=${columns}> </ak-simple-table>`,
            document.body,
        );
        // @ts-ignore
        table = await $("ak-simple-table").$(">>>table");
    });

    it("it should render a simple table", async () => {
        expect(table).toBeDisplayed();
    });

    it("the table should have as many entries as the data source", async () => {
        const tbody = await table.$(">>>tbody");
        const rows = await tbody.$$(">>>tr");
        expect(rows.length).toBe(content.length);
    });

    afterEach(async () => {
        await browser.execute(() => {
            document.body.querySelector("ak-simple-table")?.remove();
            // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
            if (document.body["_$litPart$"]) {
                // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
                delete document.body["_$litPart$"];
            }
        });
    });
});
