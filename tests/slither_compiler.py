import sys
sys.path.append(r"/mnt/d/onedrive/sdu/Research/centralization_in_blackchain/naga")

import os
from slither import Slither
from naga.naga import Naga
from naga.core.expansions import ContractExp


from crytic_compile import CryticCompile
#from crytic_compile.platform.all_platforms import Etherscan,Solc
from test_platform.multiple_sol_files import MultiSolFiles
from test_platform.etherscan import Etherscan # crytic_compile.platform.Etherscan has bug

import logging

logging.getLogger("CryticCompile").level = logging.CRITICAL

###### common config ######
etherscan_api_key= '68I2GBGUU79X6YSIMA8KVGIMYSKTS6UDPI'
solc_dir = '/mnt/c/Users/vk/Desktop/naga_test/tools/solc/'
openzeppelin_dir = '/mnt/c/Users/vk/Desktop/naga_test/tools/openzeppelin-contracts'

def get_solc_remaps(version='0.8.0',openzeppelin_dir = openzeppelin_dir):
    '''
    get the remaps for a given solc version
    '''
    v = int(version.split('.')[1])
    if v == 5:
        return "@openzeppelin/=" + openzeppelin_dir + "/openzeppelin-contracts-solc-0.5/"
    if v == 6:
        return "@openzeppelin/=" + openzeppelin_dir + "/openzeppelin-contracts-solc-0.6/"
    if v == 7:
        return "@openzeppelin/=" + openzeppelin_dir + "/openzeppelin-contracts-solc-0.7/"
    if v == 8:
        return "@openzeppelin/=" + openzeppelin_dir + "/openzeppelin-contracts-solc-0.8/"
    return "@openzeppelin/=" + openzeppelin_dir + "/openzeppelin-contracts-solc-0.8/"

class SlitherCompiler():
    def __init__(self) -> None:
        pass

    def single_compile(self,sol_path,compiler_version):
        return Slither(sol_path,
            solc = get_solc(compiler_version),
            disable_solc_warnings = True,
            solc_remaps = get_solc_remaps(compiler_version)
        )

    def multi_compile(self,sol_dir,compiler_version):
        return Slither(CryticCompile
                        (MultiSolFiles(
                            sol_dir,solc_remaps = get_solc_remaps(compiler_version)),
                        solc = get_solc(compiler_version),
                        compiler_version=compiler_version),
                    disable_solc_warnings = True)

    def etherscan_download_compile(self,contract_address,compiler_version,contracts_dir):
        return Slither(
            CryticCompile(
                Etherscan(contract_address,disable_solc_warnings = True),
                solc = get_solc(compiler_version),
                solc_remaps = get_solc_remaps(self.contract_compiler),etherscan_only_source_code = True,
                etherscan_api_key=etherscan_api_key,
                export_dir =contracts_dir))

def get_solc(compiler_version):
    return solc_dir +'solc-'+ compiler_version