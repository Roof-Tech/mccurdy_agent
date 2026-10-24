# McCurdy Coatings toolkit

Everything for selling and running commercial roof renewal jobs, in McCurdy green/blue/white/black:

| Command | What it makes |
|---|---|
| `py -m mccurdy proposal jobs\<job>.yaml` | A 4-page branded proposal PDF: findings, scope, Good/Better/Best options, renewal-vs-replacement savings, payment schedule, CSLB notice, fillable signature block |
| `py -m mccurdy invoice <invoice>.yaml` | A branded invoice PDF (deposit, progress or final; tracks payments and balance) |
| `py -m mccurdy prospects score <assessor>.csv` | Ranked Excel list of commercial properties from a county assessor export, with a 0–100 score and the reasons |
| `py -m mccurdy prospects map --area "Fresno"` | Large warehouse/industrial/commercial roofs from OpenStreetMap with estimated roof sq ft and an aerial-view link |
| `py -m mccurdy followups <prospects>.xlsx --segment owner_investor` | Personalized follow-up email drafts (CSV for mail merge + one file per prospect to review) |

Plus:
- `brand/` — logo (SVG), colors, brand guide page, Gmail signature
- `templates/` — email sequences (owners, managers, realtors, past clients), yearly care agreement, call/visit scripts, review request + case study, weekly social posts
- `docs/PC_SETUP_WINDOWS.md` — safe setup for your PC, backups, Claude desktop and private local AI
- `docs/GROWTH_PLAYBOOK.md` — the weekly sales routine and what to track

## First-time setup
1. Follow `docs/PC_SETUP_WINDOWS.md` (or run `scripts\setup_windows.ps1`).
2. Open `config/company.yaml` and replace every `REPLACE_ME` (license #, phone, email, signer). The tools warn you until you do.
3. **Set your real prices** in `config/company.yaml → pricing`. The defaults are placeholders.

## Making a proposal
1. Copy `examples/job_example.yaml` to `D:\McCurdy\Jobs\<customer>\job.yaml`.
2. Fill in customer, address, sq ft, findings and photos (paths to your JPGs).
3. `py -m mccurdy proposal D:\McCurdy\Jobs\<customer>\job.yaml --out D:\McCurdy\Jobs\<customer>\proposal.pdf`
4. Send it as-is (the owner can type into the signature fields in Acrobat/Edge), or upload it to PandaDoc/DocuSign for a legal e-signature trail.

Or just ask Claude: *"Make a proposal for the 60,000 sq ft cold storage roof at 2650 S Chestnut, recommend the 20-year option, here are my notes and photos."*

## Finding prospects
- **Assessor data** (best, has owner names): download the secured roll / parcel file from your county assessor, or buy a commercial list. Column names are detected automatically.
- **OpenStreetMap** (free, no owners): `--area` takes a city or county name exactly as OpenStreetMap spells it, e.g. `"Fresno"`, `"Visalia"`, `"Fresno County"`.
- Fill in the Status / Next step / Notes columns as you work the list.

Customer data, prospect lists and output PDFs are kept out of git (see `.gitignore`).

## Tests
`py -m pytest -q`

## Legal notes
Proposals include the California CSLB notice (B&P §7030). Have an attorney review your proposal terms and the yearly care agreement once before first use, especially payment terms and warranty language.
