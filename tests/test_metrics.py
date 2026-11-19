from datetime import date

import pytest

from woa import aging_table, backlog_by, closure_stats, load_work_orders, summary
from woa.cli import main
from woa.metrics import bucket_for, open_orders

HEADER = "id,building,trade,priority,status,created,closed\n"
AS_OF = date(2026, 11, 1)


def make_csv(tmp_path, body, header=HEADER):
    path = tmp_path / "wo.csv"
    path.write_text(header + body)
    return path


@pytest.fixture
def df(tmp_path):
    body = (
        "1,Building A,HVAC,High,Open,2026-10-30,\n"
        "2,Building A,HVAC,Low,Open,2026-08-01,\n"
        "3,Building B,Plumbing,High,Closed,2026-10-01,2026-10-05\n"
        "4,Building B,Plumbing,High,Closed,2026-10-01,2026-10-11\n"
        "5,Building B,Electrical,Medium,In Progress,2026-09-20,\n"
    )
    return load_work_orders(make_csv(tmp_path, body))


def test_bucket_edges():
    assert [bucket_for(d) for d in (0, 7, 8, 30, 31, 60, 61, 90, 91)] == [
        "0-7", "0-7", "8-30", "8-30", "31-60", "31-60", "61-90", "61-90", "90+"]


def test_bucket_negative_rejected():
    with pytest.raises(ValueError):
        bucket_for(-1)


def test_open_orders_excludes_closed(df):
    assert sorted(open_orders(df)["id"]) == ["1", "2", "5"]


def test_aging_table_counts(df):
    table = aging_table(df, AS_OF)
    assert table.loc["High", "0-7"] == 1
    assert table.loc["Low", "90+"] == 1
    assert table.loc["Low", "61-90"] == 0
    assert table.loc["Medium", "31-60"] == 1
    assert int(table.to_numpy().sum()) == 3


def test_aging_table_empty_when_all_closed(tmp_path):
    path = make_csv(tmp_path, "1,Building A,HVAC,High,Closed,2026-10-01,2026-10-02\n")
    table = aging_table(load_work_orders(path), AS_OF)
    assert int(table.to_numpy().sum()) == 0
    assert list(table.index) == ["Emergency", "High", "Medium", "Low"]


def test_backlog_by_building(df):
    result = backlog_by(df, "building")
    assert result["Building A"] == 2 and result["Building B"] == 1


def test_backlog_unknown_column(df):
    with pytest.raises(ValueError):
        backlog_by(df, "colour")


def test_closure_stats_median(df):
    stats = closure_stats(df)
    assert stats.loc["High", "median_days"] == 7.0
    assert stats.loc["High", "closed"] == 2


def test_summary_values(df):
    s = summary(df, AS_OF)
    assert s["total"] == 5 and s["open"] == 3 and s["closed"] == 2
    assert s["oldest_open_days"] == 92
    assert s["pct_open_over_30_days"] == 66.7


def test_missing_column(tmp_path):
    path = make_csv(tmp_path, "1,Building A\n", header="id,building\n")
    with pytest.raises(ValueError, match="missing columns"):
        load_work_orders(path)


def test_bad_date(tmp_path):
    path = make_csv(tmp_path, "1,Building A,HVAC,High,Open,31/10/2026,\n")
    with pytest.raises(ValueError, match="bad date"):
        load_work_orders(path)


def test_cli_reports_error(tmp_path, capsys):
    assert main([str(tmp_path / "nope.csv")]) == 1
    assert "error" in capsys.readouterr().err


def test_cli_prints_report(tmp_path, capsys):
    path = make_csv(tmp_path, "1,Building A,HVAC,High,Open,2026-10-30,\n")
    assert main([str(path), "--as-of", "2026-11-01"]) == 0
    assert "open 1" in capsys.readouterr().out


def test_summary_no_open(tmp_path):
    path = make_csv(tmp_path, "1,Building A,HVAC,High,Closed,2026-10-01,2026-10-02\n")
    s = summary(load_work_orders(path), AS_OF)
    assert s["open"] == 0 and s["oldest_open_days"] == 0
