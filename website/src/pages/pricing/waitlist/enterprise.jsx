import React from "react";
import { WaitListForm } from "../../../components/Waitlist";
import Layout from "@theme/Layout";

export default function waitListEnterprise() {
    return (
        <Layout title="Waitlist">
            <WaitListForm product="enterprise"></WaitListForm>
        </Layout>
    );
}
