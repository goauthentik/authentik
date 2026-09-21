import { pageBounds, PaginatorPageBounds } from "./bounds";
import { PageChangeEvent } from "./events";
import Styles from "./Paginator.styles";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";

import { AKElement } from "#elements/Base";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues } from "lit";
import { property, query, state } from "lit/decorators.js";

// TODO: Implement compact / bottom strictly in CSS!

type NavAction = "first" | "prev" | "next" | "last";

type MsgType = ReturnType<typeof msg>;

type NavControl = Record<NavAction, { modifier: NavAction; icon: string }>;

type NavLabel = Record<NavAction, MsgType>;

// prettier-ignore
const NAV_CONTROLS = {
    first: { modifier: "first", icon: "fa-angle-double-left" },
    prev: {  modifier: "prev",  icon: "fa-angle-left" },
    next: {  modifier: "next",  icon: "fa-angle-right" },
    last: {  modifier: "last",  icon: "fa-angle-double-right" },
};

// prettier-ignore
const NAV_LABELS = {
    first: msg("Go to first page",    { id: "pagination.first-page.aria-label" }),
    prev:  msg("Go to previous page", { id: "pagination.previous-page.aria-label" }),
    next:  msg("Go to next page",     { id: "pagination.next-page.aria-label" }),
    last:  msg("Go to last page",     { id: "pagination.last-page.aria-label" })
};

const VALID_KEYS = new Set([
    "Tab",
    "Backspace",
    "Delete",
    "ArrowLeft",
    "ArrowRight",
    "ArrowUp",
    "ArrowDown",
    "Home",
    "End",
]);

export class Paginator extends AKElement {
    static readonly styles = [PFButton, PFFormControl, PFPagination, Styles];

    @property({ type: Number, attribute: "item-count" })
    itemCount = 0;

    @property({ type: Number, attribute: "items-per-page" })
    itemsPerPage = 20;

    // At different stages of the component lifecycle, these can all be different, and the React
    // version tracks them like this.

    // The page we're *supposed* to be on.
    @property({ type: Number, attribute: "page" })
    page = 1;

    // The page we last drew;
    protected renderedPage = 0;

    // The page we last sent via an event.
    protected lastPage: number | null = null;

    @property({ type: String, attribute: "label" })
    public label: string | null = null;

    // compact controls don't render the "first" and "last" buttons
    @property({ type: Boolean, attribute: "compact" })
    compact = false;

    @property({ type: Boolean, reflect: true })
    disabled = false;

    // The fully controlled value displayed in the input field
    @state()
    protected pendingInput = "1";

    // Target for controlling the size of the input field. It's done with a property, and we want it
    // to be at the top of the component's shadow DOM, because we don't want to change it for other
    // input fields on the page.
    //
    @query('[part="pagination"]')
    paginator!: HTMLInputElement;

    protected get bounds(): PaginatorPageBounds {
        return pageBounds(this.itemCount, this.itemsPerPage, this.page);
    }

    // Note that we don't actually *go to* anything. It's up to the client code to honor the request,
    // find the new page, and tell us where it is. We don't draw based on this change; we draw based
    // on a change to `this.page`, which the client gives us in the attribute when they've updated.
    // This is why there are three page states; what the user requested, what's currently shown,
    // and what the user has in the input box can all be *different*.
    //
    protected goto(page: number) {
        const { page: nextPage } = pageBounds(this.itemCount, this.itemsPerPage, page);

        if (nextPage === this.bounds.page || this.disabled) {
            return;
        }

        this.dispatchEvent(new PageChangeEvent(nextPage));
    }

    protected renderControl(action: NavAction, page: number, disabled: boolean) {
        const { modifier, icon } = NAV_CONTROLS[action];

        return html`<div part="nav-control ${modifier}">
            <button
                part="paginator-button ${modifier}"
                data-action=${action}
                ?disabled=${disabled}
                aria-label=${NAV_LABELS[action]}
                @click=${() => this.goto(page)}
            >
                <i class="fas ${icon}" aria-hidden="true"></i>
            </button>
        </div>`;
    }

