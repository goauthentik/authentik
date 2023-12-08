---
title: Building an OSS security stack with Loki, Wazuh, and CodeQL to save $100k
description: “You don’t have to spend a lot developing a good security posture from the beginning. Here’s how we built Authentik Security’s stack with mostly free and open source tools.”
slug: 2023-11-22-how-we-saved-over-100k
authors:
    - name: authentik Security Team
      url: https://goauthentik.io
      image_url: ./icon.png
tags:
    - authentik
    - FOSS
    - security budget
    - security stack
    - Red Team
    - Blue Team
    - SBOM
    - hardening
    - penetration testing
    - monitoring
    - SSO
    - insider threats
    - certifications
    - security
    - identity provider
    - authentication
hide_table_of_contents: false
---

> **_authentik is an open source Identity Provider that unifies your identity needs into a single platform, replacing Okta, Active Directory, and auth0. Authentik Security is a [public benefit company](https://github.com/OpenCoreVentures/ocv-public-benefit-company/blob/main/ocv-public-benefit-company-charter.md) building on top of the open source project._**

---

There was an article recently about nearly 20 well-known startups’ [first 10 hires](https://www.lennysnewsletter.com/p/hiring-your-early-team-b2b)—security engineers didn’t feature at all. Our third hire at Authentik Security was a security engineer so we might be biased, but even startups without the resources for a full-time security hire should have someone on your founding team wearing the security hat, so you get started on the right foot.

As security departments are cost centers (not revenue generators) it’s not unusual for startups to take a tightwad mentality with security. The good news is that you don’t need a big budget to have a good security posture. There are plenty of free and open source tools at your disposal, and a lot of what makes good security is actually organizational practices—many of which don’t cost a thing to implement.

> We estimate that using mostly non-commercial security tools saves us approximately $100,000 annually, and the end-result is a robust stack of security tools and processes.

Here’s how we built out our security stack and processes using mostly free and open source software (FOSS).

<!--truncate-->

## Blue Team efforts

Security efforts can mostly be grouped into two categories: Blue Team and Red Team. Your Blue Team is defensive, meaning guarding against potential attacks. The Red Team is offensive, actively seeking for weaknesses and potential vulnerabilities. Startups with scant resources should focus on Blue activities first.

### Visibility: Do you know what is happening in your environment?

The first step is to get eyes into your environment through SIEM (Security Information Event Monitoring). A security person’s worst nightmare is things happening without them knowing about it. You can’t react to an attack that you don’t know is happening! You need a tool that monitors your team’s device logs and flags suspicious activity.

We’re an all-remote and globally distributed team, which makes monitoring both harder and more important; team members can log in from anywhere, at any time, and we don’t have a central headquarters to house a secure server for backups, for example. We needed something that’s available worldwide and compatible with our endpoint device architectures, cloud infrastructure, and SaaS solutions.

We settled on [Wazuh](https://wazuh.com/platform/siem/), which has been around for a long time, is open source and well supported. We’ll acknowledge that it is a bit harder to deploy than some other, proprietary solutions. This can often be the case with FOSS, and it’s a tradeoff you have to accept when you’re not paying for something.

If you don’t want to use something that’s tricky to stand up, you can of course pay for a tool with which you’ll get customer support and all those good things. Your first priority should be picking something that fits your company’s needs.

We also use Grafana’s [Loki](https://grafana.com/oss/loki/) (which is free for self-hosted environments) for certain types of log aggregation. Logging is still a staple for security awareness, so do your research for the best logging and analysis solution.

The general idea behind having good visibility is to gather as many data points as possible while minimizing ongoing maintenance overhead. Make no mistake, this step is not only crucial, but never-ending. Companies are always standing up and tearing down infrastructure, on- and off-boarding employees, etc. Without visibility and monitoring of these activities, it’s easy to leave something exposed to opportunistic attackers.

### Understand your dependencies: SBOMs for the win

If you’re a small, early-stage startup, you’re more likely to get caught in a large-scale, net-casting campaign than in any sophisticated, targeted attacks. That means it’s critical to have awareness of your dependencies, so you can quickly understand if a critical vulnerability affects any part of your software supply chain. When the [Log4Shell vulnerability](https://theconversation.com/what-is-log4j-a-cybersecurity-expert-explains-the-latest-internet-vulnerability-how-bad-it-is-and-whats-at-stake-173896) surfaced in December 2021, the companies that were aware of their dependencies were able to mitigate quickly and close the attack window.

This is where a Software Bill of Materials (SBOM) comes in handy. Your SBOM isn’t just a checkbox exercise for auditing and compliance requirements. We use OWASP’s [Dependency Track](https://dependencytrack.org/) (also free and open source) to ingest our SBOM and help identify parts of the codebase that may be at risk from new vulnerabilities. We also use [Semgrep](https://semgrep.dev/) for code scanning with pattern-based recognition. It’s open source and free to run locally.

It’s also worth mentioning that if your company’s product is open source, or you have an open core model (a proprietary product built on open source), you may qualify for access to free tooling from GitHub for your open source project: we use [Dependabot](https://github.com/dependabot) for automated dependency updates and [CodeQL](https://codeql.github.com/) for code analysis to identify vulnerable code.

### Hardening

Now that you’ve got visibility into your environment, your next step is hardening: reducing or eliminating potential threats. We can group these efforts into two categories: _organizational security_ and _product security_.

#### Organizational security

Raise your hand if you’ve worked at a small startup and have seen the following:

-   Shared credentials
-   Spreadsheets for IT/People teams to create all logins for new employees on the day they join
-   Team members introducing new software/tooling at whim

It can be a free-for-all at small companies, and while the risk is low at that scale, it can be much harder to introduce more rigorous processes later. The team will be resistant because you’ve added friction where there wasn’t before.

Ideally, you want to introduce secure-by-default practices into your team and company early on:

-   Multi-factor authentication
-   Single sign on
-   Just-in-time permissions
-   Evaluation of new tooling

In the case of open source software, you can inspect the code to check how data is being handled, how secure the databases are, what exact kind of data is being transferred, saved, etc. Another team best practice is around vetting the tools and dependencies that the team uses; even if you don’t have time or resources to do a full vet of every new piece of software your coworkers want to use, at least check for certifications.

Here at Authentik Security, we tackle a lot of risk factors with one shot: [authentik](https://goauthentik.io/). By using SSO, we can ensure every new employee has the correct credentials for accessing the appropriate workplace apps, and that every departing employee immediately has access revoked with one click. We can also quarantine suspect users, essentially cutting off access to all systems quickly. Ironically, one of the most common initial access points is ex-employee credentials.

These all contribute to ‘defense in depth’—adding layers of security and complications to make it as hard or annoying as possible for attackers to get around. These practices typically cost $0 to implement and will set you up for good security posture as you grow.

#### Product security

This layer is really anything to do with securing the actual product you’re building (not your company). This typically means getting third-party penetration testing (if you don’t have a dedicated Red Team—more on this below) and remediating vulnerabilities you’ve surfaced through your monitoring and dependency tracking efforts.

## Red Team efforts

As we mentioned above, the Red Team is offensive, meaning they attack the company (physically or remotely) to poke holes in your own defenses before the real bad actors can.

### Internal penetration testing

Now that we have implemented monitoring, and hardened a few things, it’s time to test how well we did. This is where we take the attacker’s point of view to try to break in and test our own controls over our systems, to expose weaknesses. Just recently we discovered that Authentik had a bunch of domains that we’d left open, unmonitored. It’s a constant, iterative loop of unearthing holes via your internal penetration testing (also called pentesting or white box testing) and finding ways to plug them.

There are a lot of tools to choose from here (everyone likes breaking into things!). You’re never done choosing your stack—the threat landscape evolves constantly and so does the tooling to keep up with it. You’ll want to pay attention to new developments by keeping an eye on discussions on Twitter, Reddit, Hacker News, etc. When a new way to attack something develops (and it always will), someone will go create the special automation tooling to address that threat. (Then your attackers are going to go grab that tool and see if they can hack their way in. It’s a constant wheel.)

At Authentik we use the [Kali Linux](https://www.kali.org/) distribution, which has a host of hacking tools on it, for penetration testing. It’s well known within the security world and is open source and free to use.

Testing can be a tough one for small startups, because you likely won’t have a dedicated Red Team and commercial pentesting doesn’t come cheap. If you can save on your tooling though, that can help to free up resources for contracting out this type of work. The main goal you’re after is trying to identify the low-hanging fruit that inexperienced actors may exploit.

### A note on insider threats

[Okta has been in the news](https://goauthentik.io/blog/2023-10-23-another-okta-breach) (again!) after its second major breach in two years. A team member [unknowingly uploaded a file containing sensitive information to Okta’s support management system](https://www.crn.com/news/security/okta-faces-potential-for-reputational-risk-after-second-major-breach-in-two-years-analysts), highlighting the risk of insider threats.

Your employees are a risk factor—whether through malice, ignorance, or carelessness. It’s not unheard of for someone to accidentally save a password publicly to the company’s cloud. It can be an honest mistake, but it’s very-low hanging fruit for a bad actor just watching your cloud assets.

With the rise of Ransomware as a Service, there’s also always the possibility that a disgruntled employee can act as an initial access broker: either accidentally or purposefully giving their credentials or their access to someone else. It’s obviously not possible to prevent all possible compromises, so it’s important that your tooling is set up to alert you to unusual activity and your processes are in place so you can react quickly.

## Do you really need certifications?

Apart from using security certifications like ISO/IEC 27001 and SOC 2 to evaluate vendors that make the software you are using, certifications can vouch for your organizational security, which might be important to your customers, depending on what your product does and who your customers are.

For us at Authentik Security, [our source code](https://github.com/goauthentik/authentik) is available for inspection, but that doesn’t tell people anything about how we handle emails, payment information, and so on. That’s where a third-party certification comes in: an auditor verifies your security practices, which in turn signals to your customers that you can be trusted.

Certifications can be expensive though, and as a cash-strapped startup, you may not want or be able to invest in a certification. However there’s nothing stopping you from ingraining some of those good security practices in your company’s culture anyway. That way, you’re already building a strong security posture and when the time comes, you’re not rushing to implement processes that feel unnatural to the team.

Again, it comes back to getting off on the right foot so that you’re not spending 10-20x the amount of money later in people time and resources to course correct later.

## Security doesn’t have to be a big-company luxury

People imagine that large corporations have security all figured out, but a large security department doesn’t guarantee that they have any idea what other teams are doing. As a small company, you do have one thing going for you: it’s much easier to have eyes on everything that’s happening. You’re more tightly knit and you can encompass more with fewer resources.

If you talk to a lot of security people, their happy place is when no one is doing anything. Then your job’s pretty easy. Unfortunately, if you want your company to succeed, you need your developers to develop, your salespeople to talk to prospects, your CEO to meet with whomever they need to meet with. These are standard operations that all put the company at risk, but it’s your job to mitigate that risk the best you can.

Our security engineer likes to say they work alongside teams, not blocking them. If security says it’s their job to make sure there are no vulnerabilities, and it’s the development team’s job to make new features, how do you get these two sides to work together?

Realistically, everything has vulnerabilities. You’re never going to have a completely safe, locked-down environment. So, you partner with other teams and find a compromise. Establish a minimum threshold people have to meet to keep going. If you’re too inflexible, those teams won’t want to work with you and they won’t tell you when they’re making new virtual machines or writing new code.

## Repercussions

You don’t need to be a security company for these things to matter. This advice applies no matter what type of product you’re building.

[Some 422 million individuals were impacted by data compromises in 2022](https://www.statista.com/statistics/273550/data-breaches-recorded-in-the-united-states-by-number-of-breaches-and-records-exposed/). As consumers we have almost become numb to news of new breaches. A company gets breached, they offer some sort of credit protection, cyber insurance might go up a bit, but life goes on.

If you’re still not motivated to invest in your security posture (or trying to win over teammates who prioritize feature shipping over everything), consider the [case of SolarWinds](https://www.sec.gov/news/press-release/2023-227). The company appears to have exaggerated their internal security posture, leading to an indictment from the SEC.

So not only is security important, it could actually keep you out of jail.

_What’s in your security stack? Let us know in the comments, or send us an email at hello@goauthentik.io!_
