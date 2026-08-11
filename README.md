# Gmail Bulk Draft Builder

A local-only Python/Flask web app that uses the official Gmail API to create **unsent drafts in bulk** in one authorized Gmail account.

> This app creates Gmail drafts. It does not send the messages.

---

# 1. How the app works

This build supports **two usage modes** without changing the code.

### Mode A — Run directly on your iPhone with iSH

If Python, Flask, and the application are running inside iSH on the same iPhone you are using to open the browser:

```text
iPhone
 ├── Python app
 ├── Web UI       127.0.0.1:<auto port>
 └── OAuth        127.0.0.1:<auto port>
```

There is **no Termius forwarding**.

When the program asks:

```text
Web UI port [auto]:
OAuth callback port [auto]:
```

simply press **Enter twice**.

The app automatically finds two free localhost ports.

It will then print something like:

```text
Web UI:          http://127.0.0.1:49152
OAuth callback:  http://127.0.0.1:49153/oauth2callback

If this app is running directly on your iPhone/iSH:
  Open: http://127.0.0.1:49152
  No Termius port forwarding is required.
```

Open the Web UI address in Safari/your browser on the same iPhone.

The Google authorization redirect will also return directly to the iSH application's localhost callback.

### Mode B — Run on your VPS through Termius

If Python is running on your VPS, you can enter fixed ports:

```text
Web UI port [auto]: 8080
OAuth callback port [auto]: 8765
```

Then forward both ports through Termius:

```text
Local 8080 -> VPS 127.0.0.1:8080
Local 8765 -> VPS 127.0.0.1:8765
```

Then open:

```text
http://127.0.0.1:8080
```

on your iPhone.

### Important clarification about "localhost"

`127.0.0.1` always means **the device where the application is running**.

Therefore:

- App running in iSH on iPhone → `127.0.0.1` is your iPhone.
- App running on VPS → `127.0.0.1` is the VPS.

When using the VPS, Termius forwarding makes the VPS's loopback service accessible as a local port on your iPhone.



The app uses two localhost ports on the VPS:

```text
127.0.0.1:<WEB_UI_PORT>       Web interface
127.0.0.1:<OAUTH_PORT>        Google OAuth callback
```

When you start it with:

```bash
python3 app.py
```

the program asks you which ports to use.

Example:

```text
Web UI port [8080]: 8080
OAuth callback port [8765]: 8765
```

You can change these every time you start the program.

Both ports are bound to `127.0.0.1`, so they are not directly exposed to the internet.

---

# 2. Requirements

You need:

- A Linux VPS
- Python 3.10.7 or newer
- A Google account with Gmail
- A Google Cloud project
- Gmail API enabled
- A Google OAuth 2.0 Desktop application credential
- Termius (or another SSH client that supports local port forwarding)

Google's current Gmail Python quickstart lists Python 3.10.7+ and a Google Cloud project as prerequisites.  
Official guide:

https://developers.google.com/workspace/gmail/api/quickstart/python

---

# 3. Download/extract the application

Upload the ZIP to your VPS and extract it.

For example:

```bash
mkdir -p ~/gmail-bulk-draft-builder
cd ~/gmail-bulk-draft-builder
unzip gmail_bulk_draft_builder.zip
cd gmail_bulk_draft_app
```

Your directory should look approximately like:

```text
gmail_bulk_draft_app/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── templates/
    └── index.html
```

---

# 4. Create the Python virtual environment

Inside the application directory:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

---

# 5. Create the Google Cloud project

Open Google Cloud Console:

https://console.cloud.google.com/

## Step 5.1 — Create a project

1. Sign in with the Google account you want to use.
2. Open the project selector.
3. Click **New Project**.
4. Give it a name, for example:

```text
Gmail Bulk Draft Builder
```

5. Create the project.
6. Make sure the new project is selected.

---

# 6. Enable the Gmail API

Open:

https://console.cloud.google.com/apis/library/gmail.googleapis.com

Make sure your new project is selected.

Then:

1. Click **Enable**.
2. Wait for the API to become enabled.

Google's official Gmail quickstart also requires enabling the Gmail API before making API requests.

---

# 7. Configure Google Auth Platform / OAuth consent

Open:

https://console.cloud.google.com/auth/branding

