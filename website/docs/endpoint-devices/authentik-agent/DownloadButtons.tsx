import "./styles.css";

// Paths are inlined verbatim from @iconify-json/mdi (mdi:apple, mdi:microsoft-windows) rather
// than imported, because that pack is registered for Mermaid only and importing it would pull
// all ~7600 icons into the bundle for two glyphs.
export function DownloadButtons() {
    return (
        <div className="button-row ak-agent-downloads">
            <a
                className="button button--primary button--lg"
                href="https://pkg.goauthentik.io/packages/authentik_package-macos/authentik%20Agent%20Installer.pkg"
            >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path
                        fill="currentColor"
                        d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47c-1.34.03-1.77-.79-3.29-.79c-1.53 0-2 .77-3.27.82c-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51c1.28-.02 2.5.87 3.29.87c.78 0 2.26-1.07 3.81-.91c.65.03 2.47.26 3.64 1.98c-.09.06-2.17 1.28-2.15 3.81c.03 3.02 2.65 4.03 2.68 4.04c-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5c.13 1.17-.34 2.35-1.04 3.19c-.69.85-1.83 1.51-2.95 1.42c-.15-1.15.41-2.35 1.05-3.11"
                    />
                </svg>
                Download for macOS (.pkg)
            </a>

            <a
                className="button button--primary button--lg"
                href="https://pkg.goauthentik.io/packages/authentik_package-windows/authentik%20Agent%20Installer.msi"
            >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path
                        fill="currentColor"
                        d="M3 12V6.75l6-1.32v6.48zm17-9v8.75l-10 .15V5.21zM3 13l6 .09v6.81l-6-1.15zm17 .25V22l-10-1.91V13.1z"
                    />
                </svg>
                Download for Windows (.msi)
            </a>
        </div>
    );
}
