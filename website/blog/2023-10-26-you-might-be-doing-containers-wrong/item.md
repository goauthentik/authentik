---
title: 3 ways you (might be) doing containers wrong
description: “Using containers is not a best practice in itself. Here are some mistakes beginners make with containers, and how we set them up correctly at authentik.”
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - application
    - runtime
    - SSO
    - Docker
    - containers
    - :latest
    - identity provider
    - security
    - authentication
hide_table_of_contents: false
---

_authentik is an open source Identity Provider that unifies your identity needs into a single platform, replacing Okta, Active Directory, and Auth0. Authentik Security is a [public benefit company](https://github.com/OpenCoreVentures/ocv-public-benefit-company/blob/main/ocv-public-benefit-company-charter.md) building on top of the open source project._

---

There are two ways to judge an application:

1. Does it do what it’s supposed to do?
2. Is it easy to run?

This post is about the second.

Using containers is not a best practice in itself. As an infrastructure engineer by background, I’m pretty opinionated about how to set up containers properly. Doing things the “right” way makes things easier not just for you, but for your users as well.

Below are some common mistakes that I see beginners make with containers:

1. Using one container per application
2. Installing things at runtime
3. Writing logs to files instead of stdout

## Mistake #1: One container per application

There tend to be two mindsets when approaching setting up containers:

-   The inexperienced usually think 1 container = 1 application
-   The other option is 1 container = 1 service

Your application usually consists of multiple services, and to my mind these should always be separated into their own containers (in keeping with the [Single Responsibility Principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)).

For example, authentik consists of four components (services):

-   Server
-   Worker
-   Database
-   Cache

With our deployment, that means you get four different containers because they each run one of those four services.

### Why you should use one container per _service_

At the point where you need to scale, or need High Availability, having different processes in separate containers enables horizontal scaling. Because of how authentik deploys, if we need to handle more traffic we can scale up to 50 servers, rather than having to scale up _everything_. This wouldn’t work if all those components were all bundled together.

Additionally, if you’re using a container orchestrator (whether that’s Kubernetes or something simpler like [Docker Compose](https://goauthentik.io/docs/installation/docker-compose)), if it’s all bundled together, the orchestrator can’t distinguish between components because they’re all in the black box of your container.

Say you want to start up processes in a specific order. This isn’t possible if they’re in a single container (unless you rebuild the entire image). If those processes are separate, you can just tell Docker Compose to start them up in the order you want, or you can run specific components on specific servers.

Of course, your application architecture and deployment model need to support this setup, which is why it’s critical to think about these things when you’re starting out. If you’re reading this and thinking, I have a small-scale, hobby project, this doesn’t apply to me—let me put it this way: you will never regret setting things up the “right” way. It’s not going to come back to bite you if your situation changes later. It also gives users who install the application a lot more freedom and flexibility in how _they_ want to run it.

## Mistake #2: Installing things at runtime

Your container image should be complete in itself: it should contain all code and dependencies—everything it needs to run. This is the point of a container—it’s self contained.

I’ve seen people set up their container to download an application from the vendor and install it into the container on startup. While this does work, what happens if you don’t have internet access? What if the vendor shut down and that URL now points to a malicious bit of code?

If you have 100 instances downloading files at startup (or end up scaling to that point), this can lead to rate limiting, failed downloads, or your internet connection getting saturated—it’s just inefficient and causes problems that can be avoided.

### Also, don’t use :latest

This leads me to a different but related bad practice: using the `:latest` tag. It’s a common pitfall for folks who use containers but don’t necessarily build them themselves.

It’s easy to get started with the `:latest` tag and it’s understandable to want the latest version without having to go into files and manually edit everything. But what can happen is that you update and suddenly it’s pointing to a new version and breaking things.

I’ve seen this happen where you’re just running something on a local server and your disk is full, so you empty out your Docker images. The next time you pull, it’s with a new version which now no longer works and you’re stuck trying to figure out what version you were on before.

### Instead: Pin your dependencies

You should be pinning your dependencies to a specific version, and updating to newer versions intentionally rather than by default.

The most reliable way to do this is with a process called GitOps:

-   In the context of Kubernetes, all the YAML files you deploy with Kubernetes are stored in the central Git repository.
-   You have software in your Kubernetes cluster that automatically pulls the files from your Git repo and installs them into the cluster.
-   Then you can use a tool like [Dependabot](https://github.com/dependabot) or [Renovate](https://github.com/renovatebot/renovate) to automatically create PRs with a new version (if there is one) so you can test and approve it, and it’s all captured in your Git history.

GitOps might be a bit excessive if you’re only running a small hobby project on a single server, but in any case you should still pin a version.

For a long time, authentik purposefully didn’t have a `:latest` tag, because people would use it inadvertently (sometimes not realizing they had an auto-updater running). Suddenly something wouldn’t work and there wasn’t really a way to downgrade.

We have since added it due to popular request. This is how authentik’s version tags work:

-   Our version number is 3 digits reflecting the date of the release, so the latest currently is [2023.10.1](https://goauthentik.io/docs/releases/2023.10).
    -   You can either use 2023.10.1 as the tag, pinning to that specific version
    -   You can pin to 2023.10, which you means that you always get the latest patch version, or
    -   You can use 2023, which means you always get the latest version within that year.

The principle is roughly the same with any project using [SemVer](https://semver.org/): you could just lock to v1, which means you get the latest v1 with all minor patches and fixes, without breaking updates. Then you switch to v2 when you’re ready.

With this approach you are putting some trust in the developer not to publish any breaking changes with the wrong version number (but you’re technically always putting trust in some developer when using someone else’s software!).

## Mistake #3: Writing logs to files instead of stdout

This is another issue on the infrastructure side that mainly happens when you put legacy applications into containers. It used to be standard that applications put their log output into a file, and you’d probably have a system daemon set up to rotate those files and archive the old ones. This was great when everything ran on the same server without containers.

A lot of software still logs to files by default, but this makes collecting and aggregating your services logs much harder. Docker (and containers in general) expect that you log to standard output so your orchestration platform can route the logs to your monitoring tool of choice.

Docker puts the logs into a JSON file that it can read itself and see the timestamps and which container the log refers to. You can set up log forwarding with both Docker and Kubernetes. If you have a central logging server, the plugin gets the standard output of a container and sends it to that server.

Not logging to `stdout` just makes it harder for everyone, including making it harder to debug: Instead of just running `docker logs` + the name of the container, you need to `exec` into the container, go to find the files, then look at the files to start debugging.

### This bad practice is arguably the easiest one to work around

As an engineer you can easily redirect the logs back from a file into the standard output, but there’s no real reason not to do it the “correct” way.

There aren’t many use cases where there’s an advantage to writing your logs directly to a file instead of stdout—in fact the main one is for when you’re making the first mistake (having your whole application in one container)! If you’re running multiple services in one container, then you’ll have logs from multiple different processes in one place, which _could_ be easier to work with in a file vs stdout.

Even if you specifically want your logs to exist in a file, by default if you run `docker logs` it just reads a JSON file that it adds the logs to, so you’re not losing anything by logging to stdout. You can configure Docker to just put the logs into a plain text file wherever you want to.

It’s a little simplistic, but I’d encourage you to check out [The Twelve-Factor App](https://12factor.net/) which outlines good practices for making software that’s easy to run.

Are you doing containers differently and is it working for you? Let us know in the comments, or send us an email at hello@goauthentik.io!
