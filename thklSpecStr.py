import fandLexParse as fl

location_str = f"""{fl.T_ROOT} %s
{fl.T_MONSTER} %s

"""
chunk_str = f"{fl.T_ROOT} %s"
filepath_str = f"{fl.T_RELATIVE} %s"
monster_str = f"{fl.T_MONSTER} %s"

import_str = f"{fl.T_QUALIFIED_IMPORT} %s"
selective_import_str = f"{fl.T_SELECTIVE_IMPORT} %s {fl.T_SELECTION} %s"
qualified_immport_str = f"{fl.T_QUALIFIED_IMPORT} %s {fl.T_ALIAS} %s"
function_str = f"%s = %s {fl.T_SPECIFIER} %08X"

length_str = f"""
{fl.T_ENTRY_COUNT} %d entries
"""

register_str = f"{fl.T_REGISTER} %s as %s"
register_anon_str = f"{fl.T_REGISTER} %s"