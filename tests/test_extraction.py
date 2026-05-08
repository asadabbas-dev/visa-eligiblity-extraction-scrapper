"""Unit tests for semantic extraction quality."""

from __future__ import annotations

import unittest

from bs4 import BeautifulSoup

from app.scraper.extractor import SemanticExtractor


class TestSemanticExtraction(unittest.TestCase):
    def setUp(self) -> None:
        self.extractor = SemanticExtractor()

    def _extract(self, html: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        main = soup.select_one("main")
        assert main is not None
        return self.extractor.extract(soup=soup, page_url="https://www.canada.ca/test", main_content=main).to_dict()

    def test_eligibility_extraction(self) -> None:
        html = """
        <html><head><title>Eligibility</title></head>
        <body><main>
            <h1>Visitor visa eligibility</h1>
            <h2>Who can apply</h2>
            <ul>
              <li>Have a valid passport or travel document</li>
              <li>Be in good health</li>
              <li>Have enough money for your stay</li>
              <li>Show proof of ties to your home country</li>
              <li>Show you will leave Canada at the end of your visit</li>
            </ul>
        </main></body></html>
        """
        data = self._extract(html)
        self.assertIn("valid passport/travel document", data["eligibility_signals"])
        self.assertIn("good health", data["eligibility_signals"])
        self.assertIn("sufficient funds", data["eligibility_signals"])
        self.assertIn("proof of ties to home country", data["eligibility_signals"])
        self.assertIn("proof applicant will leave Canada", data["eligibility_signals"])

    def test_supporting_documents_extraction(self) -> None:
        html = """
        <html><head><title>Supporting docs</title></head>
        <body><main>
            <h1>Supporting documents</h1>
            <h2>Documents to include</h2>
            <ul>
              <li>Passport</li>
              <li>Bank statements</li>
              <li>Invitation letter</li>
              <li>Employment proof</li>
              <li>Marriage certificate</li>
              <li>Proof of relationship</li>
              <li>Police certificates</li>
              <li>Medical documents</li>
            </ul>
        </main></body></html>
        """
        data = self._extract(html)
        for expected in (
            "passport",
            "bank statements",
            "invitation letter",
            "employment proof",
            "marriage certificate",
            "proof of relationship",
            "police certificates",
            "medical documents",
        ):
            self.assertIn(expected, data["supporting_document_signals"])

    def test_form_extraction_category(self) -> None:
        html = """
        <html><head><title>Forms and guides</title></head>
        <body><main>
            <h1>Apply for visitor visa</h1>
            <h2>Required forms</h2>
            <p>Complete form IMM 5257 and IMM 5645 before submission.</p>
        </main></body></html>
        """
        data = self._extract(html)
        required_sections = [s for s in data["sections"] if s["heading"] == "Required forms"]
        self.assertTrue(required_sections)
        self.assertEqual(required_sections[0]["category"], "required_forms")


if __name__ == "__main__":
    unittest.main()
