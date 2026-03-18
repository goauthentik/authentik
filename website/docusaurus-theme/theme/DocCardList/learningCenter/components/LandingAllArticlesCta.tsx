import landingStyles from "../../../../components/LearningCenter/styling/landing.module.css";

import Link from "@docusaurus/Link";

interface LandingAllArticlesCtaProps {
    to: string;
    text: string;
}

export default function LandingAllArticlesCta({ to, text }: LandingAllArticlesCtaProps) {
    return (
        <p className={landingStyles.discoveryInlineCta}>
            {text}{" "}
            <Link className={landingStyles.allArticlesLinkInline} to={to}>
                Open full article index
            </Link>
        </p>
    );
}
