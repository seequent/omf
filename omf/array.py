"""array.py: array validation and serialisation utilities."""
import json
import uuid

import numpy as np
import properties

from .base import BaseModel


DATA_TYPE_LOOKUP_TO_NUMPY = {
    "Int8Array": np.dtype("int8"),
    "Uint8Array": np.dtype("uint8"),
    "Int16Array": np.dtype("int16"),
    "Uint16Array": np.dtype("uint16"),
    "Int32Array": np.dtype("int32"),
    "Uint32Array": np.dtype("uint32"),
    "Int64Array": np.dtype("int64"),
    "Uint64Array": np.dtype("uint64"),
    "Float32Array": np.dtype("float32"),
    "Float64Array": np.dtype("float64"),
    "BooleanArray": np.dtype("bool"),
}
DATA_TYPE_LOOKUP_TO_STRING = {value: key for key, value in DATA_TYPE_LOOKUP_TO_NUMPY.items()}


class Array(BaseModel):
    """Class to validate and serialize a 1D or 2D numpy array

    Data type, size, shape are computed directly from the array.

    Serializing and deserializing this class requires passing an additional
    keyword argument :code:`binary_dict` where the array binary is persisted.
    The serialized JSON includes array metadata and a UUID; this UUID
    is the key in the binary_dict.
    """

    schema = "org.omf.v2.array.numeric"

    array = properties.Array(
        "1D or 2D numpy array wrapped by the Array instance",
        shape={("*",), ("*", "*")},
        dtype=(int, float, bool),
        serializer=lambda *args, **kwargs: None,
        deserializer=lambda *args, **kwargs: None,
    )

    def __init__(self, array=None, **kwargs):
        super().__init__(**kwargs)
        if array is not None:
            self.array = array

    def __len__(self):
        return self.array.__len__()

    def __getitem__(self, i):
        return self.array.__getitem__(i)

    @properties.validator
    def _validate_data_type(self):
        if self.array.dtype not in DATA_TYPE_LOOKUP_TO_STRING:
            raise properties.ValidationError(
                "bad dtype: {} - Array must have dtype in {}".format(
                    self.array.dtype,
                    ", ".join([dtype.name for dtype in DATA_TYPE_LOOKUP_TO_STRING]),
                )
            )
        return True

    @properties.StringChoice("Array data type string", choices=list(DATA_TYPE_LOOKUP_TO_NUMPY))
    def data_type(self):
        """Array type descriptor, determined directly from the array"""
        if self.array is None:
            return None
        return DATA_TYPE_LOOKUP_TO_STRING.get(self.array.dtype, None)

    @properties.List(
        "Shape of the array",
        properties.Integer(""),
    )
    def shape(self):
        """Array shape, determined directly from the array"""
        if self.array is None:
            return None
        return list(self.array.shape)

    @properties.Integer("Size of array in bytes")
    def size(self):
        """Total size of the array in bytes, determined directly from the array"""
        if self.array is None:
            return None
        if self.data_type == "BooleanArray":  # pylint: disable=W0143
            return int(np.ceil(self.array.size / 8))
        return self.array.size * self.array.itemsize

    def serialize(self, include_class=True, save_dynamic=False, **kwargs):
        output = super().serialize(include_class=include_class, save_dynamic=True, **kwargs)
        binary_dict = kwargs.get("binary_dict", None)
        if binary_dict is not None:
            array_uid = str(uuid.uuid4())
            if self.data_type == "BooleanArray":  # pylint: disable=W0143
                array_binary = np.packbits(self.array, axis=None).tobytes()
            else:
                array_binary = self.array.tobytes()
            binary_dict.update({array_uid: array_binary})
            output.update({"array": array_uid})
        return output

    @classmethod
    def deserialize(cls, value, trusted=False, strict=False, assert_valid=False, **kwargs):
        binary_dict = kwargs.get("binary_dict", {})
        if not isinstance(value, dict):
            pass
        elif any(key not in value for key in ["shape", "data_type", "array"]):
            pass
        elif value["array"] in binary_dict:
            array_binary = binary_dict[value["array"]]
            array_dtype = DATA_TYPE_LOOKUP_TO_NUMPY[value["data_type"]]
            if value["data_type"] == "BooleanArray":
                int_arr = np.frombuffer(array_binary, dtype="uint8")
                bit_arr = np.unpackbits(int_arr)[: np.product(value["shape"])]
                arr = bit_arr.astype(array_dtype)
            else:
                arr = np.frombuffer(array_binary, dtype=array_dtype)
            arr = arr.reshape(value["shape"])
            return cls(arr)
        return cls()


