# Trading Bot — Binance Futures Testnet (USDT-M)

A clean, production-structured Python CLI application for placing orders on the Binance Futures Testnet.  
Supports **MARKET**, **LIMIT**, and **STOP_MARKET** orders with full logging, validation, and error handling.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package metadata
│   ├── client.py            # Binance REST client (signing, HTTP, error handling)
│   ├── orders.py            # Order building, placement, response parsing
│   ├── validators.py        # Input validation (pure functions)
│   └── logging_config.py   # Dual console + file logging setup
├── cli.py                   # CLI entry point (argparse)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet Credentials

1. Visit [testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Go to **API Key** section and generate a key pair
4. Copy your **API Key** and **API Secret**

### 2. Clone / Download the Project

```bash
cd trading_bot
```

### 3. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Set API Credentials

**Option A — Environment variables (recommended):**

```bash
export BINANCE_API_KEY=your_testnet_api_key
export BINANCE_API_SECRET=your_testnet_api_secret
```

**Option B — .env file:**

Create a `.env` file in the project root:

```
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

Then load it before running:

```bash
export $(cat .env | xargs)
```

**Optional — override base URL:**
The default target is `https://testnet.binancefuture.com`. To point elsewhere (e.g., demo endpoints), set `BASE_URL` before running:

```bash
export BASE_URL=https://demo-fapi.binance.com
```

**Option C — CLI flags (least secure, use for quick testing only):**

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET ...
```

---

## How to Run

### Place a MARKET BUY order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a MARKET SELL order

```bash
python cli.py --symbol BTCUSDT --side SELL --type MARKET --quantity 0.01
```

### Place a LIMIT BUY order

```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 80000
```

### Place a LIMIT SELL order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 100000
```

### Place a STOP_MARKET SELL order (Bonus order type)

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 85000
```

### Use interactive mode (lightweight UI)

Let the CLI prompt you for missing inputs instead of passing flags:

```bash
python cli.py --interactive
```

You can still prefill any flag (e.g., `--symbol BTCUSDT`) and the prompts will ask only for the rest.

### View all CLI options

```bash
python cli.py --help
```

---

## Sample Output

```
--------------------------------------------------
  ORDER REQUEST SUMMARY
--------------------------------------------------
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.01
--------------------------------------------------

--------------------------------------------------
  ORDER RESPONSE
--------------------------------------------------
  Order ID      : 3799370987
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Orig Qty      : 0.01
  Executed Qty  : 0.01
  Avg Price     : 96523.50000
--------------------------------------------------

   Order placed successfully!
```

---

## Logging

All activity is logged to `trading_bot.log` in the project root.

- **Console** — INFO level and above (clean, human-readable)
- **File** — DEBUG level and above (full request/response payloads for audit)

Example log entries:

```
2025-01-15 14:23:01 | INFO     | bot.orders | Order request → BUY BTCUSDT MARKET qty=0.01
2025-01-15 14:23:01 | DEBUG    | bot.client | REQUEST  POST /fapi/v1/order | params={...}
2025-01-15 14:23:02 | DEBUG    | bot.client | RESPONSE POST /fapi/v1/order | status=200 | body={...}
2025-01-15 14:23:02 | INFO     | bot.orders | Order response → orderId=3799370987 status=FILLED executedQty=0.01 avgPrice=96523.5
2025-01-15 14:23:02 | INFO     | cli        | Order completed successfully. orderId=3799370987
```

---

## Error Handling

| Error Type           | What happens                                      |
| -------------------- | ------------------------------------------------- |
| Invalid input        | `ValueError` caught → user-friendly message shown |
| Binance API error    | `BinanceAPIError` → code + message printed        |
| Network timeout      | Friendly timeout message + logged                 |
| Connection failure   | Connection error message + logged                 |
| Unexpected exception | Full traceback logged to file, clean msg shown    |

---

## Architecture

```
CLI Layer (cli.py)
    └── Parses args, prints summaries, handles top-level exceptions

Business Logic (bot/orders.py)
    ├── Calls validators
    ├── Builds order payload
    ├── Calls client
    └── Returns OrderResult (parsed response)

API Layer (bot/client.py)
    ├── Signs requests (HMAC-SHA256)
    ├── Executes HTTP requests
    ├── Logs requests + responses
    └── Raises BinanceAPIError on API errors

Validators (bot/validators.py)
    └── Pure functions, raise ValueError on bad input

Logging (bot/logging_config.py)
    └── Console (INFO+) + File (DEBUG+) handlers
```

---

## Assumptions

1. **Testnet only** — the base URL is hardcoded to `https://testnet.binancefuture.com`. Do not use real credentials.
2. **USDT-M Futures** — all orders are placed on USDT-margined perpetual futures contracts.
3. **Minimum quantity** — Binance enforces minimum order sizes per symbol (e.g. 0.001 BTC for BTCUSDT). If you get a filter error, increase quantity.
4. **Testnet prices** — testnet prices may differ significantly from real market prices. Limit orders may need to be set near the current testnet price to get filled.
5. **No dependency on python-binance** — uses direct REST calls with `requests` for full transparency and control.
6. **STOP_MARKET orders** require that your stop price triggers based on the mark/last price. On testnet this may behave slightly differently than production.

---

## Dependencies

| Package         | Purpose                        |
| --------------- | ------------------------------ |
| `requests`      | HTTP client for REST API calls |
| `python-dotenv` | Optional `.env` file loading   |

No third-party Binance SDK required.
