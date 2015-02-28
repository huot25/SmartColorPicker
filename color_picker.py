import sublime, sublime_plugin, operator, time, fnmatch, os, threading

color_index = {}
last_check = 0

def normalize_color(color):
	if (len(color) < 5):
		c = "#"
		for char in color.lstrip("#"):
			c += char +char

		color = c

	return color.upper()

class ColorCheckListener(sublime_plugin.EventListener):
	def on_activated_async(self, view):
		self.run(view, index_only=True, force=True)

	def on_selection_modified_async(self, view):
		self.run(view)

	def run(self, view, index_only=False, force=False):
		ColorIndexer(view).index_colors(force)

		if (index_only):
			return

		scopes = [
			"meta.property-value.css"
		]

		scope_name = view.scope_name(view.sel()[0].b)

		for scope in scopes:
			if (scope+'') in scope_name:
				if (scope == 'constant.other.color.rgb-value.css' or scope == 'meta.property-value.css') and '#' in view.substr(view.word(view.sel()[0])):
					view.run_command("display_color_picker")
					return

		view.hide_popup()

class DisplayColorPickerCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.show_color_picker()

	def handle_selected_color(self, color):
		line = self.view.line(self.view.sel()[0])
		pos = self.view.find("#", line.begin())
		self.view.sel().clear()
		self.view.sel().add(sublime.Region(pos.end(), pos.end()))

		self.view.run_command("insert", {"characters": color.lstrip("#")})
		self.view.hide_popup()

	def show_color_picker(self):
		global color_index
		max_row = 6
		html = ""
		project_helper = ProjectHelper(self.view)
		project_colors = project_helper.get_project_colors()

		html += '<span class="projectWrapper">'
		html += self.build_swatches(project_colors, max_row)
		html += "</span><div>&nbsp;</div>"
		html += self.build_swatches(color_index, max_row)

		html += "<style>body{padding:0px; margin:2px;} .projectWrapper{background:#99ff99, padding:10px;} a{margin:10px; }</style>"

		self.view.show_popup(html, sublime.COOPERATE_WITH_AUTO_COMPLETE, on_navigate=self.handle_selected_color)

	def build_swatches(self, colors, max_row):
		html = ""
		for i, color in enumerate(colors):
			html += '<a href="{0}" style="background-color:{0}; color:{0}; width:50px; height:50px; font-size:40px;">█</a>'.format(color[0])

			if(not (i+1) % max_row):
				html += "<div></div>"

		return html

class SetProjectColorsCommand(sublime_plugin.WindowCommand):
	def run(self):
		ProjectHelper(self.window.active_view()).set_colors()

class ColorIndexer(threading.Thread):

	HEX_REGEX = "\#[a-f0-9]{3}(?:[a-f0-9]{3})?"
	check_interval = 20
	color_index = []

	def __init__(self, view):
		threading.Thread.__init__(self)
		self.view = view
		self.force = False
		self.project_helper = ProjectHelper(view)
		self.check_interval = 20

	def index_colors(self, force=False):
		global last_check
		self.force = force

		if ((time.time() - last_check) < self.check_interval) and not force:
			return

		last_check = time.time()
		self.start()

	def run(self):
		global last_check
		global color_index

		files = self.select_files()
		matches = self.scan_files(files)

		color_index = self.index_matches(matches)

		last_check = time.time()
		self.show_message("Colors indexed!")

	def select_files(self):
		project = self.view.window().project_data();
		index_files = []
		file_ext = ["*.css", "*.html", "*.php"]

		for folder in project["folders"]:
			for root, dirs, files in os.walk(folder["path"]):
				for file in files:
					for pattern in file_ext:
						if fnmatch.fnmatch(file, pattern):
							 index_files.append(os.path.join(root, file))
							 break;

		return index_files

	def scan_files(self, files):
		import mmap, re
		matches = []
		for file in files:
			file_matches = []
			with open(file, "r+b") as f:
				mm = mmap.mmap(f.fileno(), 0)
				mm.seek(0)
				file_matches = re.findall(self.HEX_REGEX, mm.read().decode())
				matches.extend(file_matches)
				mm.close()
		return matches

	def index_matches(self, matches):
		self.show_message("Indexing colors")
		index = {}

		project_colors = self.project_helper.get_project_colors()

		for hex_color in matches:
			in_project = False
			hex_color = normalize_color(hex_color)

			for pc,i in project_colors:
				if hex_color == pc:
					in_project = True
					break

			if in_project:
				continue

			if (hex_color in index):
				index[hex_color] = int(index[hex_color] + 1)
			else:
				index[hex_color] = int(1)

		sorted_index = sorted(index.items(), key=operator.itemgetter(1), reverse=True)
		return sorted_index

	def show_message(self, message):
		msg = "Color Picker: " + message
		print (msg)
		sublime.status_message(msg)


class ProjectHelper():

	project_settings = {}

	def __init__(self, view):
		self.view = view
		self.project_data = self.view.window().project_data()

	def get_project_settings(self):
		if (not self.project_settings):
			self.project_settings = self.project_data.get("settings", {})

		return self.project_settings

	def get_project_colors(self):
		norm_colors = []
		project_colors = self.get_project_settings().get("project_colors", [])

		for color in project_colors:
			color = normalize_color(color)
			norm_colors.append((color, 1))

		return norm_colors

	def set_colors(self):
		project_colors = self.get_project_colors()

		color_list = []
		for color, i in project_colors:
			color_list.append(color)

		text = ", ".join(color_list)

		self.view.window().show_input_panel("Enter a comma seperated list of hexidecimal colors: ", text, self.store_colors, None, None)

	def store_colors(self, colors):
		if (colors == -1):
			return

		project_colors = []
		tmp_colors = [x.strip() for x in colors.split(",")]

		for color in tmp_colors:
			project_colors.append(normalize_color(color))

		if  not "settings" in self.project_data:
			self.project_data["settings"] = {}

		self.project_data["settings"]["project_colors"] = project_colors
		self.update_project_data()

	def update_project_data(self):
		self.view.window().set_project_data(self.project_data)
