import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { TypeCreate } from "@goauthentik/api";

export abstract class TypeCreateWizardPage extends WithLicenseSummary(WizardPage) {
    @property({ attribute: false })
    types: TypeCreate[] = [];

    @state()
    selectedType?: TypeCreate;

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFGrid, PFCard];
    }

    sidebarLabel = () => msg("Select type");

    activeCallback: () => Promise<void> = async () => {
        this.host.isValid = false;
        if (this.selectedType) {
            this.onSelect(this.selectedType);
        }
    };

    abstract onSelect(type: TypeCreate): void;

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <p class="pf-c-form__helper-text">${msg("Select a provider type")}</p>
            <div class="pf-l-grid pf-m-gutter">
                ${this.types.map((type, idx) => {
                    const requiresEnterprise =
                        type.requiresEnterprise && !this.hasEnterpriseLicense;
                    return html`<div
                        class="pf-l-grid__item pf-m-3-col pf-c-card ${requiresEnterprise
                            ? "pf-m-non-selectable-raised"
                            : "pf-m-selectable-raised"} ${this.selectedType == type
                            ? "pf-m-selected-raised"
                            : ""}"
                        id=${`card-${type.component}`}
                        tabindex=${idx}
                        @click=${() => {
                            if (requiresEnterprise) {
                                return;
                            }
                            this.onSelect(type);
                            this.selectedType = type;
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
            </div>
        </form>`;
    }
}
