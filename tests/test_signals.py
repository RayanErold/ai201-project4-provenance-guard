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


def test_even_weights_text():
    # If llm=0.9, stylometric=0.6, metadata=0.3
    # S = 1/3 * 0.9 + 1/3 * 0.6 + 1/3 * 0.3 = 0.3 + 0.2 + 0.1 = 0.6
    score = scoring.weighted_confidence({"llm": 0.9, "stylometric": 0.6, "metadata": 0.3}, source="text")
    assert abs(score - 0.6) < 1e-4


def test_even_weights_image():
    # S = 0.5 * llm + 0.5 * metadata (stylometric is ignored)
    # S = 0.5 * 0.8 + 0.5 * 0.2 = 0.5
    score = scoring.weighted_confidence({"llm": 0.8, "stylometric": 0.1, "metadata": 0.2}, source="image")
    assert abs(score - 0.5) < 1e-4


def test_run_signals_image_captions():
    # Test that run_signals extracts caption and runs image_artifact_signal
    text = "[image transcript of 'test.png'] A smooth image depicting unnatural structures and impossible geometry."
    metadata = {"vlm_captioned": True}
    res = signals.run_signals(text, metadata, source="image")
    assert "llm" in res
    assert "stylometric" in res
    assert res["stylometric"] == 0.5
    assert "metadata" in res

