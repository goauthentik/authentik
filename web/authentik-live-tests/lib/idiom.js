"use strict";

const CLICK_TIME_DELAY = 250;

async function text(selector, value) {
    const input = await $(selector);
    return await input.setValue(value);
}

async function button(selector) {
    console.log("HEY:", selector);
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

exports.$AkSel = {
    button,
    pause,
    search,
    text,
};
