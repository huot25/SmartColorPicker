import sublime, sublime_plugin, operator, time, fnmatch, os

color_index = {}
last_check = 0

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
		project_colors = [("#252525", 1), ("#313131", 1), ("#265874", 1), ("#987641", 1)]

		html += self.build_swatches(project_colors, max_row)
		html += "<div></div>"
		html += self.build_swatches(color_index, max_row)

		html += "<style>body{padding:0px; margin:2px;}</style>"
		self.view.show_popup(html, sublime.COOPERATE_WITH_AUTO_COMPLETE, on_navigate=self.handle_selected_color)

	def build_swatches(self, colors, max_row):
		html = ""
		for i, color in enumerate(colors):
			html += '<span style="background-color:{0}; margin:2px;"><a href="{0}" style="color:{0}; width:50px; height:50px; font-size:20px;">██</a></span> '.format(color[0])

			if(not (i+1) % max_row):
				html += "<div></div>"

		return html

class ColorIndexer():

	HEX_REGEX = "\#[a-f0-9]{3}(?:[a-f0-9]{3})?"

	def __init__(self, view):
		self.view = view

	def index_colors(self, force=False):
		global color_index
		global last_check
		check_interval = 20

		if ((time.time() - last_check) < check_interval) and not force:
			return

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

	def get_hex_colors(self):
		matches = self.view.find_all(self.HEX_REGEX, sublime.IGNORECASE)
		return matches

	def normalize_color(self, color):
		if (len(color) < 5):
			c = "#"
			for char in color.lstrip("#"):
				c += char +char

			color = c

		return color.upper()

	def index_matches(self, matches):
		self.show_message("Indexing colors")
		index = {}

		for hex_color in matches:
			hex_color = self.normalize_color(hex_color)

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
