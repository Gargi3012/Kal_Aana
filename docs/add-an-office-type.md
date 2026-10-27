# Adding an office type

Kal Aana started with Haryana's 15 RTAs. Sub-registrar offices (28 of them) were added the way described here, and every step below is what that took. Passport offices, police stations or municipal offices go the same way.

## 1. Write down the official promise (no credits)

Create `data/official/<department>.toml` from the department's own directory. Every row needs a source, and the loader refuses a file without one.

```toml
[meta]
office_type = "subregistrar"
source_url = "https://jamabandi.nic.in"
source_name = "Department of Revenue & Disaster Management, Haryana: Sub-registrars"
fetched = 2026-10-08
city = "Haryana"

[[office]]
id = "sro-gurugram"
name = "Gurugram"
address = "Sub Registrar Office Gurugram, Mini Secretariat, Sector 1, Gurugram, Haryana 122001"
phones = ["0124-2321151"]
email = "sr.gurugram@haryana.gov.in"
aliases = ["Gurgaon Sub Registrar"]  # ours, not the source's: other spellings Google Maps uses
```

Add the service time limits to `data/official/haryana_timelines.toml`, each with its statutory timeline, plus the appeal path under the Haryana Right to Service Act, 2014. Then check them with `kalaana official`.

## 2. Describe the office type (no credits)

Add an `OfficeType` to `OFFICE_TYPES` in `kalaana/offices.py`. It sets the Maps query, which Google Maps categories count as this kind of office, what a private business trading on the office's name looks like, which keywords to search reviews for, and how the product names the type.

```python
"subregistrar": OfficeType(
    id="subregistrar",
    label="Sub-Registrar Office",
    maps_queries=("Sub Registrar Office", "Tehsil Office"),
    maps_categories=frozenset({"Government office", "Registry office", "Registration office", ...}),
    looks_like=re.compile(r"sub[\s-]?regist|registrar|tehsil|registration office", re.I),
    private=re.compile(r"\bservices?\b|document\s+writer|\badvocate|\bnotary|...", re.I),
    review_queries=("phone", "bribe", "agent"),
    search_prefix="Sub Registrar Office ",  # the name alone is just a place
    short="sub-registrar office", plural="sub-registrar offices", nav="Sub-registrars",
    department="Department of Revenue & Disaster Management, Haryana", officer="Sub-Registrar",
    name_suffix=" Sub-Registrar Office",
),
```

## 3. Pilot one page (1 credit)

```bash
kalaana collect subregistrar --no-reviews --targeted 0 --pages 1 --plan
kalaana collect subregistrar --no-reviews --targeted 0 --pages 1 --budget 1
```

Read every match by hand. For sub-registrars, this one page showed that Google files them under two more categories ("Registration office", "State government office"), and that Maps spells places its own way: "Gurgaon" for Gurugram. Those became categories and aliases. Re-matching is free, because every response is cached.

## 4. Sweep within your budget

```bash
kalaana collect subregistrar --pages 3 --targeted 8 --sample-offices 15 --newest-pages 2 --plan
kalaana collect subregistrar --pages 3 --targeted 8 --sample-offices 15 --newest-pages 2 --budget 55
kalaana citizen subregistrar --offices 10 --plan
kalaana citizen subregistrar --offices 10 --budget 20
```

- `--targeted` caps the one-per-office Maps searches for offices the sweep didn't confirm, offices with no listing at all first.
- `--sample-offices` reads reviews only for the most-reviewed offices.
- `--offices` checks Google Search and the AI Overview for the most-reviewed offices only.

Offices left out say "not sampled" or "not checked" everywhere, never "no problems".

## 5. Publish

```bash
kalaana report subregistrar      # read it in the terminal first
kalaana snapshot subregistrar    # data/snapshot/haryana-subregistrar.json
```

The web app picks the new type up from its snapshot (a tab on `/offices?type=subregistrar`, its own office pages, the map and the chat), and so do the MCP tools. Before committing the snapshot, read every quote and listing title it contains. Put any name the patterns missed in `data/private/names-to-mask.txt`, then rebuild. `pytest` then checks that no private mobile number is published in full and that the snapshot matches `kalaana/models.py`.
