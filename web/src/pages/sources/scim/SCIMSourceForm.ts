import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { SCIMSource, SCIMSourceRequest, SourcesApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/CodeMirror";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";
import { first } from "../../../utils";

@customElement("ak-source-scim-form")
export class SCIMSourceForm extends ModelForm<SCIMSource, string> {
    loadInstance(pk: string): Promise<SCIMSource> {
        return new SourcesApi(DEFAULT_CONFIG)
            .sourcesScimRetrieve({
                slug: pk,
            })
            .then((source) => {
                return source;
            });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated source.`;
        } else {
            return t`Successfully created source.`;
        }
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
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Slug`} ?required=${true} name="slug">
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
                    <label class="pf-c-check__label"> ${t`Enabled`} </label>
                </div>
            </ak-form-element-horizontal>
        </form>`;
    }
}
