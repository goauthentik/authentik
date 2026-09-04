import "#components/ak-hidden-text-input";
import "#components/ak-radio-input";
import "#components/ak-text-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

import {
    PatchedSecretRequest,
    Secret,
    SecretRequest,
    SecretsApi,
    SecretTypeEnum,
} from "@goauthentik/api";

import { fromByteArray } from "base64-js";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-secret-form")
export class SecretForm extends ModelForm<Secret, string, SecretRequest> {
    public static override verboseName = msg("Secret", { id: "secret.verbose-name" });
    public static override verboseNamePlural = msg("Secrets", { id: "secret.verbose-name-plural" });

    @state()
    protected type: SecretTypeEnum = SecretTypeEnum.Text;

    protected endpoints = {
        load: (secretUuid: string) => aki(SecretsApi).secretsSecretsRetrieve({ secretUuid }),
        create: (data: SecretRequest) =>
            aki(SecretsApi).secretsSecretsCreate({
                secretRequest: data,
            }),
        update: (secretUuid: string, patchedSecretRequest: PatchedSecretRequest) =>
            aki(SecretsApi).secretsSecretsPartialUpdate({
                secretUuid,
                patchedSecretRequest,
            }),
    };

    protected override assignInstance(instance: Secret | null): void {
        super.assignInstance(instance);
        this.type = instance?.type ?? SecretTypeEnum.Text;
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated secret.", { id: "secret.form.success.update" })
            : msg("Successfully created secret.", { id: "secret.form.success.create" });
    }

    protected override async send(data: SecretRequest): Promise<unknown> {
        if (this.type === SecretTypeEnum.File) {
            const file = this.files<"value">().get("value");
            if (file) {
                data.value = fromByteArray(new Uint8Array(await file.arrayBuffer()));
            } else {
                delete data.value;
            }
        }
        return super.send(data);
    }

    protected renderValueInput(): TemplateResult {
        switch (this.type) {
            case SecretTypeEnum.Multiline:
                return html`<ak-form-element-horizontal
                    name="value"
                    ?required=${!this.instance}
                    label=${msg(this.instance ? "New value" : "Value", {
                        id: this.instance
                            ? "secret.form.new-value.label"
                            : "secret.form.value.label",
                    })}
                >
                    <ak-codemirror mode="yaml" raw ?required=${!this.instance}></ak-codemirror>
                    <p class="pf-c-form__helper-text">
                        ${msg("A multi-line value, such as a PEM key or JSON.", {
                            id: "secret.type.multiline.description",
                        })}
                    </p>
                </ak-form-element-horizontal>`;
            case SecretTypeEnum.File:
                return html`<ak-form-element-horizontal name="value" ?required=${!this.instance}>
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "secret-file-input",
                            required: !this.instance,
                        },
                        msg(this.instance ? "New file" : "File", {
                            id: this.instance
                                ? "secret.form.new-file.label"
                                : "secret.form.file.label",
                        }),
                    )}
                    <input
                        type="file"
                        class="pf-c-form-control"
                        id="secret-file-input"
                        ?required=${!this.instance}
                    />
                    <p class="pf-c-form__helper-text">
                        ${msg("The file's content is stored base64-encoded.", {
                            id: "secret.form.file.description",
                        })}
                    </p>
                </ak-form-element-horizontal>`;
            default:
                return html`<ak-hidden-text-input
                    label=${msg(this.instance ? "New value" : "Value", {
                        id: this.instance
                            ? "secret.form.new-value.label"
                            : "secret.form.value.label",
                    })}
                    name="value"
                    autocomplete="off"
                    input-hint="code"
                    help=${msg(
                        this.instance
                            ? "Leave empty to keep the current value."
                            : "Leave empty to generate a value. Set it only when the secret must match an existing value.",
                        {
                            id: this.instance
                                ? "secret.form.new-value.description"
                                : "secret.form.value.description",
                        },
                    )}
                ></ak-hidden-text-input>`;
        }
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                label=${msg("Name", { id: "secret.form.name.label" })}
                name="name"
                required
                value="${ifDefined(this.instance?.name)}"
                autofocus
                autocomplete="off"
                spellcheck="false"
            ></ak-text-input>
            ${this.instance
                ? nothing
                : html`<ak-radio-input
                      name="type"
                      label=${msg("Type", { id: "secret.form.type.label" })}
                      .value=${this.type}
                      .options=${[
                          {
                              label: msg("Text", { id: "secret.type.text.label" }),
                              value: SecretTypeEnum.Text,
                              default: true,
                              description: html`${msg(
                                  "A single-line value. Can be generated and rotated.",
                                  { id: "secret.type.text.description" },
                              )}`,
                          },
                          {
                              label: msg("Multi-line text", {
                                  id: "secret.type.multiline.label",
                              }),
                              value: SecretTypeEnum.Multiline,
                              description: html`${msg(
                                  "A multi-line value, such as a PEM key or JSON.",
                                  { id: "secret.type.multiline.description" },
                              )}`,
                          },
                          {
                              label: msg("File", { id: "secret.type.file.label" }),
                              value: SecretTypeEnum.File,
                              description: html`${msg("An uploaded file, stored base64-encoded.", {
                                  id: "secret.type.file.description",
                              })}`,
                          },
                      ]}
                      @input=${(ev: InputEvent) => {
                          const target = ev.target as HTMLElement & {
                              value?: SecretTypeEnum;
                          };
                          if (target.value) {
                              this.type = target.value;
                          }
                      }}
                  ></ak-radio-input> `}
            ${this.renderValueInput()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-form": SecretForm;
    }
}