    // The "page select" input field from Patternfly, in the React version, is fully controlled; we
    // need to re-render the whole thing on every keystroke, but we need to *not* trigger a page
    // change until the user presses [Enter].  This uses "pendingInput" to hold the controlled
    // value, but
    //
    onInput = (event: Event) => {
        this.pendingInput = `${(event.target as HTMLInputElement).value}`;
    };

    onBlur = () => {
        this.pendingInput = `${this.renderedPage}`;
    };

    onKeyDown = (event: KeyboardEvent) => {
        const { key } = event;

        if (key === "Enter") {
            const pendingInput = Number.parseInt(this.pendingInput, 10);
            const resolvedPending = Number.isNaN(pendingInput) ? this.renderedPage : pendingInput;
            // Don't let the user exceed the bounds.
            const { page } = pageBounds(this.itemCount, this.itemsPerPage, resolvedPending);
            this.pendingInput = `${page}`;
            this.goto(page);

            return;
        }

        if (!/^\d$/.test(key) && !VALID_KEYS.has(key)) {
            event.preventDefault();
        }
    };

    protected renderPageSelect({ totalPages }: PaginatorPageBounds) {
        // I have no idea why, but the value only updates visually if you dot it.
        return html`<div part="page-select">
            <input
                part="page-select-control"
                type="number"
                inputmode="numeric"
                min="1"
                max=${Math.max(totalPages, 1)}
                .value=${this.pendingInput}
                ?disabled=${this.disabled || totalPages <= 1}
                aria-label=${msg("Current page", { id: "pagination.current-page.aria-label" })}
                @input=${this.onInput}
                @keydown=${this.onKeyDown}
                @blur=${this.onBlur}
            />
            <span aria-hidden="true">
                ${msg(str`of ${totalPages}`, { id: "pagination.page-select-of-pages" })}
            </span>
        </div>`;
    }

    protected renderTotalItems(start: number, end: number, total: number) {
        return html`<div part="total-count">
            ${msg(html`<b>${start} - ${end}</b> of <b>${total}</b>`, {
                id: "pagination.total-count.summary",
            })}
        </div>`;
    }

    protected get navAriaLabel() {
        return this.label
            ? msg(str`${this.label} pagination`, {
                  id: "pagination.nav.aria-label.labelled",
              })
            : msg("Pagination", { id: "pagination.nav.aria-label" });
    }

    public willUpdate(changed: PropertyValues<this>) {
        const { page } = this.bounds;

        // Client requests override internal tracking. Reset to track future events.
        if (changed.has("page")) {
            this.lastPage = null;
        }

        // Tell the client we're changing pages.  This shouldn't result in a loop
        // since we ignore pointless "change to the same page" events.
        if (page !== this.page && page !== this.lastPage) {
            this.lastPage = page;
            this.dispatchEvent(new PageChangeEvent(page));
        }

        // Update what's shown in the input box.
        if (page !== this.renderedPage) {
            this.renderedPage = page;
            this.pendingInput = `${page}`;
        }
    }

    render() {
        const { page, totalPages, startIndex, endIndex } = this.bounds;
        const atStart = this.disabled || page <= 1;
        const atEnd = this.disabled || totalPages === 0 || page >= totalPages;

        return html`<nav part="pagination" aria-label="${this.navAriaLabel}">
            ${this.renderTotalItems(startIndex, endIndex, this.itemCount)}
            <div part="pagination-nav">
                ${this.compact ? nothing : this.renderControl("first", 1, atStart)}
                ${this.renderControl("prev", page - 1, atStart)}
                ${this.compact ? nothing : this.renderPageSelect(this.bounds)}
                ${this.renderControl("next", page + 1, atEnd)}
                ${this.compact ? nothing : this.renderControl("last", totalPages, atEnd)}
            </div>
        </nav>`;
    }

    protected updated() {
        const { totalPages } = this.bounds;
        const numChars = Math.max(`${Math.max(totalPages, 1)}`.length, 2);

        this.paginator?.style.setProperty(
            "--ak-c-pagination__page-select--form-control--width",
            `${numChars}ch`,
        );
    }
}
