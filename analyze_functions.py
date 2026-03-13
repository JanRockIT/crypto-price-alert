# These functions compare the current price ("now") with average prices
# over different timeframes:
# - week
# - month
# - six months
# - year
#
# They return True when a specific market pattern is detected,
# otherwise they return False.


def is_multi_timeframe_downtrend(now, week, month, six_months, year):
    """
    Meaning:
    The price is lower on every shorter timeframe.

    Logic:
    now < week < month < six_months < year

    Interpretation:
    This suggests a broad downtrend.
    The current price is below the weekly average,
    the weekly average is below the monthly average,
    the monthly average is below the six-month average,
    and the six-month average is below the yearly average.

    In simple words:
    The asset has been getting weaker over time.
    """
    if now < week < month < six_months < year:
        return True
    return False


def is_deeply_discounted_vs_long_term_averages(now, six_months, year):
    """
    Meaning:
    The current price is much lower than the long-term averages.

    Logic:
    now < six_months * 0.85 and now < year * 0.8

    Interpretation:
    The asset is trading far below both the six-month average
    and the yearly average.

    In simple words:
    The price may be heavily discounted compared to its longer-term history.
    """
    if now < six_months * 0.85 and now < year * 0.8:
        return True
    return False


def is_showing_early_recovery(now, week, month, six_months, year):
    """
    Meaning:
    The longer trend is still weak, but the current price is starting to recover.

    Logic:
    week < month < six_months < year and now > week

    Interpretation:
    The averages still show weakness across larger timeframes,
    but the current price has already moved above the weekly average.

    In simple words:
    The asset may be showing the first signs of a recovery.
    """
    if week < month < six_months < year and now > week:
        return True
    return False


def is_potential_buy_zone(now, week, six_months, year):
    """
    Meaning:
    The asset is still cheap compared to long-term averages,
    but it may already be stabilizing.

    Logic:
    now < six_months * 0.9 and now < year * 0.85 and now > week

    Interpretation:
    The current price is below the six-month and yearly averages,
    but it is already above the weekly average.

    In simple words:
    This can be a possible buy zone:
    still discounted, but no longer in pure short-term weakness.
    """
    if now < six_months * 0.9 and now < year * 0.85 and now > week:
        return True
    return False


def is_overextended_to_the_upside(now, week, month, six_months, year):
    """
    Meaning:
    The price is stronger on every shorter timeframe.

    Logic:
    now > week > month > six_months > year

    Interpretation:
    The current price is above the weekly average,
    the weekly average is above the monthly average,
    the monthly average is above the six-month average,
    and the six-month average is above the yearly average.

    In simple words:
    The asset has been trending upward strongly.
    It may be very strong, but it could also be overheated.
    """
    if now > week > month > six_months > year:
        return True
    return False

# all at once
def analyze_market_signals(now, week, month, six_months, year):
    return {
        "is_multi_timeframe_downtrend": is_multi_timeframe_downtrend(now, week, month, six_months, year),
        "is_deeply_discounted_vs_long_term_averages": is_deeply_discounted_vs_long_term_averages(now, six_months, year),
        "is_showing_early_recovery": is_showing_early_recovery(now, week, month, six_months, year),
        "is_potential_buy_zone": is_potential_buy_zone(now, week, six_months, year),
        "is_overextended_to_the_upside": is_overextended_to_the_upside(now, week, month, six_months, year)
    }
    