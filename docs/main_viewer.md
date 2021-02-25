# Main Viewer

![](./pngs/blank_main_viewer.png)

When openend, AMP will display its main image viewer.  This window will contain figures generated
by plugins as well as direct images loaded in via the 'Open Cohort' menu option.

### Cohort Loading

To load a cohort of images into the viewer, find the `Open Cohort...` option under the `File`
section of the upper taskbar.

![](./pngs/open_cohort.png)

This will open a file explorer.  Navigate to the folder containing your images, select it, and 
click the `Open` button.

<div 
    style="
        border: 0px solid #35f;
        border-left-width: 6px;
        padding: 8px;
        margin-bottom: 8px;
        background-color: #acf;
        color: #000"
> 
    <b><i>Note</i></b>:  Cohorts can be loaded from any file depth less than 6
</div>

![](./pngs/cohort_file_explorer.png)

If the cohort was successfully loaded, you should now see a file tree within the `Files` section of
the main viewer.

Clicking on displayed checkboxes will add a figure displaying that image to the `Figures` section
of the viewer.

![](./pngs/viewing.png)

Figures within this section can be freely renamed, reordered, deleted, and unchecked.

![](./gifs/main_viewer_demo.gif)

### View Features

#### Contrast Adjustment

For dim images, contrast can be enhanced via the `Brightness and Contrast` adjustment tool within
the `Image` section of the upper taskbar.

![](./pngs/b_and_c.png)

To brighten the image, simply drag the `Max` slider towards the left.  It's recommended to enable
the `Locked` checkbox to preserve separate contrast settings for each figure.

<div 
    style="
        border: 0px solid #35f;
        border-left-width: 6px;
        padding: 8px;
        margin-bottom: 8px;
        background-color: #acf;
        color: #000"
> 
    <b><i>Note</i></b>:  This tool is under active development, so exact details on functionality
    are subject to change.
</div>

![](./gifs/b_and_c_demo.gif)

#### Breakout Windows

To move a figure to a separate window, press the `Breakout` button.

Deleting this window will move the figure back into the `Figures` list within the main viewer,
where it can be deleted via the `Delete` button.

***

▶️ *NEXT*: [Plugin Loading](./plugin_loading.md)

◀️ *PREVIOUS*: [Installation](./installation.md)