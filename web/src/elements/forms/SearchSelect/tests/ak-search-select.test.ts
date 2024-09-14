/* eslint-env jest */
import { AKElement } from "@goauthentik/elements/Base";
import { bound } from "@goauthentik/elements/decorators/bound.js";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";
import { $, browser, expect } from "@wdio/globals";
import { slug } from "github-slugger";

import { html, render } from "lit";
import { customElement } from "lit/decorators.js";
import { property, query } from "lit/decorators.js";

import "../ak-search-select.js";
import { SearchSelect } from "../ak-search-select.js";
import { type ViewSample, sampleData } from "../stories/sampleData.js";
import { AkSearchSelectViewDriver } from "./ak-search-select-view.comp.js";

const renderElement = (fruit: ViewSample) => fruit.produce;

const renderDescription = (fruit: ViewSample) => html`${fruit.desc}`;

const renderValue = (fruit: ViewSample | undefined) => slug(fruit?.produce ?? "");

@customElement("ak-mock-search-group")
export class MockSearch extends CustomListenerElement(AKElement) {
    /**
     * The current fruit
     *
     * @attr
     */
    @property({ type: String, reflect: true })
    fruit?: string;

    @query("ak-search-select")
    search!: SearchSelect<ViewSample>;

    selectedFruit?: ViewSample;

    get value() {
        return this.selectedFruit ? renderValue(this.selectedFruit) : undefined;
    }

    @bound
    handleSearchUpdate(ev: CustomEvent) {
        ev.stopPropagation();
        this.selectedFruit = ev.detail.value;
        this.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
    }

    @bound
    selected(fruit: ViewSample) {
        return this.fruit === slug(fruit.produce);
    }

    @bound
    fetchObjects() {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const resolver = (resolve: any) => {
            this.addEventListener("resolve", () => {
                resolve(sampleData);
            });
        };
        return new Promise(resolver);
    }

    render() {
        return html`
            <ak-search-select
                .fetchObjects=${this.fetchObjects}
                .renderElement=${renderElement}
                .renderDescription=${renderDescription}
                .value=${renderValue}
                .selected=${this.selected}
                managed
                @ak-change=${this.handleSearchUpdate}
                ?blankable=${true}
            >
            </ak-search-select>
        `;
    }
}

describe("Search select: event driven startup", () => {
    let select: AkSearchSelectViewDriver;
    let wrapper: SearchSelect<ViewSample>;

    beforeEach(async () => {
        await render(html`<ak-mock-search-group></ak-mock-search-group>`, document.body);
        // @ts-ignore
        wrapper = await $(">>>ak-search-select");
    });

    it("should shift from the loading indicator to search select view on fetch event completed", async () => {
        expect(await wrapper).toBeExisting();
        expect(await $(">>>ak-search-select-loading-indicator")).toBeDisplayed();
        await browser.execute(() => {
            const mock = document.querySelector("ak-mock-search-group");
            mock?.dispatchEvent(new Event("resolve"));
        });
        expect(await $(">>>ak-search-select-loading-indicator")).not.toBeDisplayed();
        select = await AkSearchSelectViewDriver.build(
            await $(">>>ak-search-select-view").getElement(),
        );
        expect(await select).toBeExisting();
    });

    afterEach(async () => {
        await document.body.querySelector("ak-mock-search-group")?.remove();
        // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
        if (document.body["_$litPart$"]) {
            // @ts-expect-error expression of type '"_$litPart$"' is added by Lit
            delete document.body["_$litPart$"];
        }
    });
});
