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
        if (val or "").lower() == "free":
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
        elif val_lower == "paid":
            return False
        try:
            maxvalue=float(self.query_one(f"#{self.filter_name}_max").value or 0)
            minvalue=float(self.query_one(f"#{self.filter_name}_min").value or 0)
            if not maxvalue and not minvalue:
                return True
            if not maxvalue:
                return float(value) >= minvalue
            if not minvalue:
                return float(value) <= maxvalue
            return float(value) >= minvalue and float(value) <= maxvalue
        except (ValueError, TypeError):
            return False

    
