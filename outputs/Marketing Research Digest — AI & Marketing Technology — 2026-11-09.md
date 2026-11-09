# Marketing Research Digest
**Run date:** 2026-11-09 | **Coverage window:** Last 60 days
**Journals searched:** 177 | **Articles screened:** 40 (of 374 published)
**Focus:** AI & Marketing Technology
**Primary audience:** marketers and brand leaders | **Secondary audience:** general readers and consumers

---

### 1. Your voice assistant should sound deferential, not authoritative

**Journal:** *Journal of Service Research* | **Published:** 2026-10-29
**Work ID:** W7224849080 | **DOI:** 10.1177/10946705261492116

**The study:** Across six experiments, researchers tested how consumers react when AI voice assistants use dominant language (directive, authoritative phrasing) versus submissive language (deferential, accommodating phrasing) across different service settings. Submissive language consistently raised intentions to use the assistant and the perceived value of the interaction, working through a chain of greater rapport and then greater comfort — and it won even in authority-oriented service contexts where a confident, expert-sounding agent might be expected to perform better. The one exception: under time pressure, dominant and submissive phrasing built rapport equally well, breaking the comfort pathway.

**Why it matters:** Voice interface scripts are usually written for clarity and brand tone, not for power dynamics, yet this research suggests the dominance register of a single phrasing choice moves usage intent and perceived value.

**Story angles:**
- **For marketers and brand leaders:** Audit the phrasing in your voice and chat scripts for implicit power signaling — "You should choose X" versus "Would you like me to look at X?" — and A/B test a deferential register even in categories like banking or health advice where authority seems warranted. Treat time-pressured contexts (drive-thru, in-car, checkout) as a separate design problem, since the comfort mechanism appears to drop out there.
- **For general readers and consumers:** It reveals something about how we relate to machines that talk: people appear to want a servant, not a boss, and feel more comfortable with an assistant that defers — even when they're asking it for expert guidance.

**Caveats:** All six studies are experiments rather than field deployments, so they show what can happen in controlled settings rather than what will happen at scale; the abstract does not report sample sizes, participant sources, or country.

---
### 2. When you ask an AI to stand in for consumers, the answer depends on how you asked — this method fixes that

**Journal:** *Marketing Science* | **Published:** 2026-10-30
**Work ID:** W4395015967 | **DOI:** 10.1287/mksc.2024.0983

**The study:** Marketing Science researchers tackled a growing practice: using large language models as synthetic survey respondents to measure preferences and opinions. Because LLM outputs shift across prompts, assigned personas, and model versions, analysts end up with multiple noisy versions of the same "answer" and no principled way to combine them. The authors built Human Mimicry Calibration (HuMCal), a post-hoc method that learns credibility weights across elicitation variants using only aggregate benchmark data, and tested it on U.S. bank-card transaction data (revealed market structure) and Pew public opinion survey data. It beat uniform averaging, post-stratification, and best-single-subgroup selection on the calibration data, and the learned weights mostly held up out of sample across time, geography, industry, and topic.

**Why it matters:** Synthetic respondents are being sold into insights workflows as a cheap substitute for fieldwork, and this is direct evidence that naive aggregation of LLM outputs stays misaligned with real human benchmarks unless it is explicitly calibrated.

**Story angles:**
- **For marketers and brand leaders:** If your insights team or vendor is using LLM personas to simulate consumer response, ask what they calibrate against and how weights were learned — and keep a real human benchmark in the loop, since the paper also finds that recalibrating against newer model checkpoints often improves alignment, meaning calibration is ongoing maintenance, not a one-off.
- **For general readers and consumers:** A useful reality check on AI-generated "what consumers think" claims: the same model, asked slightly differently, gives materially different readings of public opinion, and getting it to match real people takes deliberate statistical correction against actual human data.

**Caveats:** Validated in two U.S. settings (bank-card transactions and Pew data); the authors note out-of-sample transfer of learned weights is empirical rather than guaranteed. This is a measurement-methods paper, not a consumer behavior finding.

---
### 3. Empathetic chatbot language only pays off if customers know it's a bot — and think it's competent

**Journal:** *Australasian Marketing Journal (AMJ)* | **Published:** 2026-11-04
**Work ID:** W7225314486 | **DOI:** 10.1177/14413582261499475

**The study:** Two experiments examined whether anthropomorphic language from a service chatbot — empathetic phrasing and emojis — drives electronic word-of-mouth, and under what conditions. Study 1 found directional evidence that human-like language was associated with more eWOM when the customer's "chatbot schema" was active (they were framing the interaction as a bot interaction), but not when it was inactive. Study 2 found the effects on perceived authenticity and eWOM depended on the chatbot's competence: warm language appears to help only when the bot actually handles the request well.

**Why it matters:** It suggests the common fix of bolting empathy and emojis onto a service bot can be inert or counterproductive, and that disclosure and performance quality are prerequisites rather than separate issues.

