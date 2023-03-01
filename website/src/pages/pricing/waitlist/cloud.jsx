import React from "react";
import { WaitListForm } from "../_waitlist.jsx";
import Layout from "@theme/Layout";

export default function waitlistCloud() {
    return (
        <Layout title="Waitlist">
            <WaitListForm product="cloud"></WaitListForm>
        </Layout>
    );
}
