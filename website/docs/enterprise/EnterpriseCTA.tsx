import "./styles.css";

import IconExternalLink from "@theme/Icon/ExternalLink";

export function EnterpriseCTA() {
    return (
        <div className="button-row ak-enterprise-actions">
            <a className="button button--primary" href="mailto:sales@goauthentik.io">
                Contact sales
            </a>

            <a
                className="button ak-enterprise-pricing"
                href="https://goauthentik.io/pricing/"
                target="_blank"
                rel="noopener noreferrer"
            >
                See Enterprise details
                <IconExternalLink />
            </a>
        </div>
    );
}
