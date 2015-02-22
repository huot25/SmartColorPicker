# SmartColorPicker
Smart color picker plugin for Sublime Text 3. This plugin scan the current CSS file for hexadecimal color codes and create an index of the colors ordered by the nuber of times each is used.

## Installation
Sublime Text Version 3071 Required!
Currently the package is only available as a download from github but will eventually be available through package control. 

## Usage
The color index is created on activate, and the color picker can be displayed using the following keyboard command:

- Linux: `ctrl+alt+space`
- Windows: `ctrl+alt+space`
- OS X: `cmd+alt+space`

## Future Plans
- Include html, php, asp file types
- Scan entire project to build a project level index
- Allow users to exclude files and folders from indexing (libraries such Twitter bootstrap, or base css files)
- Allow user to define project colors which will always display at the top of the color list.
- If Sublime allows inline background colors in the future, I would like to display the color list in rows of 8 or so to make it easier to see a large collection of colors.