**Story angles:**
- **For marketers and brand leaders:** Test warmth cues and bot disclosure together rather than separately, and resist adding empathetic language to a bot that frequently fails to resolve queries — the evidence here points to competence as the gate through which authenticity and advocacy flow. The payoff is in language, not avatars, which is cheaper to iterate on.
- **For general readers and consumers:** Consumers may be more forgiving of a bot that sounds like a bot than of one that performs badly while sounding caring — warmth without resolution reads as inauthentic.

**Caveats:** Only two experiments, with the first described by the authors themselves as "directional"; sample sizes, participant source, and country are not reported in the abstract; measures outcomes as stated word-of-mouth intent rather than observed sharing behavior.

---
### 4. A head-to-head test of ChatGPT, Gemini and Perplexity on real B2B market research tasks

**Journal:** *Journal of Business and Industrial Marketing* | **Published:** 2026-10-28
**Work ID:** W7223791943 | **DOI:** 10.1108/jbim-07-2025-0700

**The study:** Researchers ran an exploratory pilot comparing three LLM tools — ChatGPT, Gemini and Perplexity AI — across three benchmark B2B market research tasks and three prompt types (basic, context-augmented, role-specific), generating 81 outputs in total. A 27-output subset was scored with automated metrics (relevance via cosine similarity, reference overlap, cross-run semantic stability, latency, readability) and blinded human ratings on relevance, completeness, factuality, instruction-following and insightfulness. Role-specific prompts scored best overall; Gemini showed the strongest profile on relevance, reference overlap and stability with lower latency, ChatGPT produced longer and less readable drafts, and Perplexity was concise and readable but least aligned with the brief. The authors also propose a "switch-point" rule set — accept, judge, review/redo, rewrite — mapping confidence signals to escalation actions.

**Why it matters:** Insight teams are already pushing LLM drafts into decision documents, and this offers a concrete, replicable way to screen outputs and assign human review rather than trusting fluent prose.

**Story angles:**
- **For marketers and brand leaders:** Borrow the governance idea even if you discount the model rankings: standardize role-specific prompts, run the same prompt multiple times and treat cross-run inconsistency as a red flag that triggers human review before an AI-generated insight reaches a decision-maker.
- **For general readers and consumers:** Limited direct relevance for general readers, beyond the reminder that the most readable AI answer is not the most accurate one — Perplexity's concise summaries were the least faithful to the underlying brief.

**Caveats:** The authors explicitly label this an exploratory pilot, not confirmatory: three observations per tool in the statistical tests, a small task bank, and a small rater pool. Model rankings are likely to shift with new versions and should not be read as a procurement recommendation; single B2B context.

---
### 5. Wall Street likes your AI announcement. ESG watchers don't.

**Journal:** *Internet Research* | **Published:** 2026-11-04
**Work ID:** W7225245070 | **DOI:** 10.1108/intr-10-2025-1679

**The study:** Researchers assembled 500 corporate generative-AI adoption events from 2019–2024 and ran a staggered difference-in-differences analysis with propensity-score matching, then followed up with a system GMM analysis of 1,274 firm-year observations (2016–2024). Announcing GenAI adoption was associated with a 2.7% rise in cumulative abnormal stock returns — a market read of efficiency gains — but also a 1.9% decline in ESG sentiment, a reputational signal. Firms with stronger digital dynamic capability converted the short-term gain into durable performance, and those with a declared responsible-AI orientation blunted the reputational hit.

**Why it matters:** It quantifies a tension executives have mostly argued about in the abstract: the same AI announcement that pleases investors can cost a company standing with sustainability and governance audiences, unless governance messaging arrives alongside the technology.

**Story angles:**
- **For marketers and brand leaders:** Treat the AI announcement itself as a communications decision with two audiences, not one. Brand and investor-relations teams could test pairing deployment news with explicit responsible-AI governance commitments and watch whether the ESG sentiment penalty narrows — this is archival evidence of an association, so the mechanism is worth validating inside your own reputation tracking.
- **For general readers and consumers:** When a company trumpets a new AI system, the stock market and the sustainability raters are reading opposite stories out of the same press release — a useful reminder that "efficiency" and "responsibility" are scored separately.

**Caveats:** Relies on archival market data and text-derived governance and ESG sentiment measures rather than audited sustainability outcomes; ESG sentiment is explicitly a reputational, not substantive, indicator. Event-study associations around announcements can reflect expectations rather than realized performance. Authors note no survey or internal audit corroboration.

---
### 6. Customers are abusing service robots — and the human staff watching are taking it personally

**Journal:** *Journal of Services Marketing* | **Published:** 2026-11-06
**Work ID:** W7225414092 | **DOI:** 10.1108/jsm-04-2026-0351

