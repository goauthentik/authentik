import "#elements/forms/HorizontalFormElement";
import { ModelForm } from "#elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";

export abstract class BaseSourceForm<T extends object = object> extends ModelForm<T, string> {
    public static override verboseName = msg("Source");
    public static override verboseNamePlural = msg("Sources");
    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated source.")
            : msg("Successfully created source.");
    }

    /**
     * Admins enter the properties as one comma-separated string; `toJSON()` splits it into
     * the list the API expects.
     */
    protected renderEnrollmentOnlyUserPropertiesField(value?: string[]): TemplateResult {
        return html`<ak-form-element-horizontal
            label=${msg("Enrollment-only user properties", {
                id: "sources.enrollment-only-user-properties.label",
            })}
            name="enrollmentOnlyUserProperties"
        >
            <input
                type="text"
                value=${value?.join(", ") ?? ""}
                class="pf-c-form-control pf-m-monospace"
                autocomplete="off"
                spellcheck="false"
            />
            <p class="pf-c-form__helper-text">
                ${msg(
                    "Comma-separated user properties, such as username, name, or email, that this source only sets when it creates a user. Logins and syncs through this source don't overwrite them on existing users.",
                    { id: "sources.enrollment-only-user-properties.description" },
                )}
            </p>
        </ak-form-element-horizontal>`;
    }

    public override toJSON(): T {
        const data = super.toJSON() as T & { enrollmentOnlyUserProperties?: unknown };

        if (typeof data.enrollmentOnlyUserProperties === "string") {
            data.enrollmentOnlyUserProperties = data.enrollmentOnlyUserProperties
                .split(",")
                .map((property) => property.trim())
                .filter(Boolean);
        }

        return data;
    }
}
