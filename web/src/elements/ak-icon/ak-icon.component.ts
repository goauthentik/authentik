import effects from "./ak-icon-effects.css";
import styles from "./ak-icon.css";
import { ALIASES } from "./aliases.js";
import faicons from "./fontawesome/fontawesome.css";
import pficons from "./pficons/pficons.css";

import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";

const iconFamilies = ["fa", "fas", "fab", "pf"] as const;
type IconFamily = (typeof iconFamilies)[number];

/**
 * @element ak-icon
 *
 * @summary Icon component that understands Patterfly and FontAwesome icon names.
 *
 * @description
 * Displays icons from the Fontawesome and Patternfly font-based icon libraries.  Has an
 * aggressive alias system that prioritizes "fas" and "pf-icon" names where there were no
 * conflicts; for example, you can provide "birthday-cake" to the `icon` attribute and it
 * will find and display `fas fa-birthday-cake`.
 *
 *
 * @attr {string} icon - Icon name or alias (e.g., "user", "search", "fa-home")
 * @attr {"fa"|"fas"|"fab"|"pf"} family - Icon family prefix. When provided with icon, creates
 * explicit family/icon pair
 * @attr {string} fallback - Fallback icon used when resolution fails (default: "fa fa-bug")
 * @attr {"sm"|"md"|"lg"|"xl"} size - Size variant affecting width, height, and font-size
 * @attr {"danger"|"warning"|"success"|"info"|"custom"} variant - Semantic color variant
 * @attr {"beat"|"bounce"|"fade"|"beat-fade"|"flip"|"shake"|"spin"} effect - Animation effect
 * (respects prefers-reduced-motion)
 * @attr {"rotate-90"|"rotate-180"|"rotate-270"|"flip-horizontal"|"flip-vertical"|"flip-both"|"rotate-by"}
 * effect - Transform effect
 *
 * @csspart content - The content wrapper element
 * @csspart icon - The icon element (i tag)
 *
 * @cssprop --pf-v5-c-icon--Width - Icon container width
 * @cssprop --pf-v5-c-icon--Height - Icon container height
 * @cssprop --pf-v5-c-icon__content--Color - Icon color
 * @cssprop --pf-v5-c-icon__content--FontSize - Icon font size
 * @cssprop --pf-v5-c-icon__content--Opacity - Icon opacity
 * @cssprop --fa-animation-delay - Animation delay for effects
 * @cssprop --fa-animation-duration - Animation duration for effects
 * @cssprop --fa-animation-iteration-count - Animation iteration count for effects
 * @cssprop --fa-animation-timing - Animation timing function for effects
 * @cssprop --fa-rotate-angle - Custom rotation angle for rotate-by effect
 * @cssprop --fa-beat-scale - Scale factor for beat effect
 * @cssprop --fa-bounce-height - Bounce height for bounce effect
 * @cssprop --fa-fade-opacity - Opacity for fade effect
 * @cssprop --fa-flip-x - X-axis flip coordinate for flip effect
 * @cssprop --fa-flip-y - Y-axis flip coordinate for flip effect
 * @cssprop --fa-flip-z - Z-axis flip coordinate for flip effect
 * @cssprop --fa-flip-angle - Flip angle for flip effect
 */
export class Icon extends LitElement {
    static override readonly styles = [styles, effects, faicons, pficons];

    @property()
    public icon?: string;

    @property()
    public family?: IconFamily;

    @property()
    public fallback = "fa fa-bug";

    #iconClass: string = this.fallback;

    #deriveIconClass() {
        if (this.family && this.icon) {
            this.#iconClass = `${this.family} ${this.icon}`;
            return;
        }

        if (this.icon && !this.family) {
            const icon = ALIASES.get(this.icon);
            if (icon) {
                this.#iconClass = icon;
                return;
            }
            if (this.icon.includes(" ")) {
                this.#iconClass = this.icon;
                return;
            }
        }

        console.warn("Was unable to determine requested icon.");
        this.#iconClass = this.fallback;
    }

    public override willUpdate() {
        this.#deriveIconClass();
    }

    public override render() {
        return html`<div part="content"><i part="icon" class="${this.#iconClass}"></i></div>`;
    }
}
