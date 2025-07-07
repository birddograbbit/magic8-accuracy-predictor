# Integration Update: DiscordTrading Continuous Monitoring

## Purpose
This document provides integration instructions for DiscordTrading to use magic8-accuracy-predictor's new batch prediction endpoint for continuous monitoring support.

## Background
DiscordTrading's continuous monitoring system (Section 12, PR #63) checks ML confidence every 5 minutes for all active symbols and strategies. This creates ~2,496 API calls per day vs the previous ~200 calls/day.

## Solution: Batch Prediction API (Available Now)

### Endpoint
```
POST http://localhost:8000/predict/batch
```

### Request Format
```json
{
  "requests": [
    {
      "strategy": "Butterfly",
      "symbol": "SPX", 
      "premium": 24.82,
      "predicted_price": 5855,
      "strikes": [5905, 5855, 5805],
      "action": "BUY",
      "quantity": 1
    },
    {
      "strategy": "Iron Condor",
      "symbol": "SPX",
      "premium": 0.65,
      "predicted_price": 5855,
      "strikes": [5880, 5875, 5835, 5830],
      "action": "SELL",
      "quantity": 1
    }
    // ... more requests
  ],
  "share_market_data": true  // Share market data fetch across all predictions
}
```

### Response Format
```json
{
  "predictions": [
    {
      "timestamp": "2025-01-07T12:00:00",
      "symbol": "SPX",
      "strategy": "Butterfly",
      "win_probability": 0.723,
      "prediction": "WIN",
      "data_source": "ibkr",
      "n_features": 74
    },
    // ... more predictions
  ],
  "batch_metrics": {
    "feature_hits": 10,
    "feature_misses": 2,
    "prediction_hits": 8,
    "prediction_misses": 4
  }
}
```

## Integration Code for DiscordTrading

### Update continuous_processor.py

Replace individual prediction calls with batch processing:

```python
async def check_all_confidence(self) -> List[ConfidenceRecord]:
    """Check confidence for all active symbol-strategy combinations."""
    
    # Build batch request
    batch_requests = []
    for symbol in self.enabled_symbols:
        for strategy in self.strategies:
            # Get latest trade instruction from Discord
            instruction = self.get_latest_instruction(symbol, strategy)
            if instruction:
                batch_requests.append({
                    "symbol": symbol,
                    "strategy": strategy,
                    "premium": instruction.get("limit_price", 0),
                    "predicted_price": instruction.get("predicted_price", 0),
                    "strikes": instruction.get("strikes", []),
                    "action": instruction.get("action", "SELL"),
                    "quantity": instruction.get("quantity", 1)
                })
    
    if not batch_requests:
        return []
    
    # Single batch API call instead of N individual calls
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ml_api_url}/predict/batch",
                json={"requests": batch_requests},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Log cache performance
                    metrics = data.get("batch_metrics", {})
                    logger.info(
                        f"Batch prediction complete: {len(data['predictions'])} predictions, "
                        f"cache hits: {metrics.get('feature_hits', 0)}/{metrics.get('feature_hits', 0) + metrics.get('feature_misses', 0)}"
                    )
                    
                    # Convert to confidence records
                    records = []
                    for pred in data["predictions"]:
                        records.append(ConfidenceRecord(
                            timestamp=datetime.now(),
                            symbol=pred["symbol"],
                            strategy=pred["strategy"],
                            win_probability=pred["win_probability"],
                            model_used=pred.get("model_type", "unknown"),
                            threshold=pred.get("threshold", 0.5)
                        ))
                    
                    return records
                else:
                    logger.error(f"Batch prediction failed: {resp.status}")
                    return []
                    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        return []
```

### Update ML Client (ml_prediction_client.py)

Add batch support to the existing client:

