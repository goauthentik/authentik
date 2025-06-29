import React from "react";
import { DevCard, DevCardGrid } from "../DevCards";
import styles from "./DevLanding.module.css";

export const DevLanding: React.FC = () => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Developer Documentation</h1>
          <p className={styles.subtitle}>
            Build, extend, and contribute to the authentik ecosystem
          </p>
        </div>
        <div className={styles.headerGraphic}>
          <div className={styles.graphicCircle}></div>
          <div className={styles.graphicCircle}></div>
          <div className={styles.graphicCircle}></div>
        </div>
      </div>

      <div className={styles.introduction}>
        <p>
          Welcome to the authentik developer hub! Here you'll find everything you need to build with, 
          extend, and contribute to authentik. Whether you're looking to customize your deployment, 
          create integrations, or become a core contributor, these resources will help you get started.
        </p>
      </div>

      <DevCardGrid columns={3}>
        <DevCard 
          title="Getting Started" 
          icon="🚀"
          description="Set up your development environment and start contributing"
          to="/docs/developer-docs/setup/frontend-dev-environment"
          badge="Essential"
          badgeColor="primary"
        >
          <ul>
            <li><a href="/docs/developer-docs/setup/frontend-dev-environment">Frontend Development</a></li>
            <li><a href="/docs/developer-docs/setup/backend-dev-environment">Backend Development</a></li>
            <li><a href="/docs/developer-docs/setup/outpost-dev-environment">Outpost Development</a></li>
          </ul>
        </DevCard>

        <DevCard 
          title="API Documentation" 
          icon="🔌"
          description="Learn how to interact with authentik's API"
          to="/docs/developer-docs/api/overview"
        >
          <ul>
            <li><a href="/docs/developer-docs/api/overview">API Overview</a></li>
            <li><a href="/docs/developer-docs/api/examples">API Examples</a></li>
            <li><a href="/api/v3/schema/swagger-ui/">API Reference</a></li>
          </ul>
        </DevCard>

        <DevCard 
          title="Documentation" 
          icon="📝"
          description="Contribute to authentik's documentation"
          to="/docs/developer-docs/docs/style-guide"
        >
          <ul>
            <li><a href="/docs/developer-docs/docs/style-guide">Style Guide</a></li>
            <li><a href="/docs/developer-docs/docs/templates">Templates</a></li>
            <li><a href="/docs/developer-docs/docs/contributing">Contributing</a></li>
          </ul>
        </DevCard>

        <DevCard 
          title="Releases" 
          icon="📦"
          description="Learn about authentik's release process"
          to="/docs/developer-docs/releases/release-process"
        >
          <ul>
            <li><a href="/docs/developer-docs/releases/release-process">Release Process</a></li>
            <li><a href="/docs/developer-docs/releases/versioning">Versioning</a></li>
            <li><a href="/docs/releases/current">Latest Release</a></li>
          </ul>
        </DevCard>

        <DevCard 
          title="Hackathon" 
          icon="🧩"
          description="Participate in authentik hackathons"
          to="/docs/developer-docs/hackathon"
          badge="Join us"
          badgeColor="info"
        >
          <ul>
            <li><a href="/docs/developer-docs/hackathon">Hackathon Info</a></li>
            <li><a href="https://github.com/goauthentik/authentik/issues?q=is%3Aopen+is%3Aissue+label%3Ahackathon">Hackathon Ideas</a></li>
          </ul>
        </DevCard>

        <DevCard 
          title="Translation" 
          icon="🌐"
          description="Help translate authentik into different languages"
          to="/docs/developer-docs/translation"
        >
          <ul>
            <li><a href="/docs/developer-docs/translation">Translation Guide</a></li>
            <li><a href="https://hosted.weblate.org/projects/authentik/">Weblate Project</a></li>
          </ul>
        </DevCard>

        <DevCard 
          title="Code Structure" 
          icon="🏗️"
          description="Understand authentik's architecture and code organization"
        >
          <ul>
            <li><a href="/docs/developer-docs#authentiks-structure">Package Structure</a></li>
            <li><a href="https://github.com/goauthentik/authentik">GitHub Repository</a></li>
          </ul>
        </DevCard>

        <DevCard 
          title="Contribute" 
          icon="👩‍💻"
          description="How to contribute to authentik"
          to="/docs/developer-docs#how-can-i-contribute"
          badge="New"
          badgeColor="success"
        >
          <ul>
            <li><a href="/docs/developer-docs#reporting-bugs">Report Bugs</a></li>
            <li><a href="/docs/developer-docs#suggesting-enhancements">Suggest Features</a></li>
            <li><a href="/docs/developer-docs#pull-requests">Pull Requests</a></li>
          </ul>
        </DevCard>
      </DevCardGrid>

      <div className={styles.callToAction}>
        <h2>Ready to contribute?</h2>
        <p>Join our community and help make authentik even better!</p>
        <div className={styles.ctaButtons}>
          <a href="https://github.com/goauthentik/authentik" className={styles.primaryButton}>
            GitHub Repository
          </a>
          <a href="https://goauthentik.io/discord" className={styles.secondaryButton}>
            Join Discord
          </a>
        </div>
      </div>
    </div>
  );
};

export default DevLanding; 