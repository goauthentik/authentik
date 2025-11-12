import { parseAPIResponseError } from "../../common/errors/network";
import { MessageLevel } from "../../common/messages";
import { AKElement } from "../../elements/Base";
import { showAPIErrorMessage, showMessage } from "../../elements/messages/MessageContainer";
import { WithLicenseSummary } from "../../elements/mixins/license";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-reports-export-button")
export class ExportButton extends WithLicenseSummary(AKElement) {
    static styles: CSSResult[] = [PFBase, PFButton];

    @property()
    createExport: () => void = async () => {
        throw new Error("createExport not set");
    };

    async handleExportClick() {
        try {
            await this.createExport();
            showMessage({
                level: MessageLevel.success,
                message: msg("Data export requested successfully"),
                description: msg("You will receive a notification once the data is ready"),
            });
        } catch (error) {
            const apiError = await parseAPIResponseError(error);
            await showAPIErrorMessage(apiError);
        }
    }

    render(): TemplateResult {
        if (this.hasEnterpriseLicense) {
            return html` <button
                @click=${this.handleExportClick}
                class="pf-c-button pf-m-secondary"
            >
                ${msg("Export")}
            </button>`;
        } else {
            return html``;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-reports-export-button": ExportButton;
    }
}