**The study:** A multistudy program examined what happens when frontline employees witness customers being rude or degrading toward service robots. A randomized experiment tested whether observing robot-directed mistreatment triggers vicarious moral emotions and "deontic injustice" perceptions; a boundary experiment compared robot-directed mistreatment, human-directed mistreatment and respectful interaction; a 10-day experience-sampling study tracked within-person spillover from daily observed mistreatment to evening rumination and next-day service behavior; and a field quasi-experiment tested a structured managerial intervention protocol. Witnessing robot abuse raised employees' sense that a norm had been violated, which was linked to evening rumination and limited next-day service withdrawal — even though nobody believes the robot suffers.

**Why it matters:** Companies deploying service robots have planned for robot breakdowns and customer frustration, but not for the morale cost to human staff who watch customers mistreat the machines; the study suggests that cost is real and that visible managerial response partially repairs it.

**Story angles:**
- **For marketers and brand leaders:** If you are rolling out robots in stores, hotels or restaurants, add a protocol for how managers respond when customers abuse them — the field comparison links a formal intervention to modestly better proactive service and less withdrawal. Test it as a staff-retention and service-quality lever, not just a robot-protection policy.
- **For general readers and consumers:** People get morally offended on behalf of a machine they know can't feel anything. The offense is about the conduct, not the victim — which says something about why rudeness in public spaces bothers bystanders at all.

**Caveats:** The field test of the intervention protocol was a nonrandomized quasi-experiment, so selection effects can't be ruled out; effects are repeatedly described as modest or limited. Sample sizes and countries are not reported in the abstract, and the experience-sampling window was only 10 days.

---
### 7. The hidden cost of letting AI make your marketing calls: your marketers forget how

**Journal:** *Journal of the Academy of Marketing Science* | **Published:** 2026-10-21
**Work ID:** W7223132093 | **DOI:** 10.1007/s11747-026-01217-6

**The study:** This Journal of the Academy of Marketing Science paper builds a "Return on AI" (RoAI) framework for valuing AI investments in marketing organizations, grounded in marketing accountability and resource-based theory. Rather than measuring AI by tool cost, it accounts for the people, processes and governance capabilities required to deploy it, plus value retention, evidence durability and full lifetime deployment costs. Its central argument: delegating judgment to AI can lift current performance while eroding the hands-on practice through which marketers build the judgment needed to evaluate and correct the AI — which the authors propose explains why AI returns vary so widely across firms and decay over time.

**Why it matters:** It reframes AI ROI from a procurement question to a capability question, and names a plausible reason that early AI wins fade: the organization loses the expertise required to supervise the system.

**Story angles:**
- **For marketers and brand leaders:** Audit how you measure AI returns — are you counting only incremental lift, or also the cost of governance, retraining and the skills your team stops exercising? The paper offers seven testable predictions; it is a framework, not evidence, so the actionable move is to instrument your own AI deployments to see whether judgment atrophy shows up over a few years.
- **For general readers and consumers:** Limited direct relevance for consumers, though it hints at why brand decisions may get blander over time: if the humans checking the algorithm lose the instinct to overrule it, the algorithm's defaults win by attrition.

**Caveats:** Purely conceptual — no new empirical data; the delegated-judgment mechanism and all seven predictions remain untested. No sample, firm or category evidence is presented.

---
### 8. Service robots win customers over by feeling present — not by looking human

**Journal:** *Journal of Business Research* | **Published:** 2026-10-30
**Work ID:** W7224957158 | **DOI:** 10.1016/j.jbusres.2026.116607

**The study:** Across two online studies and one laboratory study, researchers tested how a service robot's "social presence" — the sense that something is really there with you — affects customer satisfaction with a service encounter. Social presence consistently raised satisfaction, and the effect ran partly through customers perceiving the service as innovative, but only among customers who were themselves more open to innovation. Critically, anthropomorphism worked against this: the more human-like the robot was made to look, the weaker the link between social presence and satisfaction.

**Why it matters:** Firms deploying robots in customer-facing roles often assume more human-like equals more likable; this suggests the payoff comes from presence and responsiveness, while piling on human features can actively undercut it.

**Story angles:**
- **For marketers and brand leaders:** If you are piloting service robots or embodied AI agents, treat social presence and human likeness as separate design dials rather than one. Worth A/B testing a warm, attentive but clearly machine-like agent against a more humanoid version in a live service setting, and segmenting results by how innovation-receptive your customer base is.
- **For general readers and consumers:** The uncanny valley shows up in everyday service: people seem to warm to a robot that acts attentive but stays visibly a robot, and cool toward one that tries too hard to pass as a person.

**Caveats:** Two of the three studies used online samples and the third was a laboratory study, so these are controlled encounters rather than observed behavior in real service settings; satisfaction was self-reported; single research program with no field validation reported.

---
### 9. The travelers most comfortable with AI are the ones who trust its itineraries least

