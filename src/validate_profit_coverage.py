import pandas as pd
import logging

logger = logging.getLogger(__name__)


def validate_profit_data(df: pd.DataFrame) -> None:
    """Validate profit coverage and monthly win distribution.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame after target creation. Must contain 'interval_datetime',
        a profit column and 'target'.
    """
    if 'interval_datetime' not in df.columns:
        raise ValueError("DataFrame missing 'interval_datetime' column")
    if 'target' not in df.columns:
        raise ValueError("DataFrame must have a 'target' column for win checks")

    df = df.copy()
    df['month'] = pd.to_datetime(df['interval_datetime']).dt.to_period('M')

    profit_cols = [c for c in df.columns if c in ['prof_profit', 'raw', 'managed', 'profit_final']]
    profit_col = profit_cols[0] if profit_cols else None

    if not profit_col:
        logger.warning("No profit column found for validation")
        return

    monthly_counts = df.groupby('month')[profit_col].apply(lambda x: x.notna().sum())
    logger.info("Profit coverage by month:\n%s", monthly_counts.to_string())

    monthly_wins = df.groupby('month')['target'].sum()
    zero_win_months = monthly_wins[monthly_wins == 0]
    if not zero_win_months.empty:
        logger.error("Months with zero wins detected: %s", list(zero_win_months.index.astype(str)))
        raise ValueError("Data validation failed: months with zero wins")
