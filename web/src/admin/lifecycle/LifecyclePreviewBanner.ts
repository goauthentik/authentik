import { AKElement } from "#elements/Base";

import { ObjectPermissionPage } from "#admin/lifecycle/ObjectAccessReviewPage";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-lifecycle-preview-banner")
export class LifecyclePreviewBanner extends AKElement {
    static styles = [PFBanner];

    public render(): TemplateResult {
        return html`<div class="pf-c-banner pf-m-info">
            ${msg("Object Lifecycle Management is in preview.")}
            <a href="mailto:hello+feature/lifecycle@goauthentik.io">${msg("Send us feedback!")}</a>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-lifecycle-preview-banner": ObjectPermissionPage;
    }
}
