import "#components/ak-secret-text-input";
import "#components/ak-secret-textarea-input";
import "#components/ak-radio-input";
import "#components/ak-text-input";
import "#components/ak-textarea-input";
import "#elements/forms/HorizontalFormElement";
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
import { css, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-secret-form")
export class SecretForm extends ModelForm<Secret, string, SecretRequest> {
    public static override verboseName = msg("Secret", { id: "secret.verbose-name" });
    public static override verboseNamePlural = msg("Secrets", { id: "secret.verbose-name-plural" });

    public override size = PFSize.Medium;

    public static styles = [
        ...ModelForm.styles,
        css`
            .secret-upload {
                position: relative;
                overflow: hidden;
            }
            .secret-upload input {
                position: absolute;
                inset: 0;
                width: 100%;
                height: 100%;
                opacity: 0;
                cursor: pointer;
            }
            .secret-upload:focus-within {
                outline: 2px solid var(--pf-global--active-color--100);
            }
            .secret-file-name {
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
        `,
    ];

    @state()
    protected fileName = "";

    @property({ attribute: false })
    public types: SecretTypeEnum[] = [
        SecretTypeEnum.Text,
        SecretTypeEnum.Multiline,
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
        const label = this.instance
            ? msg("New value", { id: "secret.form.new-value.label" })
            : msg("Value", { id: "secret.form.value.label" });

        const help = this.instance
            ? msg("Leave empty to keep the current value.", {
                  id: "secret.form.new-value.description",
              })
            : "";

        switch (this.type) {
            case SecretTypeEnum.Multiline:
                if (this.instance) {
                    return html`<ak-secret-textarea-input
                        name="value"
                        label=${label}
                        help=${help}
                        input-hint="code"
                    ></ak-secret-textarea-input>`;
                }
                return html`<ak-textarea-input
                    name="value"
                    label=${label}
                    help=${help}
                    rows="4"
                    input-hint="code"
                    ?required=${!this.instance}
                ></ak-textarea-input>`;
            case SecretTypeEnum.File:
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
                    <div class="pf-c-input-group">
                        <span class="pf-c-form-control secret-file-name" aria-live="polite"
                            >${
                                this.fileName ||
                                msg("No file selected", { id: "secret.form.file.empty.label" })
                            }</span
                        >
                        <span
                            class="pf-c-button pf-m-control secret-upload"
                            title=${msg("Upload file", { id: "secret.form.file.upload.label" })}
                        >
                            <i class="fas fa-upload" aria-hidden="true"></i>
                            <input
                                type="file"
                                id="secret-file-input"
                                ?required=${!this.instance}
                                @change=${(event: Event) => {
                                    this.fileName =
                                        (event.target as HTMLInputElement).files?.[0]?.name ?? "";
                                }}
                            />
                        </span>
                    </div>
                    ${help ? html`<p class="pf-c-form__helper-text">${help}</p>` : nothing}
                </ak-form-element-horizontal>`;
            default:
                return html`<ak-secret-text-input
                    label=${label}
                    name="value"
                    ?revealed=${!this.instance}
                    input-hint="code"
                    help=${
                        help ||
                        msg("Leave empty to generate a value.", {
                            id: "secret.form.value.generate-description",
                        })
                    }
                ></ak-secret-text-input>`;
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
            ${
                this.instance || this.types.length === 1
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
                                  description: html`${msg("An uploaded file.", {
                                      id: "secret.type.file.description",
                                  })}`,
                              },
                          ].filter((option) => this.types.includes(option.value))}
                          @input=${(ev: InputEvent) => {
                              this.type = (ev.currentTarget as AkRadioInput<SecretTypeEnum>).value;
                              this.fileName = "";
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
