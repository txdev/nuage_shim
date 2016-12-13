API Model
=========

Schema Definition
-----------------

The schema exposes two types of fields. Fixed fields, which have a declared
name, and Patterned fields, which declare a regex pattern for the field name.
Patterned fields can have multiple occurrences as long as each has a unique
name.  Each field will have a value that is defined as a primitive type or as
an JSON object.  The JSON objects are very similar to the Schema Object found
in Swagger.  However, some extensions are added and only a small subset of the
properties are supported.  

Primitive  Data Types
---------------------

.. list-table:: 
   :widths: 15 20 30
   :header-rows: 1

   * - Type
     - Description
     - Associated Properties
   * - integer 
     - Integer number 
     - - format: int32, int64  (default int32)
       - min: *integer*
       - max: *integer*
   * - number 
     - Floating point number 
     - n/a
   * - string 
     - Text String 
     - - length: *integer*
       - format: date, date-time, json, ipv4, ipv6, mac, url, email
   * - boolean 
     - Boolean value (true/false)
     - n/a
   * - uuid 
     - Text string in UUID format
     - n/a
   * - enum 
     - Text string with set of values
     - - values: [*string*]

File Structure
--------------

The API is defined by a single file.  The Root Object is defined by the 
ProtonDef object.  


ProtonDef
+++++++++

+---------------+---------------------+---------------------------------------+
| Fixed Field   | Type                | Description                           |
+===============+=====================+=======================================+
| version       | string              | Gluon Version                         |
+---------------+---------------------+---------------------------------------+
| info          | InfoDef_            | Meta data for this API                |
+---------------+---------------------+---------------------------------------+
| objects       | ObjectsDef_         | Object definitions for the API        |
+---------------+---------------------+---------------------------------------+

.. _InfoDef:

InfoDef
+++++++
+---------------+---------------------+---------------------------------------+
| Fixed Field   | Type                | Description                           |
+===============+=====================+=======================================+
| name          | string              | Name of API                           |
+---------------+---------------------+---------------------------------------+
| description   | string              | Description of API                    |
+---------------+---------------------+---------------------------------------+
| version       | string              | Version of API                        |
+---------------+---------------------+---------------------------------------+
| author        | AuthorDef_          | Information about API authorship      |
+---------------+---------------------+---------------------------------------+

.. _AuthorDef:

AuthorDef
+++++++++
+---------------+---------------------+---------------------------------------+
| Fixed Field   | Type                | Description                           |
+===============+=====================+=======================================+
| name          | string              | Name of author                        |
+---------------+---------------------+---------------------------------------+
| url           | string              | URL to author website                 |
+---------------+---------------------+---------------------------------------+
| email         | string              | Email address of author               |
+---------------+---------------------+---------------------------------------+

.. _ObjectsDef:

ObjectsDef
++++++++++
+---------------+---------------------+---------------------------------------+
| Pattern Field | Type                | Description                           |
+===============+=====================+=======================================+
| {name}        | ObjectDef_          | Field/Value definitions for objects   |
+---------------+---------------------+---------------------------------------+

.. _ObjectDef:

ObjectDef
+++++++++
+---------------+---------------------+---------------------------------------+
| Fixed Field   | Type                | Description                           |
+===============+=====================+=======================================+
| api           | ApiDef_             | API path information for object       |
+---------------+---------------------+---------------------------------------+
| extends       | string              | Name of an object definition to extend|
+---------------+---------------------+---------------------------------------+
| attributes    | AttributeDef_       | Field/Value definitions for attributes|
+---------------+---------------------+---------------------------------------+

.. _ApiDef:

ApiDef
++++++
+---------------+---------------------+---------------------------------------+
| Fixed Field   | Type                | Description                           |
+===============+=====================+=======================================+
| name          | string              | Singular path name for object         |
+---------------+---------------------+---------------------------------------+
| plural_name   | string              | Plural path name for object           |
+---------------+---------------------+---------------------------------------+
| parent        | string              | Name of an object definition          |
+---------------+---------------------+---------------------------------------+

.. _AttributeDef:

AttributeDef
++++++++++++

+---------------+---------------------+---------------------------------------+
| Pattern Field | Type                | Description                           |
+===============+=====================+=======================================+
| {name}        | AttributeSchemaDef_ | Attribute definitions for an object   |
+---------------+---------------------+---------------------------------------+


.. _AttributeSchemaDef:

AttributeSchemaDef
++++++++++++++++++

+---------------+---------------------+---------------------------------------+
| Fixed Field   | Type                | Description                           |
+===============+=====================+=======================================+
| type          | string              | Primitive data type or ObjectDef name |
+---------------+---------------------+---------------------------------------+
| primary       | boolean             | Primary key for object if true        |
+---------------+---------------------+---------------------------------------+
| required      | boolean             | Required for object creation          |
+---------------+---------------------+---------------------------------------+
| description   | string              | Description of the attribute          |
+---------------+---------------------+---------------------------------------+
| length        | integer             | Length if type is string              |
+---------------+---------------------+---------------------------------------+
| values        | [string]            | Array of strings if type is enum      |
+---------------+---------------------+---------------------------------------+
| format        | string              | Format if type is integer or string   |
+---------------+---------------------+---------------------------------------+


.. csv-table:: 
   :header: "Fixed Field", "Type", "Description", "Optional", Default
   :widths: 5, 5, 15, 3, 3

   type, string,  Primitive data type or ObjectDef name, no, ""
   primary, boolean,  Primary key for object (if true), yes, false
   description, string,  Description of the attribute, yes, ''
   required, boolean,  Required for object creation, yes , false
   length, integer,  Length if type is string, yes, 255
   values, [string],  Array of strings if type is enum (required), yes, "n/a"
   format, string,  Format if type is integer or string, yes, "n/a"
   min, integer,  Min value if type is integer, yes, "n/a"
   max, integer,  Max value if type is integer, yes, "n/a"

