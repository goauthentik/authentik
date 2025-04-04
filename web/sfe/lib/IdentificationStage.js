/**
 * @import { IdentificationChallenge } from "@goauthentik/api";
 */
import $ from "jquery";

import { Stage } from "./Stage.js";
import { ak } from "./utils.js";

/**
 * @template {IdentificationChallenge} T
 * @extends {Stage<T>}
 */
export class IdentificationStage extends Stage {
    render() {
        this.html(/* html */ `
            <form id="ident-form">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                ${
                    this.challenge.applicationPre
                        ? /* html */ `<p>
                              Log in to continue to ${this.challenge.applicationPre}.
                          </p>`
                        : ""
                }
                <div class="form-label-group my-3 has-validation">
                    <input type="text" autofocus class="form-control" name="uid_field" placeholder="Email / Username">
                </div>
                ${
                    this.challenge.passwordFields
                        ? /* html */ `<div class="form-label-group my-3 has-validation">
                                <input type="password" class="form-control ${this.error("password").length > 0 ? "is-invalid" : ""}" name="password" placeholder="Password">
                                ${this.renderInputError("password")}
                        </div>`
                        : ""
                }
                ${this.renderNonFieldErrors()}
                <button class="btn btn-primary w-100 py-2" type="submit">${this.challenge.primaryAction}</button>
            </form>`);

        $("#ident-form input[name=uid_field]").trigger("focus");
        $("#ident-form").on("submit", (ev) => {
            ev.preventDefault();
            const target = /** @type {HTMLFormElement} */ (ev.target);

            const data = new FormData(target);
            this.executor.submit(data);
        });
    }
}
