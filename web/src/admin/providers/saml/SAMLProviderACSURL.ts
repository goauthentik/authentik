import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

import { AKControlElement } from "#elements/ControlElement";
import { ifPresent } from "#elements/utils/attributes";

import { MatchingModeEnum, SAMLACSURL } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html, LitElement } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * A single Assertion Consumer Service URL of a SAML provider, rendered as a row of
 * {@linkcode ArrayInput}.
 */
@customElement("ak-provider-saml-acs-url")
export class SAMLProviderACSURL extends AKControlElement<SAMLACSURL> {
    static shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };

    static styles = [
        PFInputGroup,
        PFFormControl,
        css`
            .pf-c-input-group select {
                width: 10em;
            }
            .pf-c-input-group input[name="index"] {
                width: 7em;
            }
            .pf-c-input-group__text {
                white-space: nowrap;
                gap: var(--pf-global--spacer--xs);
            }
        `,
    ];

    @property({ type: Object, attribute: false })
    public acsURL: SAMLACSURL = {
        matchingMode: MatchingModeEnum.Strict,
        url: "",
        index: null,
        isDefault: false,
    };

    @property({ type: String, useDefault: true })
    public name = "";

    @property({ type: String, attribute: "input-id" })
    public inputID?: string;

    @query("[name=matchingMode]")
    protected matchingModeInput?: HTMLSelectElement;

    @query("[name=url]")
    protected urlInput?: HTMLInputElement;

    @query("[name=index]")
    protected indexInput?: HTMLInputElement;

    @query("[name=isDefault]")
    protected isDefaultInput?: HTMLInputElement;

    toJSON(): SAMLACSURL {
        const matchingMode = (this.matchingModeInput?.value ??
            this.acsURL.matchingMode ??
            MatchingModeEnum.Strict) as MatchingModeEnum;

        const strict = matchingMode === MatchingModeEnum.Strict;
        const index = this.indexInput?.value ?? "";

        return {
            matchingMode,
            url: this.urlInput?.value ?? this.acsURL.url,
            // Only strict URLs can be addressed by index or be the default
            index: strict && index !== "" ? parseInt(index, 10) : null,
            isDefault: strict && (this.isDefaultInput?.checked ?? false),
        };
    }

    get valid() {
        return this.urlInput?.checkValidity() ?? true;
    }

    render() {
        const strict =
            (this.acsURL.matchingMode ?? MatchingModeEnum.Strict) === MatchingModeEnum.Strict;

        const onChange = () => {
            this.acsURL = this.toJSON();
            this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
        };

        return html`<div class="pf-c-input-group">
            <select
                name="matchingMode"
                class="pf-c-form-control ak-form-control"
                aria-label=${msg("Matching mode", {
                    id: "provider.saml.acs-url.matching-mode.aria-label",
                })}
                @change=${onChange}
            >
                <option value="${MatchingModeEnum.Strict}" ?selected=${strict}>
                    ${msg("Strict")}
                </option>
                <option value="${MatchingModeEnum.Regex}" ?selected=${!strict}>
                    ${msg("Regex")}
                </option>
            </select>
            <input
                type="text"
                @change=${onChange}
                value="${ifPresent(this.acsURL.url)}"
                class="pf-c-form-control ak-form-control pf-m-monospace"
                spellcheck="false"
                autocomplete="off"
                inputmode="url"
                required
                id=${ifDefined(this.inputID)}
                placeholder=${
                    strict
                        ? msg("https://...")
                        : msg("Regular expression", {
                              id: "provider.saml.acs-url.regex.placeholder",
                          })
                }
                aria-label=${msg("ACS URL")}
                name="url"
                tabindex="1"
            />
            <input
                type="number"
                min="0"
                step="1"
                @change=${onChange}
                .value=${strict ? String(this.acsURL.index ?? "") : ""}
                ?disabled=${!strict}
                class="pf-c-form-control ak-form-control"
                placeholder=${msg("Index", { id: "provider.saml.acs-url.index.placeholder" })}
                aria-label=${msg("Index", { id: "provider.saml.acs-url.index.aria-label" })}
                name="index"
            />
            <label class="pf-c-input-group__text">
                <input
                    type="checkbox"
                    name="isDefault"
                    .checked=${strict && !!this.acsURL.isDefault}
                    ?disabled=${!strict}
                    @change=${onChange}
                />
                ${msg("Default", { id: "provider.saml.acs-url.default.label" })}
            </label>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-acs-url": SAMLProviderACSURL;
    }
}
