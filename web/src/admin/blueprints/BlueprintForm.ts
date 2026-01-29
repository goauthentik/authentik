import "#components/ak-text-input";
import "#components/ak-toggle-group";
import "#components/ak-switch-input";
import "#elements/CodeMirror";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { docLink } from "#common/global";

import { ModelForm } from "#elements/forms/ModelForm";

import { BlueprintFile, BlueprintInstance, ManagedApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";

enum BlueprintSource {
    File = "file",
    OCI = "oci",
    Internal = "internal",
}

@customElement("ak-blueprint-form")
export class BlueprintForm extends ModelForm<BlueprintInstance, string> {
    @state()
    protected source: BlueprintSource = BlueprintSource.File;

    public override reset(): void {
        super.reset();

        this.source = BlueprintSource.File;
    }

    async loadInstance(pk: string): Promise<BlueprintInstance> {
        const inst = await new ManagedApi(DEFAULT_CONFIG).managedBlueprintsRetrieve({
            instanceUuid: pk,
        });
        if (inst.path?.startsWith("oci://")) {
            this.source = BlueprintSource.OCI;
        }
        if (inst.content !== "") {
            this.source = BlueprintSource.Internal;
        }
        return inst;
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated instance.")
            : msg("Successfully created instance.");
    }

    static styles: CSSResult[] = [...super.styles, PFContent];

    async send(data: BlueprintInstance): Promise<BlueprintInstance> {
        if (this.instance?.pk) {
            return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsUpdate({
                instanceUuid: this.instance.pk,
                blueprintInstanceRequest: data,
            });
        }
        return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsCreate({
            blueprintInstanceRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
                help=${msg("Disabled blueprints are never applied.")}
            >
            </ak-switch-input>
            <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">
                    <ak-toggle-group
                        value=${this.source}
                        @ak-toggle=${(ev: CustomEvent<{ value: BlueprintSource }>) => {
                            this.source = ev.detail.value;
                        }}
                    >
                        <option value=${BlueprintSource.File}>${msg("Local path")}</option>
                        <option value=${BlueprintSource.OCI}>${msg("OCI Registry")}</option>
                        <option value=${BlueprintSource.Internal}>${msg("Internal")}</option>
                    </ak-toggle-group>
                </div>
                <div class="pf-c-card__footer">
                    ${this.source === BlueprintSource.File
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
                                  .value=${(item: BlueprintFile | null) => {
                                      return item?.path;
                                  }}
                                  .selected=${(item: BlueprintFile): boolean => {
                                      return this.instance?.path === item.path;
                                  }}
                                  blankable
                              >
                              </ak-search-select>
                          </ak-form-element-horizontal>`
                        : nothing}
                    ${this.source === BlueprintSource.OCI
                        ? html` <ak-text-input
                              name="path"
                              label=${msg("OCI URL")}
                              input-hint="code"
                              required
                              placeholder="oci://..."
                              value="${ifDefined(this.instance?.path)}"
                              .bighelp=${html`<p class="pf-c-form__helper-text">
                                      ${msg(
                                          html` A valid OCI manifest URL, prefixed with the protocol
                                              e.g.&nbsp;<code
                                                  >oci://registry.domain.tld/path/to/manifest</code
                                              >`,
                                      )}
                                  </p>
                                  <p class="pf-c-form__helper-text">
                                      <span>
                                          ${msg("Read more about")}&nbsp;
                                          <a
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              href=${docLink(
                                                  "/customize/blueprints/#storage---oci",
                                              )}
                                              >${msg("OCI Support")}</a
                                          >.
                                      </span>
                                  </p> `}
                          >
                          </ak-text-input>`
                        : nothing}
                    ${this.source === BlueprintSource.Internal
                        ? html`<ak-form-element-horizontal label=${msg("Blueprint")} name="content">
                              <ak-codemirror
                                  mode="yaml"
                                  raw
                                  value="${ifDefined(this.instance?.content)}"
                              ></ak-codemirror>
                          </ak-form-element-horizontal>`
                        : nothing}
                </div>
            </div>

            <ak-form-group label="${msg("Additional settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Context")} name="context">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(this.instance?.context ?? {})}"
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-blueprint-form": BlueprintForm;
    }
}
