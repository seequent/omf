"""colormap.py: color-map classes used by the different types of attributes"""
import numpy as np
import properties

from .array import ArrayInstanceProperty
from .base import ContentModel


class ContinuousColormap(ContentModel):
    """Color gradient with min/max values, used with NumericAttribute

    When this colormap is applied to a numeric attribute the attribute
    values between the limits are colored based on the gradient values.
    Any attribute value below and above the limits are colored with the
    first and last gradient values, respectively.

    .. code::

      #   gradient
      #
      #     RGB4 -                   x - - - - - - ->
      #     RGB3 -                  /
      #     RGB2 -                 /
      #     RGB1 -                /
      #     RGB0 -  <- - - - - - x
      #             <------------|---|--------------> attribute values
      #                          limits
    """

    schema = "org.omf.v2.colormap.scalar"

    gradient = ArrayInstanceProperty(
        "N x 3 Array of RGB values between 0 and 255 which defines the color gradient",
        shape=("*", 3),
        dtype=int,
    )
    limits = properties.List(
        "Attribute range associated with the gradient",
        prop=properties.Float(""),
        min_length=2,
        max_length=2,
        default=properties.undefined,
    )

    @properties.validator("gradient")
    def _check_gradient_values(self, change):
        """Ensure gradient values are all between 0 and 255"""
        arr = change["value"].array
        if arr is None:
            return
        arr_uint8 = arr.astype("uint8")
        if not np.array_equal(arr, arr_uint8):
            raise properties.ValidationError("Gradient must be an array of RGB values between 0 and 255")
        change["value"].array = arr_uint8

    @properties.validator("limits")
    def _check_limits_on_change(self, change):
        """Ensure limits are valid"""
        if change["value"][0] > change["value"][1]:
            raise properties.ValidationError("Colormap limits[0] must be <= limits[1]")


class DiscreteColormap(ContentModel):
    """Colormap for grouping discrete intervals of NumericAttribute

    This colormap creates n+1 intervals where n is the length of end_points.
    Attribute values between -inf and the first end point correspond to
    the first color; attribute values between the first and second end point
    correspond to the second color; and so on until attribute values between
    the last end point and inf correspond to the last color.

    The end_inclusive property dictates if attribute values that equal the
    end point are in the lower interval (end_inclusive is True) or the upper
    interval (end_inclusive is False).

    .. code::

      #   colors
      #
      #    RGB2                         x - - - - ->
      #
      #    RGB1                 x - - - o
      #
      #    RGB0    <- - - - - - o
      #
      #            <------------|--------|------------> attribute values
      #                          end_points
    """

    schema = "org.omf.v2.colormap.discrete"

    end_points = properties.List(
        "Attribute values associated with edge of color intervals",
        prop=properties.Float(""),
        default=properties.undefined,
    )
    end_inclusive = properties.List(
        "True if corresponding end_point is included in lower interval; False if end_point is in upper interval",
        prop=properties.Boolean(""),
        default=properties.undefined,
    )
    colors = properties.List(
        "Colors for each interval",
        prop=properties.Color(""),
        min_length=1,
        default=properties.undefined,
    )

    @properties.validator
    def _validate_lengths(self):
        if len(self.end_points) != len(self.end_inclusive):
            pass
        elif len(self.colors) == len(self.end_points) + 1:
            return True
        raise properties.ValidationError(
            "Discrete colormap colors length must be one greater than end_points and end_inclusive values"
        )

    @properties.validator("end_points")
    def _validate_end_points_monotonic(self, change):
        for i in range(len(change["value"]) - 1):
            diff = change["value"][i + 1] - change["value"][i]
            if diff < 0:
                raise properties.ValidationError("end_points must be monotonically increasing")


class CategoryColormap(ContentModel):
    """Legends to be used with CategoryAttribute

    Every index in the CategoryAttribute array must correspond to a string
    value (the "category") and may additionally correspond to a color.

    .. code::

      #  values  colors
      #
      #    --     RGB2                          x
      #
      #    --     RGB1            x
      #
      #    --     RGB0       x
      #
      #                      |    |             |   <- attribute values
      #                          indices
    """

    schema = "org.omf.v2.colormap.category"

    indices = properties.List(
        "indices corresponding to CategoryAttribute array values",
        properties.Integer(""),
    )
    values = properties.List(
        "values for mapping indexed attribute",
        properties.String(""),
    )
    colors = properties.List(
        "colors corresponding to values",
        properties.Color(""),
        required=False,
    )

    @properties.validator
    def _validate_lengths(self):
        """Validate indices, values, and colors are all the same length"""
        if len(self.indices) != len(self.values):
            pass
        elif self.colors is None or len(self.colors) == len(self.values):
            return True
        raise properties.ValidationError("Legend colors and values must be the same length")
