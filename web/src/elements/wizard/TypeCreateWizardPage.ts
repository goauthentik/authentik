import "#admin/common/ak-license-notice";

import { WithLicenseSummary } from "#elements/mixins/license";
import { WizardPage } from "#elements/wizard/WizardPage";

import { TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export enum TypeCreateWizardPageLayouts {
    list = "list",
    grid = "grid",
}

@customElement("ak-wizard-page-type-create")
export class TypeCreateWizardPage extends WithLicenseSummary(WizardPage) {
    //#region Properties

    @property({ attribute: false })
    public types: TypeCreate[] = [];

    @property({ attribute: false })
    public selectedType: TypeCreate | null = null;

    @property({ type: String })
    public layout: TypeCreateWizardPageLayouts = TypeCreateWizardPageLayouts.list;

    //#endregion

    static styles: CSSResult[] = [
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

    //#region Refs

    #formRef = createRef<HTMLFormElement>();

    //#endregion

    public sidebarLabel = () => msg("Select type");

    public reset = () => {
        super.reset();
        this.selectedType = null;
        this.#formRef.value?.reset();
    };

    public override activeCallback = (): void => {
        const form = this.#formRef.value;

        this.host.isValid = form?.checkValidity() ?? false;

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
        return html`<div
            class="pf-l-grid pf-m-gutter"
            data-ouid-component-type="ak-type-create-grid"
        >
            ${this.types.map((type, idx) => {
                const requiresEnterprise = type.requiresEnterprise && !this.hasEnterpriseLicense;

                // It's valid to pass in a local modelName or the full name with application
                // part.  If the latter, we only want the part after the dot to appear as our
                // OUIA tag for test automation.
                const componentName = type.modelName.includes(".")
                    ? (type.modelName.split(".")[1] ?? "--unknown--")
                    : type.modelName;
                return html`<div
                    class="pf-l-grid__item pf-m-3-col pf-c-card ${requiresEnterprise
                        ? "pf-m-non-selectable-raised"
                        : "pf-m-selectable-raised"} ${this.selectedType === type
                        ? "pf-m-selected-raised"
                        : ""}"
                    tabindex=${idx}
                    data-ouid-component-type="ak-type-create-grid-card"
                    data-ouid-component-name=${componentName}
                    @click=${() => {
                        if (requiresEnterprise) return;

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
        return html`<form
            ${ref(this.#formRef)}
            class="pf-c-form pf-m-horizontal ak-m-radio-list"
            data-ouid-component-type="ak-type-create-list"
        >
            ${this.types.map((type, idx) => {
                const requiresEnterprise = type.requiresEnterprise && !this.hasEnterpriseLicense;
                const id = `${type.component}-${type.modelName}-${idx}`;

                return html`<div
                    class="pf-c-radio"
                    data-ouid-component-type="ak-type-create-list-card"
                    data-ouid-component-name=${type.modelName.split(".")[1] ?? "--unknown--"}
                    @click=${() => {
                        this.shadowRoot?.getElementById(id)?.click();
                    }}
                >
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${id}
                        required
                        ?checked=${this.selectedType?.modelName === type.modelName}
                        @change=${() => {
                            this.selectDispatch(type);
                            this.selectedType = type;
                        }}
                        ?disabled=${requiresEnterprise}
                    />
                    <label class="pf-c-radio__label" for=${id}>${type.name}</label>
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
            default:
                throw new Error(`Unknown layout: ${this.layout}`) as never;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-page-type-create": TypeCreateWizardPage;
    }
}
