import React from "react";
import clsx from "clsx";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import useBaseUrl from "@docusaurus/useBaseUrl";
import styles from "./styles.module.css";

const features = [
    {
        title: "Easy to Use",
        description: (
            <>
                Identity made easy. authentik makes single-sign on, user
                enrollment and access control simple.
            </>
        ),
    },
    {
        title: "Realise your workflow",
        description: (
            <>
                authentik lets you build your Workflow as you need it, no
                limitations.
            </>
        ),
    },
    {
        title: "Powered by Python",
        description: (
            <>
                Implement custom verification or access control logic using
                Python code.
            </>
        ),
    },
];

function Feature({ imageUrl, title, description }) {
    const imgUrl = useBaseUrl(imageUrl);
    return (
        <div className={clsx("col col--4", styles.feature)}>
            {imgUrl && (
                <div className="text--center">
                    <img
                        className={styles.featureImage}
                        src={imgUrl}
                        alt={title}
                    />
                </div>
            )}
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
    );
}

function Home() {
    const context = useDocusaurusContext();
    const { siteConfig = {} } = context;
    return (
        <Layout title="Welcome" description={siteConfig.tagline}>
            <header className={clsx("hero hero--primary", styles.heroBanner)}>
                <div className="container">
                    <div className="row">
                        <div className="col padding-top--lg">
                            <h1 className="hero__title">
                                {siteConfig.tagline}
                            </h1>
                            <p className="hero__subtitle">
                                authentik is an open-source Identity Provider
                                focused on flexibility and versatility
                            </p>
                            <div className={styles.buttons}>
                                <Link
                                    className={clsx(
                                        "button button--outline button--secondary button--lg",
                                        styles.getStarted
                                    )}
                                    to={useBaseUrl("docs/installation/index")}
                                >
                                    Get Started
                                </Link>
                            </div>
                        </div>
                        <div className="col text--center hero_image">
                            <img alt="authentik logo" src="/img/logo.png" />
                        </div>
                    </div>
                </div>
            </header>
            <main>
                <section className={styles.features}>
                    <div className="container">
                        <div className="row">
                            {features.map((props, idx) => (
                                <Feature key={idx} {...props} />
                            ))}
                        </div>
                        <div className="row">
                            <div className="col col--5">
                                <div></div>
                            </div>
                            <div className="col col--5 col--offset-2 padding-vert--xl">
                                <h2>What is authentik?</h2>
                                <p>
                                    authentik is an open-source Identity Provider
                                    focused on flexibility and versatility. You
                                    can use authentik in an existing environment
                                    to add support for new protocols. authentik
                                    is also a great solution for implementing
                                    signup/recovery/etc in your application, so
                                    you don't have to deal with it.
                                </p>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </Layout>
    );
}

export default Home;
