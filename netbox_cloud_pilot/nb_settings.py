from django import forms

__all__ = (
    "NbSettings",
    "NbSection",
    "Param",
)


class Base:
    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)

    def __getitem__(self, item):
        return getattr(self, item)

    def __str__(self):
        return f"{self.__class__.__name__} {self.__dict__}"

    def __repr__(self):
        class_name = self.__class__.__name__
        repr_args = ", ".join([f"{k}={repr(v)}" for k, v in self])
        return f"{class_name}({repr_args})"

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()


class Param(Base):
    def __init__(
        self,
        key: str,
        label: str,
        field=None,
        field_kwargs: dict = None,
        help_text: str = None,
        placeholder: str = None,
        required: bool = True,
        initial=None,
        choices=None,
    ):
        self.key = key
        self.label = label
        self.help_text = help_text
        self.required = required
        self.field = field or forms.CharField
        self.initial = initial
        self.choices = choices

        # Default field_kwargs if none provided
        default_kwargs = {"widget": forms.TextInput(attrs={"class": "form-control"})}

        # Update or set field_kwargs
        if field_kwargs is not None:
            widget = field_kwargs.get("widget")
            if widget and hasattr(widget, "attrs"):
                # Update the class attribute, retaining existing classes
                existing_classes = widget.attrs.get("class", "")
                widget.attrs["class"] = " ".join(filter(None, [existing_classes, "form-control"]))
            else:
                # If widget is not provided or doesn't have attrs, use the default
                field_kwargs.update(default_kwargs)
        else:
            field_kwargs = default_kwargs

        if placeholder:
            field_kwargs["widget"].attrs["placeholder"] = placeholder

        self.field_kwargs = field_kwargs


class NbSection(Base):
    def __init__(self, name: str | None, params: list[Param]):
        self.name = name
        self.params = params


class NbSettings(Base):
    def __init__(self, sections: list[NbSection]):
        self.sections = sections
