---
title: "Supply chain attacks: what we can all do better"
slug: 2023-04-07-supply-chain-attacks-what-we-can-all-do-better
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - supply chain attack
    - token
    - identity provider
    - history
    - security
    - cyberattack
    - authentication
hide_table_of_contents: false
---

Supply chains, whether for automotive parts or microprocessors, are complex, as we all know from recent history. Modern software, with more components than ever and automated package management, is also complex, and this complexity provides a rich environment for supply chain attacks. Supply chain attacks inject malicious code into an application via the building blocks of the application (for example, dependencies) in order to compromise the app in order to infect multiple users.

<!--truncate-->

Using the inherent connections and dependencies of our typical complex workflows for upgrades, deployments, build systems, and other software maintenance workflows, supply chain attackers take advantage of the distributed networks and the myriad of third-party hardware, software, services to insert malware into core systems, and take control from there.

For example, NMS (Network Management Systems) are prime targets for attackers, who can use credentials for system _monitoring_ to laterally move into positions that allow _control_ of target systems. This tunneling into the complex system is a hallmark of supply chain attacks. With so many parts and pieces, plus frequently lax gatekeeping of access between components and layers, determined attackers can easily find an unwatched access point to enter, then steadily progress through the system to gain more and more control.

The tight integration and dependency of so many vendors means that dangers are sometimes overlooked; we have become too passive due to the ease of current automation. We run updates and build processes with a click of a few buttons, often without thinking about what exact set of libraries, tools, and apps are being used. What makes supply chain attacks even more difficult to foresee is the fact that often the suite of components come with signed certificates; the vendors don’t even yet know that their own software has been compromised.

