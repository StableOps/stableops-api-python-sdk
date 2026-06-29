# Python SDK Examples

This directory contains example code for using the StableOps Python SDK.

## Examples

### Basic Usage

**create_order.py** - Create and monitor a payment order

```bash
export STABLEOPS_API_KEY=your_api_key
python examples/create_order.py
```

### Webhook Handler

**webhook_handler.py** - Flask webhook handler with signature verification

```bash
export STABLEOPS_WEBHOOK_SECRET=whsec_...
python examples/webhook_handler.py

# In another terminal, expose with ngrok
ngrok http 5000
```

### Async Usage

**async_example.py** - Async client with AsyncStableOps

```bash
export STABLEOPS_API_KEY=your_api_key
python examples/async_example.py
```

## Requirements

Install example dependencies:

```bash
pip install stableops flask
```

For async example:

```bash
pip install stableops
```

## Testing Webhooks Locally

1. Start the webhook handler:

   ```bash
   python examples/webhook_handler.py
   ```

2. Expose with ngrok:

   ```bash
   ngrok http 5000
   ```

3. Add webhook endpoint in StableOps dashboard:
   - URL: `https://your-ngrok-url.ngrok.io/webhooks/stableops`
   - Events: Select events to receive

4. Create a test payment order and send a test payment

## Documentation

- [API Documentation](https://docs.stableops.dev)
- [Integration Guides](https://docs.stableops.dev/guides)
- [Python SDK Reference](https://docs.stableops.dev/sdk/python)
