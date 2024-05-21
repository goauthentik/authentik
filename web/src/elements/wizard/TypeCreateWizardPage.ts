import "@goauthentik/admin/common/ak-license-notice";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { TypeCreate } from "@goauthentik/api";

export enum TypeCreateWizardPageLayouts {
    list = "list",
    grid = "grid",
}

@customElement("ak-wizard-page-type-create")
export class TypeCreateWizardPage extends WithLicenseSummary(WizardPage) {
    @property({ attribute: false })
    types: TypeCreate[] = [];

    @property({ attribute: false })
    selectedType?: TypeCreate;

    @property({ type: String })
    layout: TypeCreateWizardPageLayouts = TypeCreateWizardPageLayouts.list;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFForm,
            PFGrid,
            PFRadio,
            PFCard,
            css`
                .pf-c-card__header-main img {
                    max-height: 2em;
                    min-height: 2em;
                }
                :host([theme="dark"]) .pf-c-card__header-main img {
                    filter: invert(1);
                }
            `,
        ];
    }

    sidebarLabel = () => msg("Select type");

    activeCallback: () => Promise<void> = async () => {
        this.host.isValid = false;
        if (this.selectedType) {
            this.selectDispatch(this.selectedType);
        }
    };

    private selectDispatch(type: TypeCreate) {
        this.dispatchEvent(
            new CustomEvent("select", {
                detail: type,
                bubbles: true,
                composed: true,
            }),
        );
    }

    renderGrid(): TemplateResult {
        return html`<div class="pf-l-grid pf-m-gutter">
            ${this.types.map((type, idx) => {
                const requiresEnterprise = type.requiresEnterprise && !this.hasEnterpriseLicense;
                return html`<div
                    class="pf-l-grid__item pf-m-3-col pf-c-card ${requiresEnterprise
                        ? "pf-m-non-selectable-raised"
                        : "pf-m-selectable-raised"} ${this.selectedType == type
                        ? "pf-m-selected-raised"
                        : ""}"
                    tabindex=${idx}
                    @click=${() => {
                        if (requiresEnterprise) {
                            return;
                        }
                        this.selectDispatch(type);
                        this.selectedType = type;
                    }}
                >
                    ${type.iconUrl
                        ? html`<div class="pf-c-card__header">
                              <div class="pf-c-card__header-main">
                                  <img src=${type.iconUrl} alt=${msg(str`${type.name} Icon`)} />
                              </div>
                          </div>`
                        : nothing}
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

    renderList(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.types.map((type) => {
                const requiresEnterprise = type.requiresEnterprise && !this.hasEnterpriseLicense;
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${`${type.component}-${type.modelName}`}
                        @change=${() => {
                            this.selectDispatch(type);
                        }}
                        ?disabled=${requiresEnterprise}
                    />
                    <label class="pf-c-radio__label" for=${`${type.component}-${type.modelName}`}
                        >${type.name}</label
                    >
                    <span class="pf-c-radio__description"
                        >${type.description}
                        ${requiresEnterprise
                            ? html`<ak-license-notice></ak-license-notice>`
                            : nothing}
                    </span>
                </div>`;
            })}
        </form>`;
    }

    render(): TemplateResult {
        switch (this.layout) {
            case TypeCreateWizardPageLayouts.grid:
                return this.renderGrid();
            case TypeCreateWizardPageLayouts.list:
                return this.renderList();
        }
    }
}
