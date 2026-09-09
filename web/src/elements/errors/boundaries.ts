import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { CapabilitiesEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit-html";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";

/**
 * A fallback element to render when a custom element fails to load, either due to a missing import,
 * or a version mismatch between the element's definition and its usage.
 */
@customElement("ak-element-missing")
export class ElementConstructorBoundary extends AKElement {
    public styles = [PFAlert];

    protected override render(): SlottedTemplateResult {
        const debug = globalAK().config.capabilities.includes(CapabilitiesEnum.CanDebug);

        const description = debug
            ? msg(
                  "The element could not be loaded. This may be due to a missing import or a version mismatch.",
              )
            : msg(
                  "An element could not be loaded. Please try refreshing the page or clearing your cache.",
              );

        return html`<div class="pf-c-alert pf-m-danger" role="alert">
            <div class="pf-c-alert__icon">
                <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
            </div>
            <h4 class="pf-c-alert__title">${msg("Failed to load element")}</h4>
            <div class="pf-c-alert__description">${description}</div>
        </div>`;
    }
}
