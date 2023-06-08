import { html } from "lit";

import ".";

export default {
    title: "Elements/Password Strength Indicator",
};

export const Primary = () =>
    html`<div style="background: #fff; padding: 4em">
        <p>Type some text: <input id="primary-example" style="color:#000" /></p>
        <ak-password-strength-indicator src="#primary-example"></ak-password-strength-indicator>
    </div>`;
