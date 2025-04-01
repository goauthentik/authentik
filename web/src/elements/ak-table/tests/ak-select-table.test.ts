import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser } from "@wdio/globals";
import { expect } from "expect-webdriverio";
import { slug } from "github-slugger";
import type { ChainablePromiseElement } from "webdriverio";

import { html } from "lit";

import "../ak-select-table.js";
import { nutritionDbUSDA as unsortedNutritionDbUSDA } from "../stories/sample_nutrition_db.js";

type SortableRecord = Record<string, string | number>;

const dbSort = (a: SortableRecord, b: SortableRecord) =>
    a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
const alphaSort = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);
const nutritionDbUSDA = unsortedNutritionDbUSDA.toSorted(dbSort);

const columns = ["Name", "Calories", "Protein", "Fiber", "Sugar"];
const content = nutritionDbUSDA.map(({ name, calories, sugar, fiber, protein }) => ({
    key: slug(name),
    content: [name, calories, protein, fiber, sugar].map((a) => html`${a}`),
}));

const item3 = nutritionDbUSDA[2];

describe("Select Table", () => {
    let selectTable: ChainablePromiseElement;
    let table: ChainablePromiseElement;

    beforeEach(async () => {
        render(
            html`<ak-select-table .content=${content} .columns=${columns}> </ak-select-table>`,
            document,
        );

        selectTable = $("ak-select-table");
        table = selectTable.$(">>>table");
    });

    it("it should render a select table", async () => {
        expect(table).toBeDisplayed();
    });

    it("the table should have as many entries as the data source", async () => {
        const rows = table.$(">>>tbody").$$(">>>tr");
        expect(rows.length).toBe(content.length);
    });

    it(`the third item ought to have the name ${item3.name}`, async () => {
        const rows = table.$(">>>tbody").$$(">>>tr");
        const cells = rows[2].$$(">>>td");
        const cell1Text = await cells[1].getText();
        expect(cell1Text).toEqual(item3.name);
    });

    it("Selecting one item ought to result in the value of the table being set", async () => {
        const rows = table.$(">>>tbody").$$(">>>tr");
        const control = rows[2].$$(">>>td")[0].$(">>>input");
        await control.click();
        expect(await selectTable.getValue()).toEqual(slug(item3.name));
    });

    afterEach(() => {
        return browser.execute(() => {
            document.body.querySelector("ak-select-table")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        });
    });
});

describe("Multiselect Table", () => {
    let selectTable: ChainablePromiseElement;
    let table: ChainablePromiseElement;

    beforeEach(async () => {
        render(
            html`<ak-select-table multiple .content=${content} .columns=${columns}>
            </ak-select-table>`,
            document,
        );
        selectTable = $("ak-select-table");
        table = selectTable.$(">>>table");
    });

    it("it should render the select-all control", async () => {
        const thead = table.$(">>>thead");
        const selall = thead.$$(">>>tr")[0].$$(">>>td")[0];

        if (selall === undefined) {
            throw new Error("Could not find table header");
        }
        const input = selall.$(">>>input");
        expect(await input.getProperty("name")).toEqual("select-all-input");
    });

    it("it should set the value when one input is clicked", async () => {
        const input = table.$(">>>tbody").$$(">>>tr")[2].$$(">>>td")[0].$(">>>input");
        await input.click();
        expect(await selectTable.getValue()).toEqual(slug(nutritionDbUSDA[2].name));
    });

    it("it should select all when that control is clicked", async () => {
        const selall = table.$(">>>thead").$$(">>>tr")[0].$$(">>>td")[0];
        if (selall === undefined) {
            throw new Error("Could not find table header");
        }
        const input = selall.$(">>>input");
        await input.click();
        const value = await selectTable.getValue();
        const values = value.split(";").toSorted(alphaSort).join(";");
        const expected = nutritionDbUSDA.map((a) => slug(a.name)).join(";");
        expect(values).toEqual(expected);
    });

    it("it should clear all when that control is clicked twice", async () => {
        const selall = table.$(">>>thead").$$(">>>tr")[0].$$(">>>td")[0];
        if (selall === undefined) {
            throw new Error("Could not find table header");
        }
        const input = selall.$(">>>input");
        await input.click();
        const value = await selectTable.getValue();
        const values = value.split(";").toSorted(alphaSort).join(";");
        const expected = nutritionDbUSDA.map((a) => slug(a.name)).join(";");
        expect(values).toEqual(expected);
        await input.click();
        const newvalue = await selectTable.getValue();
        expect(newvalue).toEqual("");
    });

    afterEach(() => {
        return browser.execute(() => {
            document.body.querySelector("ak-select-table")?.remove();

            if ("_$litPart$" in document.body) {
                delete document.body._$litPart$;
            }
        });
    });
});
