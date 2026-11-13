# 🚀 Netlify Deployment Guide

This project is fully configured to deploy on **Netlify** using **Netlify Serverless Python Functions**.

---

## 📁 Pre-configured Deployment Files

The following configuration files are already set up in the project:
1. `netlify.toml`: Directs Netlify on build commands, static files, and routes all web traffic (`/*`) to the Python serverless function.
2. `netlify/functions/api.py`: The AWS Lambda/Netlify WSGI bridge that boots the Flask app, connects the SQLite database, and handles web requests, logins, PDF exports, and edits.
3. `requirements.txt`: Lists dependencies (`Flask`, `Flask-SQLAlchemy`, `reportlab`, `gunicorn`, etc.).

---

## 🌟 Method 1: Deploy via GitHub (Recommended - 2 Minutes)

This is the easiest and most reliable method to get a permanent live URL.

### Step 1: Initialize Git and Commit
In your VS Code terminal (or PowerShell), run:
```powershell
git init
git add .
git commit -m "Deploy Smart Timetable Generator to Netlify"
```

### Step 2: Push to Your GitHub Account
1. Go to [GitHub.com](https://github.com) and create a **New Repository** (e.g. `smart-timetable-generator`).
2. Run the commands shown by GitHub, for example:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/smart-timetable-generator.git
git branch -M main
git push -u origin main
```

### Step 3: Connect to Netlify
1. Go to [Netlify.com](https://www.netlify.com) and log in (or sign up with GitHub).
2. Click **"Add new site"** > **"Import an existing project"**.
3. Select **GitHub** and choose your `smart-timetable-generator` repository.
4. Netlify will automatically detect settings from `netlify.toml`:
   - **Build command:** `pip install -r requirements.txt`
   - **Publish directory:** `static`
   - **Functions directory:** `netlify/functions`
5. Click **"Deploy site"**.
6. In ~1–2 minutes, Netlify will build your site and give you a live HTTPS link (e.g., `https://smart-timetable-generator.netlify.app`)!

---

## 💻 Method 2: Deploy using Netlify CLI

If you have Node.js / npm installed:

1. Install the Netlify CLI globally:
```powershell
npm install -g netlify-cli
```

2. Log in to your Netlify account:
```powershell
netlify login
```

3. Deploy from the project root:
```powershell
netlify deploy --prod
```
- Select **"Create & configure a new site"**.
- Confirm publish directory as `static`.
- Netlify will upload the project and output your live production URL!

---

## 💡 Important Note on SQLite in Serverless Environments

- Netlify functions run in **ephemeral AWS Lambda containers**, where the root directory is read-only.
- Our code automatically directs SQLite to the writable `/tmp` partition and pre-seeds it on container boot with **100% of the authentic MGM COE timetable data from the PDF**.
- Any edits made in a serverless instance will work during that session, but because serverless containers periodically restart, changes are temporary.
- **If you need permanent database persistence on the cloud for your project:**
  - You can also deploy in 1 click to [Render.com](https://render.com) or [Railway.app](https://railway.app) using the included `Procfile` (`web: gunicorn app:app`). Render provides persistent background server hosting for Python Flask apps completely free!

---

## 🔑 Default Login on Deployed Site

- **URL:** `https://your-site-name.netlify.app/login`
- **Username:** `admin`
- **Password:** `admin123`
