"""base.py: OMF Project and base classes for its components"""
import json

import properties
import properties.extras


class BaseModel(properties.HasProperties):
    """BaseModel is a HasProperties subclass with schema

    When deserializing, this class prioritizes schema value over __class__
    to decide the class.
    """

    schema = ""

    def serialize(self, include_class=True, save_dynamic=False, **kwargs):
        output = super().serialize(include_class, save_dynamic, **kwargs)
        output.update({"schema": self.schema})
        return output

    @classmethod
    def __lookup_class(cls, schema):
        for class_name, class_value in cls._REGISTRY.items():
            if hasattr(class_value, "schema") and class_value.schema == schema:
                return class_name
        raise ValueError(f"schema not found: {schema}")

    @classmethod
    def deserialize(cls, value, trusted=False, strict=False, assert_valid=False, **kwargs):
        schema = value.pop("schema", None)
        if schema is not None:
            value["__class__"] = cls.__lookup_class(schema)
        return super().deserialize(value, trusted, strict, assert_valid, **kwargs)


class StringDateTime(properties.DateTime):
    """DateTime property validated to be a string"""

    def validate(self, instance, value):
        value = super().validate(instance, value)
        return self.to_json(value)


class BaseMetadata(properties.HasProperties):
    """Validated metadata properties for all objects"""

    date_created = StringDateTime(
        "Date object was created",
        required=False,
    )
    date_modified = StringDateTime(
        "Date object was modified",
        required=False,
    )


class ArbitraryMetadataDict(properties.Dictionary):
    """Custom property class for metadata dictionaries

    This property accepts JSON-compatible dictionary with any arbitrary
    fields. However, an additional :code:`metadata_class` is specified
    to validate specific fields.
    """

    @property
    def metadata_class(self):
        """HasProperties class to validate metadata fields against"""
        return self._metadata_class

    @metadata_class.setter
    def metadata_class(self, value):
        if not issubclass(value, properties.HasProperties):
            raise AttributeError("metadata_class must be HasProperites subclass")
        self._metadata_class = value  # pylint: disable=W0201

    def __init__(self, doc, metadata_class, **kwargs):
        self.metadata_class = metadata_class
        kwargs.update({"key_prop": properties.String("")})
        super().__init__(doc, **kwargs)

    def validate(self, instance, value):
        """Validate the dictionary and any property defined in metadata_class

        This also reassigns the dictionary after validation, so any
        coerced values persist.
        """
        new_value = super().validate(instance, value)
        filtered_value = properties.utils.filter_props(
            self.metadata_class,
            new_value,
        )[0]
        try:
            for key, val in filtered_value.items():
                new_value[key] = self.metadata_class._props[key].validate(instance, val)
        except properties.ValidationError as err:
            raise properties.ValidationError(
                "Invalid metadata: {}".format(err),
                reason="invalid",
                prop=self.name,
                instance=instance,
            ) from err
        try:
            json.dumps(new_value)
        except TypeError as err:
            raise properties.ValidationError(
                "Metadata is not JSON compatible",
                reason="invalid",
                prop=self.name,
                instance=instance,
            ) from err
        if not self.equal(value, new_value):
            setattr(instance, self.name, new_value)
        return value

    @property
    def info(self):
        """Description of the property, supplemental to the basic doc"""
        info = (
            "an arbitrary JSON-serializable dictionary, with certain keys "
            "validated against :class:`{cls} <{pref}.{cls}>`".format(
                cls=self.metadata_class.__name__,
                pref=self.metadata_class.__module__,
            )
        )
        return info


class ContentModel(BaseModel):
    """ContentModel is a model with name, description, and metadata"""

    name = properties.String(
        "Title of the object",
        default="",
    )
    description = properties.String(
        "Description of the object",
        default="",
    )
    metadata = ArbitraryMetadataDict(
        "Basic object metadata",
        metadata_class=BaseMetadata,
        default=dict,
    )
