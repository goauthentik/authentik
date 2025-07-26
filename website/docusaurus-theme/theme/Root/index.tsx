import { OutdatedVersionBanner } from "../../components/OutdatedVersionBanner";

import React from "react";

interface RootProps {
    children: React.ReactNode;
}

export default function Root({ children }: RootProps): JSX.Element {
    return (
        <>
            <OutdatedVersionBanner />
            {children}
        </>
    );
}
