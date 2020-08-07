from collections import deque

# prefilling dictionary prevents slow rehashing
MAX_FIGS = 64


class FigureManager(object):
    def __init__(self, plot_list):
        self.figure_map = dict.fromkeys(range((MAX_FIGS * 3) // 2))
        self.open_slots = deque([0])

        self.plot_list = plot_list

    def get_figure(self, index):
        return self.figure_map[index]

    def add_figure(self, plot_object):

        condition = len(self.open_slots) == 1

        index = self.open_slots[0] if condition else self.open_slots.popleft()

        if index in range(MAX_FIGS-10, MAX_FIGS):
            print(f'Approaching maximum figure limit, {MAX_FIGS}')
        elif index >= MAX_FIGS:
            print(f'Maximum figure limit, {MAX_FIGS} has been reached. '
                  f'No further figures were added...')
            return None

        self.figure_map[index] = plot_object
        self.open_slots[0] += int(condition)

        name = f'Figure {index}'

        self.plot_list.addItem(
            name,
            plot_object,
            index
        )

        row = self.plot_list.getItemRowByPath(index)
        self.plot_list.setCurrentRow(row)

        return index

    def update_figure(self, index, new_plot):
        del self.figure_map[index]
        self.figure_map[index] = new_plot

        row = self.plot_list.getItemRowByPath(index)
        self.plot_list.item(row).plot = new_plot

    def remove_figure(self, index):

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

        row = self.plot_list.getItemRowByPath(index)
        self.plot_list.deleteItem(row)

        return True

    def remove_figures(self, indicies=None):
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
