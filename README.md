# 📊 Salesight — Sales Analytics Platform

A complete, production-ready **sales analytics web application**: a pandas ETL
pipeline loads retail sales data into MySQL, and an interactive Streamlit app
with a marketing landing page, email/password auth, and two analysis modes:

- **Demo dataset** — the pre-loaded MySQL sales data (4,000 rows), filterable
- **Your own CSV** — upload, strict schema validation, in-memory analysis

**Architecture:**

```
CSV Dataset → Python ETL (Pandas) → MySQL Database → Streamlit Dashboard → Cloud Deployment
                                    ↘
                          Landing Page → Login/Signup → CSV Upload (validated, in-memory analysis)
```

**User flow:**

```
Landing Page ──→ [Try Demo Dataset] ──→ MySQL demo dashboard (no login needed)
      └────→ [Get Started] ──→ Signup/Login ──→ Upload CSV ──> Validate ──> Analyze (in-memory)
```

Built as a portfolio project — clean, modular code that a 3rd-year CSE student
can read, run and extend.

---

## ✨ Features

- **End-to-end ETL pipeline** — extract CSV, clean/validate/deduplicate,
  compute revenue (`total = quantity × price`), enrich with product categories,
  load into MySQL (idempotent, re-runnable, `--truncate` for full refresh)
- **Landing page** — modern SaaS-style hero with "Try Demo Dataset" and
  "Get Started" calls to action
- **Email + password auth** — signup (name, email, password) with bcrypt-hashed passwords stored
  in a MySQL `users` table; duplicate-email and format validation; guest mode
  bypasses auth entirely
- **CSV upload with schema validation** — files must match
  `date, product, quantity, price` exactly; missing/extra columns, invalid
  dates, non-numeric or negative values are rejected with specific error
  messages; clean files flow through the same ETL transform and are analyzed
  **in memory only** (never written to the shared database)
- **Interactive dashboard** — five KPI cards (Revenue, Orders, Products, Avg
  Order Value, Units Sold), revenue-by-product bar chart, category donut,
  daily revenue trend, **month-vs-month revenue comparison**, top-sellers
  table, filterable data table with CSV download — identical components in
  demo and uploaded modes
- **Filters** — date range, multi-select categories, multi-select products —
  on the **demo dashboard via parameterized SQL** (never string interpolation)
  and on the **uploaded dashboard via in-memory pandas masks** — both with a
  one-click Reset; results are cached per filter combination for instant
  re-application
- **Robust states** — loading spinners, friendly connection errors with
  step-by-step fix instructions, empty-data handling
- **Tested** — pytest suite: ETL logic, SQL correctness (against SQLite),
  connection error handling, auth and an end-to-end pipeline run
- **CI/CD** — GitHub Actions runs tests + a dashboard boot smoke test and
  builds the Docker image on every push
- **Deployment-ready** — Dockerfile + docker-compose (MySQL + ETL + app),
  cloud deployment guide below

## 🧰 Technologies

| Layer | Tools |
|---|---|
| Data processing | Python 3.10+, pandas |
| Database | MySQL 8.0, SQLAlchemy, PyMySQL |
| Dashboard | Streamlit, Plotly |
| Auth | bcrypt (password hashing), Streamlit session state |
| Config | python-dotenv (environment variables) |
| Testing | pytest |
| Ops | Docker, Docker Compose, GitHub Actions |

## 📂 Project Structure

```
Sales-data-pipeline/
├── app.py                     # Page router: landing → auth → upload → dashboard
├── auth.py                    # Signup/login, bcrypt hashing, users table
├── upload_validation.py       # Strict CSV schema + value validation
├── views/
│   ├── landing.py             # Marketing landing page
│   ├── auth_view.py           # Login / signup / guest UI
│   ├── upload_view.py         # CSV upload screen + template download
│   ├── dashboard.py           # Demo (MySQL) + uploaded (in-memory) dashboards
│   └── charts.py              # Shared chart builders
├── etl/
│   ├── etl_main.py            # ETL pipeline: extract → transform → load
│   └── product_catalog.py     # product → category mapping (single source of truth)
├── database/
│   └── connection.py          # SQLAlchemy engine + friendly error handling
├── queries/
│   └── sales_queries.py       # parameterized SQL for every dashboard element
├── utils/
│   ├── config.py              # env loading + MySQL URI builder
│   └── format.py              # money/number formatting helpers
├── sql/
│   └── schema.sql             # documented MySQL schema (optional manual init)
├── tests/                     # pytest suite (ETL, queries, connection, e2e)
├── data/
│   └── input.csv              # sales dataset (4,000 rows)
├── powerBI/                   # original Power BI dashboard + theme + screenshots
├── .streamlit/config.toml     # Streamlit theme
├── .env.example               # template for database credentials
├── docker-compose.yml         # MySQL + ETL + dashboard, one command
├── Dockerfile                 # app image (Streamlit by default)
├── generate_data.py           # regenerates the synthetic dataset
└── .github/workflows/ci.yml   # CI: tests + smoke test + image build
```

## 🚀 Local Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/nakulsharma97/Sales-data-pipeline.git
cd Sales-data-pipeline

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure MySQL credentials

```bash
cp .env.example .env      # Windows CMD: copy .env.example .env
```

Edit `.env` with your real MySQL credentials:

```env
MYSQL_USER=retail_user
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=retail_demo
```

### 3. Create the database and user

Using MySQL root:

