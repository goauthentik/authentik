import "#elements/forms/ConfirmationForm";

import { parseAPIResponseError } from "#common/errors/network";

import { AKElement } from "#elements/Base";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithLicenseSummary } from "#elements/mixins/license";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList, { DescriptionPair } from "#components/DescriptionList";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-reports-export-button")
export class ExportButton extends WithBrandConfig(WithLicenseSummary(AKElement)) {
    static styles: CSSResult[] = [PFButton, PFContent, PFDescriptionList];

    @property({ attribute: false })
    public createExport: ((params: { [key: string]: string }) => Promise<void>) | null = null;

    @property({ attribute: false })
    public exportParams: () => Promise<Record, string | undefined> = () => Promise.resolve({});

    @state()
    protected params: Record<string, string | undefined> = {};

    // safest display setting for a button
    cachedDisplay = "inline-block";

    // memoize what the button would be if it were visible:
    connectedCallback() {
        super.connectedCallback();
        const detectedDisplay = getComputedStyle(this).display;
        if (detectedDisplay) {
            this.cachedDisplay = detectedDisplay;
        }
    }

    // Take it out of the DOM flow if it's not enabled
    willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);
        this.style.display = this.hasEnterpriseLicense ? this.cachedDisplay : "none";
    }

    #clickHandler = () => {
        if (typeof this.createExport !== "function") {
            throw new TypeError("`createExport` property must be a function");
        }
        return this.createExport(this.params).catch(async (error) => {
            const apiError = await parseAPIResponseError(error);
            showAPIErrorMessage(apiError);
        });
    };

    render(): SlottedTemplateResult {
        if (!this.hasEnterpriseLicense) {
            return nothing;
        }
        return html`<ak-forms-confirm
            successMessage=${msg("Successfully requested data export")}
            errorMessage=${msg("Failed to export data")}
            .onConfirm=${this.#clickHandler}
            @ak-modal-show=${() => {
                this.exportParams().then((params) => {
                    this.params = params;
                });
            }}
            action=${msg("Start export")}
            actionLevel="pf-m-primary"
        >
            <span slot="header">${msg("Export data")}</span>
            <div slot="body">
                <p>
                    ${msg(
                        str`${this.brand.brandingTitle} will collect all objects with the specified parameters:`,
                    )}
                </p>
                <br />
                ${renderDescriptionList(
                    Object.keys(this.params)
                        .filter((key) => {
                            if (key === "page" || key === "pageSize") return false;

                            return !!this.params[key];
                        })
                        .map((key): DescriptionPair => {
                            return [key, html`<pre>${this.params[key]}</pre>`];
                        }),
                    { horizontal: true, compact: true },
                )}
            </div>
            <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                ${msg("Export")}
            </button>
            <div slot="modal"></div>
        </ak-forms-confirm> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-reports-export-button": ExportButton;
    }
}
