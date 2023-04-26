---
title: "Monorepos are great! ... for now."
slug: 2023-04-22-monorepos-are-great
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - repos
    - monorepos
    - multi-repos
    - Git
    - code base
    - startups
    - authentication
hide_table_of_contents: false
---

None of us in the software industry are immune to the question:

> _How do we want to [re]define our repository structure?_

<!--truncate-->

From tiny, open source startups to behemoth companies like Microsoft, almost everyone in the software industry now uses “repos” to store, manage, and access their product’s code, docs, tooling. A repository is the heart of the company, containing virtually every artifact that comprises the end-product, and most importantly, keeping all of the constantly changing artifacts up-to-date and in-sync across the development landscape.

Understandably, where to keep the company jewels is a massively important question. If you have ever worked in a startup, you might have had the joy of helping to shape that decision… and if you have ever worked in a large company, you probably had the occasion to either praise or curse the decision made early on.

Structure matters. A lot. To everyone.

The best structure (and specifically the use of a monorepo or multiple repos) for any given company or team is subjective. There is no one, definitive answer. In this blog we will take a look at a bit of history about code repositories, some of the reasons for using a monorepo or multiple repos, and then delve into our thinking here at Authentik Security, for how we manage our own code base.

### History of repo-based code

In 2010, software development author Joel Spolsky [described](https://www.joelonsoftware.com/2010/03/17/distributed-version-control-is-here-to-stay-baby/) distributed version control systems (DVCS) as "possibly the biggest advance in software development technology in the [past] ten years”.

He wasn’t wrong. He also, in that same blog, made a great point about DVCS innovation of tracking _changes_, rather than _versions_, which is very relative to the discussion around monorepos versus multi-repos. In a bit, we’ll discuss how the frequency and amount of changes can impact your decision on how to architect your repos.

> 👟 **Sneakerware**: software that requires walking to another machine to manually insert a physical device containing software.

A brief history of code management takes us from the massive UNIVAC machines to mainframe to distributed client/server architectures, and then continue down the road of distributed systems to tools like Subversion and Mercurial and now today’s über-distributed world of Git.

It’s worth noting the relationship between distributed code bases and two other important software development trends that came along around the same time:

-   the _Agile methodology_ provided a way for development teams to move quickly and efficiently, using the power of distributed code (and sophisticated tools like Git) to collaborate, build, and release ever faster.
-   the use of _microservices_; there’s a corollary (but also perhaps a non-analogy) between the repo structure and whether the software leans towards monolithic or is based on microservices (where smaller, loosely coupled services work together to create an application or platform). It’s likely that if you use microservices, you probably have multiple repos, but this doesn’t always have to be the case. It’s a [perfectly fine solution](https://medium.com/taxfix/scaling-microservices-architecture-using-monorepo-domain-driven-design-ced48351a36d) to use a monorepo to store all of your microservices code, and thus reap the benefits of a monorepo.

As it always is with software, and humans, most would agree that our current state in the evolution of repos is working fairly well… but we always push for optimization and further innovation.

### Hello, Goldilocks: what is “just right”?

How to decide the optimum architecture for your repo[s] requires serious research, strategy, and long-term planning. Additionally, an honest self-analysis of your current environment: working styles, experience of your engineering team, the company culture around refactoring and maintenance, and what appetite there is for infrastructure support.

Considerations about the environment and type of code base include:

-   **the number of projects** (and their relationships to each other)
-   **activity level** (active development, refactoring, anything that results in commits and pull requests)
-   **community contributions** (we want it to be easy to navigate the code base)
-   **frequency of releases** (caution, possible slow build times ahead)
-   **testing processes and frequency** (automated testing across _n_ repos)
-   **amount of resources for infrastructure support** (as you scale…)
-   **common dependency packages across projects** (update once, or… 6 times)
-   **highly regulated types of software/data** (GDPR, PIP)
-   **provider/deployment requirements** (i.e. typical 1:1 for Terraform module/repo)

Let’s take a look at some of the benefits and some of the challenges of both mono- and multi-repo structures, and how they relate to to specific environments.

#### Monorepos

One of the best [definitions](https://monorepo.tools/) out there of a monorepo comes from Nrwl:

> _“A monorepo is a single repository containing multiple distinct projects, with well-defined relationships.”_

This definition helps us see why monorepo does not necessarily equal monolith. A well-structured monorepo still has discrete, encapsulated projects, with known and defined relationships, and is not a sprawling incoherent collection of code.

It’s generally agreed that monorepos come with huge advantages. Most specifically, the ease of running build processes, tests, refactoring work, and any common-across-the-code-base tasks. Everything is there in one place, no need to run endless integration tests or cobble together complex build scripts to span multiple code bases. This can increase development, testing, and release-efficiency. Similarly, the use of a single, shared code base can speed up development and innovation.

Monorepos help avoid siloed engineering teams; everyone working in the same code base leads to increased cross-team awareness, collaboration, and learning from one another.

Now for the challenges presented with monorepos. Frankly, monorepos can be expensive when the size and number of projects start to scale up. Getting hundreds of merge conflicts is no one’s idea of fun. Google, Meta, Microsoft, Uber, Airbnb, and Twitter all employ very large monorepos and they have also sall have spent tremendous amounts of time and money and resources to create massive infrastructure systems built specifically to support large code bases in monorepos. The sheer volume of testing, building, maintenance, and release workflows run against such code bases simply would not scale with your typical out-of-the box Git-based system.

For example, even back in 2015 Google had [45,000 commits](https://www.youtube.com/watch?v=W71BTkUbdqE) _per day_ to their monorepo. Not surprisingly, they built a specialized tool for handling that scale, called Blaze. The open source version of this tool is released as Bazel.

Similarly, in order to manage their large monorepo, Microsoft developed the [Virtual File System for Git](https://en.wikipedia.org/wiki/Virtual_File_System_for_Git). The VFS for Git system utilizes a virtual file system that downloads files to local storage only as they are needed.

Needless to say, most us don’t have those types of resources.

#### Multi-repos

For companies with multiple projects with code bases that are not necessarily closely related, or with teams who work on very different areas of responsibility, a multi-repo structure is likely the obvious answer. However, even for companies with projects that are large and coupled, maintaining multiple, smaller repos can be the most simple. For example, if you have a large, enterprise-level web application as your primary product, but are also building mobile versions of the app, it makes sense to keep the mobile apps’ code bases in a separate repo. (Spoiler alert, that’s us in mid-term future!)

Most obviously, using multi-repos reduces the need for investing in large infrastructure teams and systems. With separate code bases, there’s no risk of facing hundreds of merge conflicts, or devoting hours to updates to dependencies, build processes, and deployments. Developers can move quickly, with minimal need to coordinate across teams or apply dependency updates that are not relevant to their code. Releases can happen faster, build times are down, and simplicity often translates into efficiency.

The challenges for multi-repos are basically the inverse of the advantages of a monorepo. With multiple repos, the effort to synch updates for libraries and other dependencies is increased, and if there is any coupling between projects or services, or shared code bases, then special workflows need to be implemented to manage the cross-repo communication. Furthermore, separate repos means that it is more difficult to enforce common practices and workflows, and for disparate teams to learn from one another.

### authentik advantages of a monorepo, for now

We are still a small company here at Authentik Security, moving fast to grow our product’s feature set and leap-frog our competitors, while staying true to our open source origins. We want to innovate, release, and at this stage, tilt towards rapid development. Our engineers and infrastructure team have the ability and desire to collaborate closely and learn from one another; this culture is important going forward, and using a monorepo works as a compelling incentive for team transparency and support across the projects.

The history of authenik provides some additional insight into our use of a monorepo; as the single maintainer for many years, a monorepo was simply easier for me to manage, and even as our wonderful community grew and contributions increased and sponsors appeared, the benefits of a monorepo remain.

So for us, at this stage, we benefit greatly from using a monorepo for the vast majority of our code base (and documentation). Using a monorepo means that as a team, we closely integrate our work: coding, documentation, test suites, refactoring efforts, common dependencies and tooling.

Of course, we have our eyes open and looking towards our future.

> Ironically, as our code base and feature set grows, we believe that we can best retain our focus on building and shipping new features… _by moving towards a multi-repo structure_.

The reasoning is that we do not want to be forced to focus on supporting the infrastructure needed to scale a super-large monorepo, nor on lengthy build times and complicated code management processes. So for now we will continue with our monorepo, but when the Docs or Product teams start whinging about long build times, or when the infrastructure team grows faster than the dev team, we will take another look at our repo structure!

### Where is your tilt?

Share with us your thoughts about how companies choose a repo structure, what works best when, and about our reasoning here at authentik for sticking with a monorepo for now. Leave us a comment below, reach out to us at hello@goauthentik.io, and visit our [GitHub repository](https://github.com/goauthentik/authentik).
