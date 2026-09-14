"""The rotation's topics: what each one searches for, and how studies get tagged.

One place for both, so a renamed topic cannot split a beat in two -- the bug
senior-research-digest hit when "fall prevention" became "falls" mid-archive
and trends.py stopped finding the run before it.

`QUERIES` are OpenAlex boolean title-and-abstract searches (AND / OR / quoted
phrases; OpenAlex stems, so "brand" also finds "brands"). `TAG_TERMS` are
lowercase substrings matched against the finished write-up, so a study found
on a pricing day that is really about influencers carries both tags.
"""
from __future__ import annotations

BROAD = ""
BROAD_LABEL = "Broad (all marketing topics)"

QUERIES = {
    "consumer psychology": (
        '(consumer OR consumers OR shopper OR customer) AND (emotion OR identity OR '
        '"decision making" OR choice OR motivation OR "self-control" OR nostalgia OR '
        'happiness OR "social comparison" OR loneliness OR status)'
    ),
    "advertising": (
        'advertising OR advertisement OR "ad campaign" OR "marketing communication" OR '
        '"creative execution" OR "ad avoidance" OR "native advertising" OR "ad effectiveness"'
    ),
    "branding": (
        'brand OR branding OR "brand equity" OR "brand loyalty" OR "brand trust" OR '
        '"brand activism" OR rebranding OR "brand love"'
    ),
    "social media & influencers": (
        '"social media" OR influencer OR "word of mouth" OR "user-generated" OR '
        'TikTok OR Instagram OR YouTube OR "online reviews" OR "creator economy"'
    ),
    "ai & marketing technology": (
        '"artificial intelligence" OR "generative AI" OR chatbot OR ChatGPT OR '
        '"large language model" OR algorithm OR "machine learning" OR robot OR '
        '"voice assistant" OR personalization'
    ),
    "pricing & promotions": (
        'pricing OR price OR discount OR "sales promotion" OR "price promotion" OR coupon OR '
        'subscription OR '
        '"price fairness" OR "dynamic pricing" OR "free shipping"'
    ),
    "retail & e-commerce": (
        'retail OR retailer OR "e-commerce" OR "online shopping" OR omnichannel OR '
        'marketplace OR "private label" OR "store" OR "live streaming commerce"'
    ),
    "customer experience & service": (
        '"customer experience" OR "service quality" OR "customer satisfaction" OR '
        '"frontline employee" OR complaint OR "service failure" OR "service recovery" OR '
        '"customer journey"'
    ),
    "sustainability & ethical consumption": (
        'sustainability OR sustainable OR "green consumption" OR "ethical consumption" OR '
        '"corporate social responsibility" OR greenwashing OR "circular economy" OR '
        'secondhand OR "plastic"'
    ),
    "food, health & wellbeing": (
        'food OR nutrition OR "healthy eating" OR alcohol OR tobacco OR vaping OR '
        '"health communication" OR wellbeing OR "well-being" OR obesity'
    ),
    "money & spending": (
        '"financial decision" OR saving OR debt OR spending OR "buy now pay later" OR '
        '"credit card" OR "financial well-being" OR "mental accounting" OR cryptocurrency'
    ),
    "b2b & sales": (
        '"business-to-business" OR B2B OR salesperson OR "sales force" OR "key account" OR '
        '"supplier relationship" OR "industrial marketing" OR "sales management"'
    ),
    "public relations & reputation": (
        '"public relations" OR "crisis communication" OR "corporate reputation" OR '
        'stakeholder OR "corporate communication" OR "strategic communication" OR '
        '"issues management" OR "employee advocacy"'
    ),
}

DEFAULT_ROTATION = [BROAD, *QUERIES]

TAG_TERMS = {
    "consumer psychology": ("emotion", "identity", "self-control", "nostalgia",
                            "happiness", "social comparison", "loneliness", "status"),
    "advertising": ("advertis", " ad ", " ads ", "commercial", "campaign"),
    "branding": ("brand",),
    "social media & influencers": ("social media", "influencer", "word of mouth", "tiktok",
                                   "instagram", "youtube", "online review", "creator"),
    "ai & marketing technology": ("artificial intelligence", " ai ", "ai-", "generative",
                                  "chatbot", "algorithm", "machine learning", "robot",
                                  "personaliz", "language model"),
    "pricing & promotions": ("price", "pricing", "discount", "promotion", "coupon",
                             "subscription"),
    "retail & e-commerce": ("retail", "e-commerce", "online shopping", "store", "omnichannel",
                            "marketplace", "shopper"),
    "customer experience & service": ("customer experience", "service", "satisfaction",
                                      "complaint", "frontline"),
    "sustainability & ethical consumption": ("sustainab", "green", "ethical", "environment",
                                             "csr", "social responsibility", "greenwash",
                                             "secondhand", "recycl"),
    "food, health & wellbeing": ("food", "nutrition", "eating", "alcohol", "tobacco", "vaping",
                                 "health", "wellbeing", "well-being", "obesity"),
    "money & spending": ("financial", "saving", "debt", "spending", "buy now pay later",
                         "credit card", "crypto"),
    "b2b & sales": ("b2b", "business-to-business", "salesperson", "sales force",
                    "supplier", "industrial"),
    "public relations & reputation": ("public relations", "crisis", "reputation",
                                      "stakeholder", "corporate communication"),
}

TOPIC_ALIASES: dict[str, str] = {}


def normalize_topic(topic: str) -> str:
    """Canonical name for a topic, whatever the rotation called it at the time."""
    cleaned = " ".join((topic or "").split()).lower()
    return TOPIC_ALIASES.get(cleaned, cleaned)


def query_for(topic: str) -> str:
    """The OpenAlex search for a topic. A topic with no entry here -- a one-off
    typed into the workflow_dispatch box -- is searched as a plain phrase."""
    key = normalize_topic(topic)
    if not key:
        return ""
    return QUERIES.get(key) or f'"{topic.strip()}"'


def label_for(topic: str) -> str:
    key = normalize_topic(topic)
    if not key:
        return BROAD_LABEL
    # str.title() gives "Ai & Marketing Technology"; "b2b" already comes out "B2B".
    return key.title().replace("Ai ", "AI ")


def tags_for(text: str, topic: str = "") -> list[str]:
    blob = f" {(text or '').lower()} "
    tags = {tag for tag, terms in TAG_TERMS.items() if any(t in blob for t in terms)}
    if normalize_topic(topic):
        tags.add(normalize_topic(topic))
    return sorted(tags)
