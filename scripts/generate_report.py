"""Render one output/runs/*.json run into a readable HTML report, next to the JSON file."""

import json
import sys
from html import escape
from pathlib import Path

STYLE = """
body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 2rem auto; color: #222; }
h1 { margin-bottom: 0; }
.meta { color: #666; margin-top: 0.2rem; }
.summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin: 1.5rem 0; }
.summary div { background: #f4f4f4; border-radius: 6px; padding: 0.75rem; }
.summary .label { font-size: 0.8rem; color: #666; }
.summary .value { font-size: 1.3rem; font-weight: 600; }
.row-header, .row-summary {
  display: grid;
  grid-template-columns: 90px 90px 70px 70px 110px 70px 70px 90px;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  align-items: center;
}
.baseline-agrees { color: #666; }
.baseline-disagrees { color: #c0392b; font-weight: 600; }
.row-header { font-weight: 600; font-size: 0.8rem; color: #666; border-bottom: 2px solid #ddd; }
details.row { border-bottom: 1px solid #eee; }
details.row summary { cursor: pointer; list-style: none; }
details.row summary::-webkit-details-marker { display: none; }
.row-correct { background: #eafbea; }
.row-mismatch { background: #fdecea; }
.row-rejected { background: #f0f0f0; }
.row-detail { padding: 0.75rem 1rem; background: #fafafa; font-size: 0.9rem; }
.row-detail pre { white-space: pre-wrap; background: #fff; padding: 0.5rem; border-radius: 4px; border: 1px solid #ddd; }
.row-detail .field { margin-bottom: 0.6rem; }
.row-detail .field-label { font-weight: 600; font-size: 0.8rem; color: #555; }
"""


def render_row(record: dict) -> str:
    status = record["status"]
    if status == "rejected":
        css_class = "row-rejected"
        answer = "—"
        decision_col = record["reject_reason"]
    elif record["correct"]:
        css_class = "row-correct"
        answer = record["answer"]
        decision_col = record["final_decision"]
    else:
        css_class = "row-mismatch"
        answer = record["answer"]
        decision_col = record["final_decision"]

    context = record.get("context")
    context_html = ""
    if context:
        context_html = "".join(
            f'<div class="field"><span class="field-label">[{escape(label)}]</span> {escape(text)}</div>'
            for label, text in zip(context["labels"], context["contexts"])
        )

    detail_fields = [
        ("question", record.get("question", "")),
        ("evidence_quote", record.get("evidence_quote", "")),
    ]
    if status == "rejected":
        # raw_response is the only evidence of what the model said when there's no parsed answer
        detail_fields.append(("raw_response", record.get("raw_response", "")))

    detail_html = "".join(
        f'<div class="field"><div class="field-label">{escape(name)}</div><pre>{escape(str(value))}</pre></div>'
        for name, value in detail_fields
        if value
    )
    if context_html:
        detail_html += f'<div class="field"><div class="field-label">context</div>{context_html}</div>'

    baseline_pred = record.get("reasoning_required_pred", "")
    baseline_agrees = baseline_pred == record["final_decision"]
    baseline_class = "baseline-agrees" if baseline_agrees else "baseline-disagrees"
    baseline_label = escape(baseline_pred) + ("" if baseline_agrees else " ⚠ disagrees too")

    return f"""
    <details class="row {css_class}">
      <summary class="row-summary">
        <span>{record['pubid']}</span>
        <span>{status}</span>
        <span>{escape(str(answer))}</span>
        <span>{escape(str(decision_col))}</span>
        <span class="{baseline_class}">{baseline_label}</span>
        <span>{record['latency_seconds']:.2f}s</span>
        <span>${record['cost_usd']:.6f}</span>
        <span></span>
      </summary>
      <div class="row-detail">{detail_html}</div>
    </details>
    """


def render_report(run: dict) -> str:
    report = run["report"]
    accuracy = report["accuracy"]
    accuracy_str = f"{accuracy:.0%}" if accuracy is not None else "n/a"

    rejected_by_reason = ", ".join(f"{k}: {v}" for k, v in report["rejected_by_reason"].items()) or "none"

    summary_html = f"""
    <div class="summary">
      <div><div class="label">rows</div><div class="value">{report['total_in']}</div></div>
      <div><div class="label">valid / rejected</div><div class="value">{report['valid_count']} / {report['rejected_count']}</div></div>
      <div><div class="label">accuracy</div><div class="value">{accuracy_str}</div></div>
      <div><div class="label">total cost</div><div class="value">${report['total_cost_usd']:.6f}</div></div>
      <div><div class="label">avg latency</div><div class="value">{report['avg_latency_seconds']:.2f}s</div></div>
      <div><div class="label">total latency</div><div class="value">{report['total_latency_seconds']:.2f}s</div></div>
      <div><div class="label">rejected by reason</div><div class="value" style="font-size:0.95rem">{escape(rejected_by_reason)}</div></div>
    </div>
    """

    rows_html = "".join(render_row(r) for r in run["records"])

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Stage 1 run — {escape(run['model'])}</title>
  <style>{STYLE}</style>
</head>
<body>
  <h1>{escape(run['model'])}</h1>
  <div class="meta">{escape(run['started_at'])} · {run['row_count']} rows</div>
  {summary_html}
  <div class="row-header">
    <span>pubid</span><span>status</span><span>answer</span><span>final_decision / reject_reason</span><span>2019 baseline</span><span>latency</span><span>cost</span><span></span>
  </div>
  {rows_html}
</body>
</html>
"""


def main() -> None:
    run_path = Path(sys.argv[1])
    run = json.loads(run_path.read_text())
    html = render_report(run)
    out_path = run_path.with_suffix(".html")
    out_path.write_text(html)
    print(f"Saved report to {out_path}")


if __name__ == "__main__":
    main()
