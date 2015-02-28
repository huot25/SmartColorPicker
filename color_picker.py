import sublime, sublime_plugin, operator, time, fnmatch, os, threading, re, mmap

color_index = {}
last_check = 0
HEX_REGEX = "\#[a-f0-9]{3}(?:[a-f0-9]{3})?"

def normalize_color(color):
	if (len(color) < 5):
		c = "#"
		for char in color.lstrip("#"):
			c += char +char

		color = c

	return color.upper()

def is_valid_color(color):
	global HEX_REGEX
	matches = re.findall(HEX_REGEX, color, re.IGNORECASE)

	return (len(matches) > 0)


class ColorCheckListener(sublime_plugin.EventListener):
	def on_activated_async(self, view):
		self.run(view, index_only=True, force=True)

	def on_selection_modified_async(self, view):
		self.run(view)

	def run(self, view, index_only=False, force=False):
		ColorIndexer(view).index_colors(force)

		if (index_only):
			return

		scopes = [ "meta.property-value.css" ]
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

		html += self.build_swatches(project_colors, max_row)
		html += "<div>&nbsp;</div>"
		html += self.build_swatches(color_index, max_row)
		html += "<style>body{padding:0px; margin:2px;} </style>"

		self.view.show_popup(html, sublime.COOPERATE_WITH_AUTO_COMPLETE, on_navigate=self.handle_selected_color)

	def build_swatches(self, colors, max_row):
		html = ""
		for i, color in enumerate(colors):
			html += '<a href="{0}" style="background-color:{0}; color:{0}; font-size:40px;">█</a>'.format(color[0])

			if((i+1) % max_row == 0):
				html += "<div></div>"

		return html

class SetProjectColorsCommand(sublime_plugin.WindowCommand):
	def run(self):
		ProjectHelper(self.window.active_view()).set_colors()

class ExcludeFromIndexCommand(sublime_plugin.WindowCommand):
	def run(self, paths=[]):
		files = []
		folders = []

		project_helper = ProjectHelper(self.window.active_view())
		excl_files = project_helper.get_excluded_files()
		excl_folders = project_helper.get_excluded_folders()

		for path in paths:
			if os.path.isdir(path):
				if( path in excl_folders):
					continue

				folders.append(path)

			if os.path.isfile(path):
				if( path in excl_files):
					continue
				
				files.append(path)

		folders = excl_folders + folders
		files = excl_files + files

		project_helper.set_excluded_folders(folders)
		project_helper.set_excluded_files(files)

	def is_enabled(self, paths=[]):
		project_helper = ProjectHelper(self.window.active_view())
		excl_files = project_helper.get_excluded_files()
		excl_folders = project_helper.get_excluded_folders()
		excluded = excl_files + excl_folders
		
		return any(t not in excluded for t in paths)

class IncludeIndexCommand(sublime_plugin.WindowCommand):
	def run(self, paths=[]):
		files = []
		folders = []
		for path in paths:
			if os.path.isdir(path):
				folders.append(path)
			if os.path.isfile(path):
				files.append(path)

		project_helper = ProjectHelper(self.window.active_view())

		excl_files = project_helper.get_excluded_files()
		excl_folders = project_helper.get_excluded_folders()

		for path in paths:
			if (path in excl_files):
				excl_files.remove(path)

			if (path in excl_folders):
				excl_folders.remove(path)

		project_helper.set_excluded_folders(excl_folders)
		project_helper.set_excluded_files(excl_files)


	def is_enabled(self, paths=[]):
		project_helper = ProjectHelper(self.window.active_view())
		excl_files = project_helper.get_excluded_files()
		excl_folders = project_helper.get_excluded_folders()
		excluded = excl_files + excl_folders
		
		return any(t in excluded for t in paths)


class ColorIndexer(threading.Thread):

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
		project_helper = ProjectHelper(self.view)
		project = project_helper.project_data
		exlc_folders = project_helper.get_excluded_folders()
		exlc_files = project_helper.get_excluded_files()

		index_files = []
		file_ext = ["*.css", "*.html", "*.php"]

		for folder in project["folders"]:
			for root, dirs, files in os.walk(folder["path"]):
				if root in exlc_folders:
					continue

				for file in files:
					if os.path.join(root, file) in exlc_files:
						continue

					for pattern in file_ext:
						if fnmatch.fnmatch(file, pattern):
							 index_files.append(os.path.join(root, file))
							 break;

		return index_files

	def scan_files(self, files):
		global HEX_REGEX
		matches = []
		for file in files:
			file_matches = []
			with open(file, "r+b") as f:
				mm = mmap.mmap(f.fileno(), 0)
				mm.seek(0)
				file_matches = re.findall(HEX_REGEX, mm.read().decode())
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

	def get_excluded_folders(self):
		return self.get_project_settings().get("excluded_folders", [])

	def set_excluded_folders(self, folders):
		settings = self.get_project_settings()
		settings["excluded_folders"] = folders
		self.project_data["settings"] = settings
		self.update_project_data()

	def get_excluded_files(self):
		return self.get_project_settings().get("excluded_files", [])

	def set_excluded_files(self, files):
		settings = self.get_project_settings()
		settings["excluded_files"] = files
		self.project_data["settings"] = settings
		self.update_project_data()

	def set_colors(self, text=""):
		if not len(text):
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
			color = normalize_color(color)
			if not is_valid_color(color):
				sublime.error_message("One or more of your colors is invalid!")
				self.set_colors(colors)
				return

			project_colors.append(color)

		if  not "settings" in self.project_data:
			self.project_data["settings"] = {}

		self.project_data["settings"]["project_colors"] = project_colors
		self.update_project_data()

	def update_project_data(self):
		self.view.window().set_project_data(self.project_data)


