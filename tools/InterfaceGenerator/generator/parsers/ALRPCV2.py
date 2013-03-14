"""ALRPCV2 parser.

Containser parser for ALRPCV2 XML format.

"""

import xml.etree.ElementTree

from generator import Model


class ParseError(Exception):

    """Parse error.

    This exception is raised when XML contains errors and can't be parsed.

    """

    pass


class Parser(object):

    """ALRPCV2 Parser."""

    def __init__(self):
        """Constructor."""
        self._types = {}

    def parse(self, filename):
        """Parse XML in ALRPCV2 format.

        Returns an instance of generator.Model.Interface containing parsed
        interface or raises ParseError if input XML contains errors
        and can't be parsed.

        Keyword arguments:
        filename -- name of input XML file.

        """

        tree = xml.etree.ElementTree.parse(filename)
        root = tree.getroot()

        if root.tag != "interface":
            raise ParseError("Invalid root tag: " + root.tag)

        enums = {}
        structs = {}
        functions = {}
        params = root.attrib

        self._types = {}

        for element in root:
            if element.tag == "enum":
                enum = self._parse_enum(element)
                self._add_item(enums, enum)
                self._add_type(enum)
            elif element.tag == "struct":
                struct = self._parse_struct(element)
                self._add_item(structs, struct)
                self._add_type(struct)
            elif element.tag == "function":
                function = self._parse_function(element)
                self._add_item(functions, function,
                               (function.function_id, function.message_type))
            else:
                raise ParseError("Unexpected element: " + element.tag)

        return Model.Interface(enums=enums, structs=structs,
                               functions=functions, params=params)

    @staticmethod
    def _add_item(items, item, key=None):
        if key is None:
            key = item.name

        if key in items:
            raise ParseError(type(item).__name__ + " '" + str(key) +
                             "' is declared more than once")
        items[key] = item

    def _add_type(self, _type):
        if _type.name in self._types:
            raise ParseError("Type '" + _type.name +
                             "' is declared as both struct and enum")

        self._types[_type.name] = _type

    def _parse_enum(self, element):
        params, subelements, attrib = self._parse_base_item(element)

        internal_scope = None
        for a in attrib:
            if a == "internal_scope":
                internal_scope = attrib[a]
            else:
                raise ParseError("Unexpected attribute '" + a +
                                 "' in enum '" + params["name"] + "'")
        params["internal_scope"] = internal_scope

        elements = {}
        for subelement in subelements:
            if subelement.tag == "element":
                self._add_item(elements, self._parse_enum_element(subelement))
            else:
                raise ParseError("Unexpected element '" + subelement.tag +
                                 "' in enum '" + params["name"] + "'")
        params["elements"] = elements

        return Model.Enum(**params)

    def _parse_struct(self, element):
        params, subelements, attrib = self._parse_base_item(element)

        if len(attrib) != 0:
            raise ParseError("Unexpected attributes for struct")

        members = {}
        for subelement in subelements:
            if subelement.tag == "param":
                self._add_item(members, self._parse_param(subelement))
            else:
                raise ParseError("Unexpected subelement '" + subelement.name +
                                 "' in struct '" + params["name"] + "'")
        params["members"] = members

        return Model.Struct(**params)

    def _parse_function(self, element):
        params, subelements, attrib = self._parse_base_item(element)

        function_id = None
        message_type = None
        platform = None

        for a in attrib:
            if a == "functionID":
                function_id = \
                    self._get_enum_element_for_function("FunctionID",
                                                        attrib[a])
            elif a == "messagetype":
                message_type = \
                    self._get_enum_element_for_function("messageType",
                                                        attrib[a])
            elif a == "platform":
                platform = attrib[a]
            else:
                raise ParseError("Unexpected attribute '" + a +
                                 "' in function '" + params["name"] + "'")

        params["function_id"] = function_id
        params["message_type"] = message_type
        params["platform"] = platform

        function_params = {}
        for subelement in subelements:
            if subelement.tag == "param":
                function_param = self._parse_function_param(subelement)
                if function_param.name in function_params:
                    raise ParseError("Parameter '" + function_param.name +
                                     "' is specified more than once" +
                                     " for function '" + params["name"] + "'")
                function_params[function_param.name] = function_param
            else:
                raise ParseError("Unexpected subelement '" + subelement.tag +
                                 "' in function '" + params["name"] + "'")
        params["params"] = function_params

        return Model.Function(**params)

    def _parse_base_item(self, element):
        params = {}

        description = []
        design_description = []
        issues = []
        todos = []
        subelements = []

        if "name" not in element.attrib:
            raise ParseError("Name is not specified for " + element.tag)

        params["name"] = element.attrib["name"]
        attrib = dict(element.attrib.items())
        del attrib["name"]

        for subelement in element:
            if subelement.tag == "description":
                description.append(self._parse_simple_element(subelement))
            elif subelement.tag == "designdescription":
                design_description.append(
                    self._parse_simple_element(subelement))
            elif subelement.tag == "todo":
                todos.append(self._parse_simple_element(subelement))
            elif subelement.tag == "issue":
                issues.append(self._parse_issue(subelement))
            else:
                subelements.append(subelement)

        params["description"] = description
        params["design_description"] = design_description
        params["issues"] = issues
        params["todos"] = todos

        return params, subelements, attrib

    @staticmethod
    def _parse_simple_element(element):
        if len(element) != 0:
            raise ParseError("Unexpected subelements in '" +
                             element.tag + "'")
        if len(element.attrib) != 0:
            raise ParseError("Unexpected attributes in '" +
                             element.tag + "'")
        return element.text if element.text is not None else ""

    @staticmethod
    def _parse_issue(element):
        if len(element) != 0:
            raise ParseError("Unexpected subelements in issue")
        if "creator" not in element.attrib:
            raise ParseError("No creator in issue")
        if len(element.attrib) != 1:
            raise ParseError("Unexpected attributes in issue")

        return Model.Issue(
            creator=element.attrib["creator"],
            value=element.text if element.text is not None else "")

    def _parse_enum_element(self, element):
        params, subelements, attrib = self._parse_base_item(element)

        if len(subelements) != 0:
            raise ParseError("Unexpected subelements in enum element")

        internal_name = None
        value = None
        for a in attrib:
            if a == "internal_name":
                internal_name = attrib[a]
            elif a == "value":
                try:
                    value = int(attrib[a])
                except:
                    raise ParseError("Invalid value for enum element: '" +
                                     attrib[a] + "'")
            else:
                raise ParseError("Unexpected attribute '" +
                                 a + "' in enum element")
        params["internal_name"] = internal_name
        params["value"] = value

        return Model.EnumElement(**params)

    def _parse_param(self, element):
        params, subelements, attrib = self._parse_param_base_item(element)

        if len(attrib) != 0:
            raise ParseError("Unknown attributes in param '" +
                             params["name"] + "'")

        if len(subelements) != 0:
            raise ParseError("Unknown subelements in param '" +
                             params["name"] + "'")

        return Model.Param(**params)

    def _parse_function_param(self, element):
        params, subelements, attrib = self._parse_param_base_item(element)

        params["platform"] = self._get_and_remove_attrib(attrib, "platform")

        default_value = None
        default_value_string = self._get_and_remove_attrib(attrib, "defvalue")
        if default_value_string is not None:
            param_type = params["param_type"]
            if type(param_type) is Model.Boolean:
                default_value = \
                    self._get_bool_from_string(default_value_string)
            elif type(param_type) is Model.Integer:
                try:
                    default_value = int(default_value_string)
                except:
                    raise ParseError("Invalid value for integer: '" +
                                     default_value_string + "'")
            elif type(param_type) is Model.Double:
                try:
                    default_value = float(default_value_string)
                except:
                    raise ParseError("Invalid value for float: '" +
                                     default_value_string + "'")
            elif type(param_type) is Model.String:
                default_value = default_value_string
            elif type(param_type) is Model.Enum or \
                    type(param_type) is Model.EnumSubset:
                if type(param_type) is Model.EnumSubset:
                    allowed_elements = param_type.allowed_elements
                else:
                    allowed_elements = param_type.elements
                if default_value_string not in allowed_elements:
                    raise ParseError("Default value '" + default_value_string +
                                     "' for parameter '" + params["name"] +
                                     "' is not a member of " +
                                     type(param_type).__name__ +
                                     "'" + params["name"] + "'")
                default_value = allowed_elements[default_value_string]
            else:
                raise ParseError("Default value specified for " +
                                 type(param_type).__name__)
        params["default_value"] = default_value

        if len(attrib) != 0:
            raise ParseError("Unexpected attributes in parameter '" +
                             params["name"] + "'")

        if len(subelements) != 0:
            raise ParseError("Unexpected subelements in parameter '" +
                             params["name"] + "'")

        return Model.FunctionParam(**params)

    def _parse_param_base_item(self, element):
        params, subelements, attrib = self._parse_base_item(element)

        params["is_mandatory"] = self._get_and_remove_optional_bool_attrib(
            attrib, "mandatory", True)

        param_type = None
        type_name = self._get_and_remove_attrib(attrib, "type")
        if type_name is None:
            raise ParseError("Type is not specified for parameter '" +
                             params["name"] + "'")
        if type_name == "Boolean":
            param_type = Model.Boolean()
        elif type_name == "Integer" or \
                type_name == "Float":
            min_value = self._get_and_remove_optional_number_attrib(
                attrib, "minvalue", int if type_name == "Integer" else float)
            max_value = self._get_and_remove_optional_number_attrib(
                attrib, "maxvalue", int if type_name == "Integer" else float)

            param_type = \
                (Model.Integer if type_name == "Integer" else Model.Double)(
                    min_value=min_value,
                    max_value=max_value)
        elif type_name == "String":
            max_length = self._get_and_remove_optional_number_attrib(
                attrib, "maxlength")
            param_type = Model.String(max_length=max_length)
        else:
            if type_name in self._types:
                param_type = self._types[type_name]
            else:
                raise ParseError("Unknown type '" + type_name + "'")

        if self._get_and_remove_optional_bool_attrib(attrib, "array", False):
            min_size = self._get_and_remove_optional_number_attrib(attrib,
                                                                   "minsize")
            max_size = self._get_and_remove_optional_number_attrib(attrib,
                                                                   "maxsize")
            param_type = Model.Array(element_type=param_type,
                                     min_size=min_size,
                                     max_size=max_size)

        base_type = \
            param_type.element_type if isinstance(param_type, Model.Array) \
            else param_type

        other_subelements = []
        for subelement in subelements:
            if subelement.tag == "element":
                if type(base_type) is not Model.Enum and \
                   type(base_type) is not Model.EnumSubset:
                    raise ParseError("Elements specified for parameter '" +
                                     params["name"] + "' of type " +
                                     type(base_type).__name__)
                if type(base_type) is Model.Enum:
                    base_type = Model.EnumSubset(
                        name=params["name"],
                        enum=base_type,
                        description=params["description"],
                        design_description=params["design_description"],
                        issues=params["issues"],
                        todos=params["todos"],
                        allowed_elements={})
                if "name" not in subelement.attrib:
                    raise ParseError(
                        "Element name is not specified for parameter '" +
                        params["name"] + "'")
                element_name = subelement.attrib["name"]
                if len(subelement.attrib) != 1:
                    raise ParseError("Unexpected attributes for element '" +
                                     element_name + "' of parameter '" +
                                     params["name"])
                if len(subelement.getchildren()) != 0:
                    raise ParseError("Unexpected subelements for element '" +
                                     element_name + "' of parameter '" +
                                     params["name"])
                if element_name in base_type.allowed_elements:
                    raise ParseError("Element '" + element_name +
                                     "' is specified more than once for" +
                                     " parameter '" + params["name"] + "'")
                if element_name not in base_type.enum.elements:
                    raise ParseError("Element '" + element_name +
                                     "' is not a member of enum '" +
                                     base_type.enum.name + "'")
                base_type.allowed_elements[element_name] = \
                    base_type.enum.elements[element_name]
            else:
                other_subelements.append(subelement)

        if isinstance(param_type, Model.Array):
            param_type.element_type = base_type
        else:
            param_type = base_type

        params["param_type"] = param_type

        return params, other_subelements, attrib

    def _get_and_remove_optional_bool_attrib(self, attrib, name, default):
        value = self._get_and_remove_attrib(attrib, name)

        if value is None:
            value = default
        else:
            value = self._get_bool_from_string(value)

        return value

    def _get_and_remove_optional_number_attrib(self, attrib, name, _type=int):
        value = self._get_and_remove_attrib(attrib, name)

        if value is not None:
            try:
                value = _type(value)
            except:
                raise ParseError("Invlaid value for " + _type.__name__ +
                                 ": '" + value + "'")

        return value

    @staticmethod
    def _get_and_remove_attrib(attrib, name):
        value = None

        if name in attrib:
            value = attrib[name]
            del attrib[name]

        return value

    @staticmethod
    def _get_bool_from_string(bool_string):
        value = None

        if bool_string in ['0', 'false']:
            value = False
        elif bool_string in ['1', 'true']:
            value = True
        else:
            raise ParseError("Invalid value for bool: '" +
                             bool_string + "'")

        return value

    def _get_enum_element_for_function(self, enum_name, element_name):
        if enum_name not in self._types:
            raise ParseError("Enumeration '" + enum_name +
                             "' must be declared before any function")

        enum = self._types[enum_name]

        if type(enum) is not Model.Enum:
            raise ParseError("'" + enum_name + "' is not an enumeration")

        if element_name not in enum.elements:
            raise ParseError("'" + element_name +
                             "' is not a member of enum '" + enum_name + "'")

        return enum.elements[element_name]
