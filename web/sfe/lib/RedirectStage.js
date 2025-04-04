/**
 * @import { RedirectChallenge } from "@goauthentik/api";
 */
import { Stage } from "./Stage.js";

/**
 * @template {RedirectChallenge} T
 * @extends {Stage<T>}
 */
export class RedirectStage extends Stage {
    render() {
        window.location.assign(this.challenge.to);
    }
}
