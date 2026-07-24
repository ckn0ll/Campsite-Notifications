# Campsite Watch

Watches campgrounds on **ReserveCalifornia** and **Recreation.gov** and pushes
a notification to your phone the moment a site opens up — cancellations
included.

**Recreation.gov** watches run for free on GitHub's servers every 30
minutes, so they work even when your computer is off.

**ReserveCalifornia** watches run locally on your computer instead, on a
schedule via Windows Task Scheduler. This isn't by choice — ReserveCalifornia's
booking platform (run by Tyler Technologies) blocks requests coming from
GitHub's cloud servers with a `403 Forbidden` error, but works fine from an
ordinary home internet connection. Recreation.gov has no such restriction.
So: Recreation.gov → cloud, ReserveCalifornia → your PC, same watchlist file,
same phone notifications either way.

It's built on top of [camply](https://github.com/juftin/camply), an
open-source, actively maintained campsite-finder that already knows how to
talk to both booking systems correctly, plus a small script that lets you
manage multiple parks/date-ranges at once and only notifies you about sites
you haven't already been told about.

## 1. Install the ntfy app (2 minutes)

1. Install **ntfy** on your phone: [iOS](https://apps.apple.com/us/app/ntfy/id1625396347) · [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
2. In the app, tap **+** and subscribe to a topic name only you would guess —
   e.g. `yourname-campsites-38x91`. Anyone who knows the exact topic name can
   read your notifications, so don't use something obvious like `campsites`.
3. That topic name is your `NTFY_TOPIC` — you'll add it as a secret in step 3.

## 2. Create your repo

1. Create a new (public, so Actions minutes are free and unlimited) GitHub
   repository and upload every file from this folder to it, keeping the
   `.github/workflows/watch.yml` path intact.
2. In the repo, go to **Settings → Secrets and variables → Actions → New
   repository secret**. Name it `NTFY_TOPIC`, value = the topic you picked
   above.
3. Go to the **Actions** tab and enable workflows if prompted.

This covers **Recreation.gov watches only** — see step 5 below for
ReserveCalifornia.

## 3. Build your watchlist

Open **campsite-watchlist.html** (double-click it, no install needed) in
your browser. For each park you want to watch, add an entry with:

- A label (anything you'll recognize)
- Provider: ReserveCalifornia or Recreation.gov
- The campground ID(s) or recreation-area ID
- Your date range

Click **Download watchlist.yaml** and replace the `watchlist.yaml` file in
your repo with the downloaded one (commit it).

**Sharing with friends:** you can send them just the `campsite-watchlist.html`
file — it's a single, self-contained page, no install needed on their end.
Each friend builds their own list and downloads their own `watchlist.yaml`.
Since each entry has a unique `name`, you can merge multiple people's files
by copying the `- name: ...` blocks from each into one `watches:` list before
committing it to the repo.

### Finding the ID for a park

`campsite-watchlist.html` has a **"Find your park"** search box at the top —
type a park name, pick ReserveCalifornia or Recreation.gov, hit Search, and
click "Use this" on the right match. It fills in the name and ID for you.
No install required — this is what makes it safe to hand the HTML file to
friends so they can build their own lists without installing anything.

This works because it queries two public, no-key-required government APIs
directly from the browser: California's open-data portal for state parks,
and Recreation.gov's own public facilities API for federal land. Occasionally
one of those may be slow, down, or blocked by the browser (you'll see an
error message in the app if so) — if that happens, fall back to camply on a
computer with Python installed:

```bash
pip install camply

# Search Recreation.gov (national forests, national parks, etc.)
camply recreation-areas --search "Yosemite"
camply campgrounds --rec-area 2991

# Search ReserveCalifornia (state parks/beaches)
camply campgrounds --search "Pfeiffer Big Sur" --provider ReserveCalifornia
```

Each command prints names next to their ID numbers — that's the number to
paste into the app.

## 4. Test it

From the Actions tab, open **Campsite Watch** and click **Run workflow** to
trigger it manually instead of waiting for the next 15-minute tick. Check
the run's logs to confirm it found your watchlist entries and queried them
without errors. If your dates are currently available, you should get a
push notification within a minute or two.

You can also test notifications alone, from your own computer:

```bash
NTFY_TOPIC=your-topic-name camply test-notifications --notifications ntfy
```

## 5. Set up ReserveCalifornia locally (Windows Task Scheduler)

This runs the ReserveCalifornia watches on your own PC, on a repeating
schedule, so it keeps working even without you opening anything — as long
as your computer is on.

**One-time setup:**

1. **Clone your repo locally** (this is different from the browser app —
   you need an actual copy of the repo on disk so Task Scheduler has
   something to run). Open Command Prompt:
   ```
   cd %USERPROFILE%\Documents
   git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
   cd YOUR-REPO-NAME
   ```
   (If `git` isn't recognized, install it from [git-scm.com](https://git-scm.com/download/win) first — accept the defaults during install.)

2. **Set your ntfy topic as a permanent environment variable** (one time
   only — replace with your actual topic):
   ```
   setx NTFY_TOPIC "your-topic-name"
   ```
   Close and reopen Command Prompt after this for it to take effect.

3. **Test it manually first:**
   ```
   run_local_windows.bat
   ```
   You should see it pull the repo, then run through your ReserveCalifornia
   watches. Fix any errors here before moving on to scheduling.

**Schedule it with Task Scheduler:**

1. Press the Windows key, type **"Task Scheduler"**, open it.
2. Click **Create Task...** (not "Create Basic Task" — the full dialog
   gives you repeating intervals, which the basic wizard doesn't).
3. **General tab:** Name it `Campsite Watch - ReserveCalifornia`. Under
   **Security options**, select **"Run whether user is logged on or not"**
   if you want it to run even when locked, and check **"Run with highest
   privileges"** isn't necessary — leave that unchecked.
4. **Triggers tab → New:** Begin the task **"On a schedule"** → **Daily**,
   recurring every 1 day, start time = **7:30:00 AM**. Then check
   **"Repeat task every"** → **30 minutes**, for a duration of
   **15 hours** (7:30 AM + 15 hours = 10:30 PM). This way Task Scheduler
   itself only ever tries to fire — and only ever needs to wake the PC —
   between 7:30 AM and 10:30 PM. It'll go quiet on its own overnight.
5. **Conditions tab → Power:** check **"Wake the computer to run this
   task."** This only wakes it during the 7:30 AM–10:30 PM window from
   step 4, since that's the only time triggers exist — it won't wake the
   PC overnight. Also uncheck **"Start the task only if the computer is on
   AC power"** unless you specifically want it to skip runs while
   unplugged.
6. **Actions tab → New:** Action = **"Start a program"**.
   - Program/script: the full path to `run_local_windows.bat`, e.g.
     `C:\Users\YourName\Documents\YOUR-REPO-NAME\run_local_windows.bat`
   - Start in (optional): the same folder path, without the filename, e.g.
     `C:\Users\YourName\Documents\YOUR-REPO-NAME`
7. Click **OK**, enter your Windows password if prompted.

**Belt and suspenders:** even with the trigger window above, Task Scheduler
can occasionally fire a "make-up" run right after the PC wakes from an
extended sleep, slightly outside your intended hours. `run_local_windows.bat`
double-checks the actual time before doing anything — if it's before 7:30 AM
or after 10:30 PM Pacific, it exits immediately without running camply or
touching the network. Edit `WINDOW_START` / `WINDOW_END` at the top of
`check_time_window.py` if you want different hours.

To confirm it's working: right-click the task in Task Scheduler and choose
**Run**. Check the **History** tab (you may need to enable "All Tasks
History" from the Actions pane first) to see it fire, or just watch for a
`campsite-watch` folder... actually simplest — watch your phone for a
notification, or open a fresh Command Prompt and check
`.camply-state\` inside your repo folder for recently-modified files.


## How it avoids spamming you

`run_watchlist.py` runs camply with `--search-once --offline-search`. The
`--search-once` flag is important: it makes camply run one pass and exit,
rather than looping and sleeping internally forever (that's what
`--continuous` does, and it's the wrong flag for a scheduled job — it never
lets the job finish). `--offline-search` makes camply save what it saw on
the last run and only notify about sites that are newly available. That
state is cached between GitHub Actions runs via `actions/cache`, so a site
that's been open for three days won't ping you again — only the moment it
flips from unavailable to available.

## Why ReserveCalifornia and Recreation.gov run in different places

The first couple of runs surfaced this the hard way: every ReserveCalifornia
watch failed with `403 Forbidden` from
`california-rdr.prod.cali.rd12.recreation-management.tylerapp.com`, while
every Recreation.gov watch succeeded, consistently, run after run. That
pattern — one provider always blocked, the other always fine, from the same
job — points to ReserveCalifornia's platform blocking GitHub's cloud IP
ranges specifically, not a bug in the search itself.

The `--provider` flag on `run_watchlist.py` splits the watchlist so:
- GitHub Actions (`watch.yml`) only ever requests `--provider RecreationDotGov`
- Your PC (`run_local_windows.bat`) only ever requests `--provider ReserveCalifornia`

Both read the same `watchlist.yaml`, so you only maintain one list — the
`provider` field on each entry determines which machine actually checks it.

## How the checks run

Each Recreation.gov entry in your watchlist runs as its **own parallel
GitHub Actions job**, not one after another in a single script. This
matters because a `rec_area_ids` watch (an entire park) expands to every
campground inside that recreation area and checks each one, month by
month — for a park the size of Yosemite that can be 40+ requests for a
single watchlist entry. Run ten entries like that back-to-back in one job
and the whole thing can take hours.

Running entries in parallel means the whole watchlist finishes in roughly
"however long the slowest single entry takes," not the sum of all of them.
(ReserveCalifornia watches, running locally, still go one after another in
`run_local_windows.bat` — there's no parallel matrix there since it's just
your one PC, but ReserveCalifornia watchlists tend to be smaller and
faster per-campground than the big national-park rec areas.)

**A few implications:**
- **Give each watch a unique name.** The matrix uses the `name` field to
  pick out which entry to run, so two watches with identical names will
  collide.
- **Prefer specific `campground_ids` over `rec_area_ids` when you know
  them.** Watching "Upper Pines + Lower Pines" is a couple of requests;
  watching all of "Yosemite" is dozens. Use `rec_area_ids` when you
  genuinely want anywhere in a park; use `campground_ids` when you have
  favorites.
- **Each entry has a 25-minute cap** (`timeout-minutes` in the workflow).
  A watch that's still running when this hits gets cancelled rather than
  blocking everything scheduled after it. If a specific entry regularly
  times out, it's a sign to narrow it to fewer campgrounds or a shorter
  date range.
- **New runs cancel stale ones** (`concurrency: cancel-in-progress: true`),
  so if a run is still going when the next scheduled tick fires, it gets
  stopped instead of piling up in a queue.

## Adjusting the check frequency

Edit the cron schedule in `.github/workflows/watch.yml`
(`*/30 * * * *` = every 30 minutes). GitHub's minimum is every 5 minutes,
but with rec-area watches in the mix, 30 minutes leaves more headroom than
15 does. Popular parks that release new dates at a specific moment (e.g.
ReserveCalifornia opens new dates at 8:00 AM Pacific, 6 months out) are
worth watching more frequently right around that time — you could add a
second, tighter-interval workflow just for those entries if needed.

## Files

| File | Purpose |
|---|---|
| `campsite-watchlist.html` | Browser app for building your watchlist |
| `watchlist.yaml` | Your list of parks + date ranges (edit via the app) |
| `run_watchlist.py` | Runs camply searches, filterable by `--provider` or `--entry` |
| `.github/workflows/watch.yml` | Schedules Recreation.gov checks on GitHub's servers |
| `run_local_windows.bat` | Run this via Task Scheduler for ReserveCalifornia checks |
| `check_time_window.py` | Skips the run outside 7:30 AM–10:30 PM Pacific |
| `requirements.txt` | Python dependencies (camply, pyyaml) |
