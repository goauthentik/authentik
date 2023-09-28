import React from "react";
import { WaitListForm } from "../../../components/Waitlist";
import Layout from "@theme/Layout";

export default function waitlistCloud() {
    return (
        <Layout title="Waitlist">
            <WaitListForm product="cloud"></WaitListForm>
        </Layout>
    );
}
