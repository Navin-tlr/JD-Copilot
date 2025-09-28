from app.rag import _augment_query_for_embeddings


def test_b2b_query_includes_synonyms():
    question = "Is there any company came for b2b sales?"
    augmented = _augment_query_for_embeddings(question)
    assert augmented.startswith(question)
    lowered = augmented.lower()
    assert "business development" in lowered
    assert "enterprise sales" in lowered


def test_no_augmentation_when_not_needed():
    question = "Show marketing roles"
    augmented = _augment_query_for_embeddings(question)
    assert augmented == question
