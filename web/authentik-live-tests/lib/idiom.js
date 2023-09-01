"use strict";

const CLICK_TIME_DELAY = 250;

async function text(selector, value) {
    const input = await $(selector);
    return await input.setValue(value);
}

async function button(selector) {
    const button = await $(selector);
    return await button.click();
}

async function search(searchSelector, buttonSelector) {
    const inputBind = await $(searchSelector);
    await inputBind.click();
    const searchBlock = await $('>>>div[data-managed-by="ak-search-select"]');
    const target = searchBlock.$(buttonSelector);
    return await target.click();
}

async function pause(selector) {
    if (selector) {
        return await $(selector).waitForDisplayed();
    }
    return await browser.pause(CLICK_TIME_DELAY);
}

async function waitfor(selector) {
    return await $(selector).waitForDisplayed();
}

async function deletebox(selector) {
    return await $(selector)
        .parentElement()
        .parentElement()
        .$(".pf-c-table__check")
        .$('input[type="checkbox"]')
        .click();
}
    

exports.$AkSel = {
    button,
    pause,
    search,
    text,
    waitfor,
    deletebox,
};
