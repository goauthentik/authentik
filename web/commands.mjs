/// <reference types="@wdio/globals/types" />
/// <reference types="./types/webdriver.js" />

/**
 *
 * @param {WebdriverIO.Browser} browser
 */
export function addCommands(browser) {
    /**
     * @file Custom WDIO browser commands
     */

    browser.addCommand(
        "focus",
        /**
         * @this {HTMLElement}
         */
        function () {
            this.focus();

            return this;
        },
        /* attachToElement */ true,
    );

    browser.addCommand(
        "blur",
        /**
         * @this {HTMLElement}
         */
        function () {
            this.blur();

            return this;
        },
        /* attachToElement */ true,
    );
}
