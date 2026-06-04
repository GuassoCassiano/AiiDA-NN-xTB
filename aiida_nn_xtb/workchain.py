from aiida.engine import WorkChain, ToContext
from aiida.orm import Str, Dict, Code
from aiida_nn_xtb.structure2xyz import NNxTBCalculation
from aiida_nn_xtb.smiles2structure import smiles2structure

class NNxTBWorkChain(WorkChain):
    """
    Automatic WorkChain to convert SMILES strings to NNxTB Calculations
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # define the type of data the user needs to give AiiDA
        spec.input('smiles', valid_type=Str, help='The SMILES string of the Molecule')
        spec.input('code', valid_type=Code, help='The NN-xTB code set up on the cluster')

        # defining the chronological order of scripts the WorkChain will follow
        spec.outline(
            cls.build_structure, 
            cls.run_calculation,
            cls.return_results
        )
        
        # define the type of output the NN-xTB calculation will give AiiDA
        spec.output('final_energy_dict', valid_type=Dict)

    def build_structure(self):
        """ Step 1: Converts the SMILES string to a 3D structure"""
        # get the unwrapped string from self
        raw_string = self.inputs.smiles.value

        # call 'smiles2structure' using smiles input
        structure_results = smiles2structure(raw_string)

        # using ToContext to let the results be used by the other AiiDA functions
        self.ctx.structure = structure_results
    
    def run_calculation(self):
        """Step 2: Send the math to the cluster"""
        # get the empty AiiDA shipping crate for script
        builder = NNxTBCalculation.get_builder()
        
        # input needed self inputed code and structure from last script
        builder.structure = self.ctx.structure
        builder.code = self.inputs.code
        
        # submit the code to the cluster
        running_calc = self.submit(builder)
        
        # put the WorkChain to sleep and tell it to save the output later
        return ToContext(raw_results=running_calc)

    def return_results(self):
        """ Step 3: Grab the parsed Dictionary and output it"""
        # The parser already ran while we were sleeping!
        # We just grab the finished dictionary from the calculation's outputs.
        clean_results = self.ctx.raw_results.outputs.results

        # output the results to be stored
        self.out('final_energy_dict', clean_results)