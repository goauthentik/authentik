import React from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import Card from "../../components/PricingQuestions/Card";

export default function pricingPage() {
    return (
        <Layout title="Pricing">
            <section>
                <div
                    className="container"
                    style={{ marginTop: "2rem", marginBottom: "4rem" }}
                >
                    <h1 style={{ textAlign: "center" }}>Pricing</h1>
                    <p style={{ textAlign: "center" }}>
                        All variants include security patches for all supported
                        versions.
                    </p>

                    <div className={"row"}>
                        <div className={"col col--4 margin-vert--md"}>
                            <div className="card" style={{ height: "28rem" }}>
                                <div className="card__header">
                                    <h3>Open-source</h3>
                                </div>
                                <div className="card__body">
                                    <li>Open Source</li>
                                    <li>Self Hosted</li>
                                    <li>Supports OAuth2/OpenID Connect</li>
                                    <li>Supports SAML</li>
                                    <li>Supports LDAP</li>
                                    <li>Supports Proxy authentication</li>
                                    <li>Advanced policy engine</li>
                                    <li>Community Support</li>
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
                            <div className="card" style={{ height: "28rem" }}>
                                <div className="card__header">
                                    <h3>Enterprise</h3>
                                </div>
                                <div className="card__body">
                                    <li>Source-available</li>
                                    <li>Self Hosted</li>
                                    <li>LTS releases</li>
                                    <li>Enterprise support plan (50 Users+)</li>

                                    <br></br>
                                    <h3>Upcoming features</h3>
                                    <li>Push-notification multifactor</li>
                                    <li>Desktop authentication</li>
                                    <li>AI-based risk assessment</li>
                                </div>
                                <div className="card__footer">
                                    <h1>
                                        $5 <small>/user/month</small>
                                    </h1>
                                    <a
                                        className="button button--info button--block"
                                        href="./waitlist/enterprise"
                                    >
                                        Join waitlist
                                    </a>
                                </div>
                            </div>
                        </div>

                        <div className={"col col--4 margin-vert--md"}>
                            <div className="card" style={{ height: "28rem" }}>
                                <div className="card__header">
                                    <h3>Cloud</h3>
                                </div>
                                <div className="card__body">
                                    <li>All the features of enterprise</li>
                                    <li>Hosted and Managed by authentik</li>
                                    <li>
                                        Easily shift to self hosted if needed
                                    </li>
                                </div>
                                <div className="card__footer">
                                    <h3>Starting at 100 users / $500/month</h3>
                                    <h1>
                                        $5 <small>/user/month</small>
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
                <div
                    className="container"
                    style={{ marginTop: "2rem", marginBottom: "3rem" }}
                >
                    <div class="row">
                        <div className="col col--8 col--offset-2">
                            <p className="hero__subtitle margin--md">
                                Frequently Asked Questions
                            </p>
                            <div class="card-demo margin--md">
                                <Card
                                    body="No. As part of our core principal, we will not move any features from the open source version to the enterprise version. Features from the enterprise version are periodically moved to the open source version."
                                    title="Will any feature of the open-source version ever become enterprise?"
                                />
                                <Card
                                    body="We're always curious to hear what our customers are interested in and what they want to see in authentik, so if you have any questions about features send an email to <a href='mailto:hello@goauthentik.io'>hello@goauthentik.io</a>."
                                    title="Are you planning to add X to authentik?"
                                />
                                <Card
                                    body="Anyone that wants to use the enterprise features listed above. There's no minimum user amount required for enterprise."
                                    title="Who should use Enterprise plans?"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </Layout>
    );
}
