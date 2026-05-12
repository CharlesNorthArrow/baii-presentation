# -*- coding: utf-8 -*-
"""
_patch6.py -- content polish: em dashes, RTG -> Read to Grow, "not yet" fix
"""

EM = u'—'  # em dash

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

orig_len = len(html)
changes = []

def sub(old, new, tag=""):
    global html
    if old not in html:
        raise AssertionError("FAIL not found -- " + tag)
    html = html.replace(old, new, 1)
    changes.append(tag)

# ---- PAGE TITLE --------------------------------------------------------------
sub("Book Access Index " + EM + " What goes into it?",
    "Book Access Index: What goes into it?", "title")

# ---- SUBTITLE ----------------------------------------------------------------
sub("find books " + EM + " and the ones where they should.",
    "find books, and the ones where they should.", "subtitle")

# ---- H2 HEADINGS -------------------------------------------------------------
sub("Public libraries " + EM + " the gold standard",
    "Public libraries: the gold standard", "h2-libraries")

sub("Bookstores " + EM + " books for sale",
    "Bookstores: books for sale", "h2-bookstores")

sub("Museums " + EM + " where stories live",
    "Museums: where stories live", "h2-museums")

sub("700 schools " + EM + " and no library on staff",
    "700 schools, no library on staff", "h2-schools-0")

sub("Some staffing " + EM + " but not a librarian",
    "Some staffing, but not a librarian", "h2-staffing")

sub("1,494 schools " + EM + " every shade of in-school book access",
    "1,494 schools: every shade of in-school book access", "h2-schools-summary")

sub("Book Banks " + EM + " books in, books out",
    "Book Banks: books in, books out", "h2-book-banks")

sub("1,694 community access points " + EM + " the network behind the buildings",
    "1,694 community access points: the network behind the buildings", "h2-nonprofit-summary")

sub("5,625 childcare locations " + EM + " books often welcome, not always present",
    "5,625 childcare locations: books often welcome, not always present", "h2-childcare-summary")

# ---- BODY PARAGRAPHS ---------------------------------------------------------
sub("moment is everything " + EM + " that's why birthing centers",
    "moment is everything. That's why birthing centers", "p-birthing")

sub("and unpredictable " + EM + " but there are more than",
    "and unpredictable. There are more than", "p-lfl")

sub("most volunteer-dependent " + EM + " which is the",
    "most volunteer-dependent, which is the", "p-nonprofit-summary")

sub("providers " + EM + " centers, group homes, and exempt programs " + EM + " serve",
    "providers (centers, group homes, and exempt programs) serve", "p-childcare-step15")

sub("Books for Families program " + EM + " receiving books",
    "Books for Families program, receiving books", "p-bfk-family")

sub("find a book " + EM + " assembled into a single layer",
    "find a book, assembled into a single layer", "p-closing")

sub("home-based and tiny " + EM + " typically a handful",
    "home-based and tiny, typically a handful", "p-family-day-care")

# ---- JS WHY FIELDS -----------------------------------------------------------
sub("purpose-built for reading " + EM + " and serves everyone in the community.",
    "purpose-built for reading, serving everyone in the community.", "why-1")

sub("pay for them " + EM + " and bookstores cluster where access is already strongest.",
    "pay for them. Bookstores cluster where access is already strongest.", "why-2")

sub("no certified library program " + EM + " partial credit for partial infrastructure.",
    "no certified library program. Partial credit for partial infrastructure.", "why-6")

sub("moment a child is born " + EM + " the deepest possible act of book access.",
    "moment a child is born: the deepest possible act of book access.", "why-9")

sub("Pure depth " + EM + " limited only by how few sites exist.",
    "Pure depth, limited only by how few sites exist.", "why-10")

sub("families already wait " + EM + " small footprint, smart placement.",
    "families already wait: small footprint, smart placement.", "why-13")

sub("licensed childcare " + EM + " centers, group homes, exempt programs " + EM + " serve",
    "licensed childcare (centers, group homes, exempt programs) serves", "why-15")

sub("Unweighted today " + EM + " not because they don't matter",
    "Unweighted today, not because they don't matter", "why-17")

# ---- CHART LABELS ------------------------------------------------------------
sub('{ name: "Score 5 ' + EM + ' Full program"',
    '{ name: "Score 5: Full program"', "label-score5")

sub('{ name: "Score 0 ' + EM + ' No library"',
    '{ name: "Score 0: No library"', "label-score0")

# ---- RTG -> READ TO GROW -----------------------------------------------------
# Eyebrows (replace both occurrences)
count_rtg_eyebrow = html.count("Nonprofit " + EM + " RTG")
html = html.replace("Nonprofit " + EM + " RTG", "Nonprofit")
changes.append("eyebrow-rtg (x%d)" % count_rtg_eyebrow)

sub("Where RTG's books actually arrive",
    "Where Read to Grow's books actually arrive", "h2-rtg-org")

sub(u"RTG’s book-gifting families</h2>",
    u"Read to Grow’s book-gifting families</h2>", "h2-bfk-family")

sub("RTG's Books for Babies program",
    "Read to Grow's Books for Babies program", "p-rtg-babies")

sub("This is the shape of RTG's reach",
    "This is the shape of Read to Grow's reach", "p-rtg-reach")

sub(u"With RTG’s book-gifting families included",
    u"With Read to Grow’s book-gifting families included", "p-rtg-summary")

sub("distributes RTG books.",
    "distributes Read to Grow books.", "why-11-rtg")

sub("RTG's book-gifting families: the most intimate",
    "Read to Grow's book-gifting families: the most intimate", "why-17-rtg")

sub('{ name: "RTG Birthing Center"',
    '{ name: "Read to Grow Birthing Center"', "label-rtg-birthing")

sub('{ name: "RTG Partner Org"',
    '{ name: "Read to Grow Partner Org"', "label-rtg-org")

sub('{ name: "RTG BFK Family"',
    '{ name: "Read to Grow BFK Family"', "label-rtg-bfk")

# ---- "NOT YET" PHRASE --------------------------------------------------------
sub("On the map, but not yet in the index",
    "On the map, but not in the index", "h2-not-yet")

sub("not yet weighted in the index",
    "not weighted in the index", "why-16-not-yet")

# ---- WRITE -------------------------------------------------------------------
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Done. %d -> %d chars. %d substitutions:" % (orig_len, len(html), len(changes)))
for c in changes:
    print("  + " + c)
