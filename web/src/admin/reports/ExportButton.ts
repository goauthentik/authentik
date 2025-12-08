import { parseAPIResponseError } from "../../common/errors/network";
import { MessageLevel } from "../../common/messages";
import { AKElement } from "../../elements/Base";
import { showAPIErrorMessage, showMessage } from "../../elements/messages/MessageContainer";
import { SlottedTemplateResult } from "../../elements/types";

import { WithLicenseSummary } from "#elements/mixins/license";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-reports-export-button")
export class ExportButton extends WithLicenseSummary(AKElement) {
    static styles: CSSResult[] = [PFBase, PFButton];

    @property({ attribute: false })
    public createExport!: () => Promise<void>;

    #clickHandler = () => {
        if (typeof this.createExport !== "function") {
            throw new TypeError("`createExport` property must be a function");
        }

        return this.createExport()
            .then(() => {
                showMessage({
                    level: MessageLevel.success,
                    message: msg("Data export requested successfully"),
                    description: msg("You will receive a notification once the data is ready"),
                });
            })
            .catch(async (error) => {
                const apiError = await parseAPIResponseError(error);
                showAPIErrorMessage(apiError);
            });
    };

    render(): SlottedTemplateResult {
        if (!this.hasEnterpriseLicense) {
            return nothing;
        }
        return html`<button @click=${this.#clickHandler} class="pf-c-button pf-m-secondary">
            ${msg("Export")}
        </button>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-reports-export-button": ExportButton;
    }
}