**Journal:** *Journal of Travel Research* | **Published:** 2026-10-28
**Work ID:** W7224113183 | **DOI:** 10.1177/00472875261499734

**The study:** Researchers combined a two-wave panel of 433 Chinese and European travelers, a validation wave of 372 more, and 42 interviews to examine what makes tourists trust generative AI travel planning and keep using it. Data transparency and content authenticity lifted both cognitive and affective trust, and affective trust was the strongest driver of continued use. The surprise: technology readiness flipped the expected pattern — more tech-ready travelers scrutinized fluent AI output instead of leaning on it, weakening the link between trust and actual continued usage.

**Why it matters:** It challenges the assumption that tech-savvy early adopters are the easiest audience for generative AI features; they may be the most demanding, wanting verification tools rather than smoother prose.

**Story angles:**
- **For marketers and brand leaders:** Test segmented AI interfaces: verification affordances such as checkable citations and in-context data-use disclosures for high-readiness users, reassurance and guidance for everyone else. And stop treating polished, fluent output as a proxy for credibility — fluency may buy less trust from your most sophisticated customers than from your least.
- **For general readers and consumers:** If you have ever double-checked a chatbot's hotel recommendation against a map, you are the pattern: comfort with AI tends to come bundled with skepticism, not blind faith.

**Caveats:** Self-reported trust and usage intentions via survey panels rather than observed booking behavior; limited to travel planning; two broad regional samples (Chinese and European travelers) that may not generalize elsewhere; relatively short panel horizon.

---
### 10. When AI explains its recommendations, more reasons aren't better — a moderate dose wins

**Journal:** *Journal of Retailing and Consumer Services* | **Published:** 2026-11-07
**Work ID:** W7225383427 | **DOI:** 10.1016/j.jretconser.2026.105205

**The study:** Researchers tested five escalating "explanation packages" that an AI shopping assistant could attach to a product recommendation, measuring how much nonredundant product information was shown. A randomized mobile-retail experiment in China found an inverted-U pattern: trust, perceived usefulness and decision comfort rose with more explanation up to a point, then fell as information overload and what the authors call "algorithmic over-justification" took over. A companion study showed the same messages attributed to a human salesperson rather than an AI, and a behavioral analysis of 51,248 recommendation impressions across 5,000 distinct users confirmed that moderate packages performed best among the sets tested.

**Why it matters:** Explainable AI is often treated as "more transparency is always better," but this suggests over-explaining a recommendation can read as a sales pitch and erode the very trust it is meant to build.

**Story angles:**
- **For marketers and brand leaders:** Recommendation explanations are a tunable default, not a fixed setting — brands running AI assistants could A/B test explanation length by category (complex, high-functionality or safety-relevant products may tolerate more) rather than shipping one verbosity level across the catalog. Note that the study identifies effects of whole assigned packages, not of word count alone.
- **For general readers and consumers:** If a shopping app feels like it's working too hard to justify a suggestion, that instinct has some research behind it: piling on reasons can trigger suspicion that you're being sold to rather than advised.

**Caveats:** Single country (China) and largely a single retail environment; the experiments vary amount, content and diagnostic priority together, so they do not isolate pure information quantity; the authors note same-session measurement cannot establish causal mediation; the mechanism is not shown to be uniquely algorithmic, since human-attributed messages behaved similarly.

---
### 11. What banking app reviews actually reveal: speed and security complaints hurt more than good design helps

**Journal:** *International Journal of Bank Marketing* | **Published:** 2026-10-30
**Work ID:** W7224875273 | **DOI:** 10.1108/ijbm-02-2026-0158

**The study:** Researchers mined a large corpus of user reviews of mobile banking apps using topic modeling, sentiment analysis, large language model–assisted interpretation and semantic similarity matching, mapping user-written complaints and praise onto the ISO/IEC 25010:2023 software quality dimensions. Functional suitability, interaction capability and maintainability pushed ratings up, while performance efficiency, reliability, flexibility, safety and security problems drove ratings down; compatibility had no measurable effect. The quality–satisfaction link was asymmetric and moderated by review sentiment — under positive sentiment, negative quality issues bit harder.

**Why it matters:** It gives banks an evidence-based triage order for app roadmaps: fixing failure modes is not symmetric with adding features, and the same defect costs more among otherwise satisfied users.

**Story angles:**
- **For marketers and brand leaders:** App teams can treat public review corpora as a continuous, free quality-measurement instrument — but the practical lesson is prioritization: reliability, speed and security read as dissatisfiers that destroy ratings, while usability improvements are the ones that build them. Worth testing whether the same asymmetry holds in your own review data across digital-only versus branch-based brands.
- **For general readers and consumers:** Your one-star review about a slow login is doing more work than a five-star review about a nice interface — ratings data shows failures are punished more sharply than strengths are rewarded.

