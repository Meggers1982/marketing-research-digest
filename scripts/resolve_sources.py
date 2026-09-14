"""Match every active journal in config/journals.csv to its OpenAlex source.

Maintenance, not part of the daily run. Re-run it when the journal list
changes:

    python scripts/resolve_sources.py

It writes two columns back into the CSV -- `OpenAlex Source ID` and
`OpenAlex Match` -- and leaves every original column untouched.

ISSN first, name second, and a name match must be exact after normalizing case
and punctuation. Two titles on the list carry a hijacked-title warning: a
look-alike journal trading on the real one's name. A fuzzy name match is how
the pipeline would end up reading the fake, so a near miss is recorded as one
("no match; closest: ...") for a person to decide, never accepted.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import journals as journals_mod  # noqa: E402
import openalex  # noqa: E402


def resolve(rows: list[dict]) -> list[dict]:
    parsed = journals_mod.load()
    wanted = sorted({issn for j in parsed if j.active for issn in j.issns})
    by_issn = openalex.sources_by_issn(wanted)

    for row, journal in zip(rows, parsed):
        row[journals_mod.SOURCE_ID_COLUMN] = ""
        if not journal.active:
            row[journals_mod.MATCH_COLUMN] = "skipped (inactive)"
            continue

        candidates = {}
        for issn in journal.issns:
            source = by_issn.get(issn)
            if source:
                candidates[source["id"]] = source
        if candidates:
            # Print and online ISSNs occasionally resolve to two sources; the
            # one with the larger archive is the one articles are filed under.
            best = max(candidates.values(), key=lambda s: s.get("works_count") or 0)
            row[journals_mod.SOURCE_ID_COLUMN] = openalex.short_id(best["id"])
            row[journals_mod.MATCH_COLUMN] = f"issn ({best['display_name']})"
            continue

        key = journals_mod._name_key(journal.name)
        results = openalex.sources_by_name(journal.name)
        exact = [s for s in results if journals_mod._name_key(s.get("display_name", "")) == key]
        if exact:
            best = max(exact, key=lambda s: s.get("works_count") or 0)
            row[journals_mod.SOURCE_ID_COLUMN] = openalex.short_id(best["id"])
            row[journals_mod.MATCH_COLUMN] = f"name ({best['display_name']})"
        elif results:
            row[journals_mod.MATCH_COLUMN] = f"no match; closest: {results[0].get('display_name', '')}"
        else:
            row[journals_mod.MATCH_COLUMN] = "not indexed"
    return rows


def main() -> None:
    path = journals_mod.JOURNALS_CSV
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    for column in (journals_mod.SOURCE_ID_COLUMN, journals_mod.MATCH_COLUMN):
        if column not in fields:
            fields.append(column)

    rows = resolve(rows)

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    active = [r for r in rows if not r[journals_mod.MATCH_COLUMN].startswith("skipped")]
    matched = [r for r in active if r[journals_mod.SOURCE_ID_COLUMN]]
    print(f"{len(matched)} of {len(active)} active journals matched to an OpenAlex source.")
    for row in active:
        if not row[journals_mod.SOURCE_ID_COLUMN]:
            print(f"  unmatched: {row['Journal']} -- {row[journals_mod.MATCH_COLUMN]}")


if __name__ == "__main__":
    main()
