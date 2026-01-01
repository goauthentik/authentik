import {
    assertVersionSupported,
    VersionValidationError,
} from "@goauthentik/docusaurus-theme/releases/version";

import React from "react";
import { coerce } from "semver";

export interface AuthentikVersionProps {
    semver: string;
}

/**
 * Badge indicating semantic versioning of authentik required for a feature or integration.
 */
export const VersionBadge: React.FC<AuthentikVersionProps> = ({ semver }) => {
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

        if (process.env.NODE_ENV !== "production") {
            throw error;
        }

        console.error(error.message);
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
