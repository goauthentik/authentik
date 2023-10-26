import BasePanel from "../BasePanel";

export class ApplicationWizardProviderPageBase extends BasePanel {
    handleChange(_ev: InputEvent) {
        this.dispatchWizardUpdate({
            update: {
                ...this.wizard,
                provider: this.formValues,
            },
            status: this.valid ? "valid" : "invalid",
        });
    }
}

export default ApplicationWizardProviderPageBase;
