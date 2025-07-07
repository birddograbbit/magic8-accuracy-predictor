# Magic8 Trade Data Schema

This document lists all columns produced by `process_magic8_data_optimized_v2.py` after the Phase 0 rebuild. The schema consolidates the **profit**, **trades** and **delta** sheets and is used for feature engineering in later phases.

## Identity Fields
- `date`
- `time`
- `timestamp`
- `symbol`
- `strategy`

## Profit Sheet Columns
- `price`
- `premium`
- `predicted`
- `closed`
- `expired`
- `risk`
- `reward`
- `ratio`
- `profit`
- `target` - binary win/loss indicator derived from the `profit` column

## Trades Sheet Columns
- `source`
- `expected_move`
- `low`
- `high`
- `target1`
- `target2`
- `predicted_trades`
- `closing`
- `strike1`
- `direction1`
- `type1`
- `bid1`
- `ask1`
- `mid1`
- `strike2`
- `direction2`
- `type2`
- `bid2`
- `ask2`
- `mid2`
- `strike3`
- `direction3`
- `type3`
- `bid3`
- `ask3`
- `mid3`
- `strike4`
- `direction4`
- `type4`
- `bid4`
- `ask4`
- `mid4`

## Delta Sheet Columns
- `call_delta`
- `put_delta`
- `predicted_delta`
- `short_term`
- `long_term`
- `closing_delta`

## Metadata
- `trade_description`
- `source_file`
- `format_year`
