import { AKElement } from "@goauthentik/elements/Base";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";
import type { Wizard } from "@goauthentik/elements/wizard/Wizard";

import { CSSResult, TemplateResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { TypeCreate } from "@goauthentik/api";

@customElement("ak-wizard-type-create-picker")
export class TypeCreatePicker extends WithLicenseSummary(AKElement) {
    @property({ attribute: false })
    types: TypeCreate[] = [];

    @property({ attribute: false })
    host?: Wizard;

    static get styles(): CSSResult[] {
        return [PFBase, PFGrid, PFCard];
    }

    render(): TemplateResult {
        return html`<div class="pf-l-grid pf-m-gutter">
            ${this.types.map((type, idx) => {
                const requiresEnterprise = type.requiresEnterprise && !this.hasEnterpriseLicense;
                return html`<div
                    class="pf-l-grid__item pf-m-3-col pf-c-card ${requiresEnterprise
                        ? "pf-m-non-selectable-raised"
                        : "pf-m-selectable-raised"}"
                    id=${`card-${type.component}`}
                    tabindex=${idx}
                    @click=${() => {
                        if (requiresEnterprise || !this.host) {
                            return;
                        }
                        this.host.steps = ["initial", `type-${type.component}`];
                        this.host.isValid = true;
                        // Unselect other cards
                        this.shadowRoot
                            ?.querySelectorAll<HTMLDivElement>(".pf-c-card")
                            .forEach((card) => {
                                card.classList.remove("pf-m-selected-raised");
                            });
                        const card = this.shadowRoot?.querySelector<HTMLDivElement>(
                            `#card-${type.component}`,
                        );
                        if (card) {
                            card.classList.add("pf-m-selected-raised");
                        }
                    }}
                >
                    <div class="pf-c-card__title">${type.name}</div>
                    <div class="pf-c-card__body">${type.description}</div>
                    ${requiresEnterprise
                        ? html`<div class="pf-c-card__footer">
                              <ak-license-notice></ak-license-notice>
                          </div> `
                        : nothing}
                </div>`;
            })}
        </div>`;
    }
}
