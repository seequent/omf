"""project.py: OMF project class."""
import properties

from .base import ArbitraryMetadataDict, BaseMetadata, ContentModel, StringDateTime
from .element import ProjectElement


class ProjectMetadata(BaseMetadata):
    """Validated metadata properties for Projects"""

    coordinate_reference_system = properties.String(
        "EPSG or Proj4 plus optional local transformation string",
        required=False,
    )
    author = properties.String(
        "Author of the project",
        required=False,
    )
    revision = properties.String(
        "Revision",
        required=False,
    )
    date = StringDateTime(
        "Date associated with the project data",
        required=False,
    )


class Project(ContentModel):
    """OMF Project for holding all elements and metadata

    Save these objects to OMF files with :meth:`omf.fileio.save` and
    load them with :meth:`omf.fileio.load`
    """

    schema = "org.omf.v2.project"

    elements = properties.List(
        "Project Elements",
        prop=ProjectElement,
        default=list,
    )
    metadata = ArbitraryMetadataDict(
        "Project metadata",
        metadata_class=ProjectMetadata,
        default=dict,
    )
    origin = properties.Vector3(
        "Origin for all elements in the project relative to the coordinate reference system",
        default=[0.0, 0.0, 0.0],
    )
