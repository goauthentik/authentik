import "@goauthentik/admin/common/ak-license-notice";
import { WithLicenseSummary, isEnterpriseLicense } from "@goauthentik/elements/mixins/license";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

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
    //#region Properties

    @property({ attribute: false })
    types: TypeCreate[] = [];

    @property({ attribute: false })
    selectedType?: TypeCreate;

    @property({ type: String })
    layout: TypeCreateWizardPageLayouts = TypeCreateWizardPageLayouts.list;

    //#endregion

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

                @media (prefers-color-scheme: dark) {
                    .pf-c-card__header-main img {
                        filter: invert(1);
                    }
                }
            `,
        ];
    }

    //#region Refs

    formRef: Ref<HTMLFormElement> = createRef();

    //#endregion

    public sidebarLabel = () => msg("Select type");

    public reset = () => {
        super.reset();
        this.selectedType = undefined;
        this.formRef.value?.reset();
    };

    activeCallback = (): void => {
        const form = this.formRef.value;

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
        const enterprise = isEnterpriseLicense(this.licenseSummary);

        return html`<div
            class="pf-l-grid pf-m-gutter"
            data-ouid-component-type="ak-type-create-grid"
        >
            ${this.types.map((type, idx) => {
                const requiresEnterprise = type.requiresEnterprise && !enterprise;

                // It's valid to pass in a local modelName or the full name with application
                // part.  If the latter, we only want the part after the dot to appear as our
                // OUIA tag for test automation.
                const componentName = type.modelName.includes(".")
                    ? (type.modelName.split(".")[1] ?? "--unknown--")
                    : type.modelName;
                return html`<div
                    class="pf-l-grid__item pf-m-3-col pf-c-card ${requiresEnterprise
                        ? "pf-m-non-selectable-raised"
                        : "pf-m-selectable-raised"} ${this.selectedType == type
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
        const enterprise = isEnterpriseLicense(this.licenseSummary);

        return html`<form
            ${ref(this.formRef)}
            class="pf-c-form pf-m-horizontal"
            data-ouid-component-type="ak-type-create-list"
        >
            ${this.types.map((type) => {
                const requiresEnterprise = type.requiresEnterprise && !enterprise;

                return html`<div
                    class="pf-c-radio"
                    data-ouid-component-type="ak-type-create-list-card"
                    data-ouid-component-name=${type.modelName.split(".")[1] ?? "--unknown--"}
                >
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
