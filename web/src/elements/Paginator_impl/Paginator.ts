import { pageBounds, PaginatorPageBounds } from "./bounds";
import { PageChangeEvent } from "./events";
import { AKElement } from "#elements/Base";
import { msg } from "@lit/localize";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";
import Styles from "./Paginator.styles";
import { html, nothing } from "lit";
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
}

export class Paginator extends AKElement {
    static readonly styles = [PFButton, PFFormControl, PFPagination, Styles];

    @property({ type: Number, attribute: "total-items" })
    totalItems = 0;

    @property({ type: Number, attribute: "items-per-page" })
    itemsPerPage = 20;

    @property({ type: Number })
    page = 1;

    @property({ type: String })
    public label: string | null = null;

    protected get bounds(): PaginatorPageBounds {
        return pageBounds(this.totalItems, this.itemsPerPage, this.page);
    }

    // Note that we don't actually *do* anything. It's up to the client code to honor the request,
    // find the new page, and tell us where it is. We don't draw based on this change; we draw based
    // on a change to `this.page`, which the client gives us in the attribute when they've updated.
    protected goto(page: number) {
        const { page: nextPage } = pageBounds(this.itemCount, this.itemsPerPage, page);

        if (nextPage == this.bounds.page || this.disabled) {
            return;
        }
        this.dispatchEvent(new PageChangeEvent(nextPage));
    }

    protected renderControl(action: NavAction, page: number, disabled: boolean) {
        const { modifier, icon } = NAV_CONTROLS[action];
        return html`<div part="nav-control ${modifier}">
            <button
                class="pf-c-button pf-m-plain"
                data-action=${action}
                ?disable=${disabled}
                aria-label=${NAV_LABELS[action]}
                @click=${() => this.goto(page)}
            >
                <i class="fas ${icon}" aria-hidden="true"></i>
            </button>
        </div>`;
    }

    protected renderPageSelect(bounds: PaginatorPageBounds) {
        return nothing;
    }

    protected get navAriaLabel() {
        return this.label
            ? msg(str`${this.label} pagination`, {
                  id: "pagination.nav.aria-label.labelled",
              })
            : msg("Pagination", { id: "pagination.nav.aria-label" });
    }

    render() {
        const { page, totalPages, startIndex, endIndex } = this.bounds;
        const atStart = this.disabled || page <= 1;
        const atEnd = this.disabled || totalPages === 0 || page >= totalPages;

        return html`<nav part="pagination" aria-label="${this.navAriaLabel}">
            <div part="pagination-nav">
                ${this.compact ? nothing : this.renderControl("first", 1, atStart)}
                ${this.renderControl("prev", page - 1, atStart)}
                ${this.compact ? nothing : this.renderPageSelect(this.bounds)}
                ${this.renderControl("next", page + 1, atEnd)}
                ${this.compact ? nothing : this.renderControl("last", 1, totalPages, atEnd)}
            </div>
        </nav>`;
    }
}