Supply chain attacks are on the rise, and in 2022 supply chain attacks surpassed the number of malware-based attacks [by 40%](https://www.helpnetsecurity.com/2023/01/26/data-compromises-2022/#:~:text=The%20number%20of%20data%20breaches%20resulting%20from%20supply%20chain%20attacks,%2Dbased%20attacks%20by%2040%25).

The 2020 attack on Solarwinds was one of the first major major supply chain attacks. In this case, the attackers took advantage of the very standard upgrade process used by SolarWinds and most major IT companies; SolarWinds unknowingly distributed software updates that included the hacked code to its customers, potentially as many as 33,000. The hacked code, deployed on each customer’s site, was then used to install even more malware.

> The 2021 supply chain attacks on [Malwarebytes](https://www.packetlabs.net/posts/malwarebytes-breach/) and [Mimecast](https://www.mimecast.com/blog/important-update-from-mimecast/) demonstrate that any company can be targeted, even security companies. [Immuniweb](https://www.immuniweb.com/blog/state-cybersecurity-dark-web-exposure.html) reported in 2020 that 97% of the world's leading cybersecurity companies had data leaks or other security incidents exposed on the dark web.

In response to the growing threat, a Presidential Executive Order [EO 14028](<https://www.gsa.gov/technology/technology-products-services/it-security/executive-order-14028-improving-the-nations-cybersecurity#:~:text=Executive%20Order%20(EO)%2014028%20%2D,and%20software%20supply%20chain%20integrity.>) was issued in early 2021, with the explicit purpose “to enhance cybersecurity and software supply chain integrity.” This order applies to both government and private companies, specifically any companies that provide software to the government. The order provides a framework of best practices to help strengthen protection against cyberattacks, and [new regulations](https://www.insidegovernmentcontracts.com/2023/02/january-2023-developments-under-president-bidens-cybersecurity-executive-order/) continue to be issued under this Order.

## Open source software is vulnerable too

> _90% of all applications contain open-source code_

Sonatype's [2020 State of the Software Supply Chain Report](https://www.sonatype.com/2020ssc) makes it clear that vulnerabilities in open source projects also impact major enterprise-level companies.

Consider the vulnerability in the Apache Log4j library used for logging user activity, where a remote code execution (RCE) vulnerability in the component Log4Shell is used by malicious hackers to access and control one or more remote servers. This incident highlights how bad actors can take advantage of our dependency on software as common as third-party libraries.

## The role of Identity Providers

Those of us in the business of SSO, IAM, and any type of identity provider software are uniquely positioned to help harden the industry against supply chain attacks, and mitigate the risks.

Authentication tools provide an obvious first line of defense against attacks, with the initial request for username and password. However, using SSO software also provides additional layers of authentication deep within your software ecosystem, with gatekeeping and secure handshakes using internal-only tokens between the many components. Read more about how authentik uses “[machine-to-machine](https://goauthentik.io/docs/providers/oauth2/client_credentials)” authentication, with internally generated [JWT tokens](https://goauthentik.io/blog/2023-03-30-JWT-a-token-that-changed-how-we-see-identity).

-   **Session duration**: SSO software, by default, typically have short access sessions (minutes or hours, not days) because shorter sessions force frequent re-authentication. With authentik, access sessions expire after 60 minutes, by default. You can customize the duration for sessions in authentik and for the apps that use authentik as an SSO, as well as what type of credentials (fingerprint, code, etc) are required when a user logs back in.
-   **Privileged accounts**: Additionally, IAMs allow you to manage privileged accounts (such as super-users) from a single interface. Frequent monitoring of activity, deleting old accounts, and minimizing the number of super-users greatly reduces the chances for bad actors to use dormant accounts and gain access.
-   **Multifactor Authentication**: MFA is immensely important in mitigating cyber-attacks. In fact, Microsoft’s Group Program Manager for Identity Security and Protection Alex Weinert [stated](https://healthitsecurity.com/news/multi-factor-authentication-blocks-99.9-of-automated-cyberattacks) that “_Based on our studies, your account is more than 99.9 percent less likely to be compromised if you use MFA._”
-   **RBAC**: using a role-based approach strengthens authentication because RBAC enforces the practice of “least privilege”; users are granted exactly the amount of privilege that they need to do their jobs, but no more.
-   **Visibility and control**: An IAM provides visibility via event logs that provide details about login attempts, failed logins, password changes, and much more. Running reports and looking closely at events is important to gain early insight into malicious attempts. Furthermore, observing log activity allows for swift action when needed, such as revoking permissions for users and groups. For example, the authentik dashboard for Event Logs provides insight into all authentication actions and object manipulation, and the Directory of Users and Groups drills down at the user level, and allows for rapid account deactivation.

## Best practices for mitigation

In addition to always implementing an SSO solution, there are other steps that we in the industry can take. I use the word _mitigation_ because we will never be able to 100% prevent supply chain attacks. But we can all do more to help mitigate them.

### Evaluate your trust in vendors

Develop a close relationship with your software vendors. An interesting case to study is the CircleCI hack that began in 2020. CircleCI software contains a lot of stored secrets; after the hack, customers were advised to rotate the secrets. An alternative to storing secrets is to use [JWTs](https://goauthentik.io/docs/providers/oauth2/client_credentials#jwt-authentication), tokens that are signed and certified but do not include the actual secret.

Consider taking these steps in regards to your supply chain vendors:

-   Request an SBOM (Software Bill of Materials) from your vendors. Know exactly what is included in packages and libraries that your team uses.
-   Practice “_dependency vendoring_”, which is the process of having your security team review any required 3rd party tool or library and then, if it passes all the “checks”, host the software internally and have all developers download it from there. In general, limit access to the wide-open web.
-   Read their security updates and release notes, understand exactly what the library or utility or update package is for, and how it interacts with your software and ask what security tests have been run.
-   If you have a SaaS site hosted on the cloud, consider whether moving to on-premise is a more secure long-term plan. Deciding whether to self-host or not is a complex decision, but your site’s security is definitely an important factor.

### Lean in, act in good faith, and trust the community

Two glaring examples of responses to supply chain attacks that could have been handled better:

-   The recent [3CX hack](https://thehackernews.com/2023/03/3cx-desktop-app-targeted-in-supply.html) (in which malware was uploaded as part of what users thought was a regular upgrade) was initially dismissed by the CEO, who stated that the notifications from the community were false positives since the 3CX internal security checks showed all was fine. This is a prime example of choosing not to listen to experts in the community but instead rely only on internal checks.
-   The attack on one of Okta’s vendors in 2022 also displayed a lack of transparency and good faith, as I described in a recent [blog](/blog/2023-01-24-saas-should-not-be-the-default/item.md) about the security benefits of self-hosting. Okta co-founder and CEO Todd McKinnon initially  [tweeted about the attack](https://twitter.com/toddmckinnon/status/1506184721922859010?s=20&t=o7e6RA25El2IEd7EMQD3Xg) stating that the attack was “investigated and contained” and even framing the attack as “an attempt.”

It’s important that everyone, and every company, in the industry works together collaboratively and urgently, and strives to be transparent and share information about known or suspected attacks and vulnerabilities in a timely manner.

In addition to acting in good faith and working to quickly share information, it’s equally important that supply chain attack victims also trust the community, “hear” the early warnings, and respect the collective knowledge and wisdom of the community.

### Consider building your own tools, in house

Sometimes building it yourself actually is the right answer. Don’t quickly run to a 3rd party library or tool that you can implement yourself, and if you don’t have the right resources, consider building up your security team as well as hiring and retaining enough senior-level developers to help with in-house tooling. Recognize that often, busy developers inherently trust anything that can be installed from a package server, so work to create a company culture of thinking through every download.

### Stay up-to-date with patches and security alerts

Whenever any vendor that you use within your environment’s ecosystem issues a security-related patch, make it a priority to research and apply the patch as quickly as possible. If your company or organization doesn’t have a dedicated security team, you can assign this responsibility to another appropriate person; just make sure that you have a documented, up-to-date process for handling security threats.

## What else can we all do?

Here at authentik our engineers and product team are constantly thinking of ways to further harden and protect our users’ sites. We’d love to hear from you all about what you’d like to see done by us, and by the industry as a whole. Leave us a comment below, reach out to us at hello@goauthentik.io, and visit our [GitHub repository](https://github.com/goauthentik/authentik).
