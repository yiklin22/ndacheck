from fastapi.testclient import TestClient

import ndacheck.app as appmod
from ndacheck.check import Answer

c = TestClient(appmod.app)


def fake_check(text):
    return [Answer("nda-18", "No solicitation of staff", "Entailment", "shall not solicit any employee", 0.9),
            Answer("nda-11", "No reverse engineering", "NotMentioned", None, 0.0, False)]


def test_page_shows_answers_with_evidence(monkeypatch):
    monkeypatch.setattr(appmod, "check", fake_check)
    page = c.post("/", data={"text": "The Recipient shall not solicit any employee."}).text
    assert "No solicitation of staff" in page and "shall not solicit any employee" in page
    assert "no clear clause found" in page


def test_rejects_empty_and_unsupported(monkeypatch):
    monkeypatch.setattr(appmod, "check", fake_check)
    assert "paste an NDA" in c.post("/", data={"text": " "}).text
    assert "only .pdf" in c.post("/", files={"file": ("a.xlsx", b"PK")}).text
