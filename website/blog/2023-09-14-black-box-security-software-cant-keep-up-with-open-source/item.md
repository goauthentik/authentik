---
title: Black box security software can’t keep up with open source
description: "There will always be bugs and vulnerabilities in software. Accepting that, which distribution model gives you more confidence and flexibility?"
slug: 2023-09-14-black-box-security-software-cant-keep-up-with-open-source
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - open core
    - SSO
    - open source
    - community
    - identity provider
    - enterprise
    - source available
    - closed source
    - security
    - authentication
hide_table_of_contents: false
image: ./image1.jpg
---

> **_authentik is an open source Identity Provider that unifies your identity needs into a single platform, replacing Okta, Active Directory, and auth0. Authentik Security is a [public benefit company](https://github.com/OpenCoreVentures/ocv-public-benefit-company/blob/main/ocv-public-benefit-company-charter.md) building on top of the open source project._**

---

Legacy security vendors that rely on black box development can't keep up with open source. It's an oft-discussed topic—the ability of open source communities to quickly jump in and collectively solve problems and innovate solutions—but it is equally believed that "serious" security software companies have proprietary software.

In this blog, we will take a closer look at the pros and cons of the various source availability types of SSO and other security software.

!["mike-kononov-lFv0V3_2H6s-unsplash.jpg"](./image1.jpg)

<!--truncate-->

Since we’re going to use these terms a lot in our discussion, some definitions first:

|                  |                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Open source      | Code that is free to inspect, use, modify, and distribute                                                                             |
| Closed source    | Code that is proprietary and not publicly available                                                                                   |
| Open core        | A business model based on a core codebase that’s open source (the "open core"), with licensed, proprietary features built on top      |
| Source available | Code that is publicly visible, but must be licensed to use, modify, or distribute (e.g. the proprietary code of an open core company) |

## Why do people choose closed vs open source?

### Security through obscurity

“Walled garden” security software relies on keeping the code secret, which _can_ make it harder for hackers to exploit. Some open source skeptics say that transparency makes the code more vulnerable: bad actors can inspect and modify open source code without having to dig into binary code or reverse engineer anything.

However, with closed source solutions, you’re completely reliant on the vendor having robust security practices—both before and during the event of a critical vulnerability. The technology landscape shifts so quickly and your possible attack surface grows constantly, so it can be a tall order for teams working on proprietary software to keep up with innovation. Closed source software is still vulnerable to zero-day attacks or exploitation of systems that haven’t yet applied a security patch.

### Getting ahead of vulnerabilities

Bug bounty programs are one way for closed source security vendors to preempt exploitation, but the prizes need to be sufficiently compelling. Bad actors can still choose to disclose their findings to the highest bidder instead of the vendor.

At least with open source projects, on balance there are likely to be more good actors actively working with and on the code, or ready to respond to Common Vulnerabilities and Exposures (CVEs).

### Rapid response

If you’re using a closed source solution, you have to wait for the vendor to tell you what to do in the event of a major vulnerability. In the meantime, you just stop using potentially affected parts of your system until they can communicate the impact and how to remediate.

With open source, you have the benefit of a community working together towards the same goal. In a breach, you don’t have to wait around for a vendor to act: you can get patches from the upstream project or hotfix the issue yourself (in the case of smaller open source projects which might be slower to respond).

> Average time-to-fix (TTF) vulnerabilities is now actually faster for open source projects than proprietary software (see Snyk’s [State of Open Source Security Report 2023](https://go.snyk.io/state-of-open-source-security-report-2023-dwn-typ.html)).

## Compliance

Sometimes the choice of closed source has little to do with whether or not the source code is public, and more to do with the requirements of governing bodies and auditors. It’s easier to sell a legacy proprietary solution to stakeholders (in the vein of “Nobody ever got fired for buying IBM”) because they check the right boxes and satisfy compliance requirements. For some organizations, requirements dictate that you need a contract with a vendor rather than relying on an unsupported, community-driven service. Open core solutions can help to fill this gap (which we’ll go into under Support and accountability below).

### Open source projects can have certifications too

Not all open source projects have the time and resources to invest in certifications, but some are pursuing these to make it easier for their solution to be approved for use. At Authentik Security, we’re currently working towards an [ISO/ISE 27001](https://www.iso.org/standard/27001) for authentik, the open source project.

### Certifications don’t _guarantee_ better security

Certifications don’t cover all possible paths to exploitation. Plenty of the major data breaches of the past decade ([Okta](https://www.forbes.com/sites/thomasbrewster/2022/03/23/okta-hack-exposes-a-huge-hole-in-tech-giant-security/), [Experian](https://krebsonsecurity.com/2023/01/experian-glitch-exposing-credit-files-lasted-47-days/), [T-Mobile](https://www.t-mobile.com/news/business/customer-information)) were targeted at the type of large enterprises that likely have every possible security certification, yet they were still hacked. Simply proving that a third party verified that you’re taking _some_ steps to safeguard some data isn’t enough. As the saying goes, the defender needs to win every time, but the attacker only needs to win once.

With [supply chain attacks](https://goauthentik.io/blog/2023-04-07-supply-chain-attacks-what-we-can-all-do-better) becoming more common, you can better understand the provenance of open source code, because you have visibility into dependencies and can validate whether the project is using security tools like Static Composition Analysis (SCA), static or dynamic application security testing (SAST/DAST), multi-factor authentication, etc.

## Support and accountability

> “... big corporations want a neck to choke when things go wrong and Linus is hard to track down” — [steppinraz0r on reddit](https://www.reddit.com/r/cybersecurity/comments/15c3h0q/told_by_a_senior_programmer_that_open_source/jtz0yzx/)

Having a security vendor means accountability: formal support for implementation, bugs, and vulnerabilities. When choosing open source, you do have to consider whether you have the in-house expertise for management and maintenance. Or how confident are you in community support?

There are some legitimate concerns to raise with closed source support though. Some vendors outsource technical support to a third party, which may or may not be vetted (as in the [Okta breach of January 2022](https://www.forbes.com/sites/thomasbrewster/2022/03/23/okta-hack-exposes-a-huge-hole-in-tech-giant-security/)). And, as we saw above, [open source projects actually beat closed source vendors on TTF](https://go.snyk.io/state-of-open-source-security-report-2023-dwn-typ.html).

Security, authentication, and identity management are mission-critical services. For most companies, it’s wiser to be able to run and manage these in house. Again, open core can provide a happy medium solution, as you get:

-   The visibility and transparency of open source
-   Total flexibility and modifiability over the open source core
-   A contract with a company who is actively contributing to and improving the product, and
-   Support for setup and remediation (we just launched dedicated [support for Authentik Security Enterprise](https://goauthentik.io/blog/2023-08-31-announcing-the-authentik-enterprise-release)!)

# Neither open nor closed source is _inherently_ more secure

> “The idea that software is inherently safer because it’s released under an open source license is overly simplistic in the extreme. Just the most obvious reason for this is that opportunity for independent review doesn't guarantee that review will happen. The wisdom of the crowd doesn’t guarantee a third-party review will be better or more thorough than a solid first-party system. Open source provides the possibility of review, and that’s all. Hypothetical eyes make no bugs shallow.” — [godel_unicode on Hacker News](https://news.ycombinator.com/item?id=12284600)

Open source is not a silver bullet for security. The code may be open for inspection, but that doesn’t mean that people are actively examining the code for vulnerabilities.

> “There is evidence that the people who have access to open source are more active in creating new code and extensions than auditing existing code. [One recent study](https://www.darkreading.com/application-security/open-source-developers-still-not-interested-in-secure-coding) showed that OSS developers spent less than 3% of their time working on improving security.” — Eugene H. Spafford, Josiah Dykstra, Leigh Metcalf, [What is Cybersecurity?](https://www.informit.com/articles/article.aspx?p=3172442&seqNum=9)

On the other hand, while closed source code may be hidden and has dedicated teams actively working to secure it, reverse engineering is still possible.

With open source, you also have greater flexibility to avoid vendor lock-in if you’re not comfortable with a vendor’s choices. A recent [DEFCON talk](https://github.com/nyxgeek/track_the_planet/blob/main/nyxgeek_Track_the_Planet_2023.08.14.pdf) shared a user enumeration security risk in Microsoft Azure, which Microsoft did not deem a vulnerability. If you use Azure and don’t want to take that risk, your only option is to switch providers, which can be an onerous change.

With open source, you can fork the project. This can also be true for tools with an open core model: depending on the license for the proprietary edition you may still be able to modify the code.

# Can you trust (but verify)?

There will always be bugs and vulnerabilities in software, whatever the distribution model. Accepting that, which model gives you more confidence?

Whatever solution you choose (whether it’s for authentication, authorization, or scanning), you need to trust that your security vendor will be honest and practice _responsible disclosure_.

The Okta breach eroded trust and reminded us of some critical considerations:

### Do you trust your vendor’s supply chain?

If you’re entrusting a vendor with a mission-critical, sensitive service like authentication, you are also putting your trust in every vendor they choose to work with (which you may not have visibility into).

### Can you expect your vendor to be transparent?

Closed source vendors will optimize for different things when facing a security risk or vulnerability. They must mitigate for their customers as well as considering factors like protecting their reputation. They have to balance damage control with transparency (do they disclose immediately, even before they’re sure of the extent of customers affected?).

Open source projects can also suffer reputation damage. However it’s harder to hide vulnerabilities in public code, and the culture of transparency in open source communities is also an incentive that helps to hold open source vendors accountable.

These factors make it hard to take closed source vendors at their word. With open source code (and some source available solutions, depending on the license), you have the reassurance of being able to:

-   Validate what the code does and how it does it
-   Know what developments are being made
-   Modify the code yourself
-   For greatest confidence and control, [self host](https://goauthentik.io/blog/2023-01-24-saas-should-not-be-the-default)

For mission-critical services like authentication and identity management, you don’t want to be beholden to a third party to be transparent and act quickly in the event of a CVE. Using security tools that build on open source gives you the most visibility and the flexibility.

Authentik Security offers both an open source version and a source available version of our flagship product, [authentik](https://goauthentik.io/). Either way, we don't ever give you a black box.
