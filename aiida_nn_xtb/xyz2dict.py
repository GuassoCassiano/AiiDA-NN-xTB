from aiida.parsers.parser import Parser
from aiida.orm import Dict
import re 

class NNxTBParser(Parser):
    """
    AiiDA Plugin class for parsing though our NN-xTB output into AiiDA Dict
    """

    def parse(self, **kwargs):
        # get the AiiDA node name from previous script
        output_filename = self.node.get_option('output_filename')

        # get access to AiiDA sandbox folder
        out_folder = self.retrieved

        # make sure the file exists before forcing calculations to ensure no weird errors occur
        if output_filename not in out_folder.base.repository.list_object_names():
            return self.exit_codes.ERROR_MISSING_OUTPUT

        final_energy = None
        energy_pattern = re.compile(r"TOTAL\s+ENERGY\s+([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)")


        with out_folder.base.repository.open(output_filename, 'r') as file:
            for line in file:
                
                match = energy_pattern.search(line)
                
                if match:
                    final_energy = float(match.group(1))
            
        if final_energy is None:
            return self.exit_codes.ERROR_REGEX_FAILED
        
        # wrap the result in AiiDA's Dict container
        results_node = Dict(dict={'total_energy': final_energy})

        # pull the Dict container to the data base with a "results" label
        self.out('results', results_node)