If Google asks you to configure Google Auth Platform:

1. Click **Get Started**.
2. Enter an app name.

Example:

```text
Gmail Bulk Draft Builder
```

3. Select your support email.
4. Continue through the configuration.
5. Add your contact information.
6. Finish the configuration.

## Audience

For a personal Gmail account, Google may require an **External** audience.

If the account is part of a Google Workspace organization and your administrator allows it, **Internal** may be available.

For an External app used only by yourself, you can keep the app restricted to your own test user when Google presents the testing-user option.

---

# 8. Create the OAuth credential

Open:

https://console.cloud.google.com/auth/clients

Then:

1. Click **Create Client**.
2. For application type, choose:

```text
Desktop app
```

3. Give it a name, for example:

```text
Gmail Bulk Draft Builder VPS
```

4. Click **Create**.
5. Download the JSON credential.

Google's current documentation specifically instructs Python Gmail API applications using this flow to create an OAuth client with application type **Desktop app** and save the downloaded JSON as `credentials.json`.

---

# 9. Put credentials.json on the VPS

Rename the downloaded file to:

```text
credentials.json
```

Place it beside `app.py`:

```text
gmail_bulk_draft_app/
├── app.py
├── credentials.json
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

IMPORTANT:

Do not upload `credentials.json` to GitHub or another public location.

The `.gitignore` supplied with this application already ignores:

```text
credentials.json
token.json
```

---

# 10. Start the application

Activate the virtual environment if it is not already active:

```bash
cd ~/gmail-bulk-draft-builder/gmail_bulk_draft_app
source .venv/bin/activate
```

Start:

```bash
python3 app.py
```

You will be asked:

```text
================================================
 Gmail Bulk Draft Builder - Port Configuration
================================================
The app uses two local ports:
  1. Web UI port
  2. Google OAuth callback port

Web UI port [8080]:
OAuth callback port [8765]:
```

Press Enter to use the defaults.

Or enter your own ports:

```text
Web UI port [8080]: 9090
OAuth callback port [8765]: 9091
```

The two ports must be different.

The program will then show:

```text
Web UI:          http://127.0.0.1:9090
OAuth callback:  http://127.0.0.1:9091/oauth2callback

Forward these two remote ports in Termius:
  local 9090  -> remote 127.0.0.1:9090
  local 9091  -> remote 127.0.0.1:9091

After forwarding, open:
http://127.0.0.1:9090
```

---

# 11. Configure Termius port forwarding

The important concept is:

```text
Your iPhone
     │
     │ localhost:9090
     ▼
Termius SSH tunnel
     │
     │ VPS 127.0.0.1:9090
     ▼
Flask Web UI
```

And separately:

```text
Your iPhone
     │
     │ localhost:9091
     ▼
Termius SSH tunnel
     │
     │ VPS 127.0.0.1:9091
     ▼
