/**
 * @import { AutosubmitChallenge } from "@goauthentik/api";
 */
import $ from "jquery";

import { Stage } from "./Stage.js";
import { ak } from "./utils.js";

/**
 * @template {AutosubmitChallenge} T
 * @extends {Stage<T>}
 */
export class AutosubmitStage extends Stage {
    render() {
        this.html(/* html */ `
            <form id="autosubmit-form" action="${this.challenge.url}" method="POST">
                <img class="mb-4 brand-icon" src="${ak().brand.branding_logo}" alt="">
                <h1 class="h3 mb-3 fw-normal text-center">${this.challenge?.flowInfo?.title}</h1>
                ${Object.entries(this.challenge.attrs).map(([key, value]) => {
                    return /* html */ `<input
                            type="hidden"
                            name="${key}"
                            value="${value}"
                        />`;
                })}
                <div class="d-flex justify-content-center">
                    <div class="spinner-border" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                </div>
            </form>`);

        $("#autosubmit-form").submit();
    }
}
