"""Tests for knowledge base chunking and ChromaDB retrieval."""

import pytest

from app.retriever import chunk_article, index_kb, search


def test_chunk_article():
    """Verify that chunk_article splits a KB file into sections with correct IDs."""
    chunks = chunk_article("data/kb/refund-policy.md")
    assert len(chunks) == 3
    for chunk in chunks:
        assert chunk["filename"] == "refund-policy.md"
        assert chunk["id"].startswith("refund-policy.md#")
        assert len(chunk["text"]) > 20


@pytest.fixture(scope="module")
def indexed_kb():
    """Ensure the knowledge base is indexed in ChromaDB once for all search tests."""
    total_chunks = index_kb()
    assert total_chunks > 0
    return total_chunks


@pytest.mark.parametrize(
    "question, expected_files",
    [
        (
            "my package is late and has not arrived",
            ["order-tracking-and-status.md", "shipping-and-delivery.md"],
        ),
        (
            "how do I get a refund for my returned item",
            ["refund-policy.md"],
        ),
        (
            "how do I return an item within 30 days of delivery",
            ["returns-and-replacements.md"],
        ),
        (
            "what is the delivery fee for orders below Rs 999",
            ["shipping-and-delivery.md"],
        ),
        (
            "what is covered under the standard 1 year warranty",
            ["warranty-and-repairs.md"],
        ),
        (
            "can I pay using cash on delivery at my doorstep",
            ["cash-on-delivery.md", "payment-methods-and-security.md"],
        ),
        (
            "how does no cost emi work on credit cards",
            ["emi-options-and-plans.md"],
        ),
        (
            "my package arrived damaged and the laptop screen was cracked",
            ["damaged-defective-wrong-shipment.md"],
        ),
    ],
)
def test_retriever_queries(indexed_kb, question, expected_files):
    """Verify that for 8 sample questions, the correct KB file appears in the top 3 results."""
    hits = search(question, k=4)
    assert len(hits) > 0

    top_3_files = [hit["filename"] for hit in hits[:3]]

    # Check if at least one of the expected files appears in the top 3
    match_found = any(expected in top_3_files for expected in expected_files)
    assert match_found, f"Expected one of {expected_files} in top 3 {top_3_files} for question: '{question}'"
