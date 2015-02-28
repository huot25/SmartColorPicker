# SmartColorPicker
Smart color picker plugin for Sublime Text 3. This plugin scan the current CSS file for hexadecimal color codes and create an index of the colors ordered by the number of times each is used.

***This plugin is still under development!

## Installation
Sublime Text Build 3072 Required!
Currently the package is only available as a download from github but will eventually be available through package control.

## Usage
The color index is created on activate, and the color picker is displayed when the "#" is entered in a css file.

![SmartColorPicker](/smart_color_picker.png)

###Project Colors
To add project colors which will be displayed at the top of the color list, simply execute the "Smart Color Picker: Set Project Colors" command to display an input panel which accepts a comma delimited list of hexidecimal colors. These colors will be displayed at the top of the color swatches and will not be included in the list of indexed colors below.

## Future Plans
- Include html, php, asp file types
- Allow users to exclude files and folders from indexing (libraries such Twitter bootstrap, or base css files)
- Create a method to import Adobe .ase color palettes downloaded from Kuler or exported from Adobe product.
- Create plugin settings to adjust some settings such as indexing frequency and number of colors per line in tooltip.