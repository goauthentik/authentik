import "#admin/rbac/ak-rbac-object-permission-page";
import "#elements/forms/ModalForm";

import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * This is a bit of a hack to get the viewport checking from ModelForm,
 * even though we actually don't need a form here.
 * #TODO: Rework this in the future
 */
@customElement("ak-rbac-object-permission-modal-form")
export class ObjectPermissionsPageForm extends ModelForm<never, string> {
    public static verboseName = msg("Object Permission");
    public static verboseNamePlural = msg("Object Permissions");
    public static createLabel = msg("Update");

    public override cancelButtonLabel = msg("Close");
    public override cancelable = true;

    public override size = PFSize.XLarge;

    @property({ type: String })
    public model: ModelEnum | null = null;

    @property({ type: String })
    public objectPk: string | null = null;

    protected override loadInstance(): Promise<never> {
        return Promise.resolve() as never;
    }

    protected override send(): Promise<never> {
        return Promise.resolve() as never;
    }

    public override renderActions(): SlottedTemplateResult {
        return null;
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-rbac-object-permission-page
            embedded
            .model=${this.model}
            .objectPk=${this.objectPk}
            slot="form"
        >
        </ak-rbac-object-permission-page>`;
    }
}

/**
 * @deprecated Use {@linkcode IconPermissionButton}
 */
@customElement("ak-rbac-object-permission-modal")
export class ObjectPermissionModal extends AKElement {
    protected override createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    @property({ type: String })
    public model: ModelEnum | null = null;

    // TODO: Switch to attribute-casing after the RBAC components settle.
    @property({ type: String })
    public objectPk: string | null = null;

    @property({ type: String })
    public label: string | null = null;

    protected override render(): SlottedTemplateResult {
        return IconPermissionButton(this.label, {
            model: this.model,
            objectPk: this.objectPk,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-object-permission-modal-form": ObjectPermissionsPageForm;
        "ak-rbac-object-permission-modal": ObjectPermissionModal;
    }
}
