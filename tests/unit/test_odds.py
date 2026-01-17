from odds.normalize import american_to_implied_prob, decimal_to_implied_prob


def test_american_to_implied_prob() -> None:
    assert round(american_to_implied_prob(100), 2) == 0.5
    assert round(american_to_implied_prob(-200), 2) == 0.67


def test_decimal_to_implied_prob() -> None:
    assert round(decimal_to_implied_prob(2.0), 2) == 0.5