```sql
CREATE DATABASE IF NOT EXISTS retail_demo;
CREATE USER IF NOT EXISTS 'retail_user'@'%' IDENTIFIED BY 'your_password';
GRANT SELECT, INSERT, CREATE, INDEX ON retail_demo.* TO 'retail_user'@'%';
FLUSH PRIVILEGES;
```

Or run the provided script: `mysql -u root -p < sql/schema.sql`

> The ETL also creates the table automatically on first run.

### 4. Run the ETL pipeline

```bash
python etl/etl_main.py                # load data/input.csv (append)
python etl/etl_main.py --truncate    # full refresh: empty table first
python etl/etl_main.py --csv path/to/other.csv   # custom input file
```

Expected output:

```
[1/3] Extract: reading data/input.csv
      4000 raw rows
[2/3] Transform: cleaning and enriching
      4000 clean rows
[3/3] Load: writing to MySQL
      4000 rows loaded into 'sales_staging'
✅ ETL finished successfully
```

### 5. Run the dashboard

```bash
streamlit run app.py
```

Open http://localhost:8501 🎉

### 6. Run the tests

```bash
pytest tests/ -v
```

72 tests: ETL logic, SQL correctness (verified against SQLite), connection
error handling, an end-to-end pipeline run, auth (hashing, validation,
duplicate emails, login flows) and CSV upload validation.

## 👤 Using the App

**Try the demo:** open the app → **Try Demo Dataset** — no account needed.

**Analyze your own sales data:**
1. Click **Get Started** → create an account (name + email + password, min 6 chars)
   — passwords are bcrypt-hashed in the MySQL `users` table.
2. On the upload page, download the **template CSV**, fill it with your data
   (columns: `date, product, quantity, price` — exact match).
3. Upload → the file is validated (missing/extra columns, bad dates,
   non-numeric or negative values are rejected with specific messages).
4. Valid files are cleaned by the same ETL logic and analyzed instantly —
   **in memory only**, nothing is written to the shared database.
5. Download the cleaned CSV anytime from the dashboard.

## 🐳 Run with Docker (one command)

```bash
cp .env.example .env    # edit credentials first
docker compose up --build
```

This starts:
1. **MySQL** (with healthcheck)
2. **ETL** (runs once, loads the CSV, exits)
3. **Streamlit dashboard** at http://localhost:8501

## ☁️ Cloud Deployment (student-friendly)

The simplest low-cost path: **Streamlit Community Cloud (free) + a free MySQL
cloud database**.

### Step 1 — Free MySQL cloud database

Pick one:
- **Aiven** (free MySQL plan) · **Railway** (MySQL plugin) · **PlanetScale** ·
  **AlwaysData** (free tier)

Create the database, note the **host, port, user, password, database name**,
and run the ETL locally against it once to load the data:

```bash
# .env now points at the cloud DB
MYSQL_HOST=your-host.aivencloud.com
MYSQL_PORT=12345
...
python etl/etl_main.py
```

### Step 2 — Deploy the dashboard to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** →
   select your repo, branch `main`, main file `app.py`.
3. Under **Advanced settings → Secrets**, paste (TOML format):

```toml
MYSQL_USER = "retail_user"
MYSQL_PASSWORD = "your_password"
MYSQL_HOST = "your-host.aivencloud.com"
MYSQL_PORT = "12345"
MYSQL_DATABASE = "retail_demo"
```

4. Deploy. Your public URL: `https://your-app.streamlit.app` — share it on
   your resume and GitHub profile.

> Streamlit Community Cloud reads secrets as environment variables, which is
> exactly what `utils/config.py` consumes — no code changes needed.

### Alternative: Docker on a small VM

Any cheap VM (EC2 t3.micro / Oracle Cloud free tier / DigitalOcean droplet):

```bash
git clone https://github.com/nakulsharma97/Sales-data-pipeline.git
cd Sales-data-pipeline
cp .env.example .env && nano .env
docker compose up --build -d
# open http://<vm-public-ip>:8501  (allow port 8501 in the firewall)
```

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MYSQL_USER` | yes* | MySQL username |
| `MYSQL_PASSWORD` | yes* | MySQL password |
| `MYSQL_HOST` | no | default `localhost` |
| `MYSQL_PORT` | no | default `3306` |
| `MYSQL_DATABASE` | yes* | database name |
| `MYSQL_URI` | no | full SQLAlchemy URI, overrides all of the above |

\* Not required when `MYSQL_URI` is set. Never commit `.env` — it's gitignored.

## 🖼 Screenshots

> Dashboard sections: KPI cards · Revenue by Product · Revenue Share by
> Category · Daily Revenue Trend · Top-Selling Products · filterable data
> table with CSV export.

![Dashboard page 1](powerBI/Power_BI_Dashboard_p1.jpg)
![Dashboard page 2](powerBI/Power_BI_Dashboard_p2.jpg)
![Dashboard DAX example](powerBI/Power_BI_DAX.jpg)

*(Screenshots above are from the original Power BI version; replace with
Streamlit captures after your first run.)*

## 🔮 Future Improvements

- Incremental ETL (only load rows newer than the last sync)
- Automated scheduled refresh (GitHub Actions cron → rerun ETL)
- Row-level authentication on the dashboard
- Slowly-changing dimension table for product prices
- JSON/YAML-driven category mapping instead of a Python dict
- Docker image publishing to GitHub Container Registry

---

👨‍💻 **Author**

Nakul Sharma
📧 [nakulsharma978397@gmail.com](mailto:nakulsharma978397@gmail.com)
🔗 [LinkedIn](https://www.linkedin.com/in/nakulsharma97) | [GitHub](https://github.com/nakulsharma97)
