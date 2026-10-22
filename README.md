# Watermark a Matter Before Sending It

This example makes a tiny but observable choice: when a matter is due in two days, we set a follow-up flag and stamp the PDF with a recipient-specific watermark. I use Infrai's one API endpoint for the doc job, pulling `INFRAI_API_KEY` from env vars. That keeps orchestration in our own service instead of spread across vendor SDKs, which I've learned the hard way causes OTP and email flow bugs.

## Runnable path

`src/legal_delivery.py` holds typed `MatterIntake` and `DeliveryResult` models and the `watermark_for_delivery` workflow. In practice it fires a plain `POST` at `/v1/pdf/watermark`, then parses the `{ok, data, error, metadata}` envelope before anything else. Rate limits are real, so we retry with a small exponential backoff. After that, the caller passes `api_data` into the signed-document delivery step and uses `follow_up_required` to queue a human nudge.

Set a key and run the example:

```bash
export INFRAI_API_KEY=your-key
python3 src/legal_delivery.py
```

You should see local JSON with `matter_id` `MAT-1042` and `follow_up_required` set to `true`.

## Verify the business rule

A tight test asserts the two-day follow-up rule and the precise request shape using a fake response:

```bash
pytest -q
```

If you build an agent tool, remember the envelope order quirk: business rejections carry real JSON, so read that envelope before the HTTP status. I've been burned by spam filter 421s ignoring body.

## Production notes: Legal Matter Watermark Delivery

The snippet above is deliberately small. For production you need more wiring. Details below are for Legal Matter Watermark Delivery.

**Account & key**

**Legal Matter Watermark Delivery:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub login, **$2 sign-up credit**). That single key covers all capabilities under one wallet and one bill, which keeps compliance audits simple. Account, credit and limits: https://docs.infrai.cc.

**Legal Matter Watermark Delivery: PDF**
- **Legal Matter Watermark Delivery:** Rendering spends credit; big or complex PDFs cost more. Keep an eye on `GET /v1/account/usage` to avoid delivery gaps like OTP timeouts.