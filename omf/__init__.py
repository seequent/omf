"""omf: API library for Open Mining Format file interchange format"""
from . import blockmodel
from .array import Array
from .attribute import (
    CategoryAttribute,
    NumericAttribute,
    StringAttribute,
    VectorAttribute,
)
from .colormap import CategoryColormap, ContinuousColormap, DiscreteColormap
from .composite import Composite
from .fileio import __version__, load, save
from .lineset import LineSet
from .pointset import PointSet
from .project import Project
from .surface import Surface, TensorGridSurface
from .texture import ProjectedTexture, UVMappedTexture

__author__ = "Global Mining Guidelines Group"
__license__ = "MIT License"
__copyright__ = "Copyright 2021 Global Mining Guidelines Group"
