import "#admin/common/ak-license-notice";

import { WithLicenseSummary } from "#elements/mixins/license";
import { WizardPage } from "#elements/wizard/WizardPage";

import { TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

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

    formRef: Ref<HTMLFormElement> = createRef();

    //#endregion

    public sidebarLabel = () => msg("Select type");

    public reset = () => {
        super.reset();

        this.selectedType = null;
        this.formRef.value?.reset();
    };

    public activeCallback = (): void => {
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

    protected renderGrid(): TemplateResult {
        return html`<div
            role="listbox"
            aria-label="${msg("Select a provider type")}"
            class="pf-l-grid pf-m-gutter"
            data-ouid-component-type="ak-type-create-grid"
        >
            ${this.types.map((type, idx) => {
                const disabled = !!(type.requiresEnterprise && !this.hasEnterpriseLicense);

                const selected = this.selectedType === type;

                return html`<div
                    class=${classMap({
                        "pf-l-grid__item": true,
                        "pf-m-3-col": true,
                        "pf-c-card": true,
                        "pf-m-non-selectable-raised": disabled,
                        "pf-m-selectable-raised": !disabled,
                        "pf-m-selected-raised": selected,
                    })}
                    tabindex=${idx}
                    role="option"
                    aria-disabled="${disabled ? "true" : "false"}"
                    aria-selected="${selected ? "true" : "false"}"
                    aria-label="${type.name}"
                    aria-describedby="${type.description}"
                    @click=${() => {
                        if (disabled) return;

                        this.selectDispatch(type);
                        this.selectedType = type;
                    }}
                >
                    ${type.iconUrl
                        ? html`<div role="presentation" class="pf-c-card__header">
                              <div role="presentation" class="pf-c-card__header-main">
                                  <img
                                      aria-hidden="true"
                                      src=${type.iconUrl}
                                      alt=${msg(str`${type.name} Icon`)}
                                  />
                              </div>
                          </div>`
                        : nothing}
                    <div role="heading" aria-level="2" class="pf-c-card__title">${type.name}</div>
                    <div role="presentational" class="pf-c-card__body">${type.description}</div>
                    ${disabled
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
            ${ref(this.formRef)}
            class="pf-c-form pf-m-horizontal"
            role="radiogroup"
            aria-label=${msg("Select a provider type")}
        >
            ${this.types.map((type) => {
                const disabled = !!(type.requiresEnterprise && !this.hasEnterpriseLicense);
                const inputID = `${type.component}-${type.modelName}`;
                const selected = this.selectedType === type;

                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${`${inputID}`}
                        aria-label=${type.name}
                        aria-describedby=${`${inputID}-description`}
                        @change=${() => {
                            this.selectDispatch(type);
                        }}
                        ?disabled=${disabled}
                    />
                    <label
                        aria-selected="${selected ? "true" : "false"}"
                        aria-labelledby="${inputID}"
                        class="pf-c-radio__label"
                        for="${inputID}"
                        >${type.name}</label
                    >
                    <span id="${inputID}-description" class="pf-c-radio__description"
                        >${type.description}
                        ${disabled ? html`<ak-license-notice></ak-license-notice>` : nothing}
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
