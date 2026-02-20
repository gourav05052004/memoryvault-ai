# Switching from Cloudinary to Supabase Storage

## What Changed
Your app now uses **Supabase Storage** instead of Cloudinary for file uploads. This means:
- ✅ PDFs open directly without authentication issues
- ✅ Public file access (no 401 errors)
- ✅ Simpler setup
- ✅ Free tier available

## Setup Steps

### 1. Create Supabase Account & Project
1. Go to https://supabase.com
2. Sign up with your email or GitHub
3. Create a new project
4. Wait for the project to initialize (2-3 minutes)

### 2. Create Storage Bucket
1. In Supabase Dashboard, go to **Storage** (left sidebar)
2. Click **"New Bucket"**
3. Name it: `memoryvault`
4. **IMPORTANT**: Toggle **"Public bucket"** to ON
5. Click **Create bucket**

### 3. Get Your Credentials
1. Go to **Settings** → **API** (left sidebar)
2. Copy these values:
   - `Project URL` (e.g., `https://abc123.supabase.co`)
   - `Anon public` (under `Project API keys`)

### 4. Update .env File
Edit `d:\memoryvault-ai\backend\.env`:

```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-anon-public-key-here"
```

Replace with the values you copied above.

### 5. Verify Supabase SDK is Installed
The Supabase SDK should have been installed automatically. To verify:

```bash
conda run -n mvenv pip list | findstr supabase
```

If not installed, run:
```bash
conda run -n mvenv pip install supabase
```

### 6. Restart Backend
The backend auto-reloads, but to be safe:
```bash
# Stop existing backend processes
taskkill /F /IM uvicorn.exe 2>nul

# Start backend
cd d:\memoryvault-ai\backend
conda run -n mvenv uvicorn app.main:app --reload --port 8001
```

### 7. Test Upload
1. Visit http://localhost:3000/upload
2. Upload a new PDF or image
3. Go to Memories page
4. Click "View Details" on the new file
5. For PDFs: Click "Open PDF in New Tab" - it should open directly!

## Troubleshooting

**Error: "Supabase credentials are not configured"**
- Make sure SUPABASE_URL and SUPABASE_KEY are in .env
- Restart the backend after updating .env

**Error: "Failed to upload file"**
- Check that your bucket is named exactly: `memoryvault`
- Verify the bucket is set to **Public**
- Check SUPABASE_KEY is correct (should start with `eyJ...`)

**PDFs still won't open**
- Make sure the bucket is **Public** (not private)
- Try uploading a new file

## What Happened to Old Files?
Your old Cloudinary files are still in MongoDB but with unsigned URLs. They may not display unless:
- You switch back to Cloudinary, OR
- You re-upload them to Supabase

## Next Steps
Once Supabase is configured and working, you can:
- Continue uploading files (they'll work perfectly!)
- Delete the old Cloudinary files from MongoDB if needed
- Use Supabase's free tier for production (1GB storage)
