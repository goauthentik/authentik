import React from "react";
import { WaitListForm } from "../_waitlist.jsx";
import Layout from "@theme/Layout";

export default function waitListEnterprise() {
    return (
        <Layout title="Waitlist">
            <WaitListForm product="enterprise"></WaitListForm>
        </Layout>
    );
}
