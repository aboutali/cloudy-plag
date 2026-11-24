from app.detectors.ngram import fingerprint, jaccard


def test_identical_text_high_similarity() -> None:
    a = (
        "Die föderale Ordnung der Bundesrepublik Deutschland prägt das "
        "Verhältnis von Bund und Ländern in besonderer Weise."
    )
    fp_a = fingerprint(a)
    fp_b = fingerprint(a)
    assert jaccard(fp_a, fp_b) > 0.95


def test_disjoint_text_low_similarity() -> None:
    a = "Die föderale Ordnung prägt das Verhältnis von Bund und Ländern."
    b = "Maschinelles Lernen verändert die Verarbeitung natürlicher Sprache."
    assert jaccard(fingerprint(a), fingerprint(b)) < 0.05


def test_paraphrase_partial_overlap() -> None:
    a = (
        "Die zentrale These der Arbeit lautet, dass die Föderalismusreform "
        "die Handlungsfähigkeit des Bundes substanziell erweitert hat."
    )
    near = (
        "Die zentrale These der Arbeit lautet, dass die Föderalismusreform "
        "die Handlungsfähigkeit des Bundes deutlich gestärkt hat."
    )
    score = jaccard(fingerprint(a), fingerprint(near))
    assert score > 0.4
    assert score < 1.0
