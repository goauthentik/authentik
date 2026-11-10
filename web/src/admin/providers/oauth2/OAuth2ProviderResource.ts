import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

import { AKControlElement } from "#elements/ControlElement";
import { ifPresent } from "#elements/utils/attributes";

import { msg } from "@lit/localize";
import { html, LitElement } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * A single allowed resource (RFC 8707) of an OAuth2 provider, as a row of `ak-array-input`.
 */
@customElement("ak-provider-oauth2-resource")
export class OAuth2ProviderResource extends AKControlElement<string> {
    static shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };

    static styles = [PFFormControl];

    @property({ type: String, attribute: false })
    public resource = "";

    @property({ type: String, useDefault: true })
    public name = "";

    @property({ type: String, attribute: "input-id" })
    public inputID?: string;

    @query("input")
    protected input?: HTMLInputElement;

    toJSON(): string {
        return this.input?.value ?? this.resource;
    }

    get valid() {
        return true;
    }

    render() {
        const onChange = () => {
            this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
        };

        return html`<input
            type="text"
            inputmode="url"
            @change=${onChange}
            value="${ifPresent(this.resource)}"
            class="pf-c-form-control pf-m-monospace"
            spellcheck="false"
            autocomplete="off"
            required
            id=${ifDefined(this.inputID)}
            placeholder=${msg("https://...", { id: "provider.oauth2.allowed-resources.placeholder" })}
            aria-label=${msg("Resource URI", {
                id: "provider.oauth2.allowed-resources.aria-label",
            })}
        />`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-oauth2-resource": OAuth2ProviderResource;
    }
}
