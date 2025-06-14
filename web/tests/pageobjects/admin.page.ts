import { $ } from "@wdio/globals";

import Page from "../pageobjects/page.js";

export default class AdminPage extends Page {
    public async pageHeader() {
        return await $(">>>ak-page-header").$('>>>slot[name="header"]');
    }

    async openApplicationsListPage() {
        await this.open("if/admin/#/core/applications");
    }
}