**Caveats:** Observational analysis of user-generated reviews, not an experiment, so causal claims are limited; reviewers are a self-selected and typically polarized subset of users; findings depend on how text topics were mapped to the ISO quality framework; app categories and markets covered are not specified in detail.

---
### 12. Don't target the customers most likely to leave — target the ones your offer can actually change

**Journal:** *Sport Marketing Quarterly* | **Published:** 2026-10-26
**Work ID:** W7223652225 | **DOI:** 10.1177/10616934261499880

**The study:** Researchers analyzed proprietary season-ticket-holder records from an NCAA collegiate athletics program (n=23,565), comparing the traditional binary logistic regression approach to churn prediction against random forest and support vector machine models. The machine learning models predicted renewal more accurately than the logit benchmark. The team then applied an uplift model, which estimates not who will churn but who will respond to a retention offer, and found that targeting people who are both at risk and persuadable is substantially more efficient and economically beneficial than blanket targeting of likely churners.

**Why it matters:** Most retention programs still spend incentive budget on customers flagged as "at risk," including many who would have renewed anyway or who are unreachable at any price; uplift modeling reallocates that budget to the subset where the offer changes the outcome.

**Story angles:**
- **For marketers and brand leaders:** Audit how your retention budget is allocated: if campaigns are triggered by churn probability alone, run a holdout test comparing churn-score targeting against uplift (incremental-response) targeting on the same list and measure incremental renewals, not total renewals. The gain here came from real ticketing records at one athletic program, so treat it as a strong proof of concept to replicate in your own category — subscriptions, gyms, telecom, SaaS — rather than a transferable coefficient.
- **For general readers and consumers:** It helps explain why some loyal customers never get a "please stay" discount while wavering ones get showered with offers: increasingly, the discount goes to whoever the algorithm thinks it can sway, not whoever is most valuable or most loyal.

**Caveats:** Single organization, single category (US collegiate athletics season tickets); proprietary data not independently verifiable; results are predictive modeling on historical records rather than a live randomized test of the uplift targeting strategy.

---
### 13. Telling people your influencer is AI makes them like the post less — and buy less

**Journal:** *Journal of Product & Brand Management* | **Published:** 2026-11-02
**Work ID:** W7225100007 | **DOI:** 10.1108/jpbm-09-2025-6354

**The study:** Two between-subjects online experiments with US consumers who did not follow the influencer in question (n=303 and n=316, recruited via CloudResearch Connect) tested what happens when a human-looking influencer is disclosed as AI-generated. Disclosure significantly reduced perceived authenticity, which in turn produced negative expectation disconfirmation and lower engagement intentions; in Study 2 the chain extended to lower purchase intentions.

**Why it matters:** As AI disclosure rules tighten on social platforms, brands relying on human-presenting virtual influencers need to know the disclosure itself carries a measurable cost with cold audiences encountered through algorithmic feeds.

**Story angles:**
- **For marketers and brand leaders:** If you use virtual influencers, the test worth running is timing and framing of disclosure: labeling the account as AI from the very first exposure sets category expectations rather than breaking them later, and overtly stylized or non-human-presenting avatars may avoid the authenticity penalty altogether. These are stated intentions from online panelists, so treat the direction as a warning signal to validate with live creative tests and actual click and conversion data.
- **For general readers and consumers:** The finding shows how much of influencer persuasion rests on believing a real person stands behind the recommendation — the same post lands worse the moment you learn no one actually used the product.

**Caveats:** Online panel sample; stated engagement and purchase intentions rather than observed behavior; single country (US); first-exposure, non-follower context only, so results may not apply to established virtual influencers with existing fan bases.

---
### 14. Plain-language data policies and outside audits both lifted willingness to adopt smart energy devices

**Journal:** *International Journal of Consumer Studies* | **Published:** 2026-11-01
**Work ID:** W7225315132 | **DOI:** 10.1111/ijcs.70278

**The study:** A 2x2 vignette experiment with 620 Vietnamese adults manipulated whether a household low-carbon technology provider offered a clear versus vague bundled governance disclosure, and whether data assurance came from an external body or the company itself. Both richer disclosure and external assurance independently raised all four focal outcomes, including adoption intention and willingness to join a pilot, with no interaction between them; survey measures showed trust in data handling and perceived legitimacy of using household data for climate purposes as the connecting perceptions.

**Why it matters:** For connected home and energy products, environmental benefit alone does not close the sale — how the data governance is explained and who vouches for it moves stated adoption on its own.

**Story angles:**
- **For marketers and brand leaders:** Treat data-governance copy as conversion creative, not legal boilerplate: test intelligible transparency, explicit user controls and explainability claims against vague standard language, and test third-party certification against self-assurance. The authors explicitly caution that the disclosure effect came from a bundle, so isolate which component does the work before rebuilding your privacy page around any single claim.
- **For general readers and consumers:** Smart thermostats and home energy systems cut carbon by collecting detailed data about your household; this study suggests people are willing to make that trade, but mainly when someone independent has checked the company's homework.

