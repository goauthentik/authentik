---
title: "My hobby became my job, 50% extra pay, just needed to let go of GPLv3"
slug: 2023-08-23-my-hobby-became-my-job
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - founder
    - SSO
    - open source
    - identity provider
    - licensing
    - gpl
    - mit
    - security
    - authentication
hide_table_of_contents: false
image: ./image1.jpg
---

There’s been a lot of discussion about licensing in the news, with [Red Hat](https://www.redhat.com/en/blog/furthering-evolution-centos-stream) and now [Hashicorp](https://www.hashicorp.com/blog/hashicorp-adopts-business-source-license) notably adjusting their licensing models to be more “business friendly,” and [Codecov](https://blog.sentry.io/lets-talk-about-open-source/) (proudly, and mistakenly) [pronouncing](https://about.codecov.io/blog/codecov-is-now-open-source/) they are now “open source.”

“Like the rest of them, they have redefined ‘Open’ as in ‘Open for business’”—[jquast on Hacker News](https://news.ycombinator.com/item?id=37021360)

This is a common tension when you’re building commercially on top of open source, so I wanted to share some reflections from my own experience of going from MIT, to GPL, back to MIT.

!["Photo by <a href="https://unsplash.com/@gcalebjones?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Caleb Jones</a> on <a href="https://unsplash.com/photos/J3JMyXWQHXU?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>"](./image1.jpg)

<!--truncate-->

I started working on the project that led to [authentik](https://github.com/goauthentik/authentik) when I was 20. My original vision was a single pane of glass for emails, domains, applications, hosting, and so on. This was overly ambitious for one person and their hobby project, and I ended up spending most of my time on the SSO part. This became its own project: Passbook (later [renamed to authentik](https://github.com/goauthentik/authentik/pull/361) due to a [naming conflict](https://techcrunch.com/2015/06/08/apple-rebrands-passbook-to-wallet/)).

Initially, authentik used the MIT license. When [Elastic called out AWS](https://www.elastic.co/blog/why-license-change-aws) for trademark abuse (offering Elasticsearch as an AWS service without collaborating with Elastic), I [changed it to GPLv3](https://github.com/goauthentik/authentik/commit/4671d4afb4d32988ca0058a33888862bd9652b16) because I didn’t like what AWS did in principle, and didn’t want it to happen to authentik.

# An opportunity, and a compromise

Two years later, [Sid](https://www.linkedin.com/in/sijbrandij/) at [Open Core Ventures](https://opencoreventures.com/) (OCV) contacted me about [creating a company](../2022-11-02-the-next-step-for-authentik/item.md), building on the features and functionality of authentik. It was a dream opportunity: work full time on my hobby project and make 25% more in the process. But I had to let go of the GPL license.

With an open core model customers are usually using code from both the open source and proprietary codebases. This necessitates a dual license structure, meaning customers need to accept both licenses.

The drawback of building commercially on top of open source software using GPL is that the copyleft aspect can put some people off. Not every person or business wants to have to expose their code for every minor change or bug fix they may add, and they will sooner find a competitor with a more permissive license than adopt your software. This is obviously not ideal when you’re trying to get traction and grow a business.

OCV proposed we switch back to MIT.

# Considerations and tradeoffs

I was very conflicted about reverting to MIT because we had chosen GPL for a reason, but the circumstances had changed. As a company and a real legal entity, we would have recourse if something like AWS/Elasticsearch were to happen—it wouldn’t just be me trying to defend myself while also doing my day job. The decision forced me to reflect on what it means to build a company on top of an existing open source project.

For me, it was an opportunity to work full time on a passion project, with more resources to invest in building and maintaining the open core of the project. The opportunity came with tradeoffs to be made, and a responsibility to be a good steward of the open source project.

I know how volatile startups can be. I had put so much time into authentik already, and my biggest concern was around what happens if things don’t work out. I wanted to make sure that the open source version stays free, vibrant, and open for use by all.

## A license isn’t the only way to guarantee good behavior

With a permissive license, the risk of [bait and switch](https://opencoreventures.com/blog/2022-10-preventing-the-bait-and-switch-open-core/) is always there. A commercial company needs to become profitable and there is precedent for changing to more limited licenses when it suits the business. People naturally see this as a dichotomy: you either have a copyleft license and therefore your intentions are enshrined in the license, or a permissive one and can’t be trusted to uphold open source ideals.

There is a third path though, which is the route we eventually took with [Authentik Security](https://goauthentik.io/), the company we were building on top of the project. We incorporated as a public benefit company, which means that we are legally bound by the terms in the [OCV Public Benefit Company Charter](https://github.com/OpenCoreVentures/ocv-public-benefit-company/blob/main/ocv-public-benefit-company-charter.md). This includes commitments to keeping open source products open source, and ensuring the majority of new features added in a calendar year are made available under an open source license. Being a public benefit company means we are still held accountable, just through a different mechanism than the license.

# The process of changing the license

Changing licenses is a sensitive issue. I consulted with the top contributors to authentik to hear their feedback while we were in the process of setting up Authentik Security. Nobody objected, so we [switched back to MIT](https://github.com/goauthentik/authentik/commit/47132faffbac1098dadba73435164e655901e9e7) and announced the change in the [company announcement post](https://goauthentik.io/blog/2022-11-02-the-next-step-for-authentik). I think I was surprised there wasn’t a backlash or accusations of putting profit over principle (we have all seen [how](https://news.ycombinator.com/item?id=37081306) [impassioned](https://news.ycombinator.com/item?id=36971490) [people](https://news.ycombinator.com/item?id=37003489) [get](https://news.ycombinator.com/item?id=36990036) about open source and ideals). I like to think that people saw the pragmatism in the decision: that MIT lets us further the work of authentik.

# Reflections

While a copyleft license is one way to hold companies accountable to upholding the principles of open source, with Authentik Security we struck a balance between commercial viability with the more permissive MIT license and the values I wanted to entrench with becoming a Public Benefit Company. I now get to work full time on my hobby, and the core of authentik is still open source.
