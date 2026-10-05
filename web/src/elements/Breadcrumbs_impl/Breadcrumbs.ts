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
    url?: string;
}

/**
 * @element ak-breadcrumbs
 */
export class Breadcrumbs extends AKElement {
    static readonly styles = [styles];

    @property({ type: Array })
    items: BreadcrumbItem[] = [];

    public override render() {
        if (this.items.length === 0) {
            return nothing;
        }

        const lastIndex = this.items.length - 1;

        return html`<nav part="breadcrumbs" aria-label=${msg("Breadcrumbs")}>
            <ol part="list">
                ${this.items.map(({ label, url }: BreadcrumbItem, index) => {
                    const isLast = index === lastIndex;

                    return html`<li part="item">
                        ${
                            url && !isLast
                                ? html`<a part="link" href="#${url}">${label}</a>`
                                : html`<span aria-current=${isLast ? "page" : nothing}
                                      >${label}</span
                                  >`
                        }
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
