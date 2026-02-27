import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any, TextIO

HTML_PRE = """\
<!doctype html>
<html>
<head>
<title>Polish retail bonds data</title>
<style>
:root {
  --text: rgb(0, 0, 0);
  --bg: rgb(255, 255, 255);
  --table-odd-row-bg: rgb(247, 247, 248);
  --border: rgb(195, 199, 203);

  color: var(--text);
  background: var(--bg);
}

table {
    border-collapse: collapse;
    border: 2px solid var(--border);
    margin: auto;
}

th, td {
    padding: 5px;
    border: 1px solid var(--border);
}

tr {
    background: var(--table-odd-row-bg);
}

thead, thead tr, tr:nth-of-type(2n) {
    background: var(--bg);
}

thead {
    position: sticky;
    top: 0;
}
</style>
<script type="text/javascript">
document.addEventListener('DOMContentLoaded', (event) => {
    const oldestFirstCheckbox = document.getElementById('oldest-first');
    oldestFirstCheckbox.addEventListener('change', () => {
        const tbody = document.querySelector('tbody')
        const rows = [];
        for (const row of tbody.children) {
            rows.push(row.innerHTML)
        }
        rows.reverse();
        for (let i = 0; i < rows.length; i++) {
            tbody.children[i].innerHTML = rows[i]
        }
    });
});
</script>
</head>
<body style="font-family: sans-serif; text-align: center;">
<table>
"""
HTML_POST = """\
</table>
</body>
</html>
"""
HEADERS = ("ROR", "DOR", "TOS", "COI", "EDO", "ROS", "ROD")


def generate_table[T](
    fp: TextIO,
    *,
    caption: str,
    value_collector: Callable[[dict[str, Any]], T],
    value_renderer: Callable[[T], str],
) -> None:
    fp.write(HTML_PRE)
    fp.write("<caption>History of initial interest rates by bond type</caption>")
    fp.write("<thead>\n")
    fp.write("<tr>")
    fp.write("<td>")
    fp.write('<input id="oldest-first" type="checkbox" />')
    fp.write('<label for="oldest-first">Oldest first</label>')
    fp.write("</td>")
    fp.write(f'<th colspan="{len(HEADERS)}">Bond type</th>')
    fp.write("</tr>\n")
    fp.write("<tr>")
    fp.write("<th>Month of sale</th>")
    for type_name in HEADERS:
        fp.write(f"<th>{type_name}</th>")
    fp.write("</tr>\n")
    fp.write("</thead>\n")
    fp.write("<tbody>\n")
    for year_dir in sorted(Path("data").iterdir(), reverse=True):
        if not year_dir.is_dir():
            continue
        for month_dir in sorted(year_dir.iterdir(), reverse=True):
            values = {}
            for metadata_file in month_dir.glob("*_metadata.json"):
                with metadata_file.open(encoding="utf-8") as metadata_fp:
                    data = json.load(metadata_fp)
                    values[data["type_name"]] = value_collector(data)

            fp.write("<tr>")
            fp.write(f"<td>{year_dir.name}-{month_dir.name}</td>")
            for type_name in HEADERS:
                collected_value = values.get(type_name)
                cell_value = ""
                if collected_value is not None:
                    cell_value = value_renderer(collected_value)
                fp.write(f"<td>{cell_value}</td>")
            fp.write("</tr>")

    fp.write("</tbody>\n")
    fp.write(HTML_POST)


def _collect_rate(data: dict[str, Any]) -> Decimal:
    return Decimal(data["interest_rate"][0]["rate"])


def _render_rate(value: Decimal) -> str:
    return f"{value * 100:.2f}%".replace(".", ",")


def _collect_early_redemption_cost(data: dict[str, Any]) -> Decimal:
    return Decimal(data["early_redemption_cost"])


def _render_early_redemption_cost(value: Decimal) -> str:
    return f"{value:.2f} zł".replace(".", ",")


if __name__ == "__main__":
    with open("data/table_initial_rates.html", "w", encoding="utf-8") as fp:
        generate_table(
            fp,
            caption="History of initial interest rates by bond type",
            value_collector=_collect_rate,
            value_renderer=_render_rate,
        )
    with open("data/table_early_redemption_costs.html", "w", encoding="utf-8") as fp:
        generate_table(
            fp,
            caption="History of early redemption costs by bond type",
            value_collector=_collect_early_redemption_cost,
            value_renderer=_render_early_redemption_cost,
        )
