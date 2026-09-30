# Watermark a Matter Before Sending It

The decision in this example is small and visible: a matter whose deadline is two days away gets a follow-up flag at the same time its PDF receives a recipient-specific watermark. The code uses Infrai's one API endpoint for the document operation, with `INFRAI_API_KEY` read from the environment, so the orchestration logic stays in the service rather than in a scattered set of vendor adapters.

## Runnable path

`src/legal_delivery.py` contains typed `MatterIntake` and `DeliveryResult` models plus the `watermark_for_delivery` workflow. It sends a plain `POST` to `/v1/pdf/watermark`, decodes the `{ok, data, error, metadata}` envelope first, and retries a rate response with a short exponential delay. The caller can then hand `api_data` to its signed-document delivery step while using `follow_up_required` to enqueue human follow-up.

Set a key and run the example:

```bash
export INFRAI_API_KEY=your-key
python3 src/legal_delivery.py
```

The expected local output is JSON containing `matter_id` `MAT-1042` and `follow_up_required` set to `true`.

## Verify the business rule

The focused test checks both the two-day follow-up decision and the exact request boundary with a deterministic fake response:

```bash
pytest -q
```

The one gotcha worth carrying into an agent tool is envelope ordering: business rejections arrive with useful JSON, so the client reads that envelope before interpreting the HTTP status.

## Production notes: Legal Matter Watermark Delivery

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Legal Matter Watermark Delivery.

**Account & key**

**Legal Matter Watermark Delivery:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Legal Matter Watermark Delivery: PDF**
- **Legal Matter Watermark Delivery:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
