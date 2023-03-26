.. _attributes:

Attributes
**********

All project elements include a list of `Attribute` objects. The base class defines
the attribute location ('vertices', 'faces', etc.) as well as the name, description,
metadata, and optional statuses for values that are null or invalid. The sub-classes
each extend that with an `array` property of a different type and any other details
needed to explain the values. See the class descriptions below for details.

Mapping attribute array values to a mesh is straightforward for unstructured meshes
(those defined by vertices, segments, triangles, etc); the order of the attribute
array corresponds to the order of the associated mesh parameter. For grid meshes,
however, mapping 1D attribute array to the 2D or 3D grid requires correctly ordered
ijk unwrapping.

Attribute Base Class
--------------------

.. autoclass:: omf.attribute.Attribute

Numeric Attribute
-----------------

.. autoclass:: omf.attribute.NumericAttribute

.. autoclass:: omf.attribute.ContinuousColormap

.. autoclass:: omf.attribute.DiscreteColormap

Vector Attribute
----------------

.. autoclass:: omf.attribute.VectorAttribute

Category Attribute
------------------

.. autoclass:: omf.attribute.CategoryAttribute

.. autoclass:: omf.attribute.CategoryColormap

String Attribute
----------------

.. autoclass:: omf.attribute.StringAttribute
