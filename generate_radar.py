import math
import os
import requests

def fetch_stats(username, token):
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
          totalPullRequestReviewContributions
        }
      }
    }
    """
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": username}},
        headers={"Authorization": f"bearer {token}"},
    )
    cc = resp.json()["data"]["user"]["contributionsCollection"]
    return {
        "Commits":       cc["totalCommitContributions"],
        "Pull Requests": cc["totalPullRequestContributions"],
        "Issues":        cc["totalIssueContributions"],
        "Code Review":   cc["totalPullRequestReviewContributions"],
    }

def generate_svg(stats, path):
    labels = list(stats.keys())
    values = list(stats.values())
    total  = sum(values) or 1
    pcts   = [v / total for v in values]

    cx, cy, r = 200, 210, 120
    n = len(labels)
    angles = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]

    def pt(angle, radius):
        return cx + radius * math.cos(angle), cy + radius * math.sin(angle)

    # grid rings
    grids = ""
    for lvl in [0.25, 0.5, 0.75, 1.0]:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in [pt(a, r * lvl) for a in angles])
        grids += f'<polygon points="{pts}" fill="none" stroke="#ddd" stroke-width="1"/>\n'

    # axis lines
    axes = ""
    for a in angles:
        x, y = pt(a, r)
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#ddd" stroke-width="1"/>\n'

    # data polygon
    data_pts = [pt(a, r * p) for a, p in zip(angles, pcts)]
    poly     = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_pts)

    # dots
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="white" stroke="#2d6a2d" stroke-width="2"/>'
        for x, y in data_pts
    )

    # labels
    label_els = ""
    for label, pct, angle in zip(labels, pcts, angles):
        lx, ly = pt(angle, r + 32)
        anchor = "middle"
        if lx < cx - 10: anchor = "end"
        elif lx > cx + 10: anchor = "start"
        label_els += (
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'font-family="Arial,sans-serif" font-size="13" fill="#333">{label}</text>\n'
            f'<text x="{lx:.1f}" y="{ly+16:.1f}" text-anchor="{anchor}" '
            f'font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="#2d6a2d">'
            f'{pct*100:.0f}%</text>\n'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="420" viewBox="0 0 400 420">
  <rect width="400" height="420" fill="white" rx="12"/>
  <text x="200" y="30" text-anchor="middle" font-family="Arial,sans-serif"
        font-size="15" font-weight="bold" fill="#333">Contribution Breakdown</text>
  {grids}{axes}
  <polygon points="{poly}" fill="rgba(45,106,45,0.18)" stroke="#2d6a2d" stroke-width="2"/>
  {dots}
  {label_els}
</svg>'''

    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Saved {path}")

if __name__ == "__main__":
    token = os.environ["GH_PAT"]
    stats = fetch_stats("Pollycarp", token)
    print("Stats:", stats)
    generate_svg(stats, "contribution-radar.svg")
