/**
 * @file Implementation code for the Breadcrumbs component
 */

import styles from "./Breadcrumbs.styles";

import { AKElement } from "#elements/Base";
import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { property } from "lit/decorators/property.js";

export interface BreadcrumbItem {
    label: string;
    path: string | null;
}

export function render(entries: BreadcrumbItem[] | null) {
    if (!entries || entries.length === 0) {
        return nothing;
    }

    const lastIndex = entries.length - 1;

    return html`<nav part="breadcrumbs" aria-label=${msg("Breadcrumbs")}>
        <ol part="list">
            ${entries.map(({ label, path }, index) => {
                const isLast = index === lastIndex;

                return html`<li part="item">
                    ${
                        path && !isLast
                            ? html`<a part="link" href="${path}">${label}</a>`
                            : html`<span aria-current=${isLast ? "page" : nothing}>${label}</span>`
                    }
                </li>`;
            })}
        </ol>
    </nav>`;
}

/**
 * @element ak-breadcrumbs
 */
export class Breadcrumbs extends AKElement {
    static readonly styles = [styles];

    @property({ type: Array })
    public entries: BreadcrumbItem[] | null = null;

    public override render() {
        return render(this.entries);
    }
}

export type BreadcrumbProps = ElementRest & {
    entries?: BreadcrumbItem[];
};

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-breadcrumbs element
 * @summary Helper function to create a Breadcrumbs component programmatically
 *
 * @see {@link Breadcrumbs} - The underlying web component
 */
export function akBreadcrumbs(options: BreadcrumbProps = {}) {
    const { entries, ...rest } = options;

    return html` <ak-breadcrumbs .entries=${entries ?? []} ${spread(rest)}></ak-breadcrumbs> `;
}