OAuth callback
```

## Termius setup

The exact labels can vary slightly between Termius versions.

Open your VPS host in Termius.

Look for the host's:

**Port Forwarding / Tunnels**

section.

Create a **Local** port forwarding rule.

### Rule 1 — Web UI

Set approximately:

```text
Type: Local
Local port: 9090
Remote host: 127.0.0.1
Remote port: 9090
```

Save it.

### Rule 2 — OAuth

Create another Local forwarding rule:

```text
Type: Local
Local port: 9091
Remote host: 127.0.0.1
Remote port: 9091
```

Save it.

The important thing is that the local and remote ports match the numbers you entered when `python3 app.py` started.

For example, if you selected:

```text
Web UI: 8088
OAuth: 9000
```

then forward:

```text
Local 8088 -> 127.0.0.1:8088
Local 9000 -> 127.0.0.1:9000
```

You do **not** need to open these ports in your Oracle Cloud firewall/security list because the application is listening only on `127.0.0.1`.

---

# 12. Open the web application

After the Termius tunnel is active, open Safari/Chrome on your iPhone:

```text
http://127.0.0.1:9090
```

Replace `9090` with whatever Web UI port you selected.

You should see:

```text
Gmail Bulk Draft Builder
```

---

# 13. Authorize Gmail

The web UI will show an authorization button/link.

Tap:

```text
Open Google authorization
```

Google will ask you to select your account and authorize the application.

Approve the requested Gmail permission.

The app uses:

```text
https://www.googleapis.com/auth/gmail.compose
```

This is used because the application needs permission to create Gmail drafts.

After Google finishes authentication, it redirects to:

```text
http://127.0.0.1:<OAUTH_PORT>/oauth2callback
```

Because you forwarded that port through Termius, the callback reaches the VPS.

You should see:

```text
Gmail authorization successful.
```

You can close that browser tab.

Return to the web UI.

The authorized Gmail address should now appear.

---

# 14. Configure a draft batch

Example:

### Recipient

```text
example@gmail.com
```

### First number

```text
1000
```

### Last number

```text
2000
```

### Number of drafts

```text
50
```

### Delay

```text
0.25
```

The app might create subjects such as:

```text
1747
1111
1999
1264
1832
1450
...
```

The numbers are selected randomly from the inclusive range.

They are NOT generated sequentially.

---

# 15. Create the drafts

Click:

```text
Create drafts
```

The application will call Gmail's Drafts API repeatedly.

The UI shows:

```text
Requested    50
Created      37
Failed       0
```

and a progress bar.

The drafts remain unsent in Gmail.

---

# 16. Stop a running batch

If you need to stop the current batch:

```text
Stop
```

The application uses a cooperative stop, meaning it stops between draft creation operations rather than terminating the Python process.

---

# 17. Running the application again

After the first successful authorization, the application creates:

```text
token.json
```

This stores the OAuth authorization information locally.

On later runs:

```bash
python3 app.py
```

the application will try to reuse the saved authorization.

You normally do not need to authorize again.

Google's Python Gmail quickstart similarly stores authorization information locally so subsequent runs can reuse it.

---

# 18. Authorize a different Gmail account

Stop the application:

```text
Ctrl+C
```

Delete the saved authorization:

```bash
rm token.json
```

Start again:

```bash
python3 app.py
```

Then authorize the other Gmail account.

---

# 19. Change the ports

You do not need to edit Python code.

Simply run:

```bash
python3 app.py
```

and enter different values:

```text
Web UI port [8080]: 7000
OAuth callback port [8765]: 7001
```

Then forward:

```text
Local 7000 -> VPS 127.0.0.1:7000
Local 7001 -> VPS 127.0.0.1:7001
```

and open:

```text
http://127.0.0.1:7000
```

---

# 20. Finding a free port

If you get an error such as:

```text
Address already in use
```

choose another port.

You can check a port with:

```bash
sudo ss -ltnp | grep ':8080'
```

For example:

```bash
sudo ss -ltnp | grep ':8080'
```

If nothing is returned, that port is probably available.

---

# 21. Security

Keep these files private:

```text
credentials.json
token.json
```

Do not put them into:

- GitHub
- public web directories
- Discord
- screenshots
- public paste sites

The application itself binds to:

```text
127.0.0.1
```

rather than:

```text
0.0.0.0
```

so the web UI is intended to be accessed through your SSH/Termius tunnel.

---

# 22. Stopping the application

In the VPS terminal:

```text
Ctrl+C
```

The application stops.

Your Gmail drafts are not deleted. They remain in Gmail.

---

# 23. Complete quick-start checklist

After Google Cloud setup is finished:

```bash
cd ~/gmail-bulk-draft-builder/gmail_bulk_draft_app

source .venv/bin/activate

python3 app.py
```

Choose ports:

```text
Web UI port [8080]: 8080
OAuth callback port [8765]: 8765
```

In Termius:

```text
Local 8080 -> VPS 127.0.0.1:8080
Local 8765 -> VPS 127.0.0.1:8765
```

Open on your iPhone:

```text
http://127.0.0.1:8080
```

Authorize Gmail.

Enter:

```text
Recipient
First number
Last number
Draft count
Delay
```

Click:

```text
Create drafts
```

Done.

---



## iSH-specific note

If you run the application directly inside iSH, **do not create any Termius tunnel**.

Use:

```bash
python3 app.py
```

Press Enter for:

```text
Web UI port [auto]:
OAuth callback port [auto]:
```

Then open the printed Web UI URL, for example:

```text
http://127.0.0.1:49152
```

The OAuth callback port is handled by the same iSH process, so Google can return to it directly.

If Safari cannot reach the displayed localhost URL, first verify that the Python process is still running and that iSH is listening on the printed port. Do not replace `127.0.0.1` with the VPS IP address.

---


# 23. Important: OAuth "(invalid_grant) Missing code verifier" error

If Google authorization succeeds but the callback page says:

```text
Authorization failed.

