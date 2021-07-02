#!/Users/alfredo/miniconda3/envs/py3.7/bin/python

#-------------------------------------------------------------
# Takes a c file and generates a GrFN json and a SADL model
# Inovkes UofAZ GrFN service and SADL model from GrFN service
#
# Change the first line above to the location of your python
#
# Run: python generateGrFN_SADL.py -i inputfile.c -o outputfile
# Output: outputfile.json
#         outputfile.owl.sadl
# --Alfredo
#-------------------------------------------------------------

import base64
import sys, getopt
import requests
import json

GrFN_API_ENDPOINT = 'http://hopper.sista.arizona.edu/api/v1/translate'
API_KEY = 'kZNp8uFllb3MWKFfXqMhFCa2'

SEMANNOT_ENDPOINT = 'http://localhost:10800/SemanticAnnotator/translate'

def main(argv):

    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('generateGrFN_SADL.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('generateGrFN_SADL.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    with open(inputfile, 'r') as file:
        input_string = file.read()

    input_string_bytes = input_string.encode("ascii")
    
    base64_bytes = base64.b64encode(input_string_bytes)
    base64_string = base64_bytes.decode("ascii")
  
    #print(f"Encoded string: {base64_string}")

    headers = {'apikey' : API_KEY,
               'Content-Type' : 'application/json'
    }
        
    source_files = [{'file_name' : inputfile,
                     'file_type' : 'c',
                     'base64_encoding' : base64_string
    }]
        
    payload = {'source_code_files' : source_files,
               'documentation_files' : [],
               'source_language' : 'c',
               'output_model' : 'GRFN'
    }

    # print('GrFN service payload: ', json.dumps(payload))

    response = requests.post(GrFN_API_ENDPOINT, headers = headers, data = json.dumps(payload))

    # print('GrFN service request: ', response.request.body)

    print('GrFN service response: ', response.reason)

    if response.ok:
        grfn_json = json.loads(response.text)

        # Our service takes the the top level 'grfn' value as input, so grab that
        grfn_json = grfn_json['grfn']
        
        # Save the GrFN json
        with open(outputfile + '.json', 'w') as grfnfile:
            json.dump(grfn_json, grfnfile)

        with open(outputfile + '.json', 'rb') as grfnfile:
            grfn_payload = {'file' : grfnfile}

            # Request sadl generation
            responseSADL = requests.post(SEMANNOT_ENDPOINT, files = grfn_payload)
            print('SemAnnotator service response: ', responseSADL.reason)

            # If all is well, save the sadl
            if responseSADL.ok:
                with open(outputfile + '.sadl', 'w') as sadlfile:
                    sadlfile.write(responseSADL.text)
            

if __name__ == "__main__":
   main(sys.argv[1:])
