import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

import { AKControlElement } from "#elements/ControlElement";
import { ifPresent } from "#elements/utils/attributes";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";

/** One email domain row of an OAuth source's ID-JAG email domains, for `ak-array-input` */
@customElement("ak-oauth-source-id-jag-email-domain")
export class OAuthSourceIDJAGEmailDomain extends AKControlElement<string> {
    static styles = [PFInputGroup, PFFormControl];

    @property({ type: String })
    public domain = "";

    @property({ type: String, useDefault: true })
    public name = "";

    @query("input")
    protected input?: HTMLInputElement;

    toJSON(): string {
        return this.input?.value ?? this.domain;
    }

    get valid() {
        return true;
    }

    render() {
        return html`<div class="pf-c-input-group">
            <input
                type="text"
                @change=${() => {
                    this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
                }}
                value="${ifPresent(this.domain)}"
                class="pf-c-form-control pf-m-monospace"
                spellcheck="false"
                autocomplete="off"
                required
                placeholder=${msg("example.com", {
                    id: "sources.oauth.id-jag.email-domain.placeholder",
                })}
            />
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-oauth-source-id-jag-email-domain": OAuthSourceIDJAGEmailDomain;
    }
}
