import Page from "../page.js";
import { $ } from "@wdio/globals";

export class ApplicationForm extends Page {
    async name() {
        return await $('ak-text-input[name="name"]').$("input");
    }

    async uiSettings() {
        return await $("ak-form-group").$('button[aria-label="UI Settings"]');
    }

    async launchUrl() {
        return await $('input[name="metaLaunchUrl"]');
    }
}

export default new ApplicationForm();
