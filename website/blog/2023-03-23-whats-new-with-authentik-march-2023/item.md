---
title: What’s new with authentik - March 2023
slug: 2023-03-23-whats-new-with-authentik-march-2023
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
    - name: Tana Berry
      title: Sr. Technical Content Editor at Authentik Security Inc
      url: https://github.com/tanberry
      image_url: https://github.com/tanberry.png
tags:
    - announcement
hide_table_of_contents: false
---

In a blog from last November 2022, titled “[Next steps for authentik](https://goauthentik.io/blog/2022-11-02-the-next-step-for-authentik)”, I wrote about the launch of [Authentik Security](https://goauthentik.io/), our open core company built around the open source project [authentik](https://github.com/goauthentik/authentik).

In this post, we’d like to provide updates on our progress in building out Authentik Security the company, ramping up the feature set in our open source identity provider, and taking the first steps in developing and offering an enterprise-level feature set for the Cloud or self-hosting. We are enthusiastic about our path forward and our plans to take authentik from a project to a product.

<!--truncate-->

## Company Updates

Authentik Security is now officially almost 6 months old. The energy and vitality of our community-based authentik project continues, and now with a growing staff we can keep the open source product expanding with new releases and also work on launching and growing the company. Mixed into that balance is defining our feature sets for each of our offerings, and developing new functionality for companies that want to deploy authentik at the enterprise level, either self-hosted or on the Cloud as a SaaS offering by Authentik Security.

We have a lot of exciting work in front of us. Check out our [job posts](https://goauthentik.io/jobs/) and consider joining us!

## New features for authentik

Authentik Security aims to always be open and transparent, and our trust in our community’s awesomeness means that we realize you all are experts in the field, the ones working in the security and identity management industry every day (and night!), so we look forward to strengthening our collaboration and communication with you, our user.

We have a roadmap with several new features, and we want to hear your opinions on them. You can write us directly at hello@goauthentik.io or open a [GitHub issue](https://github.com/goauthentik/authentik/issues). For more targeted conversations, we will reach out to schedule calls with users who want to provide more in-depth collaboration and feedback.

### Coming up

Roadmapped features include:

-   **RBAC ~~tighter access control~~**
    -   Currently there’s only the option of users to be superusers or regular users, and superusers can edit everything, including all authentic objects. This goes against the security principle of [least privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege), and as such goes against our security-focused mantra. Role-based access control (RBAC) restricts CRUD rights on authentik objects based on a specific _role,_ providing even more fine-grained control.
-   **UX improvements**
    -   Ease of use and clear, intuitive UIs is always one of our main goals, and we’re now focusing yet more on making the experience of using authentik even better. Less jumping around in the UI and more helpful context actions, suggestions, and recommendations.
-   **Push-notification multifactor authentication** (Enterprise)
    -   authentik recognizes the important of MFA (Multifactor Authentication); in some cases, the old username/password combination alone is less-than-sufficient.
-   **Desktop authentication** (Enterprise)
    -   robust cross-platform desktop authentication to secure access to all machines running in the environment.
-   **AI-based risk assessment** (Enterprise)
    -   AI provides the ability to analyze massive amounts of data that are relevant to security and access, accelerating risk assessment.

### We’re listening

As we grow the company and the feature sets, we are focused on building and maintaining a strong process for consistent communication and collaboration between our product team and our users. We want to hear what are the top features that you would like to see prioritized for our product and development teams. We look forward to conducting user interviews, requests for new features via GitHub Issues, and even surveys fueled by swag giveaways!

## Announcing the new Plans page

We are excited to announce that we will publish a new page on our product website, where we explain our product plans and the pricing for each offering. It’s important to us that we get this right, so we will also implement a communication and input process to gather feedback on our pricing and all offering details.

One of the primary ways for us to hear your input will be right there on the new page. We have created a “waitlist” for each pricing plan, in order to gauge interest in the plans’ feature sets and to learn what feedback you have on the pricing in general. Please join the list and the conversation!

### About the plans

The following offerings are described in detail on the new page (coming soon!) in our website.

-   Open Source

    Our forever-free offering, the open source authentik project, has been active for over 5 years, and now has the support of Authentik Security. For self-hosted environments, works using all major authentication protocols (OAuth2/OpenID Connect, SAML, LDAP, and proxy authentication), with an advanced, customizable policy engine, and community support.

-   Enterprise Self-hosted
   Our Enterprise Self-hosted plan offers all of the features of open source authentic (and is still source-available), plus releases with long-term-support (LTS), an enterprise-level support plan, and additional features for larger organizations such as AI-based risk assessment and multifactor authentication (MFA) with push notification.
-   Enterprise Cloud
   The Enterprise Cloud plan provides the convenience of our enterprise-level product as a SaaS offering, hosted and managed by Authentik Security. For many organizations, the benefits of decreased operational costs and universal data access (no VPN, servers, and network configuration required) make SaaS the best choice. With the cloud offering, the same enterprise-level support plan is included, and migrating to self-hosted is always an option.

Take a look at the new [Plans page](https://goauthentik.io/pricing/), and if you’re interested in the upcoming feature sets and learning more about our Cloud or self-hosted offerings, join the wait list and let’s start talking about what your company needs.

Thanks for reading, and being part of authentik.
