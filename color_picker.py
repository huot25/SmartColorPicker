import sublime, sublime_plugin, operator, time
from glob import glob

color_index = {}
last_check = 0

class ColorCheckListener(sublime_plugin.EventListener):
	def on_activated_async(self, view):
		if (view.file_name().endswith("css")):
			view.run_command("select_hex_colors")

class SelectHexColorsCommand(sublime_plugin.TextCommand):

	HEX_REGEX = "\#[a-f0-9]{3}(?:[a-f0-9]{3})?"

	def run(self, edit):
		global color_index
		global last_check

		check_interval = 30

		if ((time.time() - last_check) < check_interval):
			return

		matches = self.get_hex_colors()
		color_index = self.index_matches(matches)
		last_check = time.time()
		print ("Color Picker: Colors indexed")

	def get_hex_colors(self):
		matches = self.view.find_all(self.HEX_REGEX, sublime.IGNORECASE)
		return matches

	def index_matches(self, matches):
		index = {}

		print ("Color Picker: Indexing colors")
		for match in matches:
			hex_color = self.view.substr(match)

			#convert short hand colors to full values
			if (len(hex_color) < 7):
				hex_color = "#" + hex_color[1:]*2

			#record the number of times the color was used
			if (hex_color in index):
				index[hex_color] = int(index[hex_color] + 1)
			else:
				index[hex_color] = int(1)

		#sort based on value
		sorted_index = sorted(index.items(), key=operator.itemgetter(1), reverse=True)
		return sorted_index


class DisplayColorPickerCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.show_color_picker()

	def handle_selected_color(self, color):
		self.view.run_command("insert", {"characters": color})
		self.view.hide_popup()

	def show_color_picker(self):
		global color_index
		max_items = 10
		html = ""

		for i, color in enumerate(color_index):
			if (i > max_items):
				break

			html += '<div style="background-color: #cccccc;"><div style="display:inline-block; background-color:{0}; margin:2px;"><a href="{0}" style="color:{0}; font-size:20px; font-family:courier;">aa</a></div></div>'.format(color[0])

		self.view.show_popup(html, on_navigate=self.handle_selected_color)
		
