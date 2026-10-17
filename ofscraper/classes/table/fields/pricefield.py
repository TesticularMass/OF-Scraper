from textual.containers import Horizontal
from ofscraper.classes.table.inputs.intergerinput import IntegerInput


class PriceField(Horizontal):
    DEFAULT_CSS = """
    PriceField{
    column-span:4;
    row-span:1;
    }

   PriceField IntegerInput {
    width:1fr;
    }

    
"""
    def __init__(self, name: str) -> None:
        name = name.lower()
        super().__init__(id=name)
        self.filter_name = name

    def compose(self):
        yield IntegerInput(placeholder="Min Price", id=f"{self.filter_name}_min")
        yield IntegerInput(placeholder="Max Price", id=f"{self.filter_name}_max")


    def update_table_val(self, val):
        if val.lower() == "free":
            val = "0"
        for ele in self.query(IntegerInput):
            ele.value = val

    def reset(self):
        for ele in self.query(IntegerInput):
            ele.value = ""
    def compare(self, value):
        val_lower = str(value).lower()
        if val_lower == "free":
            value = "0"
        max_str = self.query_one(f"#{self.filter_name}_max").value
        min_str = self.query_one(f"#{self.filter_name}_min").value
        has_max = max_str != "" and max_str is not None
        has_min = min_str != "" and min_str is not None
        if not has_max and not has_min:
            return True
        val_float = float(value)
        if has_max and not has_min:
            return val_float <= float(max_str)
        if has_min and not has_max:
            return val_float >= float(min_str)
        return float(min_str) <= val_float <= float(max_str)

    
