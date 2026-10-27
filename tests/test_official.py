from collections import Counter
from pathlib import Path

import pytest

from kalaana import official


@pytest.fixture(scope="module")
def data() -> official.OfficialData:
    return official.load()


def write(tmp_path: Path, body: str) -> Path:
    (tmp_path / "x.toml").write_text(body)
    return tmp_path


RTO_META = '[meta]\noffice_type = "rto"\nsource_url = "https://example.gov.in"\n'


# The shipped data


def test_every_row_has_a_source(data: official.OfficialData) -> None:
    assert data.offices and data.timelines
    for row in [*data.offices.values(), *data.timelines.values()]:
        assert row.source_url.startswith("https://"), row.id


def test_directory_sizes_match_the_published_pages(data: official.OfficialData) -> None:
    # 15 RTA offices across Haryana; 28 Sub-Registrar / Tehsil offices; 10 passport offices
    assert len(data.offices_of("rto")) == 15
    assert len(data.offices_of("subregistrar")) == 28
    assert len(data.offices_of("passport")) == 10


def test_phone_labels_match_their_directory_columns(data: official.OfficialData) -> None:
    for o in data.offices_of("rto"):
        assert o.phones and all(p.label == official.LANDLINE for p in o.phones), o.id
    for o in data.offices_of("subregistrar"):
        assert o.phones and all(p.label == official.LANDLINE for p in o.phones), o.id
    for o in data.offices.values():
        for p in o.phones:
            assert p.phone.kind in ("landline", "fixed_or_mobile", "mobile"), (o.id, p)


def test_no_number_is_listed_for_two_offices(data: official.OfficialData) -> None:
    counts = Counter(k for o in data.offices.values() for k in o.phone_keys)
    shared = [k for k, n in counts.items() if n > 1]
    assert shared == []


def test_every_office_has_a_pincode_or_says_why_not(data: official.OfficialData) -> None:
    for o in data.offices.values():
        assert o.pincode or any("PIN" in n for n in o.notes), o.id


def test_owners_office_and_timeline(data: official.OfficialData) -> None:
    hr26 = data.offices["rto-hr26"]
    assert hr26.code == "HR-26" and hr26.pincode == "122001" and hr26.group == "Gurugram"
    assert "+911242321151" in hr26.phone_keys
    ll = data.timelines["learners-licence"]
    assert (ll.days, ll.unit) == (7, "working days")
    assert "First Grievance Redressal Authority" in data.appeals["rto"].first_appeal
    assert data.helplines["rto"].key == "+9118001802057"


def test_subregistrar_timelines_and_appeals(data: official.OfficialData) -> None:
    assert {t.id for t in data.timelines_for("subregistrar")} >= {"property-registration", "encumbrance-certificate"}
    assert data.timelines["marriage-registration-hindu"].unit == "days"
    assert "District Registrar" in data.appeals["subregistrar"].first_appeal


def test_passport_timelines(data: official.OfficialData) -> None:
    fresh = data.timelines["passport-fresh"]
    assert fresh.days == 30 and "police verification" in fresh.excludes and fresh.office_type == "passport"
    assert data.timelines["passport-tatkaal"].excludes == ""
    assert fresh.citation == fresh.source_url  # no page number recorded
    assert data.helplines["passport"].kind == "toll_free"


def test_every_timeline_has_offices_of_its_type(data: official.OfficialData) -> None:
    for t in data.timelines.values():
        assert data.offices_of(t.office_type), t.id


# Pincode extraction


@pytest.mark.parametrize(
    ("address", "pincode"),
    [
        ("Mini Secretariat, Rajiv Chowk, Gurugram 122001", "122001"),
        ("Sector 12, Karnal 132 001", "132001"),
        ("Ambala City- 13401", ""),
        ("No. 1220012, Somewhere", ""),
    ],
)
def test_pincode_is_the_last_six_digit_pin(address: str, pincode: str) -> None:
    assert official.Office("x", "rto", "X", "https://x", address=address).pincode == pincode


# Strict loading


@pytest.mark.parametrize(
    ("body", "error"),
    [
        (RTO_META + '[[office]]\nid = "x"\nname = "X"\nlandlines = ["080-123"]\n', "080-123"),
        (RTO_META + '[[office]]\nid = "x"\nname = "X"\nlandlines = ["9876543210"]\n', "expected landline"),
        (RTO_META + '[[office]]\nid = "x"\nname = "X"\ncug = ["080-26630989"]\n', "expected mobile"),
        (RTO_META + '[[office]]\nid = "x"\nname = "X"\nlandline = ["080-26630989"]\n', "unknown key"),
        (RTO_META + '[[office]]\nid = "x"\n', "missing name"),
        (RTO_META + '[[office]]\nid = "x"\nname = "X"\n[[office]]\nid = "x"\nname = "Y"\n', "duplicate office"),
        ('[meta]\noffice_type = "rto"\n[[office]]\nid = "x"\nname = "X"\n', "no source_url"),
        ('[meta]\nsource_url = "https://x"\n[[office]]\nid = "x"\nname = "X"\n', "no office_type"),
        (RTO_META + '[[service]]\nid = "s"\nname = "S"\ndays = 7.5\n', "positive integer"),
        (RTO_META + '[[service]]\nid = "s"\nname = "S"\ndays = "7"\n', "positive integer"),
        (RTO_META + '[[service]]\nid = "s"\nname = "S"\ndays = 7\npage = true\n', "page must be"),
        (RTO_META + '[[service]]\nid = "s"\nname = "S"\n', "days must be"),
        (RTO_META + '[appeals.rto]\nfirst_appeal = "X"\n', "appeals.rto"),
        (RTO_META + 'helpline = "123"\n', "not a valid Indian number"),
        ('[meta]\nofice_type = "rto"\n', "unknown key"),
    ],
)
def test_bad_data_is_rejected(tmp_path: Path, body: str, error: str) -> None:
    with pytest.raises(official.OfficialDataError, match=error):
        official.load(write(tmp_path, body))


def test_service_inherits_office_type_from_meta(tmp_path: Path) -> None:
    loaded = official.load(write(tmp_path, RTO_META + '[[service]]\nid = "s"\nname = "S"\ndays = 3\n'))
    assert loaded.timelines["s"].office_type == "rto" and loaded.timelines["s"].citation == "https://example.gov.in"


def test_national_helpline_is_recognised(data: official.OfficialData) -> None:
    # The Electronic City test-track listing on Maps shows this number.
    line = data.national["+911204925505"]
    assert "Parivahan" in line.name and line.source_url.startswith("https://parivahan.gov.in")
