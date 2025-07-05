import logging
import pandas as pd

logger = logging.getLogger(__name__)


def validate_delta_coverage(df: pd.DataFrame):
    """Validate delta data integration."""
    # Check source_file tracking
    has_delta = df['source_file'].str.contains('delta', na=False)
    delta_coverage = has_delta.sum() / len(df) * 100
    logger.info(f"Delta data coverage: {delta_coverage:.1f}%")

    # Check by date range
    df['date_parsed'] = pd.to_datetime(df['date'])
    monthly_coverage = df.groupby(df['date_parsed'].dt.to_period('M')).agg({
        'short_term': lambda x: x.notna().sum() / len(x) * 100,
        'long_term': lambda x: x.notna().sum() / len(x) * 100,
    })

    logger.info("Monthly delta coverage:")
    logger.info(monthly_coverage)

    # Identify missing delta periods
    missing_delta = df[df['short_term'].isna() & df['long_term'].isna()]
    logger.info(f"Trades missing delta data: {len(missing_delta)}")

    return {
        'overall_coverage': delta_coverage,
        'monthly_coverage': monthly_coverage,
        'missing_count': len(missing_delta),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate delta integration")
    parser.add_argument("csv_path", help="Path to processed CSV file")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    df = pd.read_csv(args.csv_path)
    validate_delta_coverage(df)
