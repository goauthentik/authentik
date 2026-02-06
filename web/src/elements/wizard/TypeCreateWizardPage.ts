import "#admin/common/ak-license-notice";
import "#elements/Alert";

import { ResolvedUITheme } from "#common/theme";
import { WithLicenseSummary } from "#elements/mixins/license";
import { FontAwesomeProtocol } from "#elements/utils/images";
import { WizardPage } from "#elements/wizard/WizardPage";

import { TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

import PFFAIcons from "@patternfly/patternfly/base/patternfly-fa-icons.css";
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

    @property({ attribute: false })
    types: TypeCreate[] = [];

    @property({ attribute: false })
    public selectedType: TypeCreate | null = null;

    @property({ type: String })
    layout: TypeCreateWizardPageLayouts = TypeCreateWizardPageLayouts.list;

    //#endregion

    static styles: CSSResult[] = [
        PFFAIcons,
        PFForm,
        PFGrid,
        PFRadio,
        PFCard,
        PFPage,
        css`
            .pf-c-card__header-main img {
                max-height: 2em;
                min-height: 2em;
            }
            .pf-c-card__header-main .font-awesome {
                font-size: 2em;
                line-height: 1;
            }
            :host([theme="dark"]) .pf-c-card__header-main .font-awesome {
                filter: invert(1);
            }
            .pf-c-page__main-section {
                margin-bottom: 2rem;
            }
        `,
    ];

    //#region Refs

    formRef: Ref<HTMLFormElement> = createRef();

    //#endregion

    public override label = msg("Select type");

    public reset = () => {
        super.reset();

        this.selectedType = null;
        this.formRef.value?.reset();
    };

    public override activeCallback = (): void => {
        const form = this.formRef.value;

        this.host.isValid = form?.checkValidity() ?? false;

        if (this.selectedType) {
            this.#selectDispatch(this.selectedType);
        }
    };

    #selectDispatch = (type: TypeCreate) => {
        this.dispatchEvent(
            new CustomEvent("select", {
                detail: type,
                bubbles: true,
                composed: true,
            }),
        );
    };

    #resolveTypeIcon(type: TypeCreate, theme: ResolvedUITheme): string | undefined {
        if (theme && type.iconThemedUrls?.[theme]) {
            return type.iconThemedUrls[theme];
        }
        return type.iconUrl ?? undefined;
    }

    protected renderGrid(): TemplateResult {
        return html`${this.hasSlotted("above-form")
                ? html`<div class="pf-c-page__main-section"><slot name="above-form"></slot></div>`
                : nothing}
            <div
                role="listbox"
                aria-label="${msg("Select a provider type")}"
                class="pf-l-grid pf-m-gutter"
                data-ouid-component-type="ak-type-create-grid"
            >
                ${this.types.map((type, idx) => {
                    const disabled = !!(type.requiresEnterprise && !this.hasEnterpriseLicense);
                    const resolvedIcon = this.#resolveTypeIcon(type, this.activeTheme);

                    const selected = this.selectedType === type;

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
                        aria-disabled="${disabled ? "true" : "false"}"
                        aria-selected="${selected ? "true" : "false"}"
                        aria-label="${type.name}"
                        aria-describedby="${type.description}"
                        @click=${() => {
                            if (disabled) return;

                            this.#selectDispatch(type);
                            this.selectedType = type;
                        }}
                    >
                        ${resolvedIcon
                            ? html`<div role="presentation" class="pf-c-card__header">
                                  <div role="presentation" class="pf-c-card__header-main">
                                      ${resolvedIcon.startsWith(FontAwesomeProtocol)
                                          ? html`<i
                                                aria-hidden="true"
                                                class="font-awesome fas ${resolvedIcon.slice(
                                                    FontAwesomeProtocol.length,
                                                )}"
                                            ></i>`
                                          : html`<img
                                                aria-hidden="true"
                                                src=${resolvedIcon}
                                                alt=${msg(str`${type.name} Icon`)}
                                            />`}
                                  </div>
                              </div>`
                            : nothing}
                        <div role="heading" aria-level="2" class="pf-c-card__title">
                            ${type.name}
                        </div>
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
        return html`${this.hasSlotted("above-form")
                ? html`<div class="pf-c-page__main-section"><slot name="above-form"></slot></div>`
                : nothing}
            <form
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
                                this.#selectDispatch(type);
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
                            ${type.deprecated
                                ? html`<ak-alert class="pf-c-radio__description" inline plain>
                                      ${msg("This type is deprecated.")}
                                  </ak-alert>`
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
                throw new TypeError(`Unknown layout: ${this.layout}`);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-page-type-create": TypeCreateWizardPage;
    }
}
