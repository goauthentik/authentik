import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet.js";
import { $, expect } from "@wdio/globals";

import { TemplateResult, html, render as litRender } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../AggregatePromiseCard.js";

const render = (body: TemplateResult) => {
    document.adoptedStyleSheets = [
        ...document.adoptedStyleSheets,
        ensureCSSStyleSheet(PFBase),
        ensureCSSStyleSheet(AKGlobal),
    ];
    return litRender(body, document.body);
};

const DELAY = 1000; // milliseconds

describe("ak-aggregate-card-promise", () => {
    it("should render the promise card and display the message after a 1 second timeout", async () => {
        const text = "RESULT";
        const runThis = (timeout: number, value: string) =>
            new Promise((resolve, _reject) => setTimeout(resolve, timeout, value));
        const promise = runThis(DELAY, text);
        render(html`<ak-aggregate-card-promise .promise=${promise}></ak-aggregate-card-promise>`);

        const component = await $("ak-aggregate-card-promise");
        // Assert we're in pre-resolve mode
        await expect(await component.$(">>>.pf-c-card__header a")).not.toExist();
        await expect(await component.$(">>>ak-spinner")).toExist();
        await promise;
        await expect(await component.$(">>>ak-spinner")).not.toExist();
        await expect(await component.$(">>>.pf-c-card__body")).toHaveText("RESULT");
    });

    it("should render the promise card and display failure after a 1 second timeout", async () => {
        const text = "EXPECTED FAILURE";
        const runThis = (timeout: number, value: string) =>
            new Promise((_resolve, reject) => setTimeout(reject, timeout, value));
        const promise = runThis(DELAY, text);
        render(
            html`<ak-aggregate-card-promise
                .promise=${promise}
                failureMessage=${text}
            ></ak-aggregate-card-promise>`,
        );

        const component = await $("ak-aggregate-card-promise");
        // Assert we're in pre-resolve mode
        await expect(await component.$(">>>.pf-c-card__header a")).not.toExist();
        await expect(await component.$(">>>ak-spinner")).toExist();
        try {
            await promise;
        } catch (_e: unknown) {
            await expect(await component.$(">>>ak-spinner")).not.toExist();
            await expect(await component.$(">>>.pf-c-card__body")).toHaveText(text);
        }
    });
});
