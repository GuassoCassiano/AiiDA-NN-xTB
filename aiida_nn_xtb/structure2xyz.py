from aiida.engine import CalcJob
from aiida.orm import StructureData, Dict
from aiida.common import CalcInfo, CodeInfo

class NNxTBCalculation(CalcJob):
    """ 
    AiiDA plugin to run NN-xTB calculations
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # telling AiiDA to expect the StructureData container
        spec.input('structure', valid_type=StructureData, help='The 3D molecular structure')

        # telling AiiDA what to name each variable in its "sandbox"
        spec.input('metadata.options.input_filename', valid_type=str, default='input.xyz')
        spec.input('metadata.options.output_filename',valid_type=str, default='nnxtb_output.txt')

        # NEW: tells AiiDA to route the calculation to the new parser
        spec.input('metadata.options.parser_name', valid_type=str, default='nnxtb_parser')

        # telling AiiDA to output final Dict to exit the wrapper
        spec.output('results', valid_type=Dict, help='The parsed total energy')

        spec.default_output_node = 'results'

        # NEW: registering the custom exit codes
        spec.exit_code(300, 'ERROR_MISSING_OUTPUT', message='Output files missing from retrieved folder')
        spec.exit_code(301, 'ERROR_REGEX_FAILED', message='Regex failed to find Total Energy in the Output')
    
    def prepare_for_submission(self, folder):
        """
        Unwraps the AiiDA container and writes the XYZ file into the remote folder
        """
        # grab the structure container that was passed in
        structure = self.inputs.structure

        # Get total number of atoms and orignal SMILES string for XYZ header
        num_atoms = len(structure.sites)
        name = structure.base.extras.get("original_smiles", "Unknown SMILES")

        # start building the XYZ file
        xyz_text = f"{num_atoms}\n"
        xyz_text += f"SMILES: {name}\n"

        for site in structure.sites:
            symbol = site.kind_name
            x, y, z = site.position

            # write the xyz file with the correct spacing
            xyz_text += f"{symbol:<4} {x:>12.5f} {y:>12.5f} {z:>12.5f}\n"
        
        # get the filename
        in_filename = self.inputs.metadata.options.input_filename

        # write the string into the remote sandbox
        with folder.open(in_filename, 'w') as handle:
            handle.write(xyz_text)

        # telling AiiDA what terminal commands to run on the cluster
        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.cmdline_params = [in_filename] # tells the cluster to run: nn-xtb input.xyz

        # NEW: tells aiida to save the xtb terminal output into a txt file 
        codeinfo.stdout_name = self.inputs.metadata.options.output_filename
        
        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = [self.inputs.metadata.options.output_filename]

        return calcinfo