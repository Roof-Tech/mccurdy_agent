# Setting up your PC (RTX 5090 · 64 GB RAM · 3 TB)

A safe AI workstation for McCurdy Coatings. Takes about an hour.

## 1. Lock down the basics first
1. **Windows Update** → install everything. Update the NVIDIA driver (NVIDIA App → Drivers).
2. **BitLocker** (Settings → Privacy & security → Device encryption, or Control Panel → BitLocker) → turn on for every drive. Save the recovery key in your password manager, not on the PC.
3. **Password manager** (1Password or Bitwarden). Turn on 2-step login for Google/Gmail, QuickBooks, bank, GitHub and Claude.
4. **Backups**:
   - Local: an external drive with Windows **File History** (Settings → System → Storage → Advanced → Backup options) on `D:\McCurdy`.
   - Cloud: **Backblaze Personal** or OneDrive/Google Drive sync for `D:\McCurdy`.
   - Test a restore once. A backup you've never restored isn't a backup.

## 2. Folder layout
Run `scripts\setup_windows.ps1` (below) or create by hand:
```
D:\McCurdy\
  Jobs\        one folder per job: photos, job.yaml, proposal PDF, invoices, signed contract
  Prospects\   assessor CSVs and prospect spreadsheets
  Brand\       logos, photos, case studies
  Admin\       insurance certificates, license, W-9, manufacturer certifications
  Toolkit\     this repository (mccurdy_agent)
```
Keep customer data here, **not** in git or in public cloud links.

## 3. Install the apps
| App | What for | Get it |
|---|---|---|
| **Claude desktop** | Main AI assistant: writes, builds proposals, runs this toolkit, works with your files (Cowork), Claude Code for the apps | claude.ai/download |
| **Python 3.12+** | Runs the toolkit | python.org (check "Add to PATH") |
| **Git** | Gets toolkit updates | git-scm.com |
| **LM Studio** (optional) | Private AI that runs on your 5090, offline | lmstudio.ai |
| **Adobe Acrobat Reader** | Fill and sign proposal PDFs | adobe.com |
| **PandaDoc or DocuSign** | Legal e-signatures with audit trail | their websites |
| **QuickBooks Online** | Books, invoices, payments | quickbooks.intuit.com |

## 4. Give Claude access the safe way
- In Claude desktop, allow only the `D:\McCurdy` folder, not your whole drive.
- Leave approval prompts **on** for: sending email, deleting files, payments, anything that signs or submits.
- Connect Gmail and Google Drive under Settings → Connectors. Claude can then draft follow-up emails for you to review and send.
- Never paste bank passwords, card numbers or your QuickBooks login into any chat.

## 5. Private local AI on the 5090 (optional)
1. Install LM Studio → Discover → download an instruct model in the **20–32B** range at Q4–Q6 (Qwen, Gemma, Mistral or gpt-oss families). With 32 GB of VRAM these run fast and fully offline.
2. Use it for: private notes about customers, drafting from your price sheet, summarizing inspection notes.
3. Use Claude for multi-step work: building proposals, fixing apps, research, long documents.
4. Check the LM Studio leaderboard tab every few months. Better open models come out often.

## 6. Install the toolkit
```powershell
cd D:\McCurdy\Toolkit
git clone https://github.com/roof-tech/mccurdy_agent.git .
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
notepad config\company.yaml     # fill in REPLACE_ME values and your real prices
py -m mccurdy proposal examples\job_example.yaml
```
Your first proposal PDF appears in `output\proposals\`.

## 7. Monthly safety checklist
- [ ] Windows + NVIDIA + app updates installed
- [ ] Backup ran and one file restored as a test
- [ ] Review which apps/connectors Claude can access; remove unused ones
- [ ] Prices in `config\company.yaml` still match your costs
- [ ] Insurance certificates and CSLB license current
