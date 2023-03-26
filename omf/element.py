"""element.py: OMF element base class."""
import properties
import properties.extras

from .attribute import ProjectElementAttribute
from .base import ArbitraryMetadataDict, BaseMetadata, ContentModel


class ElementMetadata(BaseMetadata):
    """Validated metadata properties for Elements"""

    coordinate_reference_system = properties.String(
        "EPSG or Proj4 plus optional local transformation string",
        required=False,
    )
    color = properties.Color(
        "Solid element color",
        required=False,
    )
    opacity = properties.Float(
        "Element opacity",
        min=0,
        max=1,
        required=False,
    )


class ProjectElement(ContentModel):
    """Base class for all OMF elements

    ProjectElement subclasses must define their geometry.
    """

    attributes = properties.List(
        "Attributes defined on the element",
        prop=ProjectElementAttribute,
        required=False,
        default=list,
    )
    metadata = ArbitraryMetadataDict(
        "Element metadata",
        metadata_class=ElementMetadata,
        default=dict,
    )

    _valid_locations = None

    def location_length(self, location):
        """Return correct attribute length based on location"""
        raise NotImplementedError()

    @properties.validator
    def _validate_attributes(self):
        """Check if element is built correctly"""
        assert self._valid_locations, "ProjectElement needs _valid_locations"
        for i, attr in enumerate(self.attributes):
            if attr.location not in self._valid_locations:  # pylint: disable=W0212
                raise properties.ValidationError(
                    "Invalid location {loc} - valid values: {locs}".format(
                        loc=attr.location,
                        locs=", ".join(self._valid_locations),  # pylint: disable=W0212
                    )
                )
            valid_length = self.location_length(attr.location)
            if len(attr.array.array) != valid_length:
                raise properties.ValidationError(
                    "attributes[{index}] length {attrlen} does not match "
                    "{loc} length {meshlen}".format(
                        index=i,
                        attrlen=len(attr.array.array),
                        loc=attr.location,
                        meshlen=valid_length,
                    )
                )
        return True
