import "./styles.css";

import IconExternalLink from "@theme/Icon/ExternalLink";

export function PlanChooser() {
    return (
        <section className="ak-plans" aria-labelledby="choose-an-enterprise-plan">
            <div className="ak-plans__plan ak-plans__plan--lead">
                <h3>Enterprise Plus</h3>
                <p>
                    Negotiated terms for organizations with procurement, compliance, or scale
                    requirements.
                </p>
                <a className="button button--primary button--lg" href="mailto:sales@goauthentik.io">
                    Contact sales
                </a>
            </div>

            <div className="ak-plans__plan">
                <h3>Enterprise</h3>
                <p>
                    Self-serve licensing for teams that want Enterprise features without a sales
                    process.
                </p>
                <a
                    className="button button--lg ak-plans__buy"
                    href="https://customers.goauthentik.io/"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Buy a license
                </a>
            </div>

            <div className="ak-plans__pricing">
                <a href="https://goauthentik.io/pricing/" target="_blank" rel="noopener noreferrer">
                    Compare both plans and current pricing
                    <IconExternalLink />
                </a>
            </div>
        </section>
    );
}
