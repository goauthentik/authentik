/**
 * @import { PasswordChallenge } from "@goauthentik/api";
 */
import $ from "jquery";

import { Stage } from "./Stage.js";
import { ak } from "./utils.js";

/**
 * @template {PasswordChallenge} T
 * @extends {Stage<T>}
 */
export class PasswordStage extends Stage {
    render() {
        this.html(/* html */ `
            <form id="password-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                <div class="form-label-group my-3 has-validation">
                    <input type="password" autofocus class="form-control ${this.error("password").length > 0 ? "is-invalid" : ""}" name="password" placeholder="Password">
                    ${this.renderInputError("password")}
                </div>
                <button class="btn btn-primary w-100 py-2" type="submit">Continue</button>
            </form>`);

        $("#password-form input").trigger("focus");

        $("#password-form").on("submit", (ev) => {
            ev.preventDefault();

            const target = /** @type {HTMLFormElement} */ (ev.target);

            const data = new FormData(target);
            this.executor.submit(data);
        });
    }
}
