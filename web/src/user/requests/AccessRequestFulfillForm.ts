import "#components/ak-text-input";
import "#elements/CodeMirror/ak-codemirror";
import "#components/ak-radio-input";

import { aki } from "#common/api/client";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import {
    GrantRequest,
    PatchedGrantRequestFulfillRequest,
    RequestsApi,
    RequestStatus,
} from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-access-request-fulfill-form")
export class AccessRequestFulfillForm extends Form<PatchedGrantRequestFulfillRequest> {
    @property({ type: Object })
    request?: GrantRequest;

    public static override createLabel = msg("Fulfill request");
    public static submitVerb: string = msg("Submit");

    protected async send(data: PatchedGrantRequestFulfillRequest): Promise<unknown> {
        return aki(RequestsApi).requestsGrantRequestsFulfillPartialUpdate({
            uuid: this.request?.uuid || "",
            patchedGrantRequestFulfillRequest: data,
        });
    }

    protected renderForm(): SlottedTemplateResult | null {
        return html`
            <ak-text-input
                label=${msg("Requester")}
                required
                readonly
                value="${ifDefined(this.request?.createdBy.username)}"
            ></ak-text-input>
            <ak-radio-input
                label=${msg("Status")}
                required
                name="status"
                .options=${[
                    {
                        label: msg("Approved"),
                        value: RequestStatus.Approved,
                        default: true,
                    },
                    {
                        label: msg("Denied"),
                        value: RequestStatus.Denied,
                    },
                ]}
            ></ak-radio-input>
            <ak-form-element-horizontal label=${msg("Note")} name="data">
                <ak-codemirror mode="yaml" value="${YAML.stringify({})}"> </ak-codemirror>
            </ak-form-element-horizontal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-access-request-fulfill-form": AccessRequestFulfillForm;
    }
}
