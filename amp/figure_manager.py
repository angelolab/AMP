from collections import deque
from amp.mplwidget import Plot
from amp.plotlistwidget import PlotListWidget
from typing import List, Union, Dict, Callable, Any

# prefilling dictionary prevents slow rehashing
MAX_FIGS = 64


class FigureManager(object):
    def __init__(self, plot_list: PlotListWidget) -> None:
        self.figure_map: Dict[int, Union[Plot, None]] = dict.fromkeys(range((MAX_FIGS * 3) // 2))

        self.open_slots = deque([0])

        self.plot_list = plot_list

    def get_figure(self, index: int) -> Plot:
        """Get plotting data for figure at given index

        Args:
            index (int):
                Figure index

        Returns:
            mplwidget.Plot:
                Plotting data at given index
        """
        return self.figure_map[index]

    def add_figure(self, plot_object: Plot, name: Union[str, None] = None,
                   delete_callback_base: Callable[[int], None] = None) -> int:
        """Add new figure to figure manager

        Args:
            plot_object (mplwidget.Plot):
                New plotting data
            name (str or None):
                Name passed to the Main Viewer's plot list.  If None, the plot list will list it
                as f'Figure {index}'. Default is None.
            delete_callback (Callable[[int], None] or None):
                Figure deletion callback generator

        Returns:
            int:
                Index of new figure
        """

        condition = len(self.open_slots) == 1

        index = self.open_slots[0] if condition else self.open_slots.popleft()

        def delete_callback():
            return delete_callback_base(index)

        if index in range(MAX_FIGS-10, MAX_FIGS):
            print(f'Approaching maximum figure limit, {MAX_FIGS}')
        elif index >= MAX_FIGS:
            print(f'Maximum figure limit, {MAX_FIGS} has been reached. '
                  f'No further figures were added...')
            return None

        self.figure_map[index] = plot_object
        self.open_slots[0] += int(condition)

        if name is None:
            name = f'Figure {index}'

        self.plot_list.add_item(
            name,
            plot_object,
            index,
            delete_callback
        )

        row = self.plot_list.get_item_row_by_path(index)
        self.plot_list.setCurrentRow(row)

        return index

    def update_figure(self, index: int, new_plot: Plot, name: Union[str, None] = None) -> None:
        """Update figure at given index with new plotting data

        Args:
            index (int):
                Figure index to update
            new_plot (mplwidget.Plot):
                New plotting data
            name (str or None):
                Updated name passed to the Main Viewer's plot list.  If None, the plot list name
                will not be updated.  Default is None.

        Returns:
            None
        """
        del self.figure_map[index]
        self.figure_map[index] = new_plot

        row = self.plot_list.get_item_row_by_path(index)
        self.plot_list.item(row).plot = new_plot
        if name is not None:
            self.plot_list.item(row).setText(name)


    # TODO: add figure name updates
    def update_figure_data(self, index: int, new_plot_data: Dict[str, Any]) -> None:
        """ Updates plot data within figure (doesn't create/need new plot object)

        Args:
            index (int):
                Figure index to update
            new_plot_data (Dict[str, Any]):
                Updated relevant plotting data
        """
        for key, value in new_plot_data.items():
            self.figure_map.get(index).plot_data[key] = value
        self.plot_list.refresh_current_plot()

    # TODO: Failing to remove figure or recomputing queue should explicitly throw error or warning
    def remove_figure(self, index: int) -> bool:
        """Remove figure from manager

        Args:
            index (int):
                Figure index to remove

        Returns:
            bool:
                true on successful removal, otherwise false
        """

        if not self.figure_map[index]:
            print(f'There is no figure to remove at index {index}...')
            return False

        if index > self.open_slots[-1]:
            # manually recompute open_slots from figure_map
            # this shouldn't happen, but just in case...
            print('The figure queue has malfunctioned! '
                  'Manually recomputing figure queue...')
            self._recompute_queue()

        del self.figure_map[index]
        self.figure_map[index] = None

        self.open_slots.insert(
            sum([d < index for d in self.open_slots]),
            index
        )

        self._trim_queue()

        row = self.plot_list.get_item_row_by_path(index)
        self.plot_list.delete_item(row)

        return True

    def remove_figures(self, indicies: Union[List[int], None] = None) -> bool:
        """Iteratively remove multiple figures

        Args:
            indicies (List[int]):
                indices of figures to remove

        Returns:
            bool:
                true on all successful removals, otherwise false
        """
        return all([self.remove_figure(index) for index in indicies])

    def _trim_queue(self):
        while len(self.open_slots) > 1:
            if self.open_slots[-2] == self.open_slots[-1] - 1:
                self.open_slots.pop()
            else:
                break

    # there might be a more efficient way of recomputing
    # the queue, but this shouldn't need to happen often
    # anyways...
    def _recompute_queue(self):
        self.open_slots = deque(
            [index
             for index in self.figure_map.keys()
             if self.figure_map[index] is None]
        )

        self._trim_queue()
