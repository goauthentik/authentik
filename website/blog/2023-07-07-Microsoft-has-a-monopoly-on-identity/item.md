---
title: "Microsoft has a monopoly on identity, and everyone knows it except the FTC"
slug: 2023-07-07-Microsoft-has-a-monopoly-on-identity
authors:
    - name: Jens Langhammer
      title: CTO at Authentik Security Inc
      url: https://github.com/BeryJu
      image_url: https://github.com/BeryJu.png
tags:
    - blog
    - monopoly
    - FTC
    - Microsoft
    - bundling
    - Active Directory
    - identity management
    - authentication
hide_table_of_contents: false
---

The FTC (Federal Trade Commission) punished Microsoft for exerting its power in 2001, but Microsoft learned to hide its power, especially when Satya Nadella took over from Steve Ballmer and pursued a services model that builds and leverages power while maintaining plausible deniability.

At Authentik, we’ve seen the monopolistic powers that Microsoft has over the identity management sector, but identity is a canary in the coal mine for a much wider, much stronger monopoly.

<!--truncate-->

## How software ate the monopoly concept

In the FTC’s definition of [monopolization](https://www.ftc.gov/advice-guidance/competition-guidance/guide-antitrust-laws/single-firm-conduct/monopolization-defined), Microsoft is the only company and case cited by name. Ironically, Microsoft has grown even more since that case. The FTC has caught on to how powerful their technology is, and even threatened to reverse Facebook and Instagram acquisition, but hasn’t updated its understanding of what a monopoly can be.

And because of that misapprehension, Microsoft has, ironically, become the tech industry’s preeminent monopoly.

### Microsoft’s three landmark antitrust cases

The following three cases that the FTC brought against Microsoft highlight not a willingness to bust monopolies, but rather the evolution of Microsoft learning how to play the game of monopolization.

-   [2001](https://www.thebignewsletter.com/p/microsoft-brings-a-cannon-to-a-knife): The FTC blocked Microsoft’s acquisition of Intuit and sued the company for bundling Internet Explorer with PCs.
    -   Microsoft learned its lesson: Become friends with the government, position itself as the friendly tech company, and focus on leveraging monopolistic powers rather than seizing actual monopolies.
    -   Thanks to how the FTC focuses on [consumer welfare](https://www.thebignewsletter.com/p/facebook-hits-1-trillion-in-market), Microsoft learned it could maintain plausible deniability.
-   [2020](https://siliconangle.com/2023/01/25/report-eu-preparing-launch-antitrust-investigation-microsoft-teams/): Slack filed an antitrust suit against Microsoft focusing on Teams
    -   Microsoft offered to charge for Teams ([source](https://www.google.com/search?q=antitrust+slack+salesforce&sourceid=chrome&ie=UTF-8#ip=1:~:text=Microsoft%20offers%20to,com%20%E2%80%BA%20articleshow)) and unbundle Teams from Office ([source](https://www.theinformation.com/briefings/microsoft-to-separate-teams-office-products-under-eu-antitrust-scrutiny))
    -   Despite a probe, Salesforce completed the acquisition of Slack ([source](https://slack.com/blog/news/salesforce-completes-acquisition-of-slack))
    -   Slack selling to Salesforce was likely a “[defensive merger](https://www.thebignewsletter.com/p/an-economy-of-godzillas-salesforce)” and Microsoft’s flexibility shows it’s willing to sacrifice a short-term monopoly for the long-term payoff of retaining monopolistic effects.
-   2023: The UK government ([source](https://www.thebignewsletter.com/p/big-tech-blocked-microsoft-stopped)) and the FTC ([source](https://www.thebignewsletter.com/p/ftc-to-block-microsoft-activision)) blocked Microsoft’s acquisition of Activision.
    -   On the one hand, this shows that governments are still watching Microsoft.
    -   On the other hand, this shows governments are likely still limiting antitrust actions to blocking major acquisitions instead of proactively breaking up companies and product suites.

### Horizontal versus vertical monopolies

Much of our societal and legal understanding of monopoly is based on a two-dimensional model: monopolies are either vertical, meaning that a company integrates and controls a supply chain, or horizontal, meaning that a company acquires and controls so much of an industry that it can then exert undue power.

When the FTC made its 2001 case against Microsoft, the entire company was worth [$28 billion](https://www.statista.com/statistics/267805/microsofts-global-revenue-since-2002/). Now, the identity and access industry alone was worth [$13 billion in 2021](https://www.globenewswire.com/news-release/2023/01/19/2591625/0/en/Identity-and-Access-Management-Market-Size-Worth-USD-34-52-Billion-by-2028-Report-by-Fortune-Business-Insights.html) and will be worth almost $35 billion by 2028.

The implicit model of the FTC’s view of monopoly is zero-sum, meaning that there is a limited amount of industry and economy to control. But software has proven that the economy is _positive-sum_, meaning that new businesses can grow without necessarily supplanting other businesses and that new industries can emerge from inside companies (e.g. AWS from Amazon).

## Monopoly via bundling

Microsoft develops and acquires services that it then groups, or “bundles”, into one package, while also offering the same services as standalone products on other devices (for example, Office on iPad and Windows on Occulus).

Microsoft does indeed “bundle”, in business terminology, by offering a suite of products and services that are greater (and cheaper) than the sum of their parts. But Microsoft is careful not to, in _legal_ _terminology_, exclusively bundle, because a bundle that involves selling one product only on the condition of buying another product is a form of “[tying](https://www.justice.gov/archives/atr/competition-and-monopoly-single-firm-conduct-under-section-2-sherman-act-chapter-5#:~:text=Tying%20occurs%20when%20a%20firm,what%20could%20be%20viewed%20as),” which is illegal.

### Microsoft Teams

Microsoft Teams, their collaboration and chat platform, has become the latest anchor point for the Microsoft ecosystem. Earlier cornerstone products for Microsoft were their personal computers (PCs), the Windows operating system, and the Microsoft Office suite.

[Ben Thompson](https://stratechery.com/2022/thin-platforms/), a former Microsoft employee who writes about technology, business strategy, and the internet, has shared some interesting insights on his website [Startechery](https://stratechery.com/2022/thin-platforms/):

“_This is exactly what Microsoft would go on to build with Teams: the beautiful thing about chat is that like any social product it is only as useful as the number of people who are using it, which is to say it only works if it is a monopoly — everyone in the company needs to be on board, and they need to not be using anything else. That, by extension, sets up Teams to play the Windows role, but instead of monopolizing an individual PC, it monopolizes an entire company._”

_“A thin platform like Teams takes this even further, because now developers don’t even have access to the devices, at least in a way that matters to an enterprise (i.e. how useful is an app on your phone that doesn’t connect to the company’s directory, file storage, network, etc.). That means the question isn’t about what system APIs are ruled to be off-limits, but what “connectors” (to use Microsoft’s term) the platform owner deigns to build. In other words, not only did Microsoft build their new operating system as a thin platform, they ended up with far more control than they ever could have achieved with their old thick platform._”

### Identity, access, and security in the ecosystem

The power of the ecosystem plays a huge role in creating and retaining a monopoly (whether it is legally defined as a monopoly or simply works as one). A series of services that exert monopolistic control, from Microsoft managed-devices, to entire suites of products supported and integrated via Teams, results in undue control simply due to the pressure of the preceding ecosystem.

One glaring example is how Microsoft makes it easy to adopt Active Directory, giving admins a central directory of users and offering users an SSO portal for all Microsoft services. Microsoft’s monopolistic power is demonstrated by the company’s ability to shift customers from AD to Azure AD. As customers make that shift, Microsoft makes more money (because Azure is more profitable) and Microsoft can more easily exclude other non-Microsoft options.

## A monopoly with plausible deniability

Microsoft has a particular advantage in the world of infrastructure, administration, and security services because end users often don’t know better options are out there and admins are rarely empowered to advocate for a better than good enough solution.

Microsoft learned its lesson from [letting Internet Explorer languish](https://stratechery.com/2022/thin-platforms/) and letting Firefox catch up – now, Microsoft ensures its services are at least “good enough.” “Good enough,” however is questionable. The on-prem version of Active Directory, for example, requires a lot of configuration to make it secure.

William Wechtenhiser argues that Microsoft has an unseen [Boeing 737 Max style crash every week](https://www.thebignewsletter.com/p/does-microsoft-have-a-boeing-737).

“_According to CVE Details Microsoft disclosed an average of 225 security vulnerabilities per year between 1999 and 2014. What did Microsoft do to address this? They dismantled their testing processes and then, when this predictably led to a really bad day, they decided to stagger their releases so that their users could do more of the testing they themselves were no longer doing. As a result the average number of vulnerabilities has increased to 627 per year in the 5 years since. Microsoft looks exactly like a company run by financiers focused on short-term gains with no fear of legal consequences and no competition in the market._”

Microsoft isn’t the only identity option but the industry has [consolidated](https://www.thebignewsletter.com/p/monopolies-and-cybersecurity-disasters) with Okta acquiring Auth0 and Thomas Bravo (which already owned Ping Identity) acquiring ForgeRock.

Slack is the ultimate example of Microsoft’s power. Slack had all the advantages identity and securities services don’t offer, and even yet, Microsoft Teams rapidly overtook Slack and Slack sold to Salesforce (likely as a defensive merger).

## And yet, opportunities remain

Despite all the bundling we’ve discussed so far, we believe that there is expansive opportunity in the identity management space. The opportunity we see is to offer an authentication product that serves all of a company’s authentication needs, from business users to consumers. We think the opportunity is viable because access is becoming an ever more important focal point for security even as Microsoft and Okta suffer breach after breach.
