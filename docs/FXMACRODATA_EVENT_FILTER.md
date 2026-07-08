# FXMacroData Event Filter Example

FXMacroData's public USD release calendar can be used as a lightweight
macro-event filter in PTrade-style strategies. A common pattern is to fetch
top-tier event dates before the session and skip new entries on those dates.

```python
import json
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = "https://fxmacrodata.com/api/v1/calendar/{currency}"


def fetch_top_tier_dates(currency="USD", days=30):
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    query = urlencode({
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    })

    with urlopen("{}?{}".format(BASE_URL.format(currency=currency), query), timeout=20) as response:
        payload = json.load(response)

    dates = set()
    for event in payload.get("data", []):
        if event.get("top_tier_for_currency") or event.get("market_tier") == 1:
            event_time = event.get("announcement_datetime_utc") or event.get("announcement_datetime_local")
            dates.add((event_time or event.get("date", ""))[:10])
    return dates


def initialize(context):
    context.macro_blackout_dates = fetch_top_tier_dates()
    context.test_stock = "000300.SS"


def before_trading_start(context, data):
    today = get_datetime().strftime("%Y-%m-%d")
    context.macro_blackout = today in context.macro_blackout_dates


def handle_data(context, data):
    if context.macro_blackout:
        log.info("Skipping new entries during top-tier USD macro release window")
        return

    order_value(context.test_stock, context.portfolio.portfolio_value * 0.10)
```
