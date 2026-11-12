from spain_vote_ev import style, tables
from spain_vote_ev.sources import RESULTS


def test_update_fills_markers_and_is_idempotent(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# x\n\n<!-- BEGIN blocs -->\n<!-- END blocs -->\n\ntext\n\n"
                      "<!-- BEGIN provinces -->\nstale\n<!-- END provinces -->\n")
    s = style.load_summary(RESULTS)
    assert tables.update(readme, s) == ["provinces", "blocs"]
    once = readme.read_text()
    assert "stale" not in once and "| Bloc |" in once and once.count("| Ceuta |") == 1
    tables.update(readme, s)
    assert readme.read_text() == once
