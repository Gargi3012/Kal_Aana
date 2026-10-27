"""Matching Google Maps listings to official offices.

The listings here are hand-made test fixtures shaped like SerpApi's google_maps results.
They are not real data. The official offices come from data/official.
"""

from typing import Any

import pytest

from kalaana import official
from kalaana.offices import OFFICE_TYPES, Listing, match, place_names, score

RTO = OFFICE_TYPES["rto"]


@pytest.fixture(scope="module")
def rtos() -> list[official.Office]:
    return official.load().offices_of("rto")


def place(title: str, address: str = "", **extra: Any) -> dict[str, Any]:
    data_id = "0x" + "".join(f"{ord(c):x}" for c in title)[:16]  # stable across runs, unlike hash()
    return {"data_id": data_id, "place_id": "p", "title": title, "address": address,
            "type": "Department of motor vehicles", **extra}


def listing(title: str, address: str = "", **extra: Any) -> Listing:
    return Listing.from_maps(place(title, address, **extra), "test", "search-1")


def test_from_maps_search_result() -> None:
    l = listing("RTA X", "Gurugram, Haryana 122001", phone="0124 232 1151", unclaimed_listing=True,
                reviews=240, operating_hours={"monday": "10 am"})
    assert l.phone.key == "+911242321151" and l.unclaimed and l.reviews == 240 and l.has_hours
    assert l.pincode == "122001" and l.category == "Department of motor vehicles"


def test_from_maps_place_result_lists_categories() -> None:
    l = Listing.from_maps({"data_id": "0x1", "title": "RTA", "type": ["Department of motor vehicles", "Government office"]}, "q", "s")
    assert l.category == "Department of motor vehicles"


def test_absent_unclaimed_flag_is_not_read_as_claimed() -> None:
    assert listing("RTA X").unclaimed is False  # "not marked unclaimed", reported as such


def test_place_names_include_aliases(rtos: list[official.Office]) -> None:
    by_id = {o.id: o for o in rtos}
    assert "Hissar RTO" in place_names(by_id["rto-hr20"])
    assert "Gurgaon North RTO" in place_names(by_id["rto-hr26"])


def test_score_explains_every_point(rtos: list[official.Office]) -> None:
    hr26 = next(o for o in rtos if o.id == "rto-hr26")
    m = score(listing("Regional Transport Authority (HR 26)", "Mini Secretariat, Rajiv Chowk 122001",
                      phone="0124 232 1151"), hr26)
    assert m.evidence == ("phone", "code", "pin") and m.score == 8 and m.strong
    assert len(m.reasons) == len(m.evidence)


def test_place_names_match_whole_words_only(rtos: list[official.Office]) -> None:
    hr03 = next(o for o in rtos if o.id == "rto-hr03")
    assert score(listing("RTA near Panchkula", "Haryana"), hr03).evidence == ("title",)
    assert score(listing("RTA", "Panchkula Sector 1, Haryana"), hr03).evidence == ("place",)
    assert score(listing("RTA", "NewPanchkulaSector, Haryana"), hr03).evidence == ()


def test_a_place_in_the_title_beats_a_shared_pin() -> None:
    sros = official.load().offices_of("subregistrar")
    result = match([listing("Sub Registrar Office, Kadipur", "Pataudi Road, Kadipur, Gurugram, Haryana 122001", type="Government office")],
                   sros, OFFICE_TYPES["subregistrar"])
    assert list(result.matched) == ["sro-kadipur"]


def test_match_assigns_roles(rtos: list[official.Office]) -> None:
    listings = [
        listing("Regional Transport Authority, Gurugram HR-26", "Mini Secretariat, Gurugram 122001", reviews=762),
        listing("Example Motors (RTO Services in Gurugram)", "Rajiv Chowk, Gurugram 122001", reviews=826, phone="099999 00000"),
        listing("RTA FARIDABAD TEST TRACK", "Faridabad, Haryana 121001", reviews=796),
        listing("Faridabad (HR-51) RTA Office", "Sector 12, Faridabad 121007", reviews=1013),
    ]
    result = match(listings, rtos, RTO)
    roles = {l.title.split()[0]: m.role for oid in result.matched for l, m in result.matched[oid]}
    assert roles == {"Regional": "office", "Example": "private", "RTA": "facility", "Faridabad": "office"}
    assert result.primary("rto-hr26").title.startswith("Regional Transport Authority, Gurugram")
    assert result.primary("rto-hr51").title.startswith("Faridabad (HR-51)")


def test_location_only_match_needs_an_office_like_title(rtos: list[official.Office]) -> None:
    result = match([listing("Sri Ganesh Xerox", "Rajiv Chowk, Gurugram 122001")], rtos, RTO)
    assert not result.matched and "no official office" in result.unmatched[0][1]


@pytest.mark.parametrize(
    ("title", "category", "why"),
    [
        ("Haryana Office of the Transport Commissioner", "Department of motor vehicles", "same department"),
        ("RTA Battarhalli", "Auto repair shop", "Auto repair shop"),
        ("RTA Office Vishweshwaraiah Layout", "Bus stop", "Bus stop"),
    ],
)
def test_non_offices_are_set_aside_with_a_reason(rtos: list[official.Office], title: str, category: str, why: str) -> None:
    result = match([listing(title, "Sector 12, Karnal 132001", type=category)], rtos, RTO)
    assert not result.matched and why in result.unmatched[0][1]


def test_unconfirmed_and_missing(rtos: list[official.Office]) -> None:
    # A location-only match leaves the office unconfirmed (worth a targeted search) but not missing.
    result = match([listing("Hisar RTA office", "Mini Secretariat, Hisar 125001")], rtos, RTO)
    assert "rto-hr20" in {o.id for o in result.unconfirmed(rtos)}
    assert "rto-hr20" not in {o.id for o in result.missing(rtos)}
    assert "rto-hr14" in {o.id for o in result.missing(rtos)}


def test_a_tie_on_location_goes_to_the_office_whose_address_matches() -> None:
    """Gurugram and Kadipur share PIN 122001; 'Tehsil Complex, Civil Lines' is Gurugram's official address."""
    sros = official.load().offices_of("subregistrar")
    found = listing("Sub-Registrar Office", "Tehsil Complex, Civil Lines, Gurugram, Haryana 122001",
                    type="Government office")
    assert list(match([found], sros, OFFICE_TYPES["subregistrar"]).matched) == ["sro-gurugram"]
