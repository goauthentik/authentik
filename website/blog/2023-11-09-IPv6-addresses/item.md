---
title: "IPv6 addresses and why you need to make the switch now"
description: "IPv6 addresses have been commercially available since 2010. But is there any compelling reason for sysadmins and security engineers to make the switch?"
slug: 2023-11-09-IPv6-addresses
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - authentik
    - IP address
    - IPv4
    - IPv6
    - IP address exhaustion
    - NAT Gateway
    - IETF
    - Internet Engineering Task Force
    - IANA
    - Internet Assigned Numbers Authority
    - IPv6 address format
    - SSO
    - security
    - identity provider
    - authentication
hide_table_of_contents: false
---

> **_authentik is an open source Identity Provider that unifies your identity needs into a single platform, replacing Okta, Active Directory, and auth0. Authentik Security is a [public benefit company](https://github.com/OpenCoreVentures/ocv-public-benefit-company/blob/main/ocv-public-benefit-company-charter.md) building on top of the open source project._**

---

IPv6 addresses have been commercially available since 2010. Yet, after Google’s IPv6 rollout the following year, the adoption by System Administrators and security engineers responsible for an entire organization’s network has been slower than you might expect. Population size and the plethora of work and personal devices that accompany this large number of workers do not accurately predict which countries have deployed this protocol.

In this blog post, I explain briefly what IP addresses are and how they work; share why at Authentik Security we went full IPv6 in May 2023; and then set out some reasons why you should switch now.

## What are IP addresses?

IP Addresses are locations (similar to street addresses) that are assigned to allow system administrators and others to identify and locate every point (often referred to as a node) on a network through which traffic and communication passes via the internet. For example, every server, printer, computer, laptop, and phone in a single workplace network has its own IP address.

We use domain names for websites, to avoid having to remember IP addresses, though our readers who are sysadmin—used to referencing all sorts of nodes deep within their organization’s networks—will recall them at the drop of a hat.

But, increasingly, since many devices are online and [96.6% of internet users now use a smartphone](https://www.oberlo.com/statistics/how-many-people-have-smartphones), most Internet of Things (IoT) devices that we have in our workplaces and homes _also_ have their own IP address. This includes:

-   Computers, laptops and smartphones
-   Database servers, web servers, mail servers, virtual servers (virtual machines), and servers that store software packages for distribution
-   Other devices such as network printers, routers and services running on computer networks
-   Domain names for websites, which are mapped to the IP address using Domain Name Servers (DNS)

IP addresses are centrally overseen by the Internet Assigned Numbers Authority ([IANA](https://www.iana.org/)), with five [Regional Internet Registries](https://www.nro.net/about/rirs/) (RIRs).

## What is the state of the IP landscape right now?

Well, it’s all down to numbers.

The previous version of this network layer communications protocol is known as IPv4. From our informed vantage point—looking over the rapid growth of ecommerce, business, government, educational, and entertainment services across the internet—it’s easy to see how its originator could not possibly have predicted that demand for IPv4 addresses would outstrip supply.

Add in the ubiquity of connected devices that allow us to access and consume those services and you can see the problem.

IP address exhaustion was foreseen in the 1980s, which is why the Internet Engineering Task Force ([IETF](https://www.ietf.org/)) started work on IPv6 in the early 1990s. The first RIR to run out of IPv4 addresses was ARIN (North America) in 2015, followed by the RIPE (Europe) in 2019, and LACNIC (South America) in 2020. The very last, free /8 address block of IPv4 addresses was issued by IANA in January 2011.

The following realities contributed to the depletion of the IPv4 addresses:

-   IPv4 addresses were designed to use 32 bits and are written with decimal numbers
-   This allowed for 4.3 billion IP addresses

The IPv4 address format is written in 4 groups of 4 numbers, each group separated by a period.

Even though IPv4 addresses still trade hands, it’s actually quite difficult now to buy a completely unused block. What’s more, they’re expensive for smaller organizations (currently around $39 each) and leasing is cheaper. Unless you can acquire them from those sources, you’ll likely now be issued IPv6 ones.

> Interesting historical fact: IPv5 was developed specifically for streaming video and voice, becoming the basis for VoIP, though it was never widely adopted as a standard protocol.

### IPv6 addresses, history and adoption

The development of IPv6 was initiated by IETF in 1994, and was published as a draft standard in December 1998. The use of IPv6, went live in June 2012, and was ratified as an internet standard in July 2017.

There is an often circulated metaphor from J. Wiljakka’s IEEE paper, [Transition to IPv6 in GPRS and WCDMA Mobile Networks](https://ieeexplore.ieee.org/document/995863), stating that every grain of sand on every seashore could be allocated its own IPv6 address. Let me illustrate.

-   IPv6 addresses were designed to use 128 bits and are written with hexadecimal digits (10 numbers from 1-10 and 6 letters from A-F).
-   So, how many IPv6 addresses are there? In short, there are over 340 trillion IP addresses available!

The IPv6 address format is written in 8 groups of 4 digits (each digit can be made up of 4 bits), each group separated by a colon.

> Importantly, the hierarchical structure optimizes global IP routing, keeping routing tables small.

If you plan to make the switch to IPv6, it’s worth noting that you’ll need to ensure that your devices, router, and ISP all support it.

### Upward trend in the worldwide adoption by country

Over 42.9% of Google users worldwide are accessing search using the IPv6 protocol. It’s intriguing to note which countries have a larger adoption of the IPv6 protocol than not:

-   France 74.38%
-   Germany 71.52%
-   India with 70.18%
-   Malaysia 62.67%
-   Greece 61.43%
-   Saudi Arabia 60.93%

And, yet China, Indonesia, Pakistan, Nigeria, and Russia lag surprisingly far behind many others in terms of adoption (between 5-15%) given their population size. Even many ISPs have been slow to switch.

You can consult Google’s [per country IPv6 adoption statistics](https://www.google.com/intl/en/ipv6/statistics.html#tab=per-country-ipv6-adoption) to see where your location sits in the league table.

## Why we decided on a full IPv6 addresses deployment

The average internet user won’t be aware of anything much beyond what an IP address is, if even that. However for system administrators, IP addresses form a crucial part of an organization’s computer network infrastructure.

In our case, the impetus to use IPv6 addresses for authentik came from our own, internal Infrastructure Engineer, Marc Schmitt. We initially considered configuring IPv4 for internal traffic and, as an interim measure, provide IPv6 at the edge only (remaining with IPv4 for everything else). However, that would still have required providing IPv6 support for customers who needed it.

In the end, we determined it would be more efficient to adopt the IPv6 addresses protocol while we still had time to purchase, deploy, and configure it at our leisure across our existing network. We found it to be mostly a straightforward process. However, there are still some applications that did not fully support IPv6, but we were aided by the fact that we use open source software. This means that we were able to contribute back the changes needed to add IPv6 support to the tools we use. We were thrilled to have close access to a responsive community with some (not all!) of the tool vendors and their communities to help with any integration issues. [Plausible](https://plausible.io/), our web analytics tool, was especially helpful and supportive in our shift to IPv6.

### Future proofing IP addresses on our network and platform

While it seemed like there was no urgent reason to deploy IPv6 across our network, we knew that one day, it _would_ suddenly become pressing once ISPs and larger organizations had completely run out of still-circulating IPv4 addresses.

For those customers who have not yet shifted to IPv6, we still provide IPv4 support at the edge, configuring our load balancers to receive requests over IPv4 and IPv6, and forwarding them internally over IPv6 to our services (such as our customer portal, for example).

### Limiting ongoing spend

Deployment of IPv6 can be less expensive as time goes on. If we’d opted to remain with IPv4 even temporarily, we knew we would have needed to buy more IPv4 addresses.

In addition, we were paying our cloud-provider for using the NAT Gateway to convert our IPv4 addresses—all of which are private—to public IP addresses. On top of that, we were also charged a few cents per GB based on users. The costs can mount up, particularly when we pull Docker images multiple times per day. These costs were ongoing and on top of our existing cloud provider subscription. With IPv6, however, since IP addresses are already public—and there is no need to pay for the cost of translating them from private to public—the costs are limited to paying for the amount of data (incoming and outgoing traffic) passing through the network.

### Unlimited pods

Specifically when using the IPv4 protocol, there’s a limitation with our cloud provider if pulling IP addresses from the same subnet for both nodes and Kubernetes pods. You are limited by the number of pods (21) you can attach to a single node. With IPv6, the limit is so much higher that it's insignificant.

### Clusters setup

All original clusters were only configured for IPv4. It seemed like a good time to build in the IPv6 protocol while we were already investing time in renewing a cluster.

We’d already been planning to switch out a cluster for several reasons:

-   We wanted to build a new cluster using ArgoCD (to replace the existing FluxCD one) for better GitOps, since ArgoCD comes with a built-in UI and provides a test deployment of the changes made in PRs to the application.
-   We wanted to change the Container Network Interface (CNI) to select an IP from the same subnet as further future-proofing for when more clusters are added (a sandbox for Authentik Security and another sandbox for customers, for example). We enhanced our AWS-VPC-CNI with [Cilium](https://cilium.io/) to handle the interconnections between clusters and currently still use it to grab IPs.

## IPv6 ensures everything works out-of-the-box

If you’re a system administrator with limited time and resources, you’ll be concerned with ensuring that all devices, software, or connections are working across your network, and that traffic can flow securely without bottlenecks. So, it’s reassuring to know that IPv6 works out of the box—reducing the onboarding, expense, and maintenance feared by already overburdened sysadmins.

### Stateless address auto-configuration (SLAAC)

When it comes to devices, each device on which IPv6 has been enabled will independently assign IP addresses by default. With IPv6, there is no need for static or manual DHCP IP address configuration (though manual configuration is still supported). This is how it works:

1. When a device is switched on, it requests a network prefix.
2. A router or routers on the link will provide the network prefix to the host.
3. Previously, the subnet prefix was combined with an interface ID generated from an interface's MAC address. However, having a common IP based on the MAC address raises privacy concerns, so now most devices just generate a random one.

### No need to maintain both protocols across your network or convert IPv4 to IPv6

Unless you already have IPv6 deployed right across your network, if your traffic comes in via IPv4 or legacy networks, you’ll have to:

-   Maintain both protocols
-   Route traffic differently, depending on what it is

### No IP addresses sharing

Typically, public IP addresses, particularly in Europe, are shared by multiple individual units in a single apartment building, or by multiple homes on the same street. This is not really a problem for private individuals, because most people have private IP addresses assigned to them by their routers.

However, those in charge of the system administration for  organizations and workplaces want to avoid sharing IP addresses. We are almost all subject to various country, state, and territory-based data protection and other compliance legislation. This makes it important to reduce the risks posed by improperly configured static IP addresses. And, given the virtually unlimited number of IP addresses now available with the IPv6 protocol, configuring unique IP addresses for every node on a network is possible.

## OK but are there any compelling reasons for _me_ to adopt IPv6 addresses _now_?

If our positive experience and outcomes, as well as the out-of-the-box nature of IPv6 have not yet persuaded you, these reasons might pique your interest.

### Ubiquitous support for the IPv6 addresses protocol

Consider how off-putting it is for users that some online services still do not offer otherwise ubiquitous identity protection mechanisms, such as sign-on Single Sign-on ([SSO](https://goauthentik.io/blog/2023-06-21-demystifying-security)) and Multi-factor Authentication (MFA). And, think of systems that do not allow you to switch off or otherwise configure pesky tracking settings that contradict data protection legislation.

Increasingly and in the same way, professionals will all simply assume that our online platforms, network services, smart devices, and tools support the IPv6 protocol—or they might go elsewhere. While IPv6 does not support all apps, and migration can be risky, putting this off indefinitely could deter buyers from purchasing your software solution.

### Man-in-the-Middle hack reduction

Man-in-the-Middle (MITM) attacks rely on redirecting or otherwise changing the communication between two parties using Address Resolution Protocol (ARP) poisoning and other naming-type interceptions. This is how many malicious ecommerce hacks target consumers, via spoofed ecommerce, banking, password reset, or MFA links sent by email or SMS. Experiencing this attack is less likely when you deploy and correctly configure the IPv6 protocol, and connect to other networks and nodes on which it is similarly configured. For example, you should enable IPv6 routing, but also include DNS information and network security policies

## Are there any challenges with IPv6 that I should be aware of before starting to make the switch?

Great question! Let’s address each of the stumbling blocks in turn.

### Long, multipart hexadecimal numbers

Since they are very long, IPv6 addresses are less memorable than IPv4 ones.

However, this has been alleviated using a built-in abbreviation standard. Here are the general principles:

-   Dropping any leadings zeros in a group
-   Replacing a group of all zeros with a single zero
-   Replacing continuous zeros with a double colon

Though this might take a moment to memorize, familiarity comes through use.

### Handling firewalls in IPv6

With IPv4, the deployment of Network Address Translation (NAT) enables system administrators in larger enterprises, with hundreds or thousands of connected and online devices, to provide a sense of security. Devices with private IP addresses are displayed to the public internet via NAT firewalls and routers that mask those private addresses behind a single, public one.

-   This helps to keep organizations’ IP addresses, devices, and networks hidden and secure.
-   Hiding the private IP address discourages malicious attacks that would attempt to target an individual IP address.

This lack of the need for a huge number of public IPv4 addresses offered by NAT has additional benefits for sysadmins:

-   Helping to manage the central problem of the limited number of available IPv4 addresses
-   Allowing for flexibility in how you build and configure your network, without having to change IP addresses of internal nodes
-   Limiting the admin burden of assigning and managing IP addresses, particularly if you manage a large number of devices across networks

### Firewall filter rules

It is difficult for some to move away from this secure and familiar setup. When it comes to IPv6 however, NAT is not deployed. This might prove to be a concern, if you are used to relying on NAT to provide a layer of security across your network.

Instead, while a firewall is still one of the default protective mechanisms, system administrators must deploy filter rules in place of NAT.

-   In your router, you’ll be able to add both IPv4 and IPv6 values—with many device vendors now enabling it by default.
-   Then, if you’ve also configured filtering rules, when packets encounter the router, they’ll meet any firewall filter rules. The filter rule will check if the packet header matches the rule’s filtering condition, including IP information.
    -   If it does, the Filter Action will be deployed
    -   If not, the packet simply proceeds to the next rule

If you configure filtering on your router, don’t forget to also enable IPv6 there, on your other devices, and on your ISP.

## Have you deployed IPv6 addresses to tackle address exhaustion?

Yes, it is true that there is still a way to go before IPv6 is adopted worldwide, as we discussed above. However, as the pace of innovative technologies, solutions, and platforms continues, we predict this will simply become one more common instrument in our tool bag.

We’d be very interested to know what you think of the IPv6 protocol, whether you’ve already converted and how you found the process. Do you have any ongoing challenges?

Join the Authentik Security community on [Github](https://github.com/goauthentik/authentik) or [Discord](https://discord.com/invite/jg33eMhnj6), or send us an email at hello@goauthentik.io. We look forward to hearing from you.
