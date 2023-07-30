import React from "react";
import styles from "./style.module.css";
import clsx from "clsx";

export function WaitListForm(props) {
    return (
        <section>
            <div
                className="container"
                style={{ marginTop: "2rem", marginBottom: "4rem" }}
            >
                <h2 style={{ textAlign: "center" }}>Join the waitlist</h2>
                <p style={{ textAlign: "center" }}>
                    Sign up to be notified once authentik Enterprise becomes
                    ready!
                </p>

                <div className={"row"}>
                    <div className={"col col--4 margin-vert--md"}></div>
                    <div className={"col col--4 margin-vert--md"}>
                        <form
                            name="enterprise-waitlist-v1"
                            method="post"
                            data-netlify="true"
                            netlify-honeypot="bot-field"
                        >
                            <p style={{ visibility: "hidden" }}>
                                <label>
                                    Don't fill this out if you're human:{" "}
                                    <input name="bot-field" />
                                </label>
                            </p>
                            <input
                                type="hidden"
                                name="form-name"
                                value="enterprise-waitlist-v1"
                            />
                            <input
                                type="hidden"
                                name="product"
                                value={props.product}
                            />
                            <input
                                type="email"
                                name="email"
                                className={clsx(styles.emailInput)}
                                placeholder="Your Email address"
                            />
                            <button
                                className="button button--primary button--lg button--block"
                                type="submit"
                            >
                                Join
                            </button>
                        </form>
                    </div>
                    <div className={"col col--4 margin-vert--md"}></div>
                </div>
            </div>
        </section>
    );
}
