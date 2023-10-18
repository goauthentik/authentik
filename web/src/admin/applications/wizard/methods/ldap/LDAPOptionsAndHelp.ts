import { msg } from "@lit/localize";
import { html } from "lit";

import { LDAPAPIAccessMode } from "@goauthentik/api";

export const bindModeOptions = [
    {
        label: msg("Cached binding"),
        value: LDAPAPIAccessMode.Cached,
        default: true,
        description: html`${msg(
            "Flow is executed and session is cached in memory. Flow is executed when session expires",
        )}`,
    },
    {
        label: msg("Direct binding"),
        value: LDAPAPIAccessMode.Direct,
        description: html`${msg(
            "Always execute the configured bind flow to authenticate the user",
        )}`,
    },
];

export const searchModeOptions = [
    {
        label: msg("Cached querying"),
        value: LDAPAPIAccessMode.Cached,
        default: true,
        description: html`${msg(
            "The outpost holds all users and groups in-memory and will refresh every 5 Minutes",
        )}`,
    },
    {
        label: msg("Direct querying"),
        value: LDAPAPIAccessMode.Direct,
        description: html`${msg(
            "Always returns the latest data, but slower than cached querying",
        )}`,
    },
];

export const mfaSupportHelp = msg(
    "When enabled, code-based multi-factor authentication can be used by appending a semicolon and the TOTP code to the password. This should only be enabled if all users that will bind to this provider have a TOTP device configured, as otherwise a password may incorrectly be rejected if it contains a semicolon.",
);

export const groupHelp = msg(
    "The start for gidNumbers, this number is added to a number generated from the group.Pk to make sure that the numbers aren't too low for POSIX groups. Default is 4000 to ensure that we don't collide with local groups or users primary groups gidNumber",
);

export const cryptoCertificateHelp = msg(
    "The certificate for the above configured Base DN. As a fallback, the provider uses a self-signed certificate.",
);

export const tlsServerNameHelp = msg(
    "DNS name for which the above configured certificate should be used. The certificate cannot be detected based on the base DN, as the SSL/TLS negotiation happens before such data is exchanged.",
);

export const uidStartNumberHelp = msg(
    "The start for uidNumbers, this number is added to the user.Pk to make sure that the numbers aren't too low for POSIX users. Default is 2000 to ensure that we don't collide with local users uidNumber",
);

export const gidStartNumberHelp = msg(
    "The start for gidNumbers, this number is added to a number generated from the group.Pk to make sure that the numbers aren't too low for POSIX groups. Default is 4000 to ensure that we don't collide with local groups or users primary groups gidNumber",
);
