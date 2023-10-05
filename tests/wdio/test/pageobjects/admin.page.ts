import Page from "../pageobjects/page.js";
import { browser } from "@wdio/globals";

const CLICK_TIME_DELAY = 250;

export default class AdminPage extends Page {
    public get pageHeader() {
        return $('>>>ak-page-header slot[name="header"]');
    }

    async openApplicationsListPage() {
        await this.open("if/admin/#/core/applications");
    }

    public open(path: string) {
        return browser.url(`http://localhost:9000/${path}`);
    }

    public pause(selector?: string) {
        if (selector) {
            return $(selector).waitForDisplayed();
        }
        return browser.pause(CLICK_TIME_DELAY);
    }
}
