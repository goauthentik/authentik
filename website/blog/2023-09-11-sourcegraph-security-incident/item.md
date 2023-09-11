---
title: "Sourcegraph security incident: the good, the bad, and the dangers of access tokens"
slug: 2023-08-11-sourcegraph-security-incident
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - Sourcegraph
    - token
    - transparency
    - identity provider
    - leaks
    - breach
    - cybersecurity
    - security
    - authentication
hide_table_of_contents: false
image: ./image1.jpg
---

Access tokens make identity management and authentication relatively painless for our end-users. But, like anything to do with access, tokens also can be fraught with risk and abuse.

The recent [announcement](https://about.sourcegraph.com/blog/security-update-august-2023) from Sourcegraph that their platform had been penetrated by a malicious hacker using a leaked access token is a classic example of this balance of tokens being great… until they are in the wrong hands.

This incident prompts all of us in the software industry to take yet another look at how our security around user identity and access can be best handled, to see if there are lessons to be learned and improvements to be made. These closer looks are not only at how our own software and users utilizes (and protects) access tokens, but also in how such incidents are caught, mitigated, and communicated.

![Photo by <a href="https://unsplash.com/@juvnsky?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Anton Maksimov 5642.su</a> on <a href="https://unsplash.com/photos/wrkNQmhmdvY?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>](./image1.jpg)

<!--truncate-->

## What happened at Sourcegraph

The behavior of the malicious hacker after they accessed the platform reveal a fairly typical pattern: access the system, gain additional rights by creating new user accounts, switching accounts to fully probe the system, and finally, inviting other malicious actors in through the breach. Unfortunately, it is usually that last step, not the first, that sets off alarm bells.

Let’s take a look at what occurred at Sourcegraph.

On July 14, 2023, an engineer at Sourcegraph created a PR and committed a code change to GitHub that contained an active site-admin access token. This level of access token had privileges to not only view but also edit user account information.

For the next two weeks, the leak seems to have remained undetected, but on Aug 28 a new account was created, apparently by the hacker-to-be, and on Aug 30th the hacker used the leaked token to grant their account admin-level privileges, thereby gaining access to the Admin dashboard.

On the dashboard, the hacker was able to see the first 20 accounts displayed, along with the license keys for each account. Sourcegraph did [state](https://www.securityweek.com/sourcegraph-discloses-data-breach-following-access-token-leak/) that possession of the license key did not allow for access to each account’s Sourcegraph instance, fortunately.

However, the intruder didn’t stop with seeing the license keys; they went on to create a proxy app that allowed any users of the app to access Sourcegraph’s APIs for free. Instructions on how to use the app were widely circulated on the internet, with almost 2 million views.

> “_Users were instructed to create free Sourcegraph.com accounts, generate access tokens, and then request the malicious user to greatly increase their rate limit._” ([source](https://about.sourcegraph.com/blog/security-update-august-2023))

The subsequent spike in API usage is what alerted the Sourcegraph security team to a problem, the very same day, August 30, 2023. The team identified the hacker’s site-admin account, closed the account and then began an investigation and mitigation process.

One significant detail is how the malicious hacker obtained the access token in the first place: from a commit made to the Sourcegraph repository on GitHub. It’s unlikely we will ever know how the token was included in the commit. What we do know is that shortly after the breach was announced a [PR](https://github.com/sourcegraph/sourcegraph/pull/56363) was opened to remove from the Sourcegraph documentation instructions about hardcodong access tokens .

Most companies have serious checks in their automated build processes, and it sounds like Sourcegraph did have some checks in place, but it didn’t catch the exposure of this access token in the commit. Back to the statement about these types of incidents causing us all to look again, more closely, at our practices; here at Authentik Security we do indeed have a very robust set of checks in place as part of our required CI/CD pipeline, and we use [Semgrep](https://github.com/returntocorp/semgrep) to search for tokens and other artifacts that we not want to expose. With Semgrep, you can write a custom rule to look for an exact token schema, so that no matter what type of tokens you use, their presence in the code base can be discovered.

## Best practice around tokens

Access tokens have for decades been an essential artifact used in application systems to efficiently and securely manage authentication. They are not going away anytime soon. The onus is on the software companies, and their security engineers, to optimize the protection of access tokens.

The best known best practice around access tokens is to make sure that they have a very short shelf-life; they should expire and be unusable within minutes, not hours or days. This is standard practice. In authentik, by default we set the expiration for access tokens at 5 minutes, and we use JWT (JSON Web Tokens) for added security. We blogged about this recently, have a [read](https://goauthentik.io/blog/2023-03-30-JWT-a-token-that-changed-how-we-see-identity).

Of course, there are also refresh tokens to be considered, and protected. There also needs to be strong security around refresh tokens, because they can be used to create new access tokens. Refresh tokens are typically never passed externally, and if the authorization server is a different one than the application server, then the application server will not even see refresh tokens (only short-lived access tokens). Note that this would not have helped in the Sourcegraph incident, since the malicious hacker had admin-level access, and thus had access to the secure cookie with the refresh token.

## Security breaches are inevitable

Constant effort is required to stay ahead of malicious hackers, and we can’t always, not every time. Beyond specific best practices for tokens, security teams can focus on building a company culture that includes an in-depth defense strategy that use encryption for tokens (and other sensitive values) in transit and at rest. Other basic, low-hanging fruit in a solid security plan include purposeful secrets management, granting the “least privilege” needed, and implementing SCA (_software composition analysis_) tooling.

However if a security breach does occur, it’s very important (on many levels) how the hacked company responds to the incident. And the very first part of the response is the _acknowledgement_ that a breach occurred. This act alone, of announcing what happened, when, how, who was impacted, and what the mitigation plans are is absolutely crucial.

Sourcegraph did a great job here; they let us know the same day they knew, and they shared as many details as possible.

> Transparency about the discovery and all the gory details of the breach is vital; it rebuilds trust with users.

Could the breach have been prevented? Sure, of course, on several fronts. The leaked access token should have been found and removed from the code _before_ the commit was made, thus never even available in GitHub repository. Or even if it got into the code base on the repo, a subsequent Semgrep analysis could have caught it, and the token revoked and removed. As it was, two weeks passed with the token sitting there, in public view, before a malicious hacker found and used it.

However, another thing that Sourcegraph got right was their internal architecture and security practices; the fact that they did not store all of the data in one place prevented the intruder from going very deep.

> Sourcegraph [stated](https://about.sourcegraph.com/blog/security-update-august-2023) “Customer private data and code resides in isolated environments and were therefore not impacted by this event.**”**

Sourcegraph was clear and open about exactly who was impacted, and exactly how they were impacted. For open source users it was email addresses. For paid customers, the malicious user could only view the first 20 license key items on the admin dashboard page, and the license keys did not provide access to the users' instances.

## Lessons learned, by all of us

In hindsight, it’s easy to comment on how SourceGraph handled this breach, what they did right and where they could have done better. But the truth is, that with every security incident, ever leaked token, every malicious hack, we all learn new ways to strengthen our security. Hopefully we also continue to learn the importance of transparency, rapid acknowledgement, and full disclosure about the breaches that do, nonetheless, occur.
