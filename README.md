# Kenya Government Tender Tracker

A command-line tool that finds **open Kenyan government tenders that match your business** and shows what you need to bid, using live data from the Public Procurement Information Portal (PPIP).

## The problem it solves

Every national and county government tender in Kenya is published on [tenders.go.ke](https://tenders.go.ke), but finding the right ones is slow. You page through hundreds of tenders, and you only see the bid requirements once you open each one. Small businesses miss deadlines they would have qualified for.

This tool answers one question in seconds: **"What open government tenders match my business, and what do I need to bid?"**

## How it works

- **Input:** keywords for your business (e.g. `computer, ICT, printer`), a category (Goods / Works / Services / any), and how many days back to look.
- **Processing:** fetches every active tender from the PPIP API (`tenders.go.ke/api/active-tenders`, paging through all results). It then keeps only tenders that:
  - are still open,
  - were posted recently, and
  - match your keywords and category.
- **Output:** a readable list, newest first, with each tender's entity, closing date and time left, and bidding requirements: tender fee, bid security, how to submit, bid validity, and whether it's reserved under AGPO (for youth, women and persons with disabilities). It also gives links to the tender documents. Results are saved to a timestamped JSON file.

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/Billrawknow/tender-tracker.git
   cd tender-tracker
   ```
2. Install the one dependency:
   ```bash
   pip install -r requirements.txt
   ```

You don't need an API key, because PPIP tender data is public.

## Usage

```bash
python tender_tracker.py
```

## Example output

```
Kenya Government Tender Tracker
-------------------------------
Keywords for your business (comma-separated, blank = all): computer, ict
Category:  1) Goods   2) Works   3) Services   [Enter] Any
Choose:
Show tenders posted in the last how many days? [14]:
Found 428 active tenders on PPIP. Downloading...

================================================================
  2 open tender(s) for: computer, ict  ·  posted in last 14 days
================================================================

[1] PROVISION OF ICT SUPPORT SERVICES
    Entity:        KENYA REVENUE AUTHORITY (Nairobi)
    Category:      Services  ·  Open Tender
    Tender no.:    REF/3/2026
    Posted:        Sun 18 Oct 2026
    Closes:        Mon 19 Oct 2026, 07:32 PM  (7 hours left - URGENT)
    Requirements:
      - Tender fee:     None
      - Bid security:   Not required
      - Submit by:      Electronic (e-Procurement)
      - Bid valid for:  180 days
      - AGPO reserved:  Yes (Persons with Disabilities)
      - Note:           An addendum was issued - read it before bidding
    Tender Document: https://tenders.go.ke/storage/Documents/...pdf
    OCID:          ocds-5whusi-...  (search this on tenders.go.ke)
...
Results saved to tenders_20261019_1220.json
```

## Errors handled

| Situation | What you see |
|---|---|
| No internet / portal unreachable | "Couldn't connect to tenders.go.ke. Check your internet connection." |
| Portal slow (timeout) | Asks you to try again in a minute |
| Portal down (HTTP 5xx) or rate limiting (429) | Plain-English explanation |
| Portal sends non-JSON or changes its format | Says the portal may be under maintenance, or the tool needs updating |
| Invalid category or number of days | Explains what to type instead |
| No matching tenders | Suggests broader keywords or more days |

## Privacy

The PPIP API response includes personal details of the government officer who posted each tender: national ID number, phone numbers and personal emails. **This tool deliberately drops all of that.** It keeps only public tender information and the procuring entity's official contact details.

## Roadmap

- Government **job vacancies** (Public Service Commission and ministries)
- Email or WhatsApp alerts when a new matching tender is posted
- Extract detailed eligibility requirements from the tender document PDFs

## Built with

Python and `requests`. AI Masterclass 2, Phase II, Week 1 project.
