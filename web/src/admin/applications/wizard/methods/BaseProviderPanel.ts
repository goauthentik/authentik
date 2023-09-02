import BasePanel from "../BasePanel";

export class ApplicationWizardProviderPageBase extends BasePanel {
    handleChange(ev: InputEvent) {
        if (!ev.target) {
            console.warn(`Received event with no target: ${ev}`);
            return;
        }
        const target = ev.target as HTMLInputElement;
        const value = target.type === "checkbox" ? target.checked : target.value;
        this.dispatchWizardUpdate({
            update: {
                provider: {
                    [target.name]: value,
                },
            },
            status: this.form.checkValidity() ? "valid" : "invalid"
        });
    }

    shouldUpdate(changed: Map<string, any>) {
        console.log("CHANGED:", JSON.stringify(Array.from(changed.entries()), null, 2));
        return true;
    }

    validator() {
        return this.form.reportValidity();
    }
}

export default ApplicationWizardProviderPageBase;
