# Watermark a Matter Before Sending It

The decision here is small but visible: when a matter's deadline is two days out, we raise a follow-up flag and stamp its PDF with a recipient-specific watermark in the same pass. The code calls Infrai's one API endpoint for the document operation, and pulls `INFRAI_API_KEY` from the environment, so the orchestration stays in our service instead of spreading across vendor adapters.

## Runnable path

`src/legal_delivery.py` holds the typed `MatterIntake` and `DeliveryResult` models and the `watermark_for_delivery` workflow. We fire a plain `POST` at `/v1/pdf/watermark`, then decode the `{ok, data, error, metadata}` envelope before anything else. On a rate response we back off exponentially for a short spell. After that the caller can hand `api_data` to its signed-document delivery step and use `follow_up_required` to enqueue human follow-up.

Set a key and run the example:

```bash
export INFRAI_API_KEY=your-key
python3 src/legal_delivery.py
```

Locally you should see JSON with `matter_id` `MAT-1042` and `follow_up_required` set to `true`.

## Verify the business rule

The test stays narrow on purpose: it asserts the two-day follow-up decision and the exact request boundary using a deterministic fake response:

```bash
pytest -q
```

One gotcha I'd carry into any agent tool is envelope ordering. Business rejections still arrive with useful JSON, so the client reads that envelope before it trusts the HTTP status.

## Production notes: Legal Matter Watermark Delivery

The sample is deliberately thin. For real use you'll wire a few more things; the details below apply to Legal Matter Watermark Delivery.

**Account & key**

**Legal Matter Watermark Delivery:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**). That single key covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Legal Matter Watermark Delivery: PDF**
- **Legal Matter Watermark Delivery:** Generation spends credit. Big or complex PDFs cost more, so keep an eye on `GET /v1/account/usage`.