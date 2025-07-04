import { AkControlElement } from "@goauthentik/elements/AkControlElement.js";
import { type Spread } from "@goauthentik/elements/types";
import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, queryAll } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { MatchingModeEnum, RedirectURI } from "@goauthentik/api";

export interface IBackchannelLogoutURIInput {
    backchannelLogoutURI: RedirectURI;
}

@customElement("ak-provider-oauth2-backchannel-logout-uri")
export class OAuth2ProviderBackchannelLogoutURI extends AkControlElement<RedirectURI> {
    static get styles() {
        return [
            PFBase,
            PFInputGroup,
            PFFormControl,
            css`
                .pf-c-input-group select {
                    width: 10em;
                }
            `,
        ];
    }

    @property({ type: Object, attribute: false })
    backchannelLogoutURI: RedirectURI = {
        matchingMode: MatchingModeEnum.Strict,
        url: "",
    };

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
                    ?selected=${this.backchannelLogoutURI.matchingMode === MatchingModeEnum.Strict}
                >
                    ${msg("Strict")}
                </option>
                <option
                    value="${MatchingModeEnum.Regex}"
                    ?selected=${this.backchannelLogoutURI.matchingMode === MatchingModeEnum.Regex}
                >
                    ${msg("Regex")}
                </option>
            </select>
            <input
                type="text"
                @change=${onChange}
                value="${ifDefined(this.backchannelLogoutURI.url ?? undefined)}"
                class="pf-c-form-control ak-form-control pf-m-monospace"
                spellcheck="false"
                autocomplete="off"
                id="url"
                placeholder=${msg("Backchannel Logout URL")}
                name="url"
                tabindex="1"
            />
        </div>`;
    }
}

export function akOAuthBackchannelLogoutURIInput(properties: IBackchannelLogoutURIInput) {
    return html`<ak-provider-oauth2-backchannel-logout-uri
        ${spread(properties as unknown as Spread)}
    ></ak-provider-oauth2-backchannel-logout-uri>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-oauth2-backchannel-logout-uri": OAuth2ProviderBackchannelLogoutURI;
    }
}
