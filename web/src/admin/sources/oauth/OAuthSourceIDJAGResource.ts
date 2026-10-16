import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

import { AKControlElement } from "#elements/ControlElement";
import { ifPresent } from "#elements/utils/attributes";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";

/** One resource row of an OAuth source's ID-JAG resources, for `ak-array-input` */
@customElement("ak-source-oauth-id-jag-resource")
export class OAuthSourceIDJAGResource extends AKControlElement<string> {
    static styles = [PFInputGroup, PFFormControl];

    @property({ type: String })
    public resource = "";

    @property({ type: String, useDefault: true })
    public name = "";

    @query("input")
    protected input?: HTMLInputElement;

    toJSON(): string {
        return this.input?.value ?? this.resource;
    }

    get valid() {
        return true;
    }

    render() {
        return html`<div class="pf-c-input-group">
            <input
                type="url"
                @change=${() => {
                    this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
                }}
                value="${ifPresent(this.resource)}"
                class="pf-c-form-control pf-m-monospace"
                spellcheck="false"
                autocomplete="off"
                required
                placeholder=${msg("https://...", { id: "source.oauth.id-jag.resource.placeholder" })}
            />
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-oauth-id-jag-resource": OAuthSourceIDJAGResource;
    }
}
