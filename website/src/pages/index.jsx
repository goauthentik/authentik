import React from "react";
import clsx from "clsx";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import Head from "@docusaurus/Head";
import BrowserOnly from "@docusaurus/core/lib/client/exports/BrowserOnly";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import useBaseUrl from "@docusaurus/useBaseUrl";
import styles from "./styles.module.css";
import Comparison from "../components/Comparison";
import "react-before-after-slider-component/dist/build.css";
import { NewsBar } from "../components/NewsBar";
import { TextSlide } from "../components/TextSlide";

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
            <Head>
                <meta
                    name="go-import"
                    content="goauthentik.io git https://github.com/goauthentik/authentik"
                ></meta>
            </Head>
            <header className={clsx("hero hero--primary", styles.heroBanner)}>
                <div className="container">
                    <div className={clsx("row", styles.headerRow)}>
                        <div className="col padding-top--lg">
                            <h1
                                className={clsx(
                                    "hero__title",
                                    styles.ak_hero__title,
                                )}
                            >
                                <div>Replace</div>
                                <TextSlide
                                    words={[
                                        "Active Directory",
                                        "Okta",
                                        "Auth0",
                                    ]}
                                ></TextSlide>
                                <div>with a unified platform.</div>
                            </h1>
                            <p className="hero__subtitle">
                                Unify all of your identity needs into a single
                                platform
                            </p>
                            <div className={styles.buttons}>
                                <Link
                                    className={clsx(
                                        "button button--outline button--primary button--lg",
                                    )}
                                    to={useBaseUrl("docs/installation/")}
                                >
                                    Get Started
                                </Link>
                                <Link
                                    className={clsx(
                                        "button button--outline button--primary button--lg",
                                    )}
                                    to="#comparison"
                                >
                                    Reasons to switch
                                </Link>
                            </div>
                        </div>
                        <div
                            className={clsx(
                                "col text--center",
                                styles.heroImage,
                                styles.hiddenOnMobile,
                            )}
                        >
                            <img
                                alt="authentik logo"
                                src={useBaseUrl("img/landing_login_card.jpg")}
                            />
                        </div>
                    </div>
                </div>
            </header>
            <main>
                <section className={styles.features}>
                    <div className="container">
                        <div className={clsx("row", styles.row)}>
                            <Feature
                                title="Easy to use"
                                description={
                                    <>
                                        Identity made easy. authentik makes
                                        single-sign on (SSO), user enrollment,
                                        and access control simple.
                                    </>
                                }
                            />
                            <Feature
                                title="Realize your workflow"
                                description={
                                    <>
                                        authentik lets you build your workflow
                                        as you need it, no limitations.
                                    </>
                                }
                            />
                            <Feature
                                title="Powered by Python"
                                description={
                                    <>
                                        Implement custom verification or access
                                        control logic using Python code.
                                    </>
                                }
                            />
                        </div>
                    </div>
                    <div
                        className={clsx(
                            "row",
                            styles.rowDark,
                            styles.rowFullWidth,
                            styles.newsBar,
                            styles.hiddenOnMobile,
                        )}
                    >
                        <div className="container">
                            <NewsBar />
                        </div>
                    </div>
                    <div className="container">
                        <div className={clsx("row", styles.row)}>
                            <div className="col col--5">
                                <BrowserOnly>
                                    {() => {
                                        const ReactBeforeSliderComponent = require("react-before-after-slider-component");
                                        return (
                                            <ReactBeforeSliderComponent
                                                firstImage={{
                                                    id: 1,
                                                    imageUrl: useBaseUrl(
                                                        "img/landing_screen_apps_dark.jpg",
                                                    ),
                                                }}
                                                secondImage={{
                                                    id: 2,
                                                    imageUrl: useBaseUrl(
                                                        "img/landing_screen_apps_light.jpg",
                                                    ),
                                                }}
                                            />
                                        );
                                    }}
                                </BrowserOnly>
                            </div>
                            <div className="col col--5 col--offset-2 padding-vert--xl">
                                <h2>What is authentik?</h2>
                                <p>
                                    authentik is an open-source Identity
                                    Provider focused on flexibility and
                                    versatility. You can use authentik in an
                                    existing environment to add support for new
                                    protocols, implement sign-up/recovery/etc.
                                    in your application so you don't have to
                                    deal with it, and many other things.
                                </p>
                            </div>
                        </div>
                        <div className={clsx("row", styles.row)}>
                            <div className="col col--5 col--offset-2 padding-vert--xl">
                                <h2>Utmost flexibility</h2>
                                <p>
                                    You can adopt authentik to your environment,
                                    regardless of your requirements. Need an
                                    Active-Directory integrated SSO Provider? Do
                                    you want to implement a custom enrollment
                                    process for your customers? Are you
                                    developing an application and don't want to
                                    deal with User verification and recovery?
                                    authentik can do all of that, and more!
                                </p>
                            </div>
                            <div className="col col--5">
                                <BrowserOnly>
                                    {() => {
                                        const ReactBeforeSliderComponent = require("react-before-after-slider-component");
                                        return (
                                            <ReactBeforeSliderComponent
                                                firstImage={{
                                                    id: 1,
                                                    imageUrl: useBaseUrl(
                                                        "img/landing_screen_admin_dark.jpg",
                                                    ),
                                                }}
                                                secondImage={{
                                                    id: 2,
                                                    imageUrl: useBaseUrl(
                                                        "img/landing_screen_admin_light.jpg",
                                                    ),
                                                }}
                                            />
                                        );
                                    }}
                                </BrowserOnly>
                            </div>
                        </div>
                    </div>
                </section>
                <section>
                    <div className="container">
                        <Comparison></Comparison>
                    </div>
                </section>
                <section>
                    <div
                        className={clsx(
                            styles.footerCTA,
                            styles.rowAuthentik,
                            styles.rowFullWidth,
                        )}
                    >
                        <h1>Try authentik now!</h1>
                        <div className={styles.buttons}>
                            <Link
                                className={clsx(
                                    "button button--outline button--primary button--lg",
                                )}
                                to={useBaseUrl("docs/installation/")}
                            >
                                Get Started
                            </Link>
                            <Link
                                className={clsx(
                                    "button button--outline button--primary button--lg",
                                )}
                                to={useBaseUrl("pricing/")}
                            >
                                Learn about enterprise
                            </Link>
                        </div>
                    </div>
                </section>
            </main>
        </Layout>
    );
}

export default Home;
