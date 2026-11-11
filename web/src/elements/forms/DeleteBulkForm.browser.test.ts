import "#elements/forms/DeleteBulkForm";
import { createPaginatedResponse } from "#common/api/responses";

import type { BulkAction, DeleteBulkForm } from "#elements/forms/DeleteBulkForm";
import { showMessage } from "#elements/messages/MessageContainer";
import { Table, type TableColumn } from "#elements/table/Table";

import { afterEach, describe, expect, it, vi } from "vitest";

import { html } from "lit";

vi.mock("#elements/messages/MessageContainer", () => ({ showMessage: vi.fn() }));

interface Item {
    pk: number;
}

/**
 * A table that declares its object names the way list pages do, and renders the form in its
 * toolbar.
 */
class BrandTable extends Table<Item> {
    public static override verboseName = "Brand";
    public static override verboseNamePlural = "Brands";

    public static override properties = {
        items: { attribute: false },
        action: {},
        failing: { type: Boolean },
    };

    declare public items: Item[];
    declare public action: BulkAction;
    declare public failing: boolean;

    protected columns: TableColumn[] = [["ID"]];

    protected apiEndpoint() {
        return Promise.resolve(createPaginatedResponse<Item>([]));
    }

    protected row(item: Item) {
        return [String(item.pk)];
    }

    protected override renderToolbarSelected() {
        return html`<ak-forms-delete-bulk
            action=${this.action}
            .objects=${this.items}
            .delete=${() => (this.failing ? Promise.reject(new Error("nope")) : Promise.resolve())}
        ></ak-forms-delete-bulk>`;
    }
}

customElements.define("test-delete-bulk-brand-table", BrandTable);

const mounted = new Set<HTMLElement>();

async function mount(
    count: number,
    action: BulkAction = "delete",
    failing = false,
): Promise<DeleteBulkForm<Item>> {
    const table = new BrandTable();

    table.items = Array.from({ length: count }, (_, pk) => ({ pk }));
    table.action = action;
    table.failing = failing;

    document.body.appendChild(table);
    mounted.add(table);
    await table.updateComplete;

    const form = table.renderRoot.querySelector<DeleteBulkForm<Item>>("ak-forms-delete-bulk")!;

    form.open = true;
    await form.updateComplete;

    return form;
}

function text(element: Element, selector: string): string {
    return element.shadowRoot!.querySelector(selector)!.textContent!.replace(/\s+/g, " ").trim();
}

function submitButton(form: DeleteBulkForm<Item>): HTMLElement {
    return form.renderRoot.querySelector<HTMLElement>("ak-spinner-button.pf-m-danger")!;
}

async function submit(form: DeleteBulkForm<Item>): Promise<void> {
    submitButton(form).shadowRoot!.querySelector("button")!.click();

    await vi.waitFor(() => expect(showMessage).toHaveBeenCalled());
}

describe("ak-forms-delete-bulk", () => {
    afterEach(() => {
        for (const element of mounted) element.remove();
        mounted.clear();
        vi.mocked(showMessage).mockClear();
    });

    it("takes the object names from the table that renders it", async () => {
        const one = await mount(1);

        expect(text(one, "h1")).toBe("Delete 1 Brand");
        expect(text(one, "p.pf-c-title")).toBe("Are you sure you want to delete 1 Brand?");

        const many = await mount(3);

        expect(text(many, "h1")).toBe("Delete 3 Brands");
        expect(text(many, "p.pf-c-title")).toBe("Are you sure you want to delete 3 Brands?");
    });

    it("words the success toast for the action and count", async () => {
        const form = await mount(2, "remove");

        await submit(form);

        expect(showMessage).toHaveBeenCalledWith(
            expect.objectContaining({ message: "Successfully removed 2 Brands." }),
        );
    });

    it("words the error toast for the action and count", async () => {
        const form = await mount(1, "delete", true);

        await submit(form);

        expect(showMessage).toHaveBeenCalledWith(
            expect.objectContaining({ message: "Failed to delete 1 Brand." }),
        );
    });

    it("labels the cancel button with the heading, not a bare Cancel", async () => {
        const form = await mount(2, "cancel");

        expect(text(form, "h1")).toBe("Cancel 2 Brands");
        expect(submitButton(form).textContent!.trim()).toBe("Cancel 2 Brands");
    });

    it("prefers explicit names and a custom prompt over the table's", async () => {
        const form = await mount(2, "remove");

        form.verboseName = "Group";
        form.verboseNamePlural = "Groups";
        form.actionSubtext = "Remove the user from these groups?";
        await form.updateComplete;

        expect(text(form, "h1")).toBe("Remove 2 Groups");
        expect(text(form, "p.pf-c-title")).toBe("Remove the user from these groups?");
    });
});
