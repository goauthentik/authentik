import "#elements/ak-array-input";
import { ArrayInput } from "#elements/ak-array-input";
import { AKControlElement } from "#elements/ControlElement";

import { afterEach, describe, expect, it } from "vitest";

import { html, LitElement, render } from "lit";

interface Link {
    name: string;
    href: string;
}

class TestRow extends AKControlElement<Link> {
    static shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };

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

    public get valid(): boolean {
        return this.toJSON().href.startsWith("https://");
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

interface MountInit {
    validate?: boolean;
    required?: boolean;
}

/**
 * Render the array input inside a form from a host template, the way a form does.
 */
async function mount(items: Link[], init: MountInit = {}) {
    const form = document.body.appendChild(document.createElement("form"));
    mounted.add(form);

    const renderHost = async (nextItems: Link[]) => {
        render(
            html`<ak-array-input
                name="links"
                ?validate=${init.validate}
                ?required=${init.required}
                .items=${nextItems}
                .newItem=${() => ({ name: "", href: "" })}
                .row=${(link: Link) =>
                    html`<ak-test-array-input-row
                        name="link"
                        .link=${link}
                    ></ak-test-array-input-row>`}
            ></ak-array-input>`,
            form,
        );

        const element = form.querySelector<ArrayInput<Link>>("ak-array-input")!;
        await element.updateComplete;

        return element;
    };

    return { form, element: await renderHost(items), renderHost };
}

function rows(element: ArrayInput<Link>) {
    return Array.from(element.renderRoot.querySelectorAll<TestRow>("ak-test-array-input-row"));
}

function addButton(element: ArrayInput<Link>) {
    return element.renderRoot.querySelector<HTMLButtonElement>("button.pf-m-link")!;
}

function removeButtons(element: ArrayInput<Link>) {
    return element.renderRoot.querySelectorAll<HTMLButtonElement>("button.pf-m-control");
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

describe("ak-array-input: host items", () => {
    it("keeps the user's edits when the host re-renders with the same array", async () => {
        const items = [{ name: "Docs", href: "https://example.com" }];
        const { element, renderHost } = await mount(items);

        await edit(element, rows(element)[0], "href", "https://goauthentik.io");
        await renderHost(items);

        expect(element.toJSON()).toStrictEqual([{ name: "Docs", href: "https://goauthentik.io" }]);
    });

    it("keeps added rows when the host re-renders with a new empty array", async () => {
        const { element, renderHost } = await mount([]);

        addButton(element).click();
        await element.updateComplete;
        await edit(element, rows(element)[0], "href", "https://goauthentik.io");
        await renderHost([]);

        expect(element.toJSON()).toStrictEqual([{ name: "", href: "https://goauthentik.io" }]);
    });

    it("replaces the user's edits when the host passes a different array", async () => {
        const { element, renderHost } = await mount([
            { name: "Docs", href: "https://example.com" },
        ]);

        await edit(element, rows(element)[0], "href", "https://goauthentik.io");
        await renderHost([{ name: "Support", href: "mailto:support@example.com" }]);

        expect(element.toJSON()).toStrictEqual([
            { name: "Support", href: "mailto:support@example.com" },
        ]);
    });
});

describe("ak-array-input: editing", () => {
    it("keeps a row's element in place while it is edited", async () => {
        const { element } = await mount([{ name: "Docs", href: "https://example.com" }]);
        const [row] = rows(element);

        await edit(element, row, "name", "Documentation");

        expect(rows(element)).toHaveLength(1);
        expect(rows(element)[0]).toBe(row);
    });

    it("dispatches one change event per edit", async () => {
        const { element } = await mount([{ name: "Docs", href: "https://example.com" }]);
        let changes = 0;

        element.addEventListener("change", () => changes++);
        await edit(element, rows(element)[0], "name", "Documentation");

        expect(changes).toBe(1);
    });

    it("adds an empty row after the existing ones and focuses it", async () => {
        const { element } = await mount([{ name: "Docs", href: "https://example.com" }]);

        addButton(element).click();
        await element.updateComplete;
        await new Promise((resolve) => requestAnimationFrame(resolve));

        expect(element.toJSON()).toStrictEqual([
            { name: "Docs", href: "https://example.com" },
            { name: "", href: "" },
        ]);

        expect(element.shadowRoot!.activeElement).toBe(rows(element)[1]);
    });

    it("deletes the row whose button was pressed", async () => {
        const { element } = await mount([
            { name: "Docs", href: "https://example.com" },
            { name: "Support", href: "mailto:support@example.com" },
        ]);

        const [, second] = rows(element);

        removeButtons(element)[0].click();
        await element.updateComplete;

        expect(rows(element)).toHaveLength(1);
        expect(rows(element)[0]).toBe(second);

        expect(element.toJSON()).toStrictEqual([
            { name: "Support", href: "mailto:support@example.com" },
        ]);
    });
});

describe("ak-array-input: form association", () => {
    it("is one of the form's elements and submits its rows as JSON", async () => {
        const { form, element } = await mount([{ name: "Docs", href: "https://example.com" }]);

        await edit(element, rows(element)[0], "name", "Documentation");

        expect(Array.from(form.elements)).toContain(element);

        expect(JSON.parse(new FormData(form).get("links") as string)).toStrictEqual([
            { name: "Documentation", href: "https://example.com" },
        ]);
    });

    it("restores the host's items when the form resets", async () => {
        const { form, element } = await mount([{ name: "Docs", href: "https://example.com" }]);

        await edit(element, rows(element)[0], "href", "https://goauthentik.io");
        form.reset();
        await element.updateComplete;

        expect(element.toJSON()).toStrictEqual([{ name: "Docs", href: "https://example.com" }]);
    });

    it("is invalid while a row is invalid, when validating", async () => {
        const { element } = await mount([{ name: "Docs", href: "https://example.com" }], {
            validate: true,
        });

        expect(element.checkValidity()).toBe(true);

        await edit(element, rows(element)[0], "href", "ftp://example.com");

        expect(element.checkValidity()).toBe(false);
        expect(element.validity.customError).toBe(true);
    });

    it("ignores invalid rows when not validating", async () => {
        const { element } = await mount([{ name: "Docs", href: "ftp://example.com" }]);

        expect(element.checkValidity()).toBe(true);
    });

    it("is missing a value when required and empty", async () => {
        const { element } = await mount([], { required: true });

        expect(element.validity.valueMissing).toBe(true);

        addButton(element).click();
        await element.updateComplete;

        expect(element.checkValidity()).toBe(true);
    });
});
