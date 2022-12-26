import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import YAML from "yaml";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFToggleGroup from "@patternfly/patternfly/components/ToggleGroup/toggle-group.css";

import { BlueprintInstance, ManagedApi } from "@goauthentik/api";

enum blueprintSource {
    local,
    oci,
}

@customElement("ak-blueprint-form")
export class BlueprintForm extends ModelForm<BlueprintInstance, string> {
    @state()
    source: blueprintSource = blueprintSource.local;

    loadInstance(pk: string): Promise<BlueprintInstance> {
        return new ManagedApi(DEFAULT_CONFIG)
            .managedBlueprintsRetrieve({
                instanceUuid: pk,
            })
            .then((inst) => {
                if (inst.path.startsWith("oci://")) {
                    this.source = blueprintSource.oci;
                }
                return inst;
            });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated instance.`;
        } else {
            return t`Successfully created instance.`;
        }
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFToggleGroup,
            PFContent,
            css`
                .pf-c-toggle-group {
                    justify-content: center;
                }
            `,
        );
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
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
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
                    <label class="pf-c-check__label"> ${t`Enabled`} </label>
                </div>
                <p class="pf-c-form__helper-text">${t`Disabled blueprints are never applied.`}</p>
            </ak-form-element-horizontal>
            <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">
                    <div class="pf-c-toggle-group">
                        <div class="pf-c-toggle-group__item">
                            <button
                                class="pf-c-toggle-group__button ${this.source ===
                                blueprintSource.local
                                    ? "pf-m-selected"
                                    : ""}"
                                type="button"
                                @click=${() => {
                                    this.source = blueprintSource.local;
                                }}
                            >
                                <span class="pf-c-toggle-group__text">${t`Local path`}</span>
                            </button>
                        </div>
                        <div class="pf-c-divider pf-m-vertical" role="separator"></div>
                        <div class="pf-c-toggle-group__item">
                            <button
                                class="pf-c-toggle-group__button ${this.source ===
                                blueprintSource.oci
                                    ? "pf-m-selected"
                                    : ""}"
                                type="button"
                                @click=${() => {
                                    this.source = blueprintSource.oci;
                                }}
                            >
                                <span class="pf-c-toggle-group__text">${t`OCI Registry`}</span>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="pf-c-card__footer">
                    ${this.source === blueprintSource.local
                        ? html`<ak-form-element-horizontal label=${t`Path`} name="path">
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
                                                  const selected =
                                                      file.path === this.instance?.path;
                                                  return html`<option
                                                      ?selected=${selected}
                                                      value=${file.path}
                                                  >
                                                      ${name}
                                                  </option>`;
                                              });
                                          }),
                                      html`<option>${t`Loading...`}</option>`,
                                  )}
                              </select></ak-form-element-horizontal
                          >`
                        : html``}
                    ${this.source === blueprintSource.oci
                        ? html`<ak-form-element-horizontal label=${t`URL`} name="path">
                              <input
                                  type="text"
                                  value="${ifDefined(this.instance?.path)}"
                                  class="pf-c-form-control"
                                  required
                              />
                              <p class="pf-c-form__helper-text">
                                  ${t`OCI URL, in the format of oci://registry.domain.tld/path/to/manifest.`}
                              </p>
                              <p class="pf-c-form__helper-text">
                                  ${t`See more about OCI support here:`}&nbsp;
                                  <a
                                      target="_blank"
                                      href="${docLink(
                                          "/developer-docs/blueprints/?utm_source=authentik#storage---oci",
                                      )}"
                                      >${t`Documentation`}</a
                                  >
                              </p>
                          </ak-form-element-horizontal>`
                        : html``}
                </div>
            </div>

            <ak-form-group>
                <span slot="header">${t`Additional settings`}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Context`} name="context">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(first(this.instance?.context, {}))}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${t`Configure the blueprint context, used for templating.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
