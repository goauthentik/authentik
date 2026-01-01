import {
    assertVersionSupported,
    VersionValidationError,
} from "@goauthentik/docusaurus-theme/releases/version";

import React from "react";
import { coerce } from "semver";

export interface AuthentikVersionProps {
    semver: string;
    docID: string;
}

/**
 * Badge indicating semantic versioning of authentik required for a feature or integration.
 */
export const VersionBadge: React.FC<AuthentikVersionProps> = ({ semver, docID }) => {
    const parsed = coerce(semver);

    if (!parsed) {
        throw new VersionValidationError(`Could not parse semver version: ${semver}`);
    }

    try {
        assertVersionSupported(parsed);
    } catch (error) {
        if (!(error instanceof VersionValidationError)) {
            throw error;
        }

        const message = `Outdated Markdown frontmatter for document \`${docID}\`: To fix this error, remove \`authentik_version: ${semver}\` from the Markdown frontmatter`;

        console.warn(`\n\n⚠️ ${message}:\n\n`, error.message, error.stack, "\n");

        if (process.env.NODE_ENV === "production") {
            console.debug("⚠️ Omitting outdated version badge in production build");

            return null;
        }

        const versionError = new Error(message, {
            cause: error,
        });

        throw versionError;
    }

    return (
        <span
            title={`Available in authentik ${parsed.format()} and later`}
            aria-description="Version badge"
            role="img"
            className="badge badge--version"
        >
            authentik:&nbsp;{parsed.format()}+
        </span>
    );
};

export default VersionBadge;
