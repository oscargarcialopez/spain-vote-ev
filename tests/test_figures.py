"""Figure 4: its labels are chosen from the data and placed where they cover nothing."""

import pytest

from spain_vote_ev import carousel, style
from spain_vote_ev.sources import RESULTS


@pytest.mark.parametrize("lang", ["es", "en"])
def test_constituency_labels_cover_nothing(lang):
    style.paper_style()
    s = style.load_summary(RESULTS)
    fig, ax, points, labels = carousel.draw_constituencies(s, carousel.Lang(lang))
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(rend) for t in labels]
    dots = carousel.point_boxes(ax, points)
    legend = ax.get_legend().get_window_extent(rend)
    frame = ax.get_window_extent(rend)
    carousel.plt.close(fig)
    prov = s["vote"]["provinces"]
    events = [e for e in ("seat", "government", "majority_any") if f"one_in_{e}" in prov[0]][:2]
    wanted = sorted(prov[i]["name"] for _, i in carousel.extremes(prov, tuple(events)))
    assert sorted(t.get_text() for t in labels) == wanted  # the extremes, from the data
    for i, b in enumerate(boxes):
        assert frame.x0 <= b.x0 and b.x1 <= frame.x1 and frame.y0 <= b.y0 and b.y1 <= frame.y1
        assert not any(b.overlaps(d) for d in dots), labels[i].get_text()
        assert not b.overlaps(legend), labels[i].get_text()
        assert not any(b.overlaps(o) for j, o in enumerate(boxes) if j != i)
    assert not any(legend.overlaps(d) for d in dots)  # the legend hides no constituency