**Caveats:** Single country (Vietnam); hypothetical vignettes and stated adoption intentions rather than real purchases; mediating mechanisms are measured perceptions in a cross-sectional structural model, so the trust-legitimacy pathway is associational even though the two cues were randomized.

---
## Citation Reference

| # | Work ID | Journal | Date | DOI |
|---|---------|---------|------|-----|
| 1 | W7224849080 | Journal of Service Research | 2026-10-29 | 10.1177/10946705261492116 |
| 2 | W4395015967 | Marketing Science | 2026-10-30 | 10.1287/mksc.2024.0983 |
| 3 | W7225314486 | Australasian Marketing Journal (AMJ) | 2026-11-04 | 10.1177/14413582261499475 |
| 4 | W7223791943 | Journal of Business and Industrial Marketing | 2026-10-28 | 10.1108/jbim-07-2025-0700 |
| 5 | W7225245070 | Internet Research | 2026-11-04 | 10.1108/intr-10-2025-1679 |
| 6 | W7225414092 | Journal of Services Marketing | 2026-11-06 | 10.1108/jsm-04-2026-0351 |
| 7 | W7223132093 | Journal of the Academy of Marketing Science | 2026-10-21 | 10.1007/s11747-026-01217-6 |
| 8 | W7224957158 | Journal of Business Research | 2026-10-30 | 10.1016/j.jbusres.2026.116607 |
| 9 | W7224113183 | Journal of Travel Research | 2026-10-28 | 10.1177/00472875261499734 |
| 10 | W7225383427 | Journal of Retailing and Consumer Services | 2026-11-07 | 10.1016/j.jretconser.2026.105205 |
| 11 | W7224875273 | International Journal of Bank Marketing | 2026-10-30 | 10.1108/ijbm-02-2026-0158 |
| 12 | W7223652225 | Sport Marketing Quarterly | 2026-10-26 | 10.1177/10616934261499880 |
| 13 | W7225100007 | Journal of Product & Brand Management | 2026-11-02 | 10.1108/jpbm-09-2025-6354 |
| 14 | W7225315132 | International Journal of Consumer Studies | 2026-11-01 | 10.1111/ijcs.70278 |

---

## Spelling

American English throughout this synthesis — "analyze," "behavior," "randomized," "center," "program," "labeled," "modeling." Several source journals in this batch are British or Australasian and their abstracts are not written that way, so I have converted in my own voice while leaving reproduced material alone: journal titles keep their original form (*Australasian Marketing Journal (AMJ)*, *Journal of Business and Industrial Marketing*, *International Journal of Bank Marketing*), as do proper names, standards and authors' coinages — Human Mimicry Calibration (HuMCal), "Return on AI" (RoAI), "deontic injustice," "algorithmic over-justification," "chatbot schema," "switch-point," ISO/IEC 25010:2023, CloudResearch Connect, Gemini, Perplexity AI.

## Research Trends & Continuity

**Convergent findings**
- **The AI disclosure penalty keeps running through perceived authenticity.** "Telling people your influencer is AI makes them like the post less — and buy less" (W7225100007) reproduces, in the influencer context, the exact mediation chain found in the previous digest's "'Designed by AI' costs you money — 'designed with AI' doesn't" (W7222531871) and "Labeling a souvenir 'AI-generated' hurt sales intent with Americans — but Chinese shoppers didn't blink" (W7223005232): disclosure lowers authenticity, authenticity lowers intent. Three studies in two consecutive digests now put the damage in the same place.
- **Human likeness is a separate dial from warmth or presence — and the wrong one to turn up.** "Service robots win customers over by feeling present — not by looking human" (W7224957158) and "Empathetic chatbot language only pays off if customers know it's a bot — and think it's competent" (W7225314486) extend the conditional-humanness thread from "When should a chatbot sound cheerful? Only when the task is subjective" (W7221784971) and "A less human chatbot may be exactly what stigmatized customers want" (W7222997881). W7224957158 is the cleanest statement yet: anthropomorphism actively weakened the presence-to-satisfaction link.
- **Transparency acts as reassurance rather than caution.** "Plain-language data policies and outside audits both lifted willingness to adopt smart energy devices" (W7225315132) is the constructive mirror of the previous digest's "Disclosure Warnings on AI Therapy Bots May Boost Use Rather Than Protect Users" (W7223088624) — in both, clearer disclosure increased adoption rather than tempering it. The policy implication differs by context, but the behavioral direction is the same.
- **Owning AI is still not the payoff.** "The hidden cost of letting AI make your marketing calls: your marketers forget how" (W7223132093) theorizes the mechanism that "AI Patents Don't Create Value — Marketing Execution Does" (W7222898245) found in panel data: capability inside the commercial organization is the conversion step, and W7223132093 proposes that AI delegation erodes exactly that capability over time.
- **Side effects nobody instrumented.** "Customers are abusing service robots — and the human staff watching are taking it personally" (W7225414092) and W7223132093 join "Daily motivational texts lifted sales — and made agents stop checking their numbers" (W7222957362) and "The More Capable People Feel with AI, the More Willing They Are to Misuse It" (W7213767799): each documents a human cost sitting outside the deployment's own success metric.

