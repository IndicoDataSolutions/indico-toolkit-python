import pytest

from indico_toolkit.metrics import Plotting

go = pytest.importorskip("plotly.graph_objects")


def test_add_barplot_data():
    plotting = Plotting()
    plotting.add_barplot_data(["a", "b"], [1, 2])
    plotting.add_barplot_data(["a", "b"], [3, 4])
    assert len(plotting._plot_data) == 2
    assert isinstance(plotting._plot_data[0], go.Bar)


def test_add_line_data():
    plotting = Plotting()
    plotting.add_line_data([50, 100], [0.4, 0.8])
    plotting.add_line_data([50, 100], [0.6, 0.9])
    assert len(plotting._plot_data) == 2
    assert isinstance(plotting._plot_data[0], go.Scatter)


def test_add_barplot_exception():
    with pytest.raises(ValueError):
        plotting = Plotting()
        plotting.add_barplot_data("Whoops!", [1, 2])
