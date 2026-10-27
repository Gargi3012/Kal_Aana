"""What Google tells a citizen. Responses are hand-made fixtures shaped like SerpApi's JSON."""

from pathlib import Path
from typing import Any

from kalaana import official
from kalaana.citizen import ai_mode_params, citizen_view, search_name, search_params
from kalaana.client import SearchClient
from kalaana.offices import CITIES

DATA = official.load()
HR26 = DATA.offices["rto-hr26"]
CITY = CITIES["Haryana"]


class Fake:
    def __init__(self, responses: dict[str, dict[str, Any]]):
        self.responses = responses

    def search(self, params: dict[str, Any]) -> dict[str, Any]:
        if params["engine"] == "google_ai_mode":
            return self.responses.get("AI Mode", {})
        return self.responses[params.get("q") or params["page_token"]]


def view_for(responses: dict[str, dict[str, Any]], tmp_path: Path) -> Any:
    client = SearchClient(api_key="k" * 64, cache_dir=tmp_path)
    client._client = Fake(responses)
    return citizen_view(client, HR26, DATA, CITY)


def test_query_is_what_a_citizen_types() -> None:
    assert search_name(HR26) == "RTA Gurugram"
    assert search_params(HR26, CITY)["q"] == "RTA Gurugram phone number"


def test_numbers_and_address_are_checked_against_the_directory(tmp_path: Path) -> None:
    view = view_for({
        "RTA Gurugram phone number": {
            "ai_overview": {"page_token": "tok"},
            "local_results": {"places": [{"title": "RTA Faridabad", "phone": "0129 222 7814"}]},
            "organic_results": [{"title": "RTA list", "snippet": "Call 0120 492 5505 or 98450 00000", "link": "https://www.example.com/x"}],
        },
        "tok": {"ai_overview": {"text_blocks": [
            {"type": "paragraph", "snippet": "The phone number is +91-124-2321151."},
            {"type": "list", "list": [{"snippet": "Address: Sector 14, Gurugram, Haryana 122018"}]},
        ], "references": [{"title": "Cars24", "link": "https://www.cars24.com/x"}]}},
    }, tmp_path)
    verdicts = {(n.surface, n.phone.display): n.verdict for n in view.numbers}
    assert verdicts == {
        ("ai_overview", "0124 232 1151"): "this office",
        ("local_pack", "0129 222 7814"): "another office",
        ("snippet", "0120 492 5505"): "national helpline",
        ("snippet", "98450 00000"): "not in the directory",
    }
    assert view.ai_pincodes == ["122018"] and view.ai_address_matches(HR26) is False
    assert view.ai_references == [("Cars24", "https://www.cars24.com/x")]


def test_no_ai_overview_and_failed_search(tmp_path: Path) -> None:
    view = view_for({"RTA Gurugram phone number": {"organic_results": []}}, tmp_path / "a")
    assert view.ai_text == "" and view.ai_address_matches(HR26) is None
    broken = citizen_view(SearchClient(api_key="", cache_dir=tmp_path / "b"), HR26, DATA, CITY)  # demo mode, nothing cached
    assert broken.notes and not broken.numbers


def test_ai_mode_is_asked_the_same_question_and_checked_the_same_way(tmp_path: Path) -> None:
    assert ai_mode_params(HR26, CITY)["q"] == search_params(HR26, CITY)["q"]
    view = view_for({
        "RTA Gurugram phone number": {"ai_overview": {"text_blocks": [{"type": "paragraph", "snippet": "Call 0124-2321151, Gurugram 122018."}]}},
        "AI Mode": {"search_metadata": {"id": "mode1", "created_at": "2026-10-08 07:38:44 UTC"}, "text_blocks": [
            {"type": "list", "list": [{"snippet": "Phone Numbers: 0124-2321151, 0124-2224444"}, {"snippet": "Address: Mini Secretariat, Sector 1, Gurugram - 122001"}]},
        ], "references": [{"title": "Transport Department", "link": "https://haryanatransport.gov.in/x"}]},
    }, tmp_path)
    assert view.ai_address_matches(HR26) is False and view.mode_address_matches(HR26) is True
    assert [n.phone.display for n in view.numbers if n.surface == "ai_mode"] == ["0124 232 1151", "0124 222 4444"]
    assert all(n.verdict == "this office" for n in view.numbers if n.surface == "ai_mode")
    assert view.mode_search_id == "mode1" and view.mode_searched_on == "2026-10-08"
