"""Tests for bucket classifier."""

import pytest
from stock_cycle_tracker.domain.buckets import BucketClassifier, BucketConfig


def test_positive_buckets():
    classifier = BucketClassifier()

    assert classifier.classify(0.0) == "Upside 0–5%"
    assert classifier.classify(2.5) == "Upside 0–5%"
    assert classifier.classify(5.0) == "Upside 0–5%"
    assert classifier.classify(5.01) == "Upside 5–10%"
    assert classifier.classify(10.0) == "Upside 5–10%"
    assert classifier.classify(10.01) == "Upside 10–15%"
    assert classifier.classify(15.0) == "Upside 10–15%"
    assert classifier.classify(15.01) == "Upside 15–20%"
    assert classifier.classify(20.0) == "Upside 15–20%"
    assert classifier.classify(20.01) == "Upside >20%"
    assert classifier.classify(150.0) == "Upside >20%"


def test_negative_buckets():
    classifier = BucketClassifier()

    assert classifier.classify(-0.01) == "Downside 0–5%"
    assert classifier.classify(-2.5) == "Downside 0–5%"
    assert classifier.classify(-5.0) == "Downside 0–5%"
    assert classifier.classify(-5.01) == "Downside 5–10%"
    assert classifier.classify(-10.0) == "Downside 5–10%"
    assert classifier.classify(-10.01) == "Downside 10–15%"
    assert classifier.classify(-15.0) == "Downside 10–15%"
    assert classifier.classify(-15.01) == "Downside 15–20%"
    assert classifier.classify(-20.0) == "Downside 15–20%"
    assert classifier.classify(-20.01) == "Downside >20%"
    assert classifier.classify(-75.0) == "Downside >20%"


def test_custom_config():
    custom_cfg = BucketConfig(threshold_low=3.0)
    classifier = BucketClassifier(config=custom_cfg)
    assert classifier.classify(2.0) == "Upside 0–3%"
    assert classifier.classify(-2.0) == "Downside 0–3%"
