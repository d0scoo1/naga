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
from crytic_compile.platform.exceptions import InvalidCompilation

import time
import logging

logging.getLogger("CryticCompile").level = logging.CRITICAL

###### common config ######
etherscan_api_key= '68I2GBGUU79X6YSIMA8KVGIMYSKTS6UDPI'
solc_dir = '/mnt/c/Users/vk/Desktop/naga_test/solc/'
openzeppelin_dir = '/mnt/c/Users/vk/Desktop/naga_test/openzeppelin-contracts'

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

def contractInfo(address,name,version,export_dir,erc_force,output_dir = None):
    info = {}
    info['address'] = address
    info['name'] = name
    info['version'] =version
    info['export_dir'] = export_dir
    info['erc_force'] = erc_force
    info['output_dir'] = output_dir
    info['entry_sol_file'] = None
    info['ether_balance'] = 0
    info['txcount'] = 0
    info['date'] = 0
    info['naga_test_cost'] =  0
    info['slither_compile_cost'] = 0
    return info

class NagaTest():
    def __init__(self,contract) -> None:
        self.contract = contract
        self.contract_address = contract['address']
        self.contract_name = contract['name']
        self.contract_version = contract['version']
        self.contract_export_dir = contract['export_dir']
        self.erc_force = contract['erc_force']
        self.output_file = contract['output_file']

        self.compiler = solc_dir +'solc-'+ self.contract_version
        self.sol_dir = os.path.join(self.contract_export_dir, self.contract_address + '_' +self.contract_name)
        self.sol_file = self.sol_dir + '.sol'

        #self.max_attemp = 3
        #self.time_sleep_second = 0.1

    def local_compile(self):
        if os.path.exists(self.sol_file):
                return Slither(self.sol_file,solc = self.compiler,disable_solc_warnings = True,solc_remaps = get_solc_remaps(self.contract_version))
        if os.path.exists(self.sol_dir):
            return Slither(CryticCompile(MultiSolFiles(self.sol_dir,solc_remaps = get_solc_remaps(self.contract_version)),solc = self.compiler,compiler_version=self.contract_version),disable_solc_warnings = True)

    def etherscan_download_compile(self):
        return Slither(CryticCompile(Etherscan(self.contract_address,disable_solc_warnings = True),solc = self.compiler,solc_remaps = get_solc_remaps(self.contract_version),etherscan_only_source_code = True,etherscan_api_key=etherscan_api_key,export_dir =self.contract_export_dir))

    def local_test(self):
        try:
            s_start_time = time.time()
            slither = self.local_compile()
            s_end_time = time.time()
            self.contract['slither_compile_cost'] = s_end_time - s_start_time
        except:
            return
        try:
            n_start_time = time.time()
            naga = Naga(slither,contract_name= self.contract_name)
            
            if len(naga.entry_contracts) == 0: return
            naga_contract = naga.entry_contracts[0]
            
            if self.erc_force != None:
                naga_contract.detect(erc_force= self.erc_force)
            elif naga_contract.is_erc:
                naga_contract.detect()
            else:
                return
            n_end_time = time.time()
            self.contract['naga_test_cost'] = n_end_time - n_start_time
        except:
            return
        
        export_dir_len = len(self.contract_export_dir) + 1

        self.contract['entry_sol_file'] = naga_contract.contract.source_mapping['filename_used'][export_dir_len:]# If a contract has multiple solidity files, we should find the entry contract

        contractInfo = self.contract
        del contractInfo['export_dir']
        del contractInfo['output_file']
        naga_contract.set_info(contractInfo)
        naga_contract.summary_json(self.output_file)
        return naga_contract


    """
    def get_slither(self,attemp = 0):
        slither = None
        try:
            slither = self.local_compile()
        except:
            pass
        
        if slither is not None:
            return slither

        try:
            return self.etherscan_download_compile()
        except: # : If throw InvalidCompilation, we try again
            if attemp < self.max_attemp:
                time.sleep(self.time_sleep_second)
                return self.get_slither(attemp +1)
            return None
    
    def test(self):

        slither = self.get_slither()

        if slither is None:
            return
        
        etherscan_contracts = os.path.join(self.contract_export_dir,"etherscan-contracts")
        export_dir_len = len(etherscan_contracts) + 1

        naga = Naga(slither,contract_name= self.contract_name)
        if len(naga.entry_contracts) == 0: return None
        naga_contract = naga.entry_contracts[0]


        if self.erc_force != None:
            naga_contract.detect(erc_force= self.erc_force)
        elif naga_contract.is_erc:
            naga_contract.detect()
        else:
            return None

        self.contract['entry_sol_file']= naga_contract.contract.source_mapping['filename_used'][export_dir_len:]# If a contract has multiple solidity files, we should find the entry contract
        naga_contract.set_info(self.contract)

        output_file = None
        if self.output_dir is not None:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            output_file = os.path.join(self.output_dir,self.contract_address)
        naga_contract.summary_json(output_file)
        return naga_contract
    """

if __name__ == "__main__":

    address= '0xaeb8121b89625576fd85bc460a1e2cdb2b7ee7d7'
    name= 'CollectionContract'
    version= '0.8.11'
    export_dir= '/mnt/c/Users/vk/Desktop/naga_test/token_tracker/erc721'
    erc_force= 'erc721'
    output_dir = None
    contract = contractInfo(address,name,version,export_dir,erc_force,output_dir)

    nagaT = NagaTest(contract)
    #nagaT.etherscan_download_compile()
    nagaT.local_compile()

    c = nagaT.test()
    #print(c.summary_json())
    for c in c.label_svars_dict['owners']:
        print(c)
    
    print(nagaT.compile_type)
