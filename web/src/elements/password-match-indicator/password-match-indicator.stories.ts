import { html } from "lit";

import ".";

export default {
    title: "Elements/Password Match Indicator",
};

export const Primary = () =>
    html`<div style="background: #fff; padding: 4em">
        <p>Type some text: <input id="primary-example" style="color:#000" /></p>
        <p>Type some other text: <input id="primary-example_repeat" style="color:#000" /></p>
        <ak-password-match-indicator src="#primary-example_repeat"></ak-password-match-indicator>
    </div>`;
