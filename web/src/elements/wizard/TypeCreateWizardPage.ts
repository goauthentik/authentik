import "#elements/LicenseNotice";
import "#elements/Alert";
import "#elements/forms/FormGroup";

import { WithLicenseSummary } from "#elements/mixins/license";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { WizardPage } from "#elements/wizard/WizardPage";

import { TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { guard } from "lit/directives/guard.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

export enum TypeCreateWizardPageLayouts {
    list = "list",
    grid = "grid",
}

@customElement("ak-wizard-page-type-create")
export class TypeCreateWizardPage extends WithLicenseSummary(WizardPage) {
    //#region Properties

    @property({ attribute: false, useDefault: true })
    public types: TypeCreate[] | null = null;

    @property({ attribute: false, useDefault: true })
    public selectedType: TypeCreate | null = null;

    @property({ type: String, useDefault: true })
    public layout: TypeCreateWizardPageLayouts = TypeCreateWizardPageLayouts.list;

    @property({ type: String, attribute: "group-label", useDefault: true })
    public groupLabel: string | null = null;

    @property({ type: String, attribute: "group-description", useDefault: true })
    public groupDescription: string | null = null;

    //#endregion

    static styles: CSSResult[] = [
        PFForm,
        PFGrid,
        PFRadio,
        PFCard,
        PFPage,
        css`
            :host {
                display: flex;
                flex-flow: column;
            }

            .pf-c-card__header-main img {
                max-height: 2em;
                min-height: 2em;
            }
            :host([theme="dark"]) .pf-c-card__header-main img {
                filter: invert(1);
            }

            :host([theme="dark"]) .pf-c-card {
                --pf-c-card--BackgroundColor: var(--pf-global--BackgroundColor--150);
                --pf-c-card--m-selectable-raised--before--Right: -1px;
                --pf-c-card--m-selectable-raised--before--Left: -1px;
                --pf-c-card--m-selectable-raised--m-selected-raised--BoxShadow:
                    0 0 0 1px var(--pf-c-card--m-non-selectable-raised--before--BackgroundColor),
                    var(--pf-global--BoxShadow--lg);
            }

            [part*="type-create"]:not(:first-child) {
                margin-block-start: var(--pf-global--spacer--md);
            }
        `,
    ];

    //#region Refs

    protected formRef: Ref<HTMLFormElement> = createRef();

    //#endregion

    public reset = () => {
        super.reset();

        this.selectedType = null;
        this.formRef.value?.reset();
    };

    public override activeCallback = (): void => {
        this.host.valid = !!this.selectedType;
    };

    #selectDispatch = (type: TypeCreate) => {
        this.dispatchEvent(
            new CustomEvent("ak-type-create-select", {
                detail: type,
                bubbles: true,
                composed: true,
            }),
        );
    };

    //#region Rendering

    //#region Grid layout

    protected renderGridItems(): SlottedTemplateResult {
        if (!this.types?.length) {
            return null;
        }

        return this.types.map((type, idx) => {
            const disabled = !!(type.requiresEnterprise && !this.hasEnterpriseLicense);

            const selected = this.selectedType === type;
            const inputID = `${type.component}-${type.modelName}`;

            return html`<div
                class=${classMap({
                    "pf-l-grid__item": true,
                    "pf-m-3-col": true,
                    "pf-c-card": true,
                    "pf-m-non-selectable-raised": disabled,
                    "ak-m-enterprise-only": disabled,
                    "pf-m-selectable-raised": !disabled,
                    "pf-m-selected-raised": selected,
                })}
                tabindex=${idx}
                role="option"
                data-component=${type.component}
                data-model-name=${type.modelName}
                aria-disabled="${disabled ? "true" : "false"}"
                aria-selected="${selected ? "true" : "false"}"
                aria-label=${type.name}
                aria-describedby=${`${inputID}-description`}
                @click=${() => {
                    if (disabled) return;

                    this.selectedType = type;
                    this.#selectDispatch(type);
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
                    : null}
                <div role="heading" aria-level="2" class="pf-c-card__title">${type.name}</div>
                <div class="pf-c-card__body" id=${`${inputID}-description`}>
                    ${type.description}
                </div>
                ${disabled
                    ? html`<div class="pf-c-card__footer">
                          <ak-license-notice></ak-license-notice>
                      </div> `
                    : null}
            </div>`;
        });
    }

    protected renderGrid(): SlottedTemplateResult {
        if (!this.types?.length) {
            return html`<div class="ak-c-loading-skeleton ak-m-grid"></div>`;
        }

        return [
            this.findSlotted() ? this.defaultSlot : null,
            html`<div
                role="listbox"
                part="type-create grid"
                class="pf-l-grid pf-m-gutter"
                data-ouid-component-type="ak-type-create-grid"
                aria-label=${ifPresent(this.headline)}
            >
                ${this.renderGridItems()}
            </div>`,
        ];
    }

    //#endregion

    //#region List layout

    protected renderListItems(): SlottedTemplateResult {
        if (!this.types?.length) {
            return null;
        }

        return this.types.map((type) => {
            const disabled = !!(type.requiresEnterprise && !this.hasEnterpriseLicense);
            const inputID = `${type.component}-${type.modelName}`;
            const selected = this.selectedType === type;

            return html`<label class="pf-c-radio" for=${inputID}>
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id=${inputID}
                    aria-label=${type.name}
                    aria-describedby=${`${inputID}-description`}
                    @change=${() => {
                        this.selectedType = type;
                        this.#selectDispatch(type);
                    }}
                    ?disabled=${disabled}
                />
                <div
                    aria-selected="${selected ? "true" : "false"}"
                    aria-labelledby="${inputID}"
                    class="pf-c-radio__label"
                >
                    ${type.name}
                </div>
                <span id="${inputID}-description" class="pf-c-radio__description"
                    >${type.description}
                    ${disabled ? html`<ak-license-notice></ak-license-notice>` : null}
                    ${type.deprecated
                        ? html`<ak-alert class="pf-c-radio__description" inline plain>
                              ${msg("This type is deprecated.")}
                          </ak-alert>`
                        : null}
                </span>
            </label>`;
        });
    }

    protected renderList(): SlottedTemplateResult {
        if (!this.types?.length) {
            return html`<div class="ak-c-loading-skeleton ak-m-list"></div>`;
        }

        const renderedItems = this.renderListItems();
        const content = this.groupLabel
            ? html`<ak-form-group
                  label=${this.groupLabel}
                  description=${ifPresent(this.groupDescription)}
                  part="group"
                  open
              >
                  ${renderedItems}
              </ak-form-group>`
            : renderedItems;

        return [
            this.findSlotted() ? this.defaultSlot : null,
            html`<form
                ${ref(this.formRef)}
                part="form type-create list"
                class="pf-c-form pf-m-horizontal ak-m-content-center"
                role="radiogroup"
                aria-label=${ifPresent(this.headline)}
            >
                <slot name="pre-items"></slot>
                ${content}
            </form>`,
        ];
    }

    //#endregion

    protected override render(): SlottedTemplateResult {
        const { layout, types, selectedType } = this;

        const content = guard([layout, types, selectedType], () => {
            switch (layout) {
                case TypeCreateWizardPageLayouts.grid:
                    return this.renderGrid();
                case TypeCreateWizardPageLayouts.list:
                    return this.renderList();
                default:
                    throw new TypeError(`Unknown layout: ${layout}`);
            }
        });

        return content;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-page-type-create": TypeCreateWizardPage;
    }
}
