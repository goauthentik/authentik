import { BaseSourceForm } from "@goauthentik/admin/sources/BaseSourceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { SCIMSource, SCIMSourceRequest, SourcesApi } from "@goauthentik/api";

@customElement("ak-source-scim-form")
export class SCIMSourceForm extends BaseSourceForm<SCIMSource> {
    async loadInstance(pk: string): Promise<SCIMSource> {
        return new SourcesApi(DEFAULT_CONFIG)
            .sourcesScimRetrieve({
                slug: pk,
            })
            .then((source) => {
                return source;
            });
    }

    send = (data: SCIMSource): Promise<SCIMSource> => {
        if (this.instance?.slug) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesScimPartialUpdate({
                slug: this.instance.slug,
                patchedSCIMSourceRequest: data,
            });
        } else {
            return new SourcesApi(DEFAULT_CONFIG).sourcesScimCreate({
                sCIMSourceRequest: data as unknown as SCIMSourceRequest,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Slug")} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <label class="pf-c-check__label"> ${msg("Enabled")} </label>
                </div>
            </ak-form-element-horizontal>
        </form>`;
    }
}
