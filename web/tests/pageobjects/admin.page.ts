import { $ } from "@wdio/globals";

import Page from "../pageobjects/page.js";

export default class AdminPage extends Page {
    public pageHeader() {
        return $(">>>ak-page-header").$('>>>slot[name="header"]');
    }

    async openApplicationsListPage() {
        return this.open("if/admin/#/core/applications");
    }
}