**Advances**
- **From "explanations help" to "explanations have a dose."** The previous digest's "Whether an AI recommender should decide for you or with you depends on how the green product is pitched" (W7221585809) found that attribute-based explanations erased a recommender penalty; "When AI explains its recommendations, more reasons aren't better — a moderate dose wins" (W7225383427) adds the curve, with trust falling once over-justification sets in — and adds behavioral scale (51,248 impressions) to what was scenario evidence.
- **From AI as a market instrument to AI instruments that need calibration.** "An AI web crawler found five times more nicotine pouch brands than Nielsen or national surveys" (W7223205040) showed LLM tooling outperforming incumbent trackers; "When you ask an AI to stand in for consumers, the answer depends on how you asked — this method fixes that" (W4395015967) and "A head-to-head test of ChatGPT, Gemini and Perplexity on real B2B market research tasks" (W7223791943) move the thread from capability to quality control — credibility weights and escalation rules rather than raw coverage.
- **Trust segmentation gets sharper.** "Chatbots keep customers in the ecosystem — but only if they make people feel sure of their decision" (W7221013951) named decision confidence as the gate; "The travelers most comfortable with AI are the ones who trust its itineraries least" (W7224113183) identifies who the gate is hardest to pass with, finding technology readiness weakens rather than strengthens the trust-to-use link.

**Counterpoints**
- **Tone register versus emotional valence.** "Your voice assistant should sound deferential, not authoritative" (W7224849080) finds submissive phrasing wins even in authority-oriented service contexts, which sits awkwardly beside W7221784971's finding that a neutral, competence-signaling tone wins on objective, data-driven tasks. They are probably measuring different dimensions — dominance versus warmth — but anyone writing bot scripts from both papers will hit the conflict.
- **Are sophisticated users the easy audience?** "Shoppers Will Hand the Credit Card to an AI Agent — If It Can Prove It Understands Them" (W7222787541) framed capability signals as the unlock and found expertise merely moderated responses; W7224113183 argues the most technology-ready users scrutinize fluent output instead of relying on it. The two disagree on whether sophistication is a tailwind or a hurdle for AI delegation.

**New themes**
- **AI announcements as a two-audience communications problem** — "Wall Street likes your AI announcement. ESG watchers don't." (W7225245070) is the first study in this run of digests to price the reputational side of adoption news against the market side.
- **Bystander morale around service robots** (W7225414092) — employees as the affected party in robot deployment, with no prior-run antecedent.
- **Incremental-response targeting** — "Don't target the customers most likely to leave — target the ones your offer can actually change" (W7223652225) opens a retention-economics strand distinct from anything in the previous digest.
- **User-review corpora as a continuous quality instrument** — "What banking app reviews actually reveal: speed and security complaints hurt more than good design helps" (W7224875273), including the asymmetry between dissatisfiers and satisfiers.

## Bigger Picture: Feature Pitch

**The pattern:** The consumer-insight function is being quietly automated, and three studies in this batch independently show the quality controls are not in place yet. "When you ask an AI to stand in for consumers, the answer depends on how you asked — this method fixes that" (W4395015967) shows LLM synthetic respondents give materially different readings of public opinion depending on prompt, persona and model version, and only match real human benchmarks after deliberate statistical calibration; "A head-to-head test of ChatGPT, Gemini and Perplexity on real B2B market research tasks" (W7223791943) finds the most readable AI research output was the least faithful to the brief and proposes escalation rules for when a human must intervene; and "The hidden cost of letting AI make your marketing calls: your marketers forget how" (W7223132093) argues that the judgment needed to catch these failures atrophies in exactly the teams that delegate most. "What banking app reviews actually reveal" (W7224875273) sits alongside as the counterexample — real user text, machine-read, producing findings a synthetic panel could not have invented.

**Why pitch this now:** Synthetic respondent panels and AI-drafted insight decks are being sold into brand and agency research budgets as a cheap substitute for fieldwork right as those budgets are under cost pressure, and this is the first cluster of peer-reviewed evidence on what the substitution actually costs in accuracy and in institutional skill.

**Angle:** A reported feature on the machine-generated consumer — who is buying synthetic research, what the calibration and governance evidence says it takes to make those outputs trustworthy, and what happens to a research department that stops practicing the judgment required to audit them. Written for insights leaders, CMOs and agency strategy teams, with enough bite for a general business reader who wants to know whether the "consumers say" line in a press release came from any consumers.

