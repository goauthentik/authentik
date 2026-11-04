import { injectBrand } from "#common/brand";

import { AKElement } from "#elements/Base";

import { afterEach, describe, expect, it } from "vitest";

import { html } from "lit";

class TestChild extends AKElement {}

class TestParent extends AKElement {
    render() {
        return html`<ak-test-base-child></ak-test-base-child>`;
    }
}

customElements.define("ak-test-base-child", TestChild);
customElements.define("ak-test-base-parent", TestParent);

declare global {
    interface HTMLElementTagNameMap {
        "ak-test-base-child": TestChild;
        "ak-test-base-parent": TestParent;
    }
}

const mounted: HTMLElement[] = [];

afterEach(() => {
    for (const element of mounted.splice(0)) {
        element.remove();
    }
});

async function mountParent(): Promise<TestParent> {
    const parent = document.createElement("ak-test-base-parent");

    document.body.append(parent);
    mounted.push(parent);

    await parent.updateComplete;

    return parent;
}

function childOf(parent: TestParent): TestChild {
    const child = parent.shadowRoot?.querySelector("ak-test-base-child");

    expect(child, "the parent must render its child").toBeInstanceOf(TestChild);

    return child!;
}

/**
 * The adopted sheet holding a rule for the given selector.
 */
function sheetWithSelector(element: AKElement, selector: string): CSSStyleSheet | undefined {
    return element.shadowRoot?.adoptedStyleSheets.find((sheet) =>
        Array.from(sheet.cssRules).some(
            (rule) => rule instanceof CSSStyleRule && rule.selectorText === selector,
        ),
    );
}

describe("AKElement brand CSS", () => {
    it("adopts one shared style sheet in every element and nested shadow root", async () => {
        injectBrand({ brandingCustomCss: ".brand-shared { color: red; }" });

        const first = await mountParent();
        const second = await mountParent();

        const sheet = sheetWithSelector(first, ".brand-shared");

        expect(sheet).toBeInstanceOf(CSSStyleSheet);
        expect(sheetWithSelector(second, ".brand-shared")).toBe(sheet);
        expect(sheetWithSelector(childOf(first), ".brand-shared")).toBe(sheet);
        expect(sheetWithSelector(childOf(second), ".brand-shared")).toBe(sheet);
    });

    it("builds a new style sheet when the brand CSS changes", async () => {
        injectBrand({ brandingCustomCss: ".brand-before { color: red; }" });
        const before = await mountParent();

        injectBrand({ brandingCustomCss: ".brand-after { color: blue; }" });
        const after = await mountParent();

        expect(sheetWithSelector(after, ".brand-before")).toBeUndefined();
        expect(sheetWithSelector(after, ".brand-after")).toBeInstanceOf(CSSStyleSheet);
        expect(sheetWithSelector(before, ".brand-before")).toBeInstanceOf(CSSStyleSheet);
    });
});
