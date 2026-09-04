from market_signals.evaluator.evaluate import trade_range_verdict


def test_trade_range_verdict_favors_other_person() -> None:
    result = trade_range_verdict(
        give_ci_low=120.0,
        give_ci_high=140.0,
        get_ci_low=80.0,
        get_ci_high=100.0,
    )

    assert result == "FAVORS OTHER PERSON -- you're giving up more than you'd get"


def test_trade_range_verdict_favors_you() -> None:
    result = trade_range_verdict(
        give_ci_low=80.0,
        give_ci_high=100.0,
        get_ci_low=120.0,
        get_ci_high=140.0,
    )

    assert result == "FAVORS YOU -- you'd get more value than you're giving"


def test_trade_range_verdict_reports_overlap_as_roughly_fair() -> None:
    result = trade_range_verdict(
        give_ci_low=80.0,
        give_ci_high=130.0,
        get_ci_low=100.0,
        get_ci_high=150.0,
    )

    assert result == "ROUGHLY FAIR -- summed ranges overlap, so it is hard to call precisely"
