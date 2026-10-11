from ofscraper.classes.table.fields.numfield import NumField
import ofscraper.utils.settings as settings


class SizeMaxField(NumField):
    def on_input_changed(self, event):
        value = event.value if event.value else "0"
        args = settings.get_args()
        args.size_max = int(value)
        settings.update_args(args)


class SizeMinField(NumField):
    def on_input_changed(self, event):
        value = event.value if event.value else "0"
        args = settings.get_args()
        args.size_min = int(value)
        settings.update_args(args)
