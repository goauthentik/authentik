const { execSync } = require('child_process')
const { readdirSync } = require('fs')
const path = require('path')

const CLICK_TIME_DELAY = 250;

describe('Login', () => {
    it(`Should correctly log in to Authentik}`, async () => {
        await browser.reloadSession()
        await browser.url("http://localhost:9000")

        const uidField = await $('>>>input[name="uidField"]');
        await uidField.setValue('ken@goauthentik.io');

        const next1 = await $('>>>button[type="submit"]');
        await next1.click();
        await browser.pause(CLICK_TIME_DELAY);
        
        const pwdField = await $('>>>input[name="password"]');
        await pwdField.setValue('eat10bugs');
        const next2 = await $('>>>button[type="submit"]');
        await next2.click();
        await browser.pause(CLICK_TIME_DELAY);

        const home = await $('>>>div.header h1');
        expect(home).toHaveText('My applications');

        const goToAdmin = await $('>>>a[href="/if/admin"]');
        goToAdmin.click();

        await $('>>>ak-admin-overview').waitForDisplayed();

        const applicationLink = await $('>>>a[href="#/core/applications;%7B%22createForm%22%3Atrue%7D"]');
        applicationLink.click();

        await $('>>>ak-application-list').waitForDisplayed();
        const startWizard = await $('>>>ak-wizard-frame button[slot="trigger"]')
        startWizard.click();

        {
            const nameInput = await $('>>>ak-form-element-horizontal input[name="name"]');
            await nameInput.setValue('This Is My Application');

            const slugInput = await $('>>>ak-form-element-horizontal input[name="slug"]');
            await slugInput.setValue('this-is-my-application');

            const nextButton = await $('>>>ak-wizard-frame footer button.pf-m-primary');
            await nextButton.click();
        }

        {
            const input = await $('>>>input[value="proxyprovider-proxy"]');
            await input.click();

            const nextButton = await $('>>>ak-wizard-frame footer button.pf-m-primary');
            await nextButton.click();
        }

        {
            const input = await $('>>>ak-form-element-horizontal input[name="name"]');
            await input.setValue('This Is My Provider');
        }

        await browser.pause(2000);
    })
})

