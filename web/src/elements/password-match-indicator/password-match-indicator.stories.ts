import { html } from "lit";

import ".";

export default {
    title: "Elements/Password Match Indicator",
};

export const Primary = () =>
    html`<div style="background: #fff; padding: 4em">
        <p>Type some text: <input id="primary-example" style="color:#000" /></p>
        <p style="margin-top:0.5em">
            Type some other text: <input id="primary-example_repeat" style="color:#000" />
            <ak-password-match-indicator
                first="#primary-example"
                second="#primary-example_repeat"
            ></ak-password-match-indicator>
        </p>
    </div>`;
