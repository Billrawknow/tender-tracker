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

A real run on 20 October 2026:

```
Kenya Government Tender Tracker
-------------------------------
Keywords for your business (comma-separated, blank = all): ICT
Category:  1) Goods   2) Works   3) Services   [Enter] Any
Choose: 2
Show tenders posted in the last how many days? [14]: 30
Found 414 active tenders on PPIP. Downloading...
Downloaded 414 tenders. Filtering...

================================================================
  3 open tender(s) for: ict  ·  Works  ·  posted in last 30 days
================================================================

[1] SUPPLY, DELIVERY, INSTALLATION, TESTING, COMMISSIONING AND MAINTENANCE OF A SOLAR POWERED BACK UP AT ICT HUBS AND MUNICIPALITY SERVER ROOM. (BAHARI, HONGWE, MANDA, MKUNUMBI, FAZA)
    Entity:        Lamu County Government
    Category:      Works  ·  Open Tender
    Tender no.:    CGL/ONT/ICT/SP/007/2026-2027
    Posted:        Mon 19 Oct 2026
    Closes:        Tue 03 Nov 2026, 11:00 AM  (13 days left)
    Requirements:
      - Tender fee:     None
      - Bid security:   Not stated on PPIP - check the tender document
      - Submit by:      Electronic submission
      - Bid valid for:  120 days
    Tender Notice: https://tenders.go.ke/storage/Documents/1792436418978-supply-delivery-installation-testing-commissioning-and-maintenance-of-a-solar-powered-.pdf
    Tender Document: https://tenders.go.ke/storage/Documents/1792436419008-supply-delivery-installation-testing-commissioning-and-maintenance-of-a-solar-powered-.pdf
    Additional Documents: https://tenders.go.ke/storage/Documents/1792436419017-bq.pdf
    OCID:          ocds-5whusi-309148-CGL/ONT/ICT/SP/007/2026-2027  (search this on tenders.go.ke)

[2] CONSTRUCTION OF BASIC DIGITAL HUB AT SINYERERI DIGITAL ICT HUB
    Entity:        NGCDF CHERANGANY (KITALE)
    Category:      Works  ·  Open Tender
    Tender no.:    SINYECHEF/01/2026-2027
    Posted:        Tue 13 Oct 2026
    Closes:        Wed 21 Oct 2026, 10:30 AM  (22 hours left - URGENT)
    Requirements:
      - Tender fee:     None
      - Bid security:   Not stated on PPIP - check the tender document
      - Submit by:      Written (Physical/Hard Copy)
      - Bid valid for:  120 days
    Tender Document: https://tenders.go.ke/storage/Documents/1791980431673-tender-documents.pdf
    Tender Notice: https://tenders.go.ke/storage/Documents/1792051324492-tender-notice.pdf
    OCID:          ocds-5whusi-308671-SINYECHEF/01/2026-2027  (search this on tenders.go.ke)

[3] Refurbishment Works for Huduma Centres in Borderland Areas
    Entity:        ICT Authority (Nairobi)
    ...

================================================================

Results saved to tenders_20261020_1228.json
```

## Errors handled

| Situation                                     | What you see                                                         |
| --------------------------------------------- | -------------------------------------------------------------------- |
| No internet / portal unreachable              | "Couldn't connect to tenders.go.ke. Check your internet connection." |
| Portal slow (timeout)                         | Asks you to try again in a minute                                    |
| Portal down (HTTP 5xx) or rate limiting (429) | Plain-English explanation                                            |
| Portal sends non-JSON or changes its format   | Says the portal may be under maintenance, or the tool needs updating |
| Invalid category or number of days            | Explains what to type instead                                        |
| No matching tenders                           | Suggests broader keywords or more days                               |

## Assumptions and limitations

- **Data source:** tenders come from the PPIP portal's public JSON endpoint (`tenders.go.ke/api/active-tenders`). That endpoint is used by the portal's own website but isn't officially documented, so PPRA could change it without notice. All PPIP-specific code is in `fetch_page()` and `summarise()`, so a change only affects those two functions.
- **Keyword matching** looks at the tender title and the procuring entity's name, not the text inside tender documents.
- **Bid security:** when PPIP leaves bid security blank, the tool says "Not stated on PPIP - check the tender document" instead of assuming none is required. Always confirm requirements in the tender document before bidding.
- **Dates** are shown as published on PPIP, in Kenyan time (EAT).
- **Jobs and other opportunities** are not covered in this version. See the roadmap.

## Privacy

The PPIP API response includes personal details of the government officer who posted each tender: national ID number, phone numbers and personal emails. **This tool deliberately drops all of that.** It keeps only public tender information and the procuring entity's official contact details.

## Roadmap

- Government **job vacancies** (Public Service Commission and ministries)
- Email or WhatsApp alerts when a new matching tender is posted
- Extract detailed eligibility requirements from the tender document PDFs

## Version

**v1.0** (20 October 2026): first delivered release. Tagged on GitHub as `v1.0`.

## Built with

Python and `requests`. AI Masterclass 2, Phase II, Week 1 project.