class ArrayInstanceProperty(properties.Instance):
    """Instance property for OMF Array objects

    This is a custom :class:`Instance <properties.Instance>` property
    that has :code:`instance_class` set as :class:`Array <omf.array.Array>`.
    It exposes additional keyword arguments that further validate the
    shape and data type of the array.

    **Available keywords**:

    * **shape** - Valid array shape(s), as described by :class:`properties.Array`
    * **dtype** - Valid array dtype(s), as described by :class:`properties.Array`
    """

    def __init__(self, doc, **kwargs):
        if "instance_class" in kwargs:
            raise AttributeError("ArrayInstanceProperty does not allow custom instance_class")
        self.validator_prop = properties.Array(
            "",
            shape={("*",), ("*", "*")},
            dtype=(int, float, bool),
        )
        super().__init__(doc, instance_class=Array, **kwargs)

    @property
    def shape(self):
        """Required shape of the Array instance's array property"""
        return self.validator_prop.shape

    @shape.setter
    def shape(self, value):
        self.validator_prop.shape = value

    @property
    def dtype(self):
        """Required dtype of the Array instance's array property"""
        return self.validator_prop.dtype

    @dtype.setter
    def dtype(self, value):
        self.validator_prop.dtype = value

    def validate(self, instance, value):
        self.validator_prop.name = self.name
        value = super().validate(instance, value)
        if value.array is not None:
            value.array = self.validator_prop.validate(instance, value.array)
        return value

    @property
    def info(self):
        info = "{instance_info} with shape {shape} and dtype {dtype}".format(
            instance_info=super().info,
            shape=self.shape,
            dtype=self.dtype,
        )
        return info


class StringList(BaseModel):
    """Class to validate and serialize a large list of strings

    Data type, size, shape are computed directly from the list.

    Serializing and deserializing this class requires passing an additional
    keyword argument :code:`binary_dict` where the string list is persisted.
    The serialized JSON includes array metadata and a UUID; this UUID
    is the key in the binary_dict.
    """

    schema = "org.omf.v2.array.string"

    array = properties.List(
        "List of datetimes or strings",
        properties.String(""),
        serializer=lambda *args, **kwargs: None,
        deserializer=lambda *args, **kwargs: None,
    )

    def __init__(self, array=None, **kwargs):
        super().__init__(**kwargs)
        if array is not None:
            self.array = array

    def __len__(self):
        return self.array.__len__()

    def __getitem__(self, i):
        return self.array.__getitem__(i)

    @properties.StringChoice("List data type string", choices=["DateTimeArray", "StringArray"])
    def data_type(self):
        """Array type descriptor, determined directly from the array"""
        if self.array is None:
            return None
        try:
            properties.List("", properties.DateTime("")).validate(self, self.array)
        except properties.ValidationError:
            return "StringArray"
        return "DateTimeArray"

    @properties.List(
        "Shape of the string list",
        properties.Integer(""),
        min_length=1,
        max_length=1,
    )
    def shape(self):
        """Array shape, determined directly from the array"""
        if self.array is None:
            return None
        return [len(self.array)]

    @properties.Integer("Size of string list dumped to JSON in bytes")
    def size(self):
        """Total size of the string list in bytes"""
        if self.array is None:
            return None
        return len(json.dumps(self.array))

    def serialize(self, include_class=True, save_dynamic=False, **kwargs):
        output = super().serialize(include_class=include_class, save_dynamic=True, **kwargs)
        binary_dict = kwargs.get("binary_dict", None)
        if binary_dict is not None:
            array_uid = str(uuid.uuid4())
            binary_dict.update({array_uid: bytes(json.dumps(self.array), "utf8")})
            output.update({"array": array_uid})
        return output

    @classmethod
    def deserialize(cls, value, trusted=False, strict=False, assert_valid=False, **kwargs):
        binary_dict = kwargs.get("binary_dict", {})
        if not isinstance(value, dict):
            pass
        elif any(key not in value for key in ["shape", "data_type", "array"]):
            pass
        elif value["array"] in binary_dict:
            arr = json.loads(binary_dict[value["array"]].decode("utf8"))
            return cls(arr)
        return cls()
