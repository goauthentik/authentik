const { execSync } = require("child_process");
const { readdirSync } = require("fs");
const path = require("path");
const { $AkSel } = require("../lib/idiom");

const CLICK_TIME_DELAY = 250;

const login = [
    ['text', '>>>input[name="uidField"]', "ken@goauthentik.io"],
    ['button', '>>>button[type="submit"]'],
    ['pause'],
    ['text', '>>>input[name="password"]', "eat10bugs"],
    ['button', '>>>button[type="submit"]'],
    ['pause', ">>>div.header h1"],
];


const simpleApplication = [
    ['text',   '>>>ak-form-element-horizontal input[name="name"]', "This Is My Application"],
    ['button', ">>>ak-wizard-frame footer button.pf-m-primary"],
    ['button', '>>>input[value="ldapprovider"]'],
    ['button', ">>>ak-wizard-frame footer button.pf-m-primary"],
    ['text',   '>>>ak-form-element-horizontal input[name="name"]', "This Is My Provider"],
    ['search', '>>>ak-tenanted-flow-search input[type="text"]', "button*=default-authentication-flow"],
    ['text',   '>>>ak-form-element-horizontal input[name="tlsServerName"]', "example.goauthentik.io"],
    ['button', ">>>ak-wizard-frame footer button.pf-m-primary"]
];


describe("Login", () => {
    it(`Should correctly log in to Authentik}`, async () => {
        await browser.reloadSession();
        await browser.url("http://localhost:9000");

        let start = Date.now();
        for ([command, ...args] of login) {
            await $AkSel[command].apply($, args);
        }

        const home = await $(">>>div.header h1");
        expect(home).toHaveText("My applications");

        const goToAdmin = await $('>>>a[href="/if/admin"]');
        goToAdmin.click();

        await $(">>>ak-admin-overview").waitForDisplayed();
        $AkSel.button('>>>a[href="#/core/applications;%7B%22createForm%22%3Atrue%7D"]');

        await $(">>>ak-application-list").waitForDisplayed();
        $AkSel.button('>>>ak-wizard-frame button[slot="trigger"]');

        for ([command, ...args] of simpleApplication) {
            await $AkSel[command].apply($, args);
        }

        let timeTaken = Date.now() - start;
        console.log("Total time taken : " + timeTaken + " milliseconds");
    });
});
