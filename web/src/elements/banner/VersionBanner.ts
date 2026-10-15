import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";

import { AKElement } from "#elements/Base";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithVersion } from "#elements/mixins/version";

import { UpdateVersionReason } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-version-banner")
export class VersionBanner extends WithBrandConfig(WithVersion(AKElement)) {
    static styles = [PFBanner, PFFlex];

    renderUIMismatch() {
        if (!this.version?.versionCurrent) return nothing;

        if (this.version.versionCurrent === import.meta.env.AK_VERSION) return nothing;

        return html`
            <div class="pf-c-banner pf-m-sticky pf-m-gold">
                <div class="pf-l-flex pf-m-space-items-sm">
                    <div class="pf-l-flex__item">
                        <span class="sr-only">${msg("Warning banner:")}</span>
                        <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                    </div>
                    <div class="pf-l-flex__item">
                        ${msg(
                            str`A newer version (${this.version.versionCurrent}) of the UI is available.`,
                        )}
                    </div>
                </div>
            </div>
        `;
    }

    renderUpdate() {
        if (!this.version?.outdated || !this.version.versionLatest?.valid) return nothing;

        const [level, message] = match(this.version.versionLatest)
            .when(
                (v) => v.reason === UpdateVersionReason.Security,
                (v) => [
                    "pf-m-red",
                    msg(
                        str`Security release ${v.version} of ${this.brandingTitle} is available. Update now.`,
                    ),
                ],
            )
            .otherwise((v) => [
                "pf-m-gold",
                msg(str`Version ${v.version} of ${this.brandingTitle} is available.`),
            ]);

        return html`<div class="pf-c-banner pf-m-sticky ${level}">
            <div class="pf-l-flex pf-m-space-items-sm">
                <div class="pf-l-flex__item">
                    <span class="sr-only">${msg("Warning banner:")}</span>
                    <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                </div>
                <div class="pf-l-flex__item">
                    ${message}
                    <a href=${this.version.versionLatest.changelogUrl}
                        >${msg("Click here for the changelog.")}</a
                    >
                </div>
            </div>
        </div>`;
    }

    render() {
        return html`${this.renderUIMismatch()}${this.renderUpdate()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-version-banner": VersionBanner;
    }
}
