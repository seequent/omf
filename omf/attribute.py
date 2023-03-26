"""attribute.py: OMF element attribute classes."""
import numpy as np
import properties

from .array import ArrayInstanceProperty, StringList
from .base import ArbitraryMetadataDict, BaseMetadata, ContentModel
from .colormap import CategoryColormap, ContinuousColormap, DiscreteColormap


class AttributeMetadata(BaseMetadata):
    """Validated metadata properties for Attributes"""

    units = properties.String(
        "Units of attribute values",
        required=False,
    )


class Attribute(ContentModel):
    """Base class for attributes on elements.

    Sub-classes will define attributes with different value types. The common parts here are the
    `metadata`, `status`, and `status_messages` properties.

    The `status` property is used to mark attribute values as null or otherwise invalid. It may be
    omitted if all attribute values are valid, otherwise contains an unsigned integer status for
    each value in the attribute array. Invalid values should remain in the attribute array so the
    two arrays are always the same length. Fill with zero, NaN, or an empty string as you prefer.

    A zero status indicates the value is valid, one indicates a null value, and higher statuses
    refer to one of the messages in the `status_messages` property to describe *why* a value is
    invalid. The content of the error messages is left up to the application writing the data,
    for example:

    .. code::

        attr.status_messages = {
            2: "Estimator did not find enough points",
            3: "Calculation divided by zero",
        }

    When there aren't any messages `status` can be a boolean array to save space. If all values are
    valid then both `status` and `status_messages` may be omitted.
    """

    location = properties.StringChoice(
        "Location of the attribute on the element",
        choices=(
            "vertices",
            "segments",
            "faces",
            "cells",
            "parent_blocks",
            "subblocks",
            "elements",
        ),
    )
    metadata = ArbitraryMetadataDict(
        "Attribute metadata",
        metadata_class=AttributeMetadata,
        default=dict,
    )
    status = ArrayInstanceProperty(
        "Array containing a boolean or integer status for each attribute value, false/zero means valid, "
        "true/non-zero means invalid",
        shape=("*",),
        dtype=(int, bool),
        required=False,
    )
    status_messages = properties.Dictionary(
        "A mapping for statuses greater than one to an error message",
        key_prop=properties.Integer(""),
        value_prop=properties.String(""),
        observe_mutations=True,
        required=False,
    )

    @properties.validator("status_messages")
    def _validate_status_messages(self, change):
        for status, message in change["value"].items():
            if status == 0:
                raise properties.ValidationError(
                    "status 0 is reserved for 'valid'", prop="status_messages", instance=self
                )
            if status == 1:
                raise properties.ValidationError(
                    "status 1 is reserved for 'null'", prop="status_messages", instance=self
                )
            if status < 0:
                raise properties.ValidationError("statuses can't be negative", prop="status_messages", instance=self)
            if not message.strip():
                raise properties.ValidationError(
                    "status messages can't be empty or blank", prop="status_messages", instance=self
                )

    @properties.validator
    def _validate_all_status_attrs(self):
        if self.status is None:
            return
        status = self.status.array
        if status.min() < 0:
            raise properties.ValidationError("statuses can't be negative", prop="status", instance=self)
        msgs = self.status_messages or {}
        valid = list(msgs.keys())
        valid += [0, 1]
        miss_mask = np.isin(status, np.array(valid), invert=True)
        if miss_mask.any():
            missing = np.unique(status[miss_mask])
            text = ", ".join(str(v) for v in missing[:5])
            if len(missing) > 5:
                text += ", ..."
            if len(missing) == 1:
                raise properties.ValidationError(
                    f"status without error string: {text}", prop="status_messages", instance=self
                )
            raise properties.ValidationError(
                f"{len(missing)} statuses without error strings: {text}", prop="status_messages", instance=self
            )
        if len(self.status) != len(self.array):
            raise properties.ValidationError(
                f"status should have length {len(self.array)} to match array, not {len(self.status)}",
                prop="status",
                instance=self,
            )

    def valid_mask(self):
        """Returns a boolean array that is true for valid values, or None if all are valid."""
        if self.status is None:
            return None
        mask = self.status.array == 0
        return None if mask.all() else mask

    def valid_values(self):
        """Returns an array of only the valid values.

        The result will always be a copy so it's safe to modify it. Returns `None` if the `array`
        property has not been set.
        """
        return self.valid_values_and_mask()[0]

    def valid_values_and_mask(self):
        """Returns the valid values and mask.

        This is the same as calling `valid_mask()` and `valid_values()` just more efficient.
        """
        if self.array is None:
            return None, None
        mask = self.valid_mask()
        arr = self.array.array
        if isinstance(arr, list):
            values = arr[:] if mask is None else [string for string, valid in zip(arr, mask) if valid]
        else:
            values = arr.copy() if mask is None else arr[mask]
        return values, mask


class NumericAttribute(Attribute):
    """Attribute with scalar values and optional continuous or discrete colormap"""

    schema = "org.omf.v2.attribute.numeric"

    array = ArrayInstanceProperty(
        "Numeric values at locations on a mesh (see location parameter); these values must be scalars",
        shape=("*",),
    )
    colormap = properties.Union(
        "colormap associated with the attribute",
        [ContinuousColormap, DiscreteColormap],
        required=False,
    )


class VectorAttribute(Attribute):
    """Attribute with 2D or 3D vector values

    This attribute type cannot have a colormap, since you cannot map colormaps
    to vectors.
    """

    schema = "org.omf.v2.attribute.vector"

    array = ArrayInstanceProperty(
        "Numeric vectors at locations on a mesh (see location parameter); these vectors may be 2D or 3D",
        shape={("*", 2), ("*", 3)},
    )


class StringAttribute(Attribute):
    """Attribute with a list of strings or datetimes

    This attribute type cannot have a colormap; to use colors with strings,
    use :class:`omf.attribute.CategoryAttribute` instead.
    """

    schema = "org.omf.v2.attribute.string"

    array = properties.Instance(
        "String values at locations on a mesh (see "
        "location parameter); these values may be DateTimes or "
        "arbitrary strings",
        StringList,
    )


class CategoryAttribute(Attribute):
    """Attribute of indices linked to category values."""

    schema = "org.omf.v2.attribute.category"

    array = ArrayInstanceProperty(
        "indices into the category values for locations on a mesh",
        shape=("*",),
        dtype=int,
    )
    categories = properties.Instance(
        "categories into which the indices map",
        CategoryColormap,
    )
