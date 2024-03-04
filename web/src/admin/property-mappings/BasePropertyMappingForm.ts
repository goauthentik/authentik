import { docLink } from "@goauthentik/common/global";
import "@goauthentik/components/ak-text-input";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import type {
    LDAPSourcePropertyMapping,
    NotificationWebhookMapping,
    OAuthSourcePropertyMapping,
    SAMLPropertyMapping,
    SAMLSourcePropertyMapping,
    SCIMMapping,
    ScopeMapping,
} from "@goauthentik/api";

// This is the sort of nonsense that you need to coerce Typescript into accepting, "No, really, they
// *say* they're all unique, but they have a base class, we just don't have access to it."

type TBase = Extract<
    | LDAPSourcePropertyMapping
    | NotificationWebhookMapping
    | OAuthSourcePropertyMapping
    | SAMLPropertyMapping
    | SAMLSourcePropertyMapping
    | SAMLSourcePropertyMapping
    | SCIMMapping
    | ScopeMapping,
    { name: string; expression: string }
>;

export abstract class BasePropertyMappingForm<T extends TBase> extends ModelForm<T, string> {
    getSuccessMessage() {
        return this.instance
            ? msg("Successfully updated mapping.")
            : msg("Successfully created mapping.");
    }

    renderForm() {
        return html` <ak-text-input
                name="name"
                label=${msg("Name")}
                required
                value="${ifDefined(this.instance?.name)}"
            ></ak-text-input>
            <ak-form-element-horizontal
                label=${msg("Expression")}
                ?required=${true}
                name="expression"
            >
                <ak-codemirror
                    mode=${CodeMirrorMode.Python}
                    value="${ifDefined(this.instance?.expression)}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Expression using Python.")}
                    <a
                        target="_blank"
                        href="${docLink("/docs/property-mappings/expression?utm_source=authentik")}"
                    >
                        ${msg("See documentation for a list of all variables.")}
                    </a>
                </p>
            </ak-form-element-horizontal>`;
    }
}
