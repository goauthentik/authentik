import "./styles.css";

import IconExternalLink from "@theme/Icon/ExternalLink";

export function EnterpriseCTA() {
    return (
        <section className="ak-enterprise" aria-labelledby="choose-an-enterprise-plan">
            <div className="ak-enterprise__copy">
                <h3>Enterprise and Enterprise Plus</h3>
                <p>
                    Compare both plans, see current pricing, and either start a subscription or
                    schedule a call with our team.
                </p>
            </div>

            <a
                className="button button--primary ak-enterprise__cta"
                href="https://goauthentik.io/pricing/"
                target="_blank"
                rel="noopener noreferrer"
            >
                View pricing
                <IconExternalLink />
            </a>
        </section>
    );
}
