"""
T-30: Tool Handlers Package — separation of "handler contract" from "business mock logic".

Convention:
  Each complex tool gets its own handler module here with:
    - validate_input(params) → None | error_dict
    - execute(params)        → result_dict  (async)

  tools/base.py calls handler.validate_input() BEFORE the tool function,
  providing cleaner error messages than raw exceptions propagating up.

Current handlers:
  - erp_handler.py   → ErpBudgetHandler, ErpInventoryHandler
"""
