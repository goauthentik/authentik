---
title: Okta got breached again and they still have not learned their lesson
description: “HAR files uploaded to Okta support system contained session tokens.”
slug: 2023-10-23-another-okta-breach
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - security breach
    - SSO
    - malicious hacker
    - HAR file
    - session token
    - identity provider
    - security
    - authentication
    - okta
    - cloudflare
    - beyondtrust
    - har
hide_table_of_contents: false
---

> **_authentik is an open source Identity Provider that unifies your identity needs into a single platform, replacing Okta, Active Directory, and Auth0. Authentik Security is a [public benefit company](https://github.com/OpenCoreVentures/ocv-public-benefit-company/blob/main/ocv-public-benefit-company-charter.md) building on top of the open source project._**

---

## Another security breach for Okta

Late last week, on October 20, Okta publicly [shared](https://sec.okta.com/harfiles) that they had experienced a security breach. Fortunately, the damage was limited. However, the incident highlights not only how incredibly vigilant vendors (especially huge vendors of security solutions!) must be, but also how risky the careless following of seemingly reasonable requests can be.

We now know that the breach was enabled by a hacker who used stolen credentials to access the Okta support system. This malicious actor then collected session tokens that were included in HAR files (HTTP **_Archive_** Format) that were uploaded to the Okta support system by customers. A HAR file is a JSON **_archive file_** format that stores session data for all browsers running during the session. It is not rare for a support team troubleshooting an issue to request a HAR file from their customer: [Zendesk](https://support.zendesk.com/hc/en-us/articles/4408828867098-Generating-a-HAR-file-for-troubleshooting) does it, [Atlassian](https://confluence.atlassian.com/kb/generating-har-files-and-analyzing-web-requests-720420612.html) does it, [Salesforce](https://help.salesforce.com/s/articleView?id=000385988&type=1) as well.

So it’s not the HAR file itself; it was what was in the file, and left in the file. And, destructively, it is our collective training to not second-guess support teams; especially the support team at one of the world’s most renowned identity protection vendors.

But it is not all on Okta; every customer impacted by this hack, including 1Password (who communicated the breach to Okta on September 29), BeyondTrust (who communicated the breach on October 2), and Cloudflare (October 18) were "guilty" of uploading HAR files that had not been scrubbed clean and still included session tokens and other sensitive access data. (Cleaning an HAR file is not always a simple task, there are tools like [Google's HAR Sanitizer](https://github.com/google/har-sanitizer), but even tools like that don't 100% guarantee that the resulting file will be clean.)

## Target the ancillaries

An interesting aspect of this hack was that it exploited the less-considered vulnerability of Support teams, not considered to be the typical entry-way for hackers.

But security engineers know that hackers go in at the odd, unexpected angles. A classic parallel is when someone wants data that a CEO has, they don’t go to the CEO, they go to (and through) the CEO’s assistant!

Similarly, the support team at Okta was used as entry point. Once the hacker gained control of a single customer’s account, they worked to take control of the main Okta dashboard and the entire support system. This lateral-to-go-up movement through access control layers is common technique of hackers.

## It’s the response… lesson not yet learned

The timing of Okta's response, not great. The initial denial of the incident, not great. And then, add insult to injury, there’s what can objectively be labeled an [abysmal “announcement” blog](https://sec.okta.com/harfiles) from Okta on October 20.

Everything from the obfuscatory title to the blog’s brevity to the actual writing… and importantly, the lack of any mention at all of BeyondTrust, the company that informed Okta on October 2nd that they suspected a breach of the Okta support system.

> “_Tracking Unauthorized Access to Okta's Support System_” has to be the lamest of all confession titles in the history of security breach announcements.

Not to acknowledge that their customers first informed them seems like willful omission, and it absolutely illustrates that Okta has not yet learned their lesson about transparency, trusting their customers and security partners, and the importance of moving more quickly towards full disclosure. Ironically, BeyondTrust thanks Okta for their efforts and communications during the two week period of investigation (and denial).

Back to the timing; BeyondTrust has written an excellent [article about the breach](https://www.beyondtrust.com/blog/entry/okta-support-unit-breach), with a rather damning timeline of Okta’s responses.

> “We raised our concerns of a breach to Okta on October 2nd. Having received no acknowledgement from Okta of a possible breach, we persisted with escalations within Okta until October 19th when Okta security leadership notified us that they had indeed experienced a breach and we were one of their affected customers.”([source](https://www.beyondtrust.com/blog/entry/okta-support-unit-breach))

The BeyondTrust blog provides important details about the persistence and ingenuity of the hacker.

> “Within 30 minutes of the administrator uploading the file to Okta’s support portal an attacker used the session cookie from this support ticket, attempting to perform actions in the BeyondTrust Okta environment. BeyondTrust’s custom policies around admin console access initially blocked them, but they pivoted to using admin API actions authenticated with the stolen session cookie. API actions cannot be protected by policies in the same way as actual admin console access. Using the API, they created a backdoor user account using a naming convention like existing service accounts.”

Oddly, the BeyondTrust blog about the breach does a better job of selling Okta (by highlighting the things that went right with Okta) than the Okta announcement blog. For example, in the detailed timeline, BeyondTrust points out that one layer of prevention succeeded when the hacker attempted to access the main internal Okta dashboard, but because Okta still views dashboard access as a new sign in, it prompted for MFA thus thwarting the log in attempt.

Cloudflare’s revelation of their communications timeline with Okta shows another case of poor response timing by Okta, another situation where the customer informed the breached vendor first, and the breached company took too long to publicly acknowledge the breach.

> “In fact, we contacted Okta about the breach of their systems before they had notified us.” … “We detected this activity internally more than 24 hours before we were notified of the breach by Okta.” ([source](https://blog.cloudflare.com/how-cloudflare-mitigated-yet-another-okta-compromise/))

In their blog about this incident, Cloudflare provides a helpful [set of recommendations](https://blog.cloudflare.com/how-cloudflare-mitigated-yet-another-okta-compromise/) to users, including sensible suggestions such as monitoring for new Okta users created, and reactivation of Okta users.

Which just takes us back to the rather lean response by Okta; their customers wrote much more informative and helpful responses than Okta themselves.

## Keep telling us

> We can’t be reminded often enough about keeping our tokens safe.

This incident at Okta is parallel to the breach at Sourcegraph that we recently [blogged about](https://goauthentik.io/blog/2023-08-11-sourcegraph-security-incident), in which a token was inadvertently included in a GitHub commit, and thus exposed to the world. With Okta, it was session tokens included in an uploaded HAR file, exposed to a hacker who had already gained access to the Okta support system.

But talk about things that keep security engineers up at night; timing was tight on this one.

The initial breach attempt was noticed by BeyondTrust within only 30 minutes of their having uploaded a HAR file to Okta Support. By default (and this is a good, strong, industry-standard default) Okta session tokens have a lifespan of two hours. However, with hackers moving as quickly as these, 2 hours is plenty long for the damage to be done. So, the extra step of scrubbing clean any and all files that are uploaded would have saved the day in this case.

> Keep your enemies close, but your tokens even closer.

## Stay vigilant out there

Lessons learned abound with every breach. Each of us in the software and technology area watch and learn from each attack. In the blog by BeyondTrust, they provide some valuable steps that customers and security teams can take to monitor for possible infiltration.

Strong security relies on multiple layers, enforced processes, and defense-in-depth policies.

> “The failure of a single control or process should not result in breach. Here, multiple layers of controls -- e.g. Okta sign on controls, identity security monitoring, and so on, prevented a breach.” ([source](https://www.beyondtrust.com/blog/entry/okta-support-unit-breach))

A [writer on HackerNews](https://news.ycombinator.com/item?id=37963074) points out that Okta has updated their [documentation](https://help.okta.com/oag/en-us/content/topics/access-gateway/troubleshooting-with-har.htm) about generating HAR files, to tell users to sanitize the files first. But whether HAR files or GutHub commits, lack of MFA or misuse of APIs, we all have to stay ever-vigilant to keep ahead of malicious hackers.

## Addendum

This blog was edited to provide updates about the [1Password announcement](https://blog.1password.com/okta-incident/) that they too were hacked, and to clarify that the hacker responsible for obtaining session tokens from the HAR files had originally gained entry into the Okta support system using stolen credentials.
