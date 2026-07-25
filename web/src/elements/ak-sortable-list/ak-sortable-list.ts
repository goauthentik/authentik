import { reorderKeys, SortableReorderDetail } from "./reorder.js";

import { AKElement } from "#elements/Base";

import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

export type { SortableReorderDetail };

/**
 * A generic drag-and-drop reorderable list.
 *
 * The consumer owns the list data and renders each row as a light-DOM child carrying a
 * `data-sortable-key` attribute, with a drag handle somewhere inside the row marked by
 * `draggable="true"` and `data-sortable-handle`. On drop, this element emits a `reorder`
 * {@link CustomEvent} whose detail contains the keys in their new order; the consumer is
 * expected to reorder its own data accordingly and re-render.
 *
 * @slot - the rows to reorder
 * @fires reorder - when the user drops a row in a new position
 */
@customElement("ak-sortable-list")
export class AKSortableList extends AKElement {
    static styles: CSSResult[] = [
        css`
            :host {
                display: block;
            }
        `,
    ];

    private draggingKey: string | null = null;

    constructor() {
        super();
        this.addEventListener("dragstart", this.onDragStart);
        this.addEventListener("dragover", this.onDragOver);
        this.addEventListener("drop", this.onDrop);
        this.addEventListener("dragend", this.onDragEnd);
    }

    /** All row elements (direct light-DOM children carrying a sortable key), in DOM order. */
    private rows(): HTMLElement[] {
        return Array.from(this.querySelectorAll<HTMLElement>("[data-sortable-key]")).filter(
            (row) => row.closest("ak-sortable-list") === this,
        );
    }

    private keyOf(target: EventTarget | null): string | null {
        const element = target as HTMLElement | null;
        const row = element?.closest?.("[data-sortable-key]") as HTMLElement | null;
        if (!row || row.closest("ak-sortable-list") !== this) {
            return null;
        }
        return row.dataset.sortableKey ?? null;
    }

    private rowFor(key: string): HTMLElement | undefined {
        return this.rows().find((row) => row.dataset.sortableKey === key);
    }

    private onDragStart = (event: DragEvent): void => {
        const handle = (event.target as HTMLElement | null)?.closest?.("[data-sortable-handle]");
        if (!handle) {
            // Only drags initiated from the handle count as a reorder.
            event.preventDefault();
            return;
        }
        const key = this.keyOf(event.target);
        if (!key || !event.dataTransfer) {
            return;
        }
        this.draggingKey = key;
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", key);
        const row = this.rowFor(key);
        if (row) {
            event.dataTransfer.setDragImage(row, 0, 0);
            row.style.opacity = "0.4";
        }
    };

    private onDragOver = (event: DragEvent): void => {
        if (!this.draggingKey) {
            return;
        }
        // Allow dropping.
        event.preventDefault();
        if (event.dataTransfer) {
            event.dataTransfer.dropEffect = "move";
        }
    };

    private onDrop = (event: DragEvent): void => {
        if (!this.draggingKey) {
            return;
        }
        event.preventDefault();
        const draggingKey = this.draggingKey;
        const currentKeys = this.rows().map((row) => row.dataset.sortableKey as string);
        const targetKey = this.keyOf(event.target);
        const targetRow = targetKey ? this.rowFor(targetKey) : undefined;
        const rect = targetRow?.getBoundingClientRect();
        const insertAfter = rect ? event.clientY > rect.top + rect.height / 2 : false;

        const keys = reorderKeys(currentKeys, draggingKey, targetKey, insertAfter);

        this.resetDrag();
        this.dispatchEvent(
            new CustomEvent<SortableReorderDetail>("reorder", {
                detail: { keys },
                bubbles: true,
                composed: true,
            }),
        );
    };

    private onDragEnd = (): void => {
        this.resetDrag();
    };

    private resetDrag(): void {
        if (this.draggingKey) {
            const row = this.rowFor(this.draggingKey);
            if (row) {
                row.style.opacity = "";
            }
        }
        this.draggingKey = null;
    }

    render(): TemplateResult {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sortable-list": AKSortableList;
    }
}
