import arrow
from textual.containers import Container, Horizontal
from textual.widgets import Label

from ofscraper.classes.table.inputs.intergerinput import IntegerInput
import ofscraper.utils.settings as settings  # Reconnect to the source of truth


class TimeField(Container):
    DEFAULT_CSS = """
    TimeField{
    column-span:4;
    row-span:2;
    }

    TimeField Label{
    width:2fr;
    }

    .min_length,.max_length{
    width:1fr;
    }
    """

    def __init__(self, name: str) -> None:
        name = name.lower()
        super().__init__(id=name)
        self.filter_name = name
        self.timeconversions = [60 * 60, 60, 1]

    def compose(self):
        with Horizontal(id="minContainer"):
            yield Label("MinLength")
            yield IntegerInput(placeholder="Hour", classes="min_length", id="min_hour")
            yield IntegerInput(placeholder="Min", classes="min_length", id="min_minute")
            yield IntegerInput(placeholder="Sec", classes="min_length", id="min_second")
        with Horizontal(id="maxContainer"):
            yield Label("MaxLength")
            yield IntegerInput(placeholder="Hour", classes="max_length", id="max_hour")
            yield IntegerInput(placeholder="Min", classes="max_length", id="max_minute")
            yield IntegerInput(placeholder="Sec", classes="max_length", id="max_second")

    def on_mount(self):
        """
        Self-Aware Logic: Runs immediately after the inputs are drawn to the screen.
        Dynamically fetches "{name}_min" and "{name}_max" (e.g., length_min and length_max).
        """
        # Dynamically map the name (e.g., 'length') to settings (e.g., 'length_min')
        min_val = getattr(settings.get_settings(), f"{self.filter_name}_min", None)
        max_val = getattr(settings.get_settings(), f"{self.filter_name}_max", None)

        if min_val is not None:
            self.update_table_min(min_val)
        if max_val is not None:
            self.update_table_max(max_val)

    def update_table_val(self, val):
        self.update_table_min(val)
        self.update_table_max(val)

    def update_table_min(self, val):
        minLenthInputs = list(self.query_one("#minContainer").query(IntegerInput))
        if isinstance(val, int) or str(val).isnumeric():
            val = int(val)
            hours = val // 3600
            minutes = (val % 3600) // 60
            seconds = val % 60

        elif val != "N/A" and val != "N\\A":
            valArray = str(val).split(":")
            if len(valArray) == 3:
                hours, minutes, seconds = valArray
            elif len(valArray) == 2:
                hours, minutes, seconds = 0, valArray[0], valArray[1]
            else:
                hours, minutes, seconds = 0, 0, valArray[0]
        else:
            hours, minutes, seconds = 0, 0, 0
        for pack in zip(minLenthInputs, [hours, minutes, seconds]):
            pack[0].value = str(pack[1])

    def update_table_max(self, val):
        maxLenthInputs = list(self.query_one("#maxContainer").query(IntegerInput))
        if isinstance(val, int) or str(val).isnumeric():
            val = int(val)
            hours = val // 3600
            minutes = (val % 3600) // 60
            seconds = val % 60

        elif val != "N/A" and val != "N\\A":
            valArray = str(val).split(":")
            if len(valArray) == 3:
                hours, minutes, seconds = valArray
            elif len(valArray) == 2:
                hours, minutes, seconds = 0, valArray[0], valArray[1]
            else:
                hours, minutes, seconds = 0, 0, valArray[0]
        else:
            hours, minutes, seconds = 0, 0, 0
        for pack in zip(maxLenthInputs, [hours, minutes, seconds]):
            pack[0].value = str(pack[1])

    def reset(self):
        for ele in self.query(IntegerInput):
            ele.value = ""

    def _parse_duration_seconds(self, value):
        if not value or value in {"N\\A", "N/A"}:
            return 0
        parts = str(value).split(":")
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2]))
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(float(parts[1]))
            elif len(parts) == 1:
                return int(float(parts[0]))
        except (ValueError, TypeError):
            return 0
        return 0

    def compare(self, value):
        max_sec = (
            int(self.query_one("#max_hour").value or 0) * 3600
            + int(self.query_one("#max_minute").value or 0) * 60
            + int(self.query_one("#max_second").value or 0)
        )
        min_sec = (
            int(self.query_one("#min_hour").value or 0) * 3600
            + int(self.query_one("#min_minute").value or 0) * 60
            + int(self.query_one("#min_second").value or 0)
        )
        compare_sec = self._parse_duration_seconds(value)

        if min_sec == max_sec and min_sec == 0:
            return True
        elif max_sec == 0:
            return compare_sec >= min_sec
        elif min_sec == 0:
            return compare_sec <= max_sec
        else:
            return min_sec <= compare_sec <= max_sec


    @property
    def key(self):
        return self.id.replace("_input", "")
