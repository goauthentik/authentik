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
            provider: {
                ...this.wizard.provider,
                [target.name]: value,
            },
        });
    }
}

export default ApplicationWizardProviderPageBase;
