# Binance Futures Testnet Trading Bot

A clean, production-style Python CLI application for placing orders on the **Binance Futures Testnet (USDT-M)**. Built with a clear separation between the API client layer, business logic, and CLI interface.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API wrapper (auth, signing, HTTP)
│   ├── orders.py          # Order placement business logic
│   ├── validators.py      # Input validation (raises ValueError on bad input)
│   └── logging_config.py  # Rotating file + console logging setup
├── cli.py                 # CLI entry point (argparse)
├── logs/
│   └── trading_bot.log    # Auto-created on first run
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Prerequisites

- Python 3.10+
- A Binance Futures **Testnet** account

### 2. Get Testnet Credentials

1. Visit [testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in / register
3. Navigate to **API Management** and generate a key pair
4. Copy your **API Key** and **Secret**

### 3. Install Dependencies

```bash
cd trading_bot
pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

On Windows (PowerShell):

```powershell
$env:BINANCE_API_KEY = "your_api_key_here"
$env:BINANCE_API_SECRET = "your_api_secret_here"
```

---

## How to Run

### Place a MARKET order

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

### Place a LIMIT order

```bash
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 65000
```

### Place a STOP_MARKET order (Bonus order type)

```bash
python cli.py place --symbol ETHUSDT --side BUY --type STOP_MARKET --qty 0.01 --stop-price 3200
```

### List open orders

```bash
# All symbols
python cli.py orders

# Filtered by symbol
python cli.py orders --symbol BTCUSDT
```

### Show account balances

```bash
python cli.py account
```

### Enable debug logging to console

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

---

## Example Output

```
──────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
──────────────────────────────────────────────────
  Symbol          BTCUSDT
  Side            BUY
  Type            MARKET
  Quantity        0.001
  Price           —
  Stop Price      —
──────────────────────────────────────────────────

  ORDER RESPONSE
──────────────────────────────────────────────────
  Order ID         4104820374
  Symbol           BTCUSDT
  Side             BUY
  Type             MARKET
  Quantity         0.001
  Executed Qty     0.001
  Avg Price        62345.70000
  Status           FILLED
──────────────────────────────────────────────────

  ✓  Order placed successfully! orderId=4104820374
```

---

## Logging

Logs are written to `logs/trading_bot.log` (rotating, max 5 MB × 3 backups).

- **File handler**: `DEBUG` level — captures all API request/response details, signatures, and errors
- **Console handler**: `INFO` level by default (override with `--log-level`)

Log format:
```
2025-05-08T10:14:01 | INFO     | trading_bot.orders | Order placed ✓ | orderId=4104820374 status=FILLED ...
```

Sample log files from real testnet runs are in the `logs/` directory.

---

## Supported Order Types

| Type          | Required params                        | Notes                            |
|---------------|----------------------------------------|----------------------------------|
| `MARKET`      | `--symbol`, `--side`, `--qty`          | Fills immediately at market price |
| `LIMIT`       | `--symbol`, `--side`, `--qty`, `--price` | Rests on book until filled       |
| `STOP_MARKET` | `--symbol`, `--side`, `--qty`, `--stop-price` | Triggers a market order at stop price *(Bonus)* |

---

## Error Handling

| Error type        | Behaviour                                          |
|-------------------|----------------------------------------------------|
| Invalid input      | `ValueError` → printed to stderr, logged, exit 1  |
| API rejection      | `BinanceAPIError` → code + message shown           |
| Network failure    | `requests` exception → logged + shown              |

---

## Assumptions

- The testnet base URL `https://testnet.binancefuture.com` is hard-coded (configurable via `BinanceClient(base_url=...)`).
- Credentials are supplied via environment variables only (no `.env` file support in core — easy to add with `python-dotenv`).
- `timeInForce` defaults to `GTC` for LIMIT orders.
- `STOP_MARKET` is treated as the bonus third order type; it uses `stopPrice` as the trigger and places a market order when triggered.
- Quantity and price precision are passed as-is; if Binance rejects due to tick/lot size rules, the API error message will indicate the issue.

---

## Requirements

```
requests>=2.31.0
```

No third-party Binance SDK used — all API calls are made directly over REST with HMAC-SHA256 signing.
