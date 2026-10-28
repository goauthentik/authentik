/**
 * @file Implementation code for the Breadcrumbs component
 */

import styles from "./Breadcrumbs.styles";

import { AKElement } from "#elements/Base";
import { type ElementRest } from "#elements/types";

import { BreadcrumbContext, BreadcrumbEntries } from "#admin/sidebar/BreadcrumbController";

import { spread } from "@open-wc/lit-helpers";

import { consume } from "@lit/context";
import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { property } from "lit/decorators/property.js";

export interface BreadcrumbItem {
    label: string;
    url?: string;
}

/**
 * @element ak-breadcrumbs
 */
export class Breadcrumbs extends AKElement {
    static readonly styles = [styles];

    @consume({ context: BreadcrumbContext, subscribe: true })
    entries: BreadcrumbEntries | null = null;

    @property({ type: Array })
    items: BreadcrumbItem[] = [];

    public override render() {
        if (!this.entries || this.entries.fullCrumbs.length === 0) {
            return nothing;
        }

        console.log(this.entries);

        const lastIndex = this.entries.fullCrumbs.length - 1;

        return html`<nav part="breadcrumbs" aria-label=${msg("Breadcrumbs")}>
            <ol part="list">
                ${this.entries.fullCrumbs.map((label: string, index) => {
                    const isLast = index === lastIndex;

                    return html`<li part="item">
                        <span aria-current=${isLast ? "page" : nothing}>${label}</span>
                    </li>`;
                })}
            </ol>
        </nav>`;
    }
}

export type DividerProps = ElementRest & {
    items?: BreadcrumbItem[];
};

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-breadcrumbs element
 * @summary Helper function to create a Breadcrumbs component programmatically
 *
 * @see {@link Breadcrumbs} - The underlying web component
 */
export function akBreadcrumbs(options: DividerProps = {}) {
    const { items, ...rest } = options;

    return html` <ak-breadcrumbs .item=${items ?? []} ${spread(rest)}></ak-breadcrumbs> `;
}
