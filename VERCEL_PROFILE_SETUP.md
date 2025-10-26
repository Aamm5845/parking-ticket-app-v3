# Setting Up Your Profile on Vercel

Since Vercel is serverless and doesn't persist files, you need to store your profile data as an environment variable.

## Steps:

1. Go to your Vercel dashboard: https://vercel.com/dashboard
2. Select your project: `parking-ticket-app-v3`
3. Go to **Settings** → **Environment Variables**
4. Add a new environment variable:
   - **Name**: `USER_PROFILE_DATA`
   - **Value**: 
   ```json
   {"first_name": "Aaron", "last_name": "Meisner", "license": "m256112128808", "address": "661 Querbes", "city": "Montreal", "province": "Québec", "postal_code": "H2V3W6", "country": "Canada", "email": "AAMM5845@GMAIL.COM"}
   ```
   - **Environment**: Select all (Production, Preview, Development)

5. Click **Save**
6. Redeploy your app (Vercel will automatically trigger a redeploy when you push to Git)

## Alternative: Session-based Storage

The app now also stores your profile in the Flask session after you fill it out once. This means:
- After you set up your profile once, it will persist during your browser session
- If you clear cookies or use a different browser, you'll need to fill it out again

To make it truly persistent across all sessions and browsers, use the environment variable method above.
