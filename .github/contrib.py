import json, os, random, sys, urllib.request

LOGIN = os.environ.get("GH_LOGIN", "Alfcht")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = "assets/contribution-explosion.svg"
BOOM_COUNT = 40

# GitHub dark-mode greens (same as the real graph)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
# Witch-theme alternative:
# PALETTE = ["#111a3a", "#1b2a5c", "#3a4f9a", "#8fa8e8", "#dfe6f5"]

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{totalContributions weeks{contributionDays{
date contributionCount contributionLevel weekday}}}}}}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": "bearer " + TOKEN,
                 "Content-Type": "application/json",
                 "User-Agent": "contrib-explosion"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(json.dumps(data["errors"]))
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


CSS = """
.t{font-family:'Courier New',Courier,monospace;font-weight:bold}
.cap{font-size:12px;fill:#e8c97a;letter-spacing:2px}
.warn{font-size:12px;fill:#b3202f;letter-spacing:2px}
.lg{font-size:10px;fill:#7d8590}
.blink{animation:bl 1s steps(1) infinite}
@keyframes bl{0%{opacity:1}50%{opacity:.15}100%{opacity:1}}
.cell,.fl,.p{animation-duration:10s;animation-iteration-count:infinite;animation-delay:var(--d);animation-timing-function:steps(1)}
.cell,.fl{transform-box:fill-box;transform-origin:center}
.cell{animation-name:crater}
.fl{opacity:0;fill:#fff;animation-name:flash}
.p{opacity:0;animation-name:shard;animation-timing-function:steps(4)}
@keyframes crater{0%{opacity:1;transform:scale(1)}1%{opacity:0}60%{opacity:.4;transform:scale(.5)}64%{opacity:1;transform:scale(1)}100%{opacity:1;transform:scale(1)}}
@keyframes flash{0%{opacity:1;transform:scale(1);fill:#fff}1%{transform:scale(2);fill:#e8c97a}2.5%{transform:scale(3);fill:#b3202f;opacity:.9}4%{transform:scale(3.6);opacity:.5}5%{opacity:0}100%{opacity:0}}
@keyframes shard{0%{opacity:1;transform:translate(0,0)}9%{opacity:1;transform:translate(var(--dx),var(--dy))}11%{opacity:0;transform:translate(calc(var(--dx)*1.3),calc(var(--dy)*1.3))}100%{opacity:0}}
.q1{--dx:-30px;--dy:0px;fill:#e8c97a}.q2{--dx:30px;--dy:0px;fill:#b3202f}
.q3{--dx:0px;--dy:-26px;fill:#e8c97a}.q4{--dx:0px;--dy:26px;fill:#fff}
.q5{--dx:-22px;--dy:-22px;fill:#b3202f}.q6{--dx:22px;--dy:-22px;fill:#e8c97a}
.q7{--dx:-22px;--dy:22px;fill:#e8c97a}.q8{--dx:22px;--dy:22px;fill:#b3202f}
"""


def build(cal):
    random.seed(7)
    weeks = cal["weeks"]
    PITCH, SZ = 15, 12
    X0, Y0 = 64, 58

    cells = []
    for w, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            cells.append((w, d["weekday"], LEVELS[d["contributionLevel"]],
                          d["contributionCount"]))
    active = [i for i, c in enumerate(cells) if c[3] > 0]
    boom = set(random.sample(active, min(BOOM_COUNT, len(active))))

    palette_css = "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(PALETTE))
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 210" '
           'width="900" height="210">',
           f"<style>{CSS}{palette_css}</style>",
           '<rect x="12" y="12" width="876" height="186" fill="#0d1117" '
           'stroke="#e8c97a" stroke-width="4"/>']

    title = f"{cal['totalContributions']:,} CONTRIBUTIONS IN THE LAST YEAR"
    out.append(f'<text class="t cap" x="28" y="36">{title}</text>')
    out.append(f'<text class="t warn blink" x="{28 + len(title) * 9.2 + 10:.0f}" '
               'y="36">// UNSTABLE</text>')

    # month labels (same idea as GitHub: label where the month changes)
    labels, prev = [], None
    for w, wk in enumerate(weeks):
        m = int(wk["contributionDays"][0]["date"][5:7]) - 1
        if m != prev:
            labels.append((w, m))
            prev = m
    if len(labels) > 1 and labels[1][0] - labels[0][0] < 3:
        labels.pop(0)
    for w, m in labels:
        out.append(f'<text class="t lg" x="{X0 + w * PITCH}" y="{Y0 - 8}">{MONTHS[m]}</text>')

    # weekday labels
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text class="t lg" x="28" y="{Y0 + row * PITCH + 10}">{name}</text>')

    # legend (bottom right, like GitHub)
    ly = Y0 + 7 * PITCH + 10
    out.append(f'<text class="t lg" x="672" y="{ly + 10}">Less</text>')
    for i in range(5):
        out.append(f'<rect class="l{i}" x="{706 + i * 15}" y="{ly}" width="{SZ}" '
                   f'height="{SZ}" rx="2"/>')
    out.append(f'<text class="t lg" x="790" y="{ly + 10}">More</text>')

    plain, booms = [], []
    for i, (w, row, lv, count) in enumerate(cells):
        x, y = X0 + w * PITCH, Y0 + row * PITCH
        if i in boom:
            d = -random.uniform(0, 10)
            g = [f'<g transform="translate({x} {y})" style="--d:{d:.1f}s">',
                 f'<rect class="cell l{lv}" width="{SZ}" height="{SZ}" rx="2"/>',
                 f'<rect class="fl" width="{SZ}" height="{SZ}" rx="2"/>']
            for q in range(1, 9):
                g.append(f'<rect class="p q{q}" x="4" y="4" width="4" height="4"/>')
            g.append("</g>")
            booms.append("".join(g))
        else:
            plain.append(f'<rect class="l{lv}" x="{x}" y="{y}" width="{SZ}" '
                         f'height="{SZ}" rx="2"/>')
    out += plain + booms + ["</svg>"]
    return "\n".join(out)


if __name__ == "__main__":
    svg = build(fetch())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT, len(svg), "bytes")
