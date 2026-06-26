from app import scoring, signals


def test_stylometric_returns_unit_interval():
    score = signals.stylometric_signal("The cat sat. The dog ran fast! Birds sing softly.")
    assert 0.0 <= score <= 1.0


def test_stylometric_neutral_on_empty():
    assert signals.stylometric_signal("") == 0.5


def test_metadata_detects_ai_marker():
    assert signals.metadata_signal({"Software": "Midjourney v6"}) >= 0.9


def test_metadata_detects_human_marker():
    assert signals.metadata_signal({"Make": "Canon", "Model": "EOS R5"}) <= 0.3


def test_metadata_neutral_when_absent():
    assert signals.metadata_signal(None) == 0.4


def test_weighted_confidence_weights():
    score = scoring.weighted_confidence({"llm": 1.0, "stylometric": 1.0, "metadata": 1.0})
    assert score == 1.0
    score = scoring.weighted_confidence({"llm": 0.0, "stylometric": 0.0, "metadata": 0.0})
    assert score == 0.0


def test_attribution_bands():
    assert scoring.attribution_for(0.2) == "likely_human"
    assert scoring.attribution_for(0.5) == "uncertain"
    assert scoring.attribution_for(0.85) == "likely_ai"


def test_label_generator_matches_band():
    assert "AI-generated" in scoring.label_generator(0.9)
    assert "inconclusive" in scoring.label_generator(0.5)
    assert "human-typical" in scoring.label_generator(0.1)
