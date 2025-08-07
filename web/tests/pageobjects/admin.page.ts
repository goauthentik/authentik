import Page from "../pageobjects/page.js";

import { $ } from "@wdio/globals";

export default class AdminPage extends Page {
    public pageHeader() {
        return $(">>>ak-page-navbar").$(".page-title");
    }

    async openApplicationsListPage() {
        await this.open("if/admin/#/core/applications");
    }
}
