.. _nb_metadata_schema:

Notebook/Cell Metadata Schema
-----------------------------

This schema is applied to keys under the ``nbreg`` key.

For example:

.. code:: json

   {
      "nbreg": {
        "skip": true,
        "skip_reason": "There is an unresolved exception"
      }
   }

.. literalinclude:: ../../../pytest_notebook/resources/nb_metadata.schema.json
  :language: JSON
