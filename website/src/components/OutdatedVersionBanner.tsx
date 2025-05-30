import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import clsx from "clsx";
import React, { useEffect, useState } from "react";

/**
 * Banner that appears on outdated documentation versions.
 * Checks if the current hostname is version-XXXX-X.goauthentik.io
 * and displays a banner if it is outdated compared to the current version.
 */
export const OutdatedVersionBanner: React.FC = () => {
    const [isOutdated, setIsOutdated] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { siteConfig } = useDocusaurusContext();

    useEffect(() => {
        try {
            // Get hostname and check if it's a version subdomain
            const hostname = window.location.hostname;

            // If not a version subdomain, don't show banner
            if (!hostname.startsWith("version-")) {
                return;
            }

            // Extract version numbers from hostname (e.g., version-2025-4)
            const parts = hostname.split("-");
            if (parts.length < 3) {
                throw new Error("Invalid version in hostname");
            }

            const hostnameDomain = parts[2];
            if (!hostnameDomain) {
                throw new Error("Missing domain part in hostname");
            }

            const domainParts = hostnameDomain.split(".");
            if (!domainParts.length) {
                throw new Error("Invalid domain format");
            }

            // Parse version numbers - use non-null assertion after validation
            const versionPart = parts[1];
            const monthPart = domainParts[0];

            if (!versionPart || !monthPart) {
                throw new Error("Missing version parts");
            }

            const hostnameYear = parseInt(versionPart, 10);
            const hostnameMonth = parseInt(monthPart, 10);

            if (isNaN(hostnameYear) || isNaN(hostnameMonth)) {
                throw new Error("Invalid version numbers");
            }

            // Get current version from Docusaurus config
            const configVersion = siteConfig.customFields?.currentVersion as string;
            if (!configVersion) {
                throw new Error("Missing current version in config");
            }

            // Extract major and minor versions (ignore patch)
            const versionParts = configVersion.split(".");
            if (versionParts.length < 2) {
                throw new Error("Invalid current version format");
            }

            const majorPart = versionParts[0];
            const minorPart = versionParts[1];

            if (!majorPart || !minorPart) {
                throw new Error("Missing current version parts");
            }

            const currentMajor = parseInt(majorPart, 10);
            const currentMinor = parseInt(minorPart, 10);

            if (isNaN(currentMajor) || isNaN(currentMinor)) {
                throw new Error("Invalid current version numbers");
            }

            // Compare versions (ignoring patch)
            // Only show banner if hostname version is OLDER than current version
            const isOlder =
                hostnameYear < currentMajor ||
                (hostnameYear === currentMajor && hostnameMonth < currentMinor);

            setIsOutdated(isOlder);
            setError(null);
        } catch (e) {
            // Properly handle errors
            const errorMessage = e instanceof Error ? e.message : "Unknown error";
            console.error("OutdatedVersionBanner error:", errorMessage);
            setError("Could not determine version status. See browser console for details.");
        }
    }, [siteConfig.customFields?.currentVersion]);

    // Show error message if we encountered an error
    if (error) {
        return (
            <div
                style={{
                    backgroundColor: "rgba(253, 75, 45, 0.1)",
                    borderBottom: "1px solid rgba(253, 75, 45, 0.2)",
                    padding: "8px 16px",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    fontSize: "14px",
                    color: "var(--ifm-color-content)",
                }}
            >
                <div style={{ display: "flex", alignItems: "center", maxWidth: "1200px" }}>
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="var(--ifm-color-primary)"
                        style={{
                            width: "20px",
                            height: "20px",
                            marginRight: "10px",
                            flexShrink: 0,
                        }}
                    >
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v7h-2zm0 8h2v2h-2z" />
                    </svg>
                    <span>{error}</span>
                </div>
            </div>
        );
    }

    if (!isOutdated) {
        return null;
    }

    return (
        <div
            style={{
                backgroundColor: "rgba(253, 75, 45, 0.1)", // Based on --ifm-color-primary
                borderBottom: "1px solid rgba(253, 75, 45, 0.2)",
                padding: "8px 16px",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                fontSize: "14px",
                color: "var(--ifm-color-content)",
            }}
        >
            <div style={{ display: "flex", alignItems: "center", maxWidth: "1200px" }}>
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="var(--ifm-color-primary)"
                    style={{ width: "20px", height: "20px", marginRight: "10px", flexShrink: 0 }}
                >
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v7h-2zm0 8h2v2h-2z" />
                </svg>
                <span>
                    You are viewing an outdated version of the documentation. Visit{" "}
                    <a
                        href="https://docs.goauthentik.io"
                        style={{
                            color: "var(--ifm-color-primary)",
                            fontWeight: 500,
                            textDecoration: "none",
                            borderBottom: "1px solid var(--ifm-color-primary)",
                        }}
                    >
                        docs.goauthentik.io
                    </a>{" "}
                    for the latest version.
                </span>
            </div>
        </div>
    );
};

export default OutdatedVersionBanner;