**Potential headlines:**
- The consumers in your research may not exist, and the evidence says that takes work to fix
- The most readable AI research answer was the least accurate one
- Who in your company will still be able to tell when the AI gets consumers wrong?

**Potential outlets:**
- **Research Live** — its readership is the market research industry deciding right now whether synthetic samples belong in a client deliverable, and the calibration-versus-naive-averaging distinction is their core argument.
- **Marketing Brew** — well suited to an explainer on how AI personas entered the insights workflow and what brand teams should be asking vendors.
- **Ad Age** — covers the commercial squeeze on research and strategy functions, which is the economic engine behind this substitution.
- **Harvard Business Review** — the capability-atrophy argument, that delegating judgment erodes the ability to supervise the system, is an organizational governance piece in their register.

## Story Ideas by Study

- **Your voice assistant should sound deferential, not authoritative (Work ID W7224849080):** Six experiments arguing that voice scripts carry a power register nobody writes for, with deference winning even in banking- and health-style authority contexts, for a customer-experience or conversation-design trade piece, with a consumer-psychology sidebar on wanting a servant rather than a boss.
- **When you ask an AI to stand in for consumers, the answer depends on how you asked (Work ID W4395015967):** A *Marketing Science* method for weighting LLM survey outputs against real human benchmarks, and the questions a brand should put to any synthetic-sample vendor, for a market research trade lead or an insights-leadership column.
- **Empathetic chatbot language only pays off if customers know it's a bot — and think it's competent (Work ID W7225314486):** Competence as the gate through which warmth cues flow, meaning empathy bolted onto a failing bot is inert or worse, for a customer-service technology trade brief.
- **A head-to-head test of ChatGPT, Gemini and Perplexity on real B2B market research tasks (Work ID W7223791943):** Skip the rankings and take the governance idea — run the same prompt repeatedly and treat cross-run inconsistency as a trigger for human review, for a B2B marketing or insights-operations explainer, flagged clearly as an exploratory pilot.
- **Wall Street likes your AI announcement. ESG watchers don't. (Work ID W7225245070):** 500 adoption events showing a 2.7% abnormal return paired with a 1.9% drop in ESG sentiment, and responsible-AI messaging blunting the second, for a corporate communications or investor-relations trade feature, or a business-section piece on the two scoreboards reading one press release.
- **Customers are abusing service robots — and the human staff watching are taking it personally (Work ID W7225414092):** Robot rollouts need a managerial response protocol as a staff-retention lever, not just a hardware-protection policy, for a retail or hospitality operations trade piece, with a strong general-interest angle on moral offense on behalf of a machine that cannot suffer.
- **The hidden cost of letting AI make your marketing calls: your marketers forget how (Work ID W7223132093):** Reframing AI ROI from procurement cost to capability cost, including the skills a team stops exercising, for a CMO-audience column — with the caveat that it is a framework offering testable predictions rather than evidence.
- **Service robots win customers over by feeling present — not by looking human (Work ID W7224957158):** Presence and human likeness as separate design dials, with anthropomorphism weakening the payoff, for a service-design or retail technology trade explainer, plus a consumer piece on the uncanny valley at the hotel front desk.
- **The travelers most comfortable with AI are the ones who trust its itineraries least (Work ID W7224113183):** Early adopters as the most demanding audience, wanting checkable citations rather than smoother prose, for a travel trade analysis or a product-marketing column on segmenting AI interfaces by readiness.
- **When AI explains its recommendations, more reasons aren't better — a moderate dose wins (Work ID W7225383427):** Explanation length as a tunable default by product category, with over-justification reading as a sales pitch, for an e-commerce or personalization trade brief, and a consumer explainer on why an over-eager shopping app feels suspicious.
- **What banking app reviews actually reveal (Work ID W7224875273):** An evidence-based triage order for app roadmaps — reliability, speed and security destroy ratings while usability builds them, and defects cost most among otherwise satisfied users, for a banking or fintech trade explainer, with a consumer angle on the asymmetric power of a one-star review.
- **Don't target the customers most likely to leave — target the ones your offer can actually change (Work ID W7223652225):** Uplift modeling against churn-score targeting on 23,565 season-ticket records, and the holdout test any subscription business could run, for a CRM/retention marketing trade piece, with a consumer-facing spin on why loyal customers never get the "please stay" discount.
- **Telling people your influencer is AI makes them like the post less — and buy less (Work ID W7225100007):** Disclosure timing and avatar styling as the variables worth testing, since labeling from first exposure sets expectations rather than breaking them, for an influencer marketing or social platform trade news piece.
- **Plain-language data policies and outside audits both lifted willingness to adopt smart energy devices (Work ID W7225315132):** Data-governance copy as conversion creative, with third-party assurance working independently of disclosure clarity, for a connected-device or sustainability marketing trade explainer, plus a consumer piece on trading household data for lower carbon.
