"""The Bing Maps cross-check: which Bing place is the office, and what its phone is."""

from kalaana import official
from kalaana.crosscheck import bing_params, match, places
from kalaana.offices import CITIES

DATA = official.load()
HR26 = DATA.offices["rto-hr26"]
GOOGLE_AT = (28.4595, 77.0266)  # HR-26's Google Maps listing


def place(title: str, lat: float, lng: float, **extra: str) -> dict[str, object]:
    return {"title": title, "gps_coordinates": {"latitude": lat, "longitude": lng}, **extra}


def test_query_is_the_office_name_centred_on_the_city() -> None:
    assert bing_params(HR26, CITIES["Haryana"]) == {
        "engine": "bing_maps", "q": "RTA Gurugram", "cp": "29.0588~76.0856"}


def test_places_reads_both_response_shapes() -> None:
    assert [p["title"] for p in places({"local_results": [{"items": [{"title": "A"}, {"title": "B"}]}]})] == ["A", "B"]
    assert [p["title"] for p in places({"place_results": {"title": "Only one"}})] == ["Only one"]
    assert places({}) == []


def test_the_office_is_the_nearby_place_that_looks_like_it() -> None:
    candidates = [
        place("RTA Consultant Joseph", 28.45951, 77.02661, type="Driving school"),  # right spot, but a private agent
        place("RTA GURUGRAM NORTH HR 26", 28.45952, 77.02661, type="Department of motor vehicles"),
        place("RTA Faridabad HR-51", 28.4089, 77.3178, type="Department of motor vehicles"),
    ]
    hit = match(HR26, candidates, GOOGLE_AT)
    assert hit and hit[0]["title"] == "RTA GURUGRAM NORTH HR 26" and "m from its Google Maps listing" in hit[1]


def test_no_match_when_the_only_office_is_far_away_or_unnamed() -> None:
    far = [place("Haryana Transport Commissioner Office", 30.7333, 76.7794, type="Department of motor vehicles")]
    assert match(HR26, far, GOOGLE_AT) is None
    named = [place("RTA Gurugram North Office", 28.459, 77.026, type="Department of motor vehicles")]
    assert match(HR26, named, None) is not None  # no Google listing: fall back to the place name
