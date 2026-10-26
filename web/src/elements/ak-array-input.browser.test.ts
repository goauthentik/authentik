import "#elements/ak-array-input";
import { ArrayInput } from "#elements/ak-array-input";
import { AKControlElement } from "#elements/ControlElement";

import { afterEach, describe, expect, it } from "vitest";

import { html, render } from "lit";

interface Link {
    name: string;
    href: string;
}

class TestRow extends AKControlElement<Link> {
    static properties = {
        link: { attribute: false },
        name: { type: String },
    };

    declare link: Link;
    declare name: string | null;

    constructor() {
        super();
        this.link = { name: "", href: "" };
        this.name = null;
    }

    public toJSON(): Link {
        const [name, href] = this.renderRoot.querySelectorAll("input");

        return { name: name.value, href: href.value };
    }

    render() {
        const onChange = () => {
            this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
        };

        return html`<input name="name" .value=${this.link.name} @change=${onChange} />
            <input name="href" .value=${this.link.href} @change=${onChange} />`;
    }
}

customElements.define("ak-test-array-input-row", TestRow);

declare global {
    interface HTMLElementTagNameMap {
        "ak-test-array-input-row": TestRow;
    }
}

const mounted = new Set<HTMLElement>();

/**
 * Render the array input from a host template, the way a form does.
 */
async function mount(items: Link[]) {
    const container = document.body.appendChild(document.createElement("div"));
    mounted.add(container);

    const renderHost = async (nextItems: Link[]) => {
        render(
            html`<ak-array-input
                .items=${nextItems}
                .newItem=${() => ({ name: "", href: "" })}
                .row=${(link: Link) =>
                    html`<ak-test-array-input-row
                        name="link"
                        .link=${link}
                    ></ak-test-array-input-row>`}
            ></ak-array-input>`,
            container,
        );

        const element = container.querySelector<ArrayInput<Link>>("ak-array-input")!;
        await element.updateComplete;

        return element;
    };

    return { element: await renderHost(items), renderHost };
}

function rows(element: ArrayInput<Link>) {
    return Array.from(element.renderRoot.querySelectorAll<TestRow>("ak-test-array-input-row"));
}

async function edit(element: ArrayInput<Link>, row: TestRow, field: keyof Link, value: string) {
    await row.updateComplete;

    const input = row.renderRoot.querySelector<HTMLInputElement>(`input[name="${field}"]`)!;
    input.value = value;
    input.dispatchEvent(new Event("change", { bubbles: true }));

    await element.updateComplete;
}

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-array-input", () => {
    it("keeps the user's edits when the host re-renders with the same items", async () => {
        const items = [{ name: "Docs", href: "https://example.com" }];
        const { element, renderHost } = await mount(items);

        await edit(element, rows(element)[0], "href", "https://goauthentik.io");
        await renderHost(items);
        await renderHost([...items]);

        expect(element.toJSON()).toStrictEqual([{ name: "Docs", href: "https://goauthentik.io" }]);
    });

    it("replaces the user's edits when the host passes different items", async () => {
        const { element, renderHost } = await mount([
            { name: "Docs", href: "https://example.com" },
        ]);

        await edit(element, rows(element)[0], "href", "https://goauthentik.io");
        await renderHost([{ name: "Support", href: "mailto:support@example.com" }]);

        expect(element.toJSON()).toStrictEqual([
            { name: "Support", href: "mailto:support@example.com" },
        ]);
    });

    it("keeps a row's element in place while it is edited", async () => {
        const { element } = await mount([{ name: "Docs", href: "https://example.com" }]);
        const [row] = rows(element);

        await edit(element, row, "name", "Documentation");

        expect(rows(element)).toHaveLength(1);
        expect(rows(element)[0]).toBe(row);
    });

    it("adds an empty row after the existing ones", async () => {
        const { element } = await mount([{ name: "Docs", href: "https://example.com" }]);

        element.renderRoot.querySelector<HTMLButtonElement>("button.pf-m-link")!.click();
        await element.updateComplete;

        expect(element.toJSON()).toStrictEqual([
            { name: "Docs", href: "https://example.com" },
            { name: "", href: "" },
        ]);
    });

    it("deletes the row whose button was pressed", async () => {
        const { element } = await mount([
            { name: "Docs", href: "https://example.com" },
            { name: "Support", href: "mailto:support@example.com" },
        ]);

        const [, second] = rows(element);

        element.renderRoot.querySelectorAll<HTMLButtonElement>("button.pf-m-control")[0].click();
        await element.updateComplete;

        expect(rows(element)).toHaveLength(1);
        expect(rows(element)[0]).toBe(second);

        expect(element.toJSON()).toStrictEqual([
            { name: "Support", href: "mailto:support@example.com" },
        ]);
    });
});
