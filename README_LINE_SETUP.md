# LINE Webhook Setup Guide

## 1. Update Environment Variables

Edit the `.env` file and replace the test values with your actual LINE credentials:

```bash
# Replace these with your actual LINE credentials
LINE_CHANNEL_SECRET=your_actual_channel_secret_here
LINE_CHANNEL_ACCESS_TOKEN=your_actual_channel_access_token_here
```

## 2. Get Your LINE Credentials

1. Go to [LINE Developers Console](https://developers.line.biz/console/)
2. Select your channel (or create a new one)
3. In the "Basic settings" tab:
   - Find your **Channel secret**
4. In the "Messaging API" tab:
   - Find your **Channel access token** (long-lived)
   - If you don't have one, click "Issue" to generate it

## 3. Configure Webhook URL in LINE Console

1. In the "Messaging API" tab of your LINE channel
2. Under "Webhook settings":
   - Set **Webhook URL** to: `https://your-domain.com/webhook`
   - Enable **Use webhook**
   - Disable **Auto-reply messages** (optional)
   - Disable **Greeting messages** (optional, or customize them)

## 4. Test the Webhook

### Local Testing with ngrok (for development)

1. Install ngrok: `npm install -g ngrok`
2. Start your API server: `pnpm --filter @invoice-ocr/api dev`
3. In another terminal: `ngrok http 3000`
4. Use the ngrok HTTPS URL in LINE Console: `https://xxxxx.ngrok.io/webhook`

### Verify Webhook

1. In LINE Developers Console, click "Verify" next to the webhook URL
2. Add your bot as a friend using the QR code in the console
3. Send a message to your bot
4. Check the server logs to see incoming webhook events

## 5. Production Deployment

For production, you'll need:
- HTTPS endpoint (required by LINE)
- Valid SSL certificate
- Proper domain configuration
- Environment variables set on your hosting platform

## 6. Testing Your Setup

Once configured, you can:
1. Send text messages to your bot
2. Send images for OCR processing
3. Test follow/unfollow events
4. Send stickers and other message types

## 7. Monitor Your Bot

Check the server logs to see:
- Incoming webhook events
- Event processing details
- Any errors or issues

The webhook API is now ready to receive and process LINE events!