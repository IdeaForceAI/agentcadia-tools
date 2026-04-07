# OpenClaw Runtime Integration

Read this file only when the host runtime can proactively send a follow-up message after a successful upload.

## Preferred delivery order

Owner delivery must happen in three separate text messages:

1. send the upload-complete notice first
2. send the share-image prompt second, including the `shareImageUrl` as text when available
3. send the share-copy prompt third, including the final share text

Preferred resolution order:

1. If `runtimeActions` contains compatible `send_text` items, send them in order.
2. Otherwise, use `ownerMessage.uploadNotice`, `ownerMessage.imagePrompt`, and `ownerMessage.shareCopyPrompt` when present.
3. Otherwise, fall back to `notification.text`, `notification.shareImagePrompt`, and `notification.shareCopyPrompt`.
4. Otherwise, send the best available plain-text fallback.

Do not require a real image attachment for the share-image step. The intended behavior is to send the public share image URL as text with a short owner-facing prompt.

## Expected fields from the uploader

A successful run may return these public-facing fields:

- `messageText`
- `messageCaption`
- `shareImageUrl`
- `agentUrl`
- `notification`
- `hostReply`
- `preferredOwnerDelivery`
- `runtimeActions`
- `metadataWritebackAttempted`
- `metadataWritebackSucceeded`
- `metadataPreview`
- `incompleteReason`

If the uploader returns `success: false` together with `incompleteReason: METADATA_WRITEBACK_REQUIRED`, do not describe the overall task as completed.

## Metadata preview requirement

The upload-complete notice must still include the final written metadata preview in text form: title, category, tags, summary, and detailDescription.
The later share-image prompt and share-copy prompt are additional follow-ups, not replacements for the metadata preview.

## Safety

- Never expose upload tokens
- Never expose internal upload URLs
- Only send public detail links and public share image URLs
- If upload succeeded but share generation failed, report success without inventing share media
