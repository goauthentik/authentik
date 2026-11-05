import { Breadcrumbs } from "#elements/Breadcrumbs";

import { BreadcrumbContext, BreadcrumbEntries } from "#admin/sidebar/BreadcrumbController";

import { consume } from "@lit/context";
import { PropertyValues } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-ui-breadcrumbs")
export class AkBreadcrumbs extends Breadcrumbs {
    @consume({ context: BreadcrumbContext, subscribe: true })
    public items: BreadcrumbEntries | null = null;

    // [Lit Lifecycle](https://lit.dev/docs/components/lifecycle/#willupdate)
    public override willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);
        this.entries = this.items?.fullCrumbs ?? null;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-ui-breadcrumbs": AkBreadcrumbs;
    }
}
