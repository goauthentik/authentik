import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { UserSetting } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

export abstract class BaseUserSettings extends AKElement {
    static styles: CSSResult[] = [PFButton, PFForm, PFFormControl];

    @property({ attribute: false })
    public source: UserSetting | null = null;

    @property({ type: Number, attribute: "connection-pk" })
    public connectionPk = -1;

    @property({ type: Boolean, attribute: "allow-configuration" })
    public allowConfiguration = false;

    public get configureURL(): string | null {
        return this.allowConfiguration && this.source?.configureUrl
            ? this.source.configureUrl
            : null;
    }

    public get title(): string {
        return this.source?.title ?? "";
    }

    public get objectId(): string {
        return this.source?.objectUid ?? "";
    }

    /**
     * Disconnects the source from the user.
     */
    protected abstract disconnectSource(): Promise<void>;

    protected renderConnectButton?(): SlottedTemplateResult;

    protected renderDisconnectButton(): SlottedTemplateResult {
        if (this.connectionPk !== -1) {
            return html`<button
                class="pf-c-button pf-m-danger"
                @click=${() => this.disconnectSource()}
            >
                ${msg("Disconnect")}
            </button>`;
        }

        if (this.renderConnectButton) {
            return this.renderConnectButton();
        }

        return html`<span aria-hidden="true">${msg("-")}</span>`;
    }

    public render(): unknown {
        return this.renderDisconnectButton();
    }
}
