import "#components/ak-secret-textarea-input";
import "#components/ak-radio-input";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/Alert";
import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";
import type { AkRadioInput } from "#components/ak-radio-input";

import {
    PatchedSecretRequest,
    Secret,
    SecretRequest,
    SecretsApi,
    SecretTypeEnum,
} from "@goauthentik/api";

import { fromByteArray } from "base64-js";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

export function secretTypeLabel(type: SecretTypeEnum): string {
    switch (type) {
        case SecretTypeEnum.Json:
            return msg("JSON", { id: "secret.type.json.label" });
        case SecretTypeEnum.File:
            return msg("File", { id: "secret.type.file.label" });
        default:
            return msg("Text", { id: "secret.type.text.label" });
    }
}

function secretTypeDescription(type: SecretTypeEnum): string {
    switch (type) {
        case SecretTypeEnum.Json:
            return msg("A JSON or YAML object, such as a service account key or kubeconfig.", {
                id: "secret.type.json.description",
            });
        case SecretTypeEnum.File:
            return msg("An uploaded file, such as a Kerberos keytab.", {
                id: "secret.type.file.description",
            });
        default:
            return msg("A password, token, or key. Can be generated and rotated.", {
                id: "secret.type.text.description",
            });
    }
}

@customElement("ak-secret-form")
export class SecretForm extends ModelForm<Secret, string, SecretRequest> {
    public static override verboseName = msg("Secret", { id: "secret.verbose-name" });
    public static override verboseNamePlural = msg("Secrets", { id: "secret.verbose-name-plural" });

    public override size = PFSize.Medium;

    @property({ attribute: false })
    public types: SecretTypeEnum[] = [
        SecretTypeEnum.Text,
        SecretTypeEnum.Json,
        SecretTypeEnum.File,
    ];

    protected override willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);

        if (changed.has("types") && !this.instance) {
            this.type = this.types[0];
        }
    }

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

    protected override async send(data: SecretRequest): Promise<unknown> {
        data.type = this.type;

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
        if (this.type === SecretTypeEnum.File) {
            return html`<ak-form-element-horizontal name="value" ?required=${!this.instance}>
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "secret-file-input",
                        required: !this.instance,
                    },
                    this.instance
                        ? msg("New file", { id: "secret.form.new-file.label" })
                        : msg("File", { id: "secret.form.file.label" }),
                )}
                <input
                    type="file"
                    class="pf-c-form-control"
                    id="secret-file-input"
                    ?required=${!this.instance}
                />
                ${
                    this.instance
                        ? html`<p class="pf-c-form__helper-text">
                              ${msg("Leave empty to keep the current file.", {
                                  id: "secret.form.new-file.description",
                              })}
                          </p>`
                        : nothing
                }
            </ak-form-element-horizontal>`;
        }

        let help = msg("Leave empty to keep the current value.", {
            id: "secret.form.new-value.description",
        });

        if (!this.instance) {
            help =
                this.type === SecretTypeEnum.Text
                    ? msg("Leave empty to generate a value.", {
                          id: "secret.form.value.generate.description",
                      })
                    : msg("A JSON or YAML object.", { id: "secret.form.value.json.description" });
        }

        return html`<ak-secret-textarea-input
            name="value"
            label=${
                this.instance
                    ? msg("New value", { id: "secret.form.new-value.label" })
                    : msg("Value", { id: "secret.form.value.label" })
            }
            help=${help}
            input-hint="code"
            ?revealed=${!this.instance}
            ?required=${!this.instance && this.type === SecretTypeEnum.Json}
        ></ak-secret-textarea-input>`;
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-alert inline level="pf-m-warning">
                ${msg(
                    "authentik does not encrypt secret values in the database. Protect access to your database and its backups.",
                    { id: "secret.form.storage.description" },
                )}
            </ak-alert>
            <ak-text-input
                label=${msg("Name", { id: "secret.form.name.label" })}
                name="name"
                required
                value="${ifDefined(this.instance?.name)}"
                autofocus
                autocomplete="off"
                spellcheck="false"
            ></ak-text-input>
            ${
                this.instance || this.types.length === 1
                    ? nothing
                    : html`<ak-radio-input
                          name="type"
                          label=${msg("Type", { id: "secret.form.type.label" })}
                          .value=${this.type}
                          .options=${this.types.map((value) => ({
                              label: secretTypeLabel(value),
                              value,
                              default: value === this.types[0],
                              description: html`${secretTypeDescription(value)}`,
                          }))}
                          @input=${(ev: InputEvent) => {
                              this.type = (ev.currentTarget as AkRadioInput<SecretTypeEnum>).value;
                          }}
                      ></ak-radio-input> `
            }
            ${this.renderValueInput()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-form": SecretForm;
    }
}