```python
async def check_trades_batch(self, instructions: List[Dict], 
                           use_dynamic_thresholds: bool = True) -> List[Tuple[bool, Dict]]:
    """
    Check multiple trades in a single batch request.
    
    Args:
        instructions: List of parsed trade instructions
        use_dynamic_thresholds: Use API's optimized thresholds
        
    Returns:
        List of (should_execute, details) tuples
    """
    if not self.session:
        logger.error("Session not initialized")
        return [(True, {"error": "Session not initialized"})] * len(instructions)
    
    try:
        # Build batch request
        batch_request = {
            "requests": [
                {
                    "strategy": self._map_strategy(inst.get('trade_type', '')),
                    "symbol": inst.get('symbol', 'SPX'),
                    "premium": float(inst.get('limit_price', 0)),
                    "predicted_price": self._estimate_predicted_price(inst),
                    "strikes": inst.get('strikes', []),
                    "action": inst.get('action', 'SELL'),
                    "quantity": inst.get('quantity', 1)
                }
                for inst in instructions
            ]
        }
        
        # Add risk/reward if available
        for i, inst in enumerate(instructions):
            if 'risk' in inst and 'reward' in inst:
                batch_request['requests'][i]['risk'] = float(inst['risk'])
                batch_request['requests'][i]['reward'] = float(inst['reward'])
        
        # Make batch request
        async with self.session.post(
            f"{self.api_url}/predict/batch",
            json=batch_request,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                
                # Log cache metrics
                metrics = data.get('batch_metrics', {})
                if metrics:
                    logger.debug(f"Batch cache performance: {metrics}")
                
                # Process predictions
                results = []
                for pred in data['predictions']:
                    win_prob = pred['win_probability']
                    threshold = 0.5
                    
                    if use_dynamic_thresholds:
                        # Use threshold from API if available
                        threshold = pred.get('threshold', 0.5)
                    
                    should_execute = win_prob >= threshold
                    
                    result_details = {
                        "win_probability": win_prob,
                        "threshold_used": threshold,
                        "prediction": pred.get('prediction', 'UNKNOWN'),
                        "should_execute": should_execute
                    }
                    
                    results.append((should_execute, result_details))
                
                return results
            else:
                error_text = await resp.text()
                logger.error(f"Batch API error {resp.status}: {error_text}")
                return [(True, {"error": f"API error {resp.status}"})] * len(instructions)
                
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        return [(True, {"error": str(e)})] * len(instructions)
```

## Performance Benefits

### Before (Individual Calls)
- 32 API calls every 5 minutes
- 32 market data fetches
- 32 feature calculations
- Total time: ~10-15 seconds

### After (Batch Endpoint)
- 1 API call every 5 minutes
- 1-8 market data fetches (shared by symbol)
- Cached features reused
- Total time: <1 second

### Cache Performance
- Feature cache: 60-second TTL
- Prediction cache: 300-second TTL
- Market data cache: 300-second TTL

Monitor cache hit rates via `batch_metrics` in the response.

## Configuration

Ensure magic8-accuracy-predictor has appropriate cache settings in `config/config.yaml`:

```yaml
performance:
  cache:
    enabled: true
    market_data_ttl: 300    # 5 minutes - matches monitoring interval
    feature_ttl: 60         # 1 minute - features change slowly
    prediction_ttl: 300     # 5 minutes - predictions valid for full cycle
    max_size: 1000         # Enough for all symbol-strategy combinations
    
  batch_predictions:
    max_batch_size: 100    # More than enough for 32 combinations
```

## Testing the Integration

1. **Start magic8-accuracy-predictor**:
   ```bash
   cd magic8-accuracy-predictor
   python src/prediction_api_realtime.py
   ```

2. **Test batch endpoint**:
   ```bash
   curl -X POST http://localhost:8000/predict/batch \
     -H "Content-Type: application/json" \
     -d '{
       "requests": [
         {"symbol": "SPX", "strategy": "Butterfly", "premium": 24.82, "predicted_price": 5855},
         {"symbol": "SPX", "strategy": "Iron Condor", "premium": 0.65, "predicted_price": 5855}
       ]
     }'
   ```

3. **Monitor cache performance**:
   - Check `batch_metrics` in responses
   - Feature hits should increase over time
   - Prediction hits for repeated requests

## Rollout Plan

1. **Test in Development**
   - Use small batch sizes initially
   - Monitor response times
   - Verify cache effectiveness

2. **Gradual Migration**
   - Start with 1-2 symbols using batch
   - Monitor performance and accuracy
   - Expand to all symbols

3. **Full Production**
   - All continuous monitoring uses batch endpoint
   - Monitor cache hit rates >70%
   - Adjust TTLs based on usage patterns

## Troubleshooting

### "Request too large"
- Default max batch size is 100
- Split larger batches if needed

### Low cache hit rate
- Check if requests have consistent format
- Verify feature TTL is appropriate
- Ensure prediction keys are stable

### Timeout errors
- Batch timeout is 30 seconds
- Reduce batch size if needed
- Check market data provider latency

## Next Steps

Once integrated:
1. Monitor performance metrics
2. Tune cache TTLs based on hit rates
3. Consider WebSocket integration (Phase 3) for real-time updates
4. Add confidence history tracking (Phase 2) for trend analysis

---

**Document Created**: January 7, 2025  
**API Version**: Batch endpoint available in latest main branch  
**Support**: Create issue in magic8-accuracy-predictor repo
