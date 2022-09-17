import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { BlueprintInstance, ManagedApi } from "@goauthentik/api";

@customElement("ak-blueprint-form")
export class BlueprintForm extends ModelForm<BlueprintInstance, string> {
    loadInstance(pk: string): Promise<BlueprintInstance> {
        return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsRetrieve({
            instanceUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated instance.");
        } else {
            return msg("Successfully created instance.");
        }
    }

    send = (data: BlueprintInstance): Promise<BlueprintInstance> => {
        if (this.instance?.pk) {
            return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsUpdate({
                instanceUuid: this.instance.pk,
                blueprintInstanceRequest: data,
            });
        } else {
            return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsCreate({
                blueprintInstanceRequest: data,
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
            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <label class="pf-c-check__label"> ${msg("Enabled")} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${msg("Disabled blueprints are never applied.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Path")} name="path">
                <select class="pf-c-form-control">
                    ${until(
                        new ManagedApi(DEFAULT_CONFIG)
                            .managedBlueprintsAvailableList()
                            .then((files) => {
                                return files.map((file) => {
                                    let name = file.path;
                                    if (file.meta && file.meta.name) {
                                        name = `${name} (${file.meta.name})`;
                                    }
                                    const selected = file.path === this.instance?.path;
                                    return html`<option ?selected=${selected} value=${file.path}>
                                        ${name}
                                    </option>`;
                                });
                            }),
                        html`<option>${msg("Loading...")}</option>`,
                    )}
                </select>
            </ak-form-element-horizontal>
            <ak-form-group>
                <span slot="header">${msg("Additional settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Context")} name="context">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(first(this.instance?.context, {}))}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Configure the blueprint context, used for templating.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
