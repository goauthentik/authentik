import "#elements/LicenseNotice";
import "#elements/Alert";
import "#elements/forms/FormGroup";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { WithLicenseSummary } from "#elements/mixins/license";
import { renderSourceIcon } from "#elements/sources/utils";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { WizardPage } from "#elements/wizard/WizardPage";

import { TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { guard } from "lit/directives/guard.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

export enum TypeCreateWizardPageLayouts {
    list = "list",
    grid = "grid",
}

/**
 * A choice that binds an existing object instead of creating one.
 */
export interface TypeCreateBindOption {
    label: string;
    description: string;
    /**
     * Sent as the detail of the `ak-type-create-bind` event.
     */
    value: string;
}

export interface TypeCreateBindChoices {
    label: string;
    description?: string;
    options: TypeCreateBindOption[];
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

    /**
     * Choices listed before the types, in the list layout, that bind an existing object
     * instead of creating one. They share the types' radio group, so the page holds one choice.
     */
    @property({ attribute: false, useDefault: true })
    public bindChoices: TypeCreateBindChoices | null = null;

    /**
     * The value of the chosen bind option, if one was chosen instead of a type.
     */
    @property({ attribute: false, useDefault: true })
    public selectedBind: string | null = null;

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

    //#region Lifecycle

    public reset = () => {
        super.reset();

        this.selectedType = null;
        this.selectedBind = null;
        this.formRef.value?.reset();
    };

    public override activeCallback = (): void => {
        this.host.valid = !!this.selectedType || this.selectedBind !== null;
    };

    protected override updated(changedProperties: PropertyValues<this>): void {
        // A type cleared by choosing a bind option is not a choice of its own.
        if (changedProperties.has("selectedType") && this.selectedType) {
            this.#selectDispatch(this.selectedType);
        }
    }

    #selectDispatch = (type: TypeCreate) => {
        this.dispatchEvent(
            new CustomEvent("ak-type-create-select", {
                detail: type,
                bubbles: true,
                composed: true,
            }),
        );
    };

    /**
     * Choose a type from the list. A click rather than a change, so that clicking the type
     * already chosen, as after going Back, moves on again.
     */
    #chooseListType(type: TypeCreate): void {
        this.selectedBind = null;

        // A changed type dispatches from `updated()`; an unchanged one would not.
        if (this.selectedType === type) {
            this.#selectDispatch(type);
        } else {
            this.selectedType = type;
        }
    }

    #chooseBind(value: string): void {
        this.selectedType = null;
        this.selectedBind = value;

        this.dispatchEvent(
            new CustomEvent("ak-type-create-bind", {
                detail: value,
                bubbles: true,
                composed: true,
            }),
        );
    }

    //#endregion

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
                ${
                    type.iconUrl
                        ? html`<div role="presentation" class="pf-c-card__header">
                              <div
                                  role="presentation"
                                  aria-hidden="true"
                                  class="pf-c-card__header-main"
                              >
                                  ${renderSourceIcon(
                                      msg(str`${type.name} Icon`),
                                      type.iconUrl,
                                      type.iconThemedUrls,
                                      this.activeTheme,
                                  )}
                              </div>
                          </div>`
                        : null
                }
                <div role="heading" aria-level="2" class="pf-c-card__title">${type.name}</div>
                <div class="pf-c-card__body" id=${`${inputID}-description`}>
                    ${type.description}
                </div>
                ${
                    disabled
                        ? html`<div class="pf-c-card__footer">
                              <ak-license-notice></ak-license-notice>
                          </div> `
                        : null
                }
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
                    @click=${() => this.#chooseListType(type)}
                    ?disabled=${disabled}
                    .checked=${selected}
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
                    ${
                        type.deprecated
                            ? html`<ak-alert class="pf-c-radio__description" inline plain>
                                  ${msg("This type is deprecated.")}
                              </ak-alert>`
                            : null
                    }
                </span>
            </label>`;
        });
    }

    protected renderBindChoices(): SlottedTemplateResult {
        if (!this.bindChoices) {
            return null;
        }

        const { label, description, options } = this.bindChoices;

        return html`<ak-form-group
            label=${label}
            description=${ifPresent(description)}
            part="group bind"
            open
        >
            ${options.map((option) => {
                const inputID = `bind-${option.value}`;
                const selected = this.selectedBind === option.value;

                return html`<label class="pf-c-radio" for=${inputID}>
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${inputID}
                        aria-label=${option.label}
                        aria-describedby=${`${inputID}-description`}
                        @click=${() => this.#chooseBind(option.value)}
                        .checked=${selected}
                    />
                    <div class="pf-c-radio__label">${option.label}</div>
                    <span id="${inputID}-description" class="pf-c-radio__description"
                        >${option.description}</span
                    >
                </label>`;
            })}
        </ak-form-group>`;
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
                class="pf-c-form pf-m-horizontal"
                role="radiogroup"
                aria-label=${ifPresent(this.headline)}
            >
                ${this.renderBindChoices()} ${content}
            </form>`,
        ];
    }

    //#endregion

    protected override render(): SlottedTemplateResult {
        const { layout, types, selectedType, bindChoices, selectedBind, activeTheme } = this;

        const content = guard(
            [layout, types, selectedType, bindChoices, selectedBind, activeTheme],
            () => {
                switch (layout) {
                    case TypeCreateWizardPageLayouts.grid:
                        return this.renderGrid();
                    case TypeCreateWizardPageLayouts.list:
                        return this.renderList();
                    default:
                        throw new TypeError(`Unknown layout: ${layout}`);
                }
            },
        );

        return content;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-page-type-create": TypeCreateWizardPage;
    }
}
