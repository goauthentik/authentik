import BasePanel from "../BasePanel";

export class ApplicationWizardProviderPageBase extends BasePanel {
    handleChange(_ev: InputEvent) {
        const formValues = this.formValues;
        if (!formValues) {
            throw new Error("No provider values on form?");
        }
        this.dispatchWizardUpdate({
            update: {
                ...this.wizard,
                provider: formValues,
            },
            status: this.valid ? "valid" : "invalid",
        });
    }
}

export default ApplicationWizardProviderPageBase;
