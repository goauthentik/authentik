import "#admin/providers/oauth2/OAuth2ProviderRedirectURI";

import { AkControlElement } from "#elements/AkControlElement";
import { LitPropertyRecord } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { MatchingModeEnum, RedirectURI, RedirectUriTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, queryAll } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

export type RedirectURIProperties = LitPropertyRecord<{
    redirectURI: RedirectURI;
}> & {
    style?: string;
    name: string;
};

@customElement("ak-provider-oauth2-redirect-uri")
export class OAuth2ProviderRedirectURI extends AkControlElement<RedirectURI> {
    static styles = [
        PFInputGroup,
        PFFormControl,
        css`
            .pf-c-input-group select {
                width: 10em;
            }
        `,
    ];

    @property({ type: Object, attribute: false })
    public redirectURI: RedirectURI = {
        matchingMode: MatchingModeEnum.Strict,
        url: "",
        redirectUriType: RedirectUriTypeEnum.Authentication,
    };

    @property({ type: String, useDefault: true })
    public name = "";

    @property({ type: String, attribute: "input-id" })
    public inputID?: string;

    @queryAll(".ak-form-control")
    controls?: HTMLInputElement[];

    json() {
        return Object.fromEntries(
            Array.from(this.controls ?? []).map((control) => [control.name, control.value]),
        ) as unknown as RedirectURI;
    }

    get isValid() {
        return true;
    }

    render() {
        const onChange = () => {
            this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
        };

        return html`<div class="pf-c-input-group">
            <select
                name="matchingMode"
                class="pf-c-form-control ak-form-control"
                @change=${onChange}
            >
                <option
                    value="${MatchingModeEnum.Strict}"
                    ?selected=${this.redirectURI.matchingMode === MatchingModeEnum.Strict}
                >
                    ${msg("Strict")}
                </option>
                <option
                    value="${MatchingModeEnum.Regex}"
                    ?selected=${this.redirectURI.matchingMode === MatchingModeEnum.Regex}
                >
                    ${msg("Regex")}
                </option>
            </select>
            <select
                name="redirectUriType"
                class="pf-c-form-control ak-form-control"
                @change=${onChange}
            >
                <option
                    value="${RedirectUriTypeEnum.Authentication}"
                    ?selected=${(this.redirectURI.redirectUriType ??
                        RedirectUriTypeEnum.Authentication) === RedirectUriTypeEnum.Authentication}
                >
                    ${msg("Authentication")}
                </option>
                <option
                    value="${RedirectUriTypeEnum.PostLogout}"
                    ?selected=${this.redirectURI.redirectUriType === RedirectUriTypeEnum.PostLogout}
                >
                    ${msg("Post Logout")}
                </option>
            </select>
            <input
                type="text"
                @change=${onChange}
                value="${ifPresent(this.redirectURI.url)}"
                class="pf-c-form-control ak-form-control pf-m-monospace"
                spellcheck="false"
                autocomplete="off"
                required
                id=${ifDefined(this.inputID)}
                placeholder=${msg("URL")}
                name="url"
                tabindex="1"
            />
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-oauth2-redirect-uri": OAuth2ProviderRedirectURI;
    }
}