(invalid_grant) Missing code verifier.
```

this was an OAuth implementation issue in an earlier build.

Google's installed-app OAuth flow uses PKCE. The authorization request has a `code_verifier`, and the same verifier must be supplied when the authorization code is exchanged for tokens. `google-auth-oauthlib` stores that verifier on the `Flow` object and uses it during `fetch_token()`. citeturn0search0turn0search2

The fixed build keeps the **same Flow object** from:

```text
Generate authorization URL
        ↓
Google login
        ↓
127.0.0.1 OAuth callback
        ↓
fetch_token()
```

So you do not need to change anything in Google Cloud.

### What to do

Stop the previous version:

```text
Ctrl+C
```

Replace your old `app.py` with the one from this build.

Then start again:

```bash
source .venv/bin/activate
python3 app.py
```

If the previous authorization attempt failed, you can optionally remove:

```bash
rm -f token.json
```

Then generate a **new** authorization link from the web UI.

Do not reuse an old Google authorization tab/link from a previous run. A PKCE authorization request is tied to the flow that generated it.

---

# 23. Important: OAuth "insecure_transport" error

If Google authorization succeeds but the final page says:

```text
Authorization failed.

(insecure_transport) OAuth 2 MUST utilize https.
```

**Do not change your Termius forwarding to HTTPS.**

This happens because OAuthLib normally rejects an HTTP OAuth callback, even when the callback is a local loopback address such as:

```text
http://127.0.0.1:8765/oauth2callback
```

Google's Desktop-app OAuth flow supports the loopback redirect mechanism on `localhost` / `127.0.0.1`, and localhost redirect URIs are exempt from the normal HTTPS redirect-URI requirement. citeturn0search9turn0search2

The updated `app.py` already contains:

```python
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
```

You **do not need to manually add this setting**.

It is appropriate here because:

- the Google OAuth client is a **Desktop app**;
- the callback server binds only to `127.0.0.1`;
- the VPS does not expose the callback port publicly;
- Termius carries the local loopback port through your SSH tunnel.

OAuthLib documents this variable as a way to permit HTTP for local testing and warns against using it for public/production OAuth endpoints. citeturn0search1

## What you need to do

Stop the old application:

```text
Ctrl+C
```

Replace your old `app.py` with the `app.py` from this updated build.

You can keep:

```text
credentials.json
token.json
```

If `token.json` does not exist because authorization failed, that's completely fine.

Start again:

```bash
source .venv/bin/activate
python3 app.py
```

Choose your ports:

```text
Web UI port [8080]: 8080
OAuth callback port [8765]: 8765
```

In Termius, forward:

```text
Local 8080 -> VPS 127.0.0.1:8080
Local 8765 -> VPS 127.0.0.1:8765
```

Then open:

```text
http://127.0.0.1:8080
```

and run the Google authorization again.

### Do NOT do these things

You do **not** need to:

- create an SSL certificate for `127.0.0.1`;
- expose the OAuth port in Oracle Cloud;
- add the OAuth port to your VCN security rules;
- use `https://127.0.0.1`;
- create an iOS OAuth client;
- create a Web application OAuth client for this flow.

Your Google OAuth client should be:

```text
Application type: Desktop app
```

Google states that the loopback IP redirect flow remains supported for Desktop-app OAuth clients. citeturn0search2

## If you want to restart Google authorization completely

Delete the saved token:

```bash
rm -f token.json
```

Then restart:

```bash
python3 app.py
```

You normally do **not** need to create a new Google Cloud project or OAuth client because of this `insecure_transport` error.

---

# Official Google reference

Google's current Gmail API Python quickstart:

https://developers.google.com/workspace/gmail/api/quickstart/python

The current Google instructions cover enabling Gmail API, configuring Google Auth Platform, creating a Desktop OAuth client, downloading `credentials.json`, installing the Python libraries, and running the OAuth flow.
