import os
import re
import xml.etree.ElementTree as ET

import inspect
import importlib

# utility script for parsing .ui files for type information

# collect ui files
ui_files = [file for file in os.listdir() if file.endswith('.ui')]

# collect .py files
py_files = [file for file in os.listdir() if file.endswith('.py')]

# pair ui with py files (ui CamelCase to py snake_case)
pairs = []
for ui_file in ui_files:
    for py_file in py_files:
        if py_file.split('.')[0] == re.sub(r'(?<!^)(?=[A-Z])', '_', ui_file.split('.')[0]).lower():
            pairs.append((ui_file, py_file))
            break

# parse ui file and create stub file
for ui_file, py_file in pairs:
    with open(py_file, 'r') as f:
        py_data = f.readlines()

    tree = ET.parse(ui_file)
    root = tree.getroot()

    # collect custom classes and handle imports
    custom_classes = [cust[0].text for cust in root.findall('.//customwidget')]
    if 'start custom imports' in py_data[0]:
        while 'end custom imports' not in py_data[0]:
            del py_data[0]
        del py_data[0]

    py_data.insert(0, '# end custom imports - DO NOT MANUALLY EDIT ABOVE\n')
    for cc in custom_classes:
        for h_file in py_files:
            all_classes = [
                obj
                for obj in inspect.getmembers(importlib.import_module(h_file.split('.')[0]))
                if inspect.isclass(obj[1]) and obj[1].__module__ == h_file.split('.')[0]
            ]
            if all_classes:
                all_names, all_classes = zip(*all_classes)
                if cc in all_names:
                    py_data.insert(
                        0,
                        f'from {all_classes[cc == all_names].__module__} import {cc}\n'
                    )
                    break
    py_data.insert(0, '# start custom imports - DO NOT MANUALLY EDIT BELOW\n')

    # create stub type for all widgets
    init_line_idx = [idx for idx, line in enumerate(py_data) if '__init__' in line][0]
    if 'start typedef' in py_data[init_line_idx + 1]:
        while 'end typedef' not in py_data[init_line_idx + 1]:
            del py_data[init_line_idx + 1]
        del py_data[init_line_idx + 1]

    py_data.insert(init_line_idx + 1, '        # end typedef - DO NOT MANUALLY EDIT ABOVE\n')
    for elem in root.findall('.//widget'):
        # handle non customs
        if elem.get('class') not in custom_classes + ['QMainWindow']:
            py_data.insert(
                init_line_idx + 1,
                f"        self.{elem.get('name')}: QtWidgets.{elem.get('class')}\n"
            )
        elif elem.get('class') in custom_classes:
            py_data.insert(
                init_line_idx + 1,
                f"        self.{elem.get('name')}: {elem.get('class')}\n"
            )
    py_data.insert(init_line_idx + 1, '        # start typedef - DO NOT MANUALLY EDIT BELOW\n')
    with open(py_file, 'w') as f:
        f.writelines(py_data)
