const { execSync } = require("child_process");
const { readdirSync } = require("fs");
const path = require("path");
const { $AkSel } = require("../lib/idiom");
const { randomPrefix, convertToSlug } = require("../lib/utils");

const CLICK_TIME_DELAY = 250;

const login = [
    ["text", '>>>input[name="uidField"]', "ken@goauthentik.io"],
    ["button", '>>>button[type="submit"]'],
    ["pause"],
    ["text", '>>>input[name="password"]', "eat10bugs"],
    ["button", '>>>button[type="submit"]'],
    ["pause", ">>>div.header h1"],
];

const navigateToWizard = [
    ["button", '>>>a[href="/if/admin"]'],
    ["waitfor", ">>>ak-admin-overview"],
    ["button", '>>>a[href="#/core/applications;%7B%22createForm%22%3Atrue%7D"]'],
    ["waitfor", ">>>ak-application-list"],
    ["button", '>>>ak-wizard-frame button[slot="trigger"]']
];

// prettier-ignore
const ldapApplication = (theCode) => ([
    ["text", '>>>ak-form-element-horizontal input[name="name"]', `This Is My Application ${theCode}`],
    ["button", ">>>ak-wizard-frame footer button.pf-m-primary"],
    ["button", '>>>input[value="ldapprovider"]'],
    ["button", ">>>ak-wizard-frame footer button.pf-m-primary"],
    ["search", '>>>ak-tenanted-flow-search input[type="text"]', "button*=default-authentication-flow",],
    ["text", '>>>ak-form-element-horizontal input[name="tlsServerName"]', "example.goauthentik.io"],
    ["button", ">>>ak-wizard-frame footer button.pf-m-primary"],
]);

const deleteProvider = (theSlug) => ([
    ["button", '>>>ak-sidebar-item a[href="#/core/providers"]'],
    ["deletebox", `>>>a[href="#/core/applications/${theSlug}"]`],
    ["button", '>>>ak-forms-delete-bulk button[slot="trigger"]'],
    ["button", '>>>ak-forms-delete-bulk div[role="dialog"] ak-spinner-button'],
]);

const deleteApplication = (theSlug) => ([
    ["button", '>>>ak-sidebar-item a[href="#/core/applications"'],
    ["deletebox", `>>>a[href="#/core/applications/${theSlug}"]`],
    ["button", '>>>ak-forms-delete-bulk button[slot="trigger"]'],
    ["button", '>>>ak-forms-delete-bulk div[role="dialog"] ak-spinner-button']
]);
    

function prepApplicationAndSlug() {
    const newSuffix = randomPrefix();
    const thisApplication = ldapApplication(newSuffix);
    return [thisApplication, convertToSlug(thisApplication[0][2])];
}

async function runSequence(sequence, watch = false) {
    for ([command, ...args] of sequence) {
        await $AkSel[command].apply($, args);
        if (watch) {
            await browser.pause(250);
        }
    }
}

describe("Login", () => {
    it("Should correctly log in to Authentik}", async () => {
        const [theApplication, theSlug] = prepApplicationAndSlug();

        await browser.reloadSession();
        await browser.url("http://localhost:9000");

        runSequence(login, true);

        const home = await $(">>>div.header h1");
        await expect(home).toHaveText("My applications");

        await runSequence(navigateToWizard, true);
        await runSequence(theApplication, true)

        const success = await $(">>>ak-application-wizard-commit-application h1.pf-c-title");
        await expect(success).toHaveText("Your application has been saved");

        await $AkSel.button(">>>ak-wizard-frame .pf-c-wizard__footer-cancel button");

        await runSequence(deleteProvider(theSlug), true);
        await runSequence(deleteApplication(theSlug), true);

        const expectedApplication = await $(`>>>a[href="#/core/applications/${theSlug}"]`);
        expect(expectedApplication).not.toExist();
    });
});
