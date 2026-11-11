import "#components/ak-radio-input";
import "#components/ak-text-input";
import "#components/ak-textarea-input";
import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { reportInvalidFields } from "#elements/forms/errors";
import { Form } from "#elements/forms/Form";
import { PreventFormSubmit } from "#elements/forms/helpers";
import { SlottedTemplateResult } from "#elements/types";

import {
    ApplicationTemplate,
    ClientTypeEnum,
    GrantTypeEnum,
    RequestedApplicationRequest,
    RequestsApi,
    ResponseError,
    ValidationError,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

/** The form's fields; redirect URIs arrive as one per line. */
type RequestApplicationFormData = Omit<RequestedApplicationRequest, "redirectUris"> & {
    redirectUris?: string;
};

@customElement("ak-request-application-form")
export class RequestApplicationForm extends Form<RequestApplicationFormData> {
    public static override createLabel = msg("Request application", {
        id: "requests.request-application.create-label",
    });
    public static override submitVerb = msg("Request", {
        id: "requests.request-application.submit-verb",
    });

    @property({ attribute: false })
    public template: ApplicationTemplate | null = null;

    protected override async send(data: RequestApplicationFormData): Promise<unknown> {
        const application: RequestedApplicationRequest = {
            ...data,
            redirectUris: (data.redirectUris ?? "")
                .split("\n")
                .map((uri) => uri.trim())
                .filter(Boolean),
        };

        try {
            const { link } = await aki(RequestsApi).requestsGrantRequestsCreate({
                grantRequestCreateRequest: { pbms: [this.template?.pbmUuid ?? ""], application },
            });

            if (link) {
                window.location.assign(link);
            }

            return link;
        } catch (error) {
            await this.#reportApplicationErrors(error);

            throw error;
        }
    }

    /**
     * The API nests errors about the requested application under `application`, while this form's
     * fields are named after the application's own fields. Point each error at its field.
     */
    async #reportApplicationErrors(error: unknown): Promise<void> {
        if (!(error instanceof ResponseError) || error.response.status !== 400) {
            return;
        }

        // Clone: the form reads the original body again to report everything else.
        const body: { application?: ValidationError } = await error.response.clone().json();

        if (!body.application || typeof body.application !== "object") {
            return;
        }

        const invalidFields = reportInvalidFields(
            body.application,
            this.renderRoot.querySelectorAll("ak-form-element-horizontal"),
        );

        if (invalidFields.length) {
            throw new PreventFormSubmit(
                msg("Correct the highlighted fields.", {
                    id: "requests.request-application.invalid-fields.error",
                }),
            );
        }
    }

    protected override formatHeadline(): string {
        return msg(str`Request a new application from ${this.template?.name ?? ""}`, {
            id: "requests.request-application.header",
        });
    }

    protected override renderForm(): SlottedTemplateResult {
        const grantTypes = this.template?.allowedGrantTypes ?? [];

        return html`<ak-text-input
                label=${msg("Name", { id: "requests.requested-application.name.label" })}
                name="name"
                required
            ></ak-text-input>
            <ak-radio-input
                label=${msg("Client type", {
                    id: "requests.requested-application.client-type.label",
                })}
                name="clientType"
                required
                .value=${ClientTypeEnum.Confidential}
                .options=${[
                    {
                        label: msg("Confidential", {
                            id: "requests.request-application.client-type.confidential.label",
                        }),
                        value: ClientTypeEnum.Confidential,
                        description: html`${msg(
                            "The application runs on a server and can keep a client secret.",
                            {
                                id: "requests.request-application.client-type.confidential.description",
                            },
                        )}`,
                    },
                    {
                        label: msg("Public", {
                            id: "requests.request-application.client-type.public.label",
                        }),
                        value: ClientTypeEnum.Public,
                        description: html`${msg(
                            "The application runs in a browser or on a device and cannot keep a secret.",
                            {
                                id: "requests.request-application.client-type.public.description",
                            },
                        )}`,
                    },
                ]}
            ></ak-radio-input>
            <ak-form-element-horizontal
                label=${msg("Grant types", {
                    id: "requests.requested-application.grant-types.label",
                })}
                required
                name="grantTypes"
            >
                <ak-checkbox-group
                    name="grantTypes"
                    .options=${grantTypes.map((grantType) => [grantType, grantType])}
                    .value=${
                        grantTypes.includes(GrantTypeEnum.AuthorizationCode)
                            ? [GrantTypeEnum.AuthorizationCode]
                            : []
                    }
                ></ak-checkbox-group>
            </ak-form-element-horizontal>
            <ak-textarea-input
                label=${msg("Redirect URIs", {
                    id: "requests.requested-application.redirect-uris.label",
                })}
                name="redirectUris"
                help=${msg(
                    "One per line, matched exactly. Needed for authorization_code, implicit and hybrid.",
                    { id: "requests.request-application.redirect-uris.help" },
                )}
            ></ak-textarea-input>
            <ak-form-element-horizontal
                label=${msg("Groups given access", {
                    id: "requests.requested-application.groups.label",
                })}
                required
                name="groups"
            >
                <ak-checkbox-group
                    name="groups"
                    .options=${(this.template?.bindableGroupsObj ?? []).map((group) => [
                        group.pk,
                        group.name,
                    ])}
                ></ak-checkbox-group>
            </ak-form-element-horizontal>
            <ak-text-input
                label=${msg("Launch URL", {
                    id: "requests.requested-application.launch-url.label",
                })}
                name="metaLaunchUrl"
                help=${msg("Where the application's tile in the library links to. Optional.", {
                    id: "requests.request-application.launch-url.help",
                })}
            ></ak-text-input>
            <ak-textarea-input
                label=${msg("Description", {
                    id: "requests.requested-application.description.label",
                })}
                name="metaDescription"
            ></ak-textarea-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-request-application-form": RequestApplicationForm;
    }
}
