import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-toggle-group";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";

import { BlueprintFile, BlueprintInstance, ManagedApi } from "@goauthentik/api";

enum blueprintSource {
    file = "file",
    oci = "oci",
    internal = "internal",
}

@customElement("ak-blueprint-form")
export class BlueprintForm extends ModelForm<BlueprintInstance, string> {
    @state()
    source: blueprintSource = blueprintSource.file;

    async loadInstance(pk: string): Promise<BlueprintInstance> {
        const inst = await new ManagedApi(DEFAULT_CONFIG).managedBlueprintsRetrieve({
            instanceUuid: pk,
        });
        if (inst.path?.startsWith("oci://")) {
            this.source = blueprintSource.oci;
        }
        if (inst.content !== "") {
            this.source = blueprintSource.internal;
        }
        return inst;
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated instance.");
        } else {
            return msg("Successfully created instance.");
        }
    }

    static get styles(): CSSResult[] {
        return [...super.styles, PFContent];
    }

    async send(data: BlueprintInstance): Promise<BlueprintInstance> {
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
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Enabled")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("Disabled blueprints are never applied.")}
                </p>
            </ak-form-element-horizontal>
            <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">
                    <ak-toggle-group
                        value=${this.source}
                        @ak-toggle=${(ev: CustomEvent<{ value: blueprintSource }>) => {
                            this.source = ev.detail.value;
                        }}
                    >
                        <option value=${blueprintSource.file}>${msg("Local path")}</option>
                        <option value=${blueprintSource.oci}>${msg("OCI Registry")}</option>
                        <option value=${blueprintSource.internal}>${msg("Internal")}</option>
                    </ak-toggle-group>
                </div>
                <div class="pf-c-card__footer">
                    ${this.source === blueprintSource.file
                        ? html`<ak-form-element-horizontal label=${msg("Path")} name="path">
                              <ak-search-select
                                  .fetchObjects=${async (
                                      query?: string,
                                  ): Promise<BlueprintFile[]> => {
                                      const items = await new ManagedApi(
                                          DEFAULT_CONFIG,
                                      ).managedBlueprintsAvailableList();
                                      return items.filter((item) =>
                                          query ? item.path.includes(query) : true,
                                      );
                                  }}
                                  .renderElement=${(item: BlueprintFile): string => {
                                      const name = item.path;
                                      if (item.meta && item.meta.name) {
                                          return `${name} (${item.meta.name})`;
                                      }
                                      return name;
                                  }}
                                  .value=${(
                                      item: BlueprintFile | undefined,
                                  ): string | undefined => {
                                      return item?.path;
                                  }}
                                  .selected=${(item: BlueprintFile): boolean => {
                                      return this.instance?.path === item.path;
                                  }}
                                  ?blankable=${true}
                              >
                              </ak-search-select>
                          </ak-form-element-horizontal>`
                        : html``}
                    ${this.source === blueprintSource.oci
                        ? html`<ak-form-element-horizontal label=${msg("URL")} name="path">
                              <input
                                  type="text"
                                  value="${ifDefined(this.instance?.path)}"
                                  class="pf-c-form-control"
                                  required
                              />
                              <p class="pf-c-form__helper-text">
                                  ${msg(
                                      "OCI URL, in the format of oci://registry.domain.tld/path/to/manifest.",
                                  )}
                              </p>
                              <p class="pf-c-form__helper-text">
                                  ${msg("See more about OCI support here:")}&nbsp;
                                  <a
                                      target="_blank"
                                      href="${docLink(
                                          "/developer-docs/blueprints/?utm_source=authentik#storage---oci",
                                      )}"
                                      >${msg("Documentation")}</a
                                  >
                              </p>
                          </ak-form-element-horizontal>`
                        : html``}
                    ${this.source === blueprintSource.internal
                        ? html`<ak-form-element-horizontal label=${msg("Blueprint")} name="content">
                              <ak-codemirror
                                  mode="yaml"
                                  .parseValue=${false}
                                  value="${ifDefined(this.instance?.content)}"
                              ></ak-codemirror>
                          </ak-form-element-horizontal>`
                        : html``}
                </div>
            </div>

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
            </ak-form-group>`;
    }
}
