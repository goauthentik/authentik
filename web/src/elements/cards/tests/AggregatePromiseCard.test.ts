import { render } from "@goauthentik/elements/tests/utils.js";
import { $, browser, expect } from "@wdio/globals";

import { html } from "lit";

import "../AggregatePromiseCard.js";

const DELAY = 1000; // milliseconds

describe("ak-aggregate-card-promise", () => {
    it("should render the promise card and display the message after a 1 second timeout", async () => {
        const text = "RESULT";
        const runThis = (timeout: number, value: string) =>
            new Promise((resolve, _reject) => setTimeout(resolve, timeout, value));
        const promise = runThis(DELAY, text);

        render(html`<ak-aggregate-card-promise .promise=${promise}></ak-aggregate-card-promise>`);

        const component = $("ak-aggregate-card-promise");
        // Assert we're in pre-resolve mode
        await expect(component.$(">>>.pf-c-card__header a")).resolves.not.toExist();
        await expect(component.$(">>>ak-spinner")).resolves.toExist();
        await promise;
        await expect(component.$(">>>ak-spinner")).resolves.not.toExist();
        await expect(component.$(">>>.pf-c-card__body")).resolves.toHaveText("RESULT");
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

        const component = $("ak-aggregate-card-promise");
        // Assert we're in pre-resolve mode
        await expect(component.$(">>>.pf-c-card__header a")).resolves.not.toExist();
        await expect(component.$(">>>ak-spinner")).resolves.toExist();

        try {
            await promise;
        } catch (_e: unknown) {
            await expect(component.$(">>>ak-spinner")).resolves.not.toExist();
            await expect(component.$(">>>.pf-c-card__body")).resolves.toHaveText(text);
        }
    });
});
