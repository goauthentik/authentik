/**
 * @file Barrel file and default registry ('ak-breadcrumbs') for the Breadcrumbs component
 */

import { akBreadcrumbs, Breadcrumbs, type BreadcrumbItem } from "./Breadcrumbs_impl/Breadcrumbs";

export { akBreadcrumbs, Breadcrumbs };
export type { BreadcrumbItem };

customElements.define("ak-breadcrumbs", Breadcrumbs);

declare global {
    interface HTMLElementTagNameMap {
        "ak-breadcrumbs": Breadcrumbs;
    }
}
