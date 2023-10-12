import React from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import Card from "../../components/PricingQuestions/Card";
import useBaseUrl from "@docusaurus/useBaseUrl";

export default function pricingPage() {
    return (
        <Layout title="Pricing">
            <section>
                <div
                    className="container"
                    style={{ marginTop: "2rem", marginBottom: "2rem" }}
                >
                    <h1 style={{ textAlign: "center" }}>Pricing</h1>

                    <div className={"row"}>
                        <div className={"col col--4 margin-vert--md"}>
                            <div className="card" style={{ height: "100%" }}>
                                <div className="card__header">
                                    <h3>Open Source</h3>
                                </div>
                                <div className="card__body">
                                    <li>Open source</li>
                                    <li>Self-hosted</li>
                                    <li>Supports OAuth2/OpenID Connect</li>
                                    <li>Supports SAML</li>
                                    <li>Supports LDAP</li>
                                    <li>Supports SCIM</li>
                                    <li>Supports Proxy authentication</li>
                                    <li>Advanced policy engine</li>
                                </div>
                                <div className="card__footer">
                                    <h1>Free, forever</h1>
                                    <Link
                                        className="button button--primary button--block"
                                        href={"/docs/"}
                                    >
                                        Get Started
                                    </Link>
                                </div>
                            </div>
                        </div>
                        <div className={"col col--4 margin-vert--md"}>
                            <div className="card" style={{ height: "100%" }}>
                                <div className="card__header">
                                    <h3>Enterprise Self-Hosted</h3>
                                </div>
                                <div className="card__body">
                                    <li>Self-hosted</li>
                                    <li>Source-available</li>
                                    <li>Long-term-support releases</li>
                                    <li>Enterprise support plan</li>
                                    <li>Web-based RDP/SSH access (planned)</li>
                                    <li>Push-notification MFA (planned)</li>
                                    <li>Desktop authentication (planned)</li>
                                    <li>AI-based risk assessment (planned)</li>
                                </div>
                                <div className="card__footer">
                                    <h1>
                                        $5 <small>/internal user/month</small>
                                    </h1>
                                    <h1>
                                        $0.02{" "}
                                        <small>/external user/month</small>
                                    </h1>
                                    <a
                                        className="button button--primary button--block"
                                        target="_blank"
                                        href="https://customers.goauthentik.io/"
                                    >
                                        Get Started
                                    </a>
                                </div>
                            </div>
                        </div>
                        <div className={"col col--4 margin-vert--md"}>
                            <div className="card" style={{ height: "100%" }}>
                                <div className="card__header">
                                    <h3>Enterprise Cloud</h3>
                                </div>
                                <div className="card__body">
                                    <li>Hosted and Managed by authentik</li>
                                    <li>
                                        Easily shift to self-hosted if needed
                                    </li>
                                    <li>Source-available</li>
                                    <li>Long-term-support releases</li>
                                    <li>Enterprise support plan</li>
                                    <li>Web-based RDP/SSH access (planned)</li>
                                    <li>Push-notification MFA (planned)</li>
                                    <li>Desktop authentication (planned)</li>
                                    <li>AI-based risk assessment (planned)</li>
                                </div>
                                <div className="card__footer">
                                    <h4>Minimum 100 users</h4>
                                    <h1>
                                        $5 <small>/user/month</small>
                                    </h1>
                                    <h1>
                                        $0.02{" "}
                                        <small>/external user/month</small>
                                    </h1>
                                    <a
                                        className="button button--info button--block"
                                        href="./waitlist/cloud"
                                    >
                                        Join waitlist
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section>
                <div className="container" style={{ marginBottom: "3rem" }}>
                    <div className="row">
                        <div className="col col--8 col--offset-2">
                            <h2 className="hero__subtitle margin--md">
                                Frequently Asked Questions
                            </h2>
                            <div className="card-demo margin--md">
                                <Card
                                    title="Will any feature of the open-source version ever become enterprise?"
                                    body="No. As part of our core principle, we will not move any features from the open source version to the enterprise version. Features from the enterprise version are periodically moved to the open source version."
                                />
                                <Card
                                    title="Can I get paid support for the open-source version?"
                                    body="We only offer support as part of an enterprise license. You can get community support on GitHub and Discord for the open-source version."
                                />
                                <Card
                                    title="What's the difference between internal and external users?"
                                    body="Internal users might be users such as company employees, which will get access to the full Enterprise feature set. External users might be external consultants or B2C customers. These users don't get access to enterprise features."
                                />
                                <Card
                                    title="Are you planning to add X to authentik?"
                                    body="We're always curious to hear what our customers are interested in and what they want to see in authentik, so if you have any questions about features send an email to <a href='mailto:hello@goauthentik.io'>hello@goauthentik.io</a>."
                                />
                                <Card
                                    title="Who should use Enterprise plans?"
                                    body="Anyone that wants to use the enterprise features listed above. There's no minimum user amount required for enterprise."
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </Layout>
    );
}
