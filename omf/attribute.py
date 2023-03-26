"""attribute.py: different ProjectElementAttribute classes"""
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


class ProjectElementAttribute(ContentModel):
    """Base class for attributes on elements."""

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

    @property
    def array(self):
        """Attribute subclasses should override array"""
        raise ValueError("Cannot access array of base ProjectElementAttribute")


class NumericAttribute(ProjectElementAttribute):
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


class VectorAttribute(ProjectElementAttribute):
    """Attribute with 2D or 3D vector values

    This attribute type cannot have a colormap, since you cannot map colormaps
    to vectors.
    """

    schema = "org.omf.v2.attribute.vector"

    array = ArrayInstanceProperty(
        "Numeric vectors at locations on a mesh (see location parameter); these vectors may be 2D or 3D",
        shape={("*", 2), ("*", 3)},
    )


class StringAttribute(ProjectElementAttribute):
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


class CategoryAttribute(ProjectElementAttribute):
    """Attribute of indices linked to category values

    To specify no data, index value in the array should be any value
    not present in the categories.
    """

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
