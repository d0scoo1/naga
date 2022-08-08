from typing import List, Dict,Optional
from slither.core.variables.state_variable import StateVariable
from .detector_base import (_set_state_vars_label,_get_no_label_svars,_get_label_svars)


#  state variable name, return function signature, type, possible names (lower names)
ERC20_STATE_VARIAVLES = [
    ('name','name()', 'string', ['name']),
    ('symbol','symbol()', 'string', ['symbol']),
    ('decimals','decimals()', 'uint', ['decimals','decimal']),
    ('totalSupply','totalSupply()', 'uint', ['totalsupply','supply']),
    ('balances','balanceOf(address)', 'mapping(address => uint256)', ['balances','balance']),
    ('allowances','allowance(address,address)','mapping(address => mapping(address => uint256))',['allowances','allowance']),
]

ERC721_STATE_VARIAVLES = [
    ('name','name()', 'string',  ['name']),
    ('symbol','symbol()', 'string',['symbol']),
    ('ownerOf','ownerOf(uint256)','mapping(uint256 => address)',['owners'],), # 这个owner不是管理员 owner
    ('balances','balanceOf(address)','mapping(address => uint256)',['balances','balance']),
    ('tokenApprovals','getApproved(uint256)','mapping(address => uint256)',['tokenapprovals','tokenapproval']),
    ('operatorApprovals','isApprovedForAll(address, address)','mapping(address => mapping(address => bool))',['operatorapprovals','operatorapproval']),
    ('uri','tokenURI(uint256)','string',['baseuri','uri'])
]
ERC1155_STATE_VARIAVLES = [
    ('balances','balanceOf(address, uint256)','mapping(uint256 => mapping(address => uint256))',['balances','balance']),
    ('operatorApprovals','isApprovedForAll(address, address)','mapping(address => mapping(address => bool))',['_operatorapprovals','operatorapproval']),
    ('uri','uri(uint256)','string',['uri']),
    ('totalSupply','totalSupply()', 'mapping(uint256 => uint256)', ['totalsupply','supply'])
]

exclude_stateVaribles = [
    # type,name
    ('bytes16','_HEX_SYMBOLS')
]


def _search_state_var_in_return(self, f_sig:str, type_str:str, svar_lower_names:List[str]) -> StateVariable:
    """ 
    查找 return 中的返回值
    """
    func = None
    for f in self.functions:
        if f.function.full_name == f_sig:
            func = f
            break

    candidates = []
    if func is not None:
        candidates = [svar for svar in func.return_var_group.state_vars if str(svar.type).startswith(type_str)]
        if candidates != []:
            return candidates

    for svar in self.all_state_vars:
        if any(
            svar
            for esvar in exclude_stateVaribles
            if str(svar.type).startswith(esvar[0]) and svar.name == esvar[1] 
        ):
            continue
        
        if svar.name.lower().replace('_','') == svar_lower_names[0]:
            return [svar]
        for name in svar_lower_names:
            if name in svar.name.lower():
                candidates.append(svar)
    candidates = list(set(candidates))
    if len(candidates) > 1:
        """
        直接匹配类型最相近，如果都相近，则全都返回
        """
        candidates = [svar for svar in candidates if str(svar.type).startswith(type_str)]
    return candidates

"""
    Search common state variables in the ERC 20 721 1155
"""

def _detect_erc_state_vars(self, erc_state_vars):
    for v in erc_state_vars:
        svars = _search_state_var_in_return(self,v[1],v[2],v[3])
        _set_state_vars_label(self,v[0],svars)

def detect_erc_state_vars(self,erc):
    if erc == 'erc20':
        _detect_erc_state_vars(self,ERC20_STATE_VARIAVLES)
    elif erc == 'erc721':
        _detect_erc_state_vars(self,ERC721_STATE_VARIAVLES)
    elif erc == 'erc1155':
        _detect_erc_state_vars(self,ERC1155_STATE_VARIAVLES)


'''
def detect_unfair_settings(self):
    """
        Before Functions: detect_owners_bwList, detect_paused, detect_erc_state_vars
        检查所有剩下的 owner 可以修改的 state vars
    """
    unfair_settings = []
    for svar in self.state_vars_owner_updated:
        unfair_settings.append(svar)

    marked_svars = []
    for svars in self.label_svars_dict.values():
        marked_svars += svars
    unfair_settings = list(set(unfair_settings) - set(marked_svars))

    self.label_svars_dict.update({'unfair_settings':unfair_settings})
'''
