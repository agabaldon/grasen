#!/Users/alfredo/miniconda3/envs/py3.7/bin/python

#-------------------------------------------------------------
# Takes a c file or two json files and performs Semantic analysis.
# Inovkes UofAZ GrFN service and Semantic Analysis service
#
# Change the first line above to the location of your python
#
# Run:  python semanticAnalysis.py -i filename.c
#       python semanticAnalysis.py -i grfn.json expTree.json
# Output: filename_GrFN.json         - GrFN json (only if the input was a c file)
#         filename_ExpTree.json      - Expression tree json (only if the input was a c file)
#         filename.json              - GrFN Expression tree combined json (only if the input was a c file)
#         filename_Base.sadl         - Base SADL model (w/o having run the inference rules)
#         filename_SemAnalysis.sadl  - Semantic analysis SADL model (results of inference)
#         filename.csv               - Semantic analysis query results in CSV
#         SemAnnotation.csv          - Semantic analysis query results in CSV for Ghidra vis.
# --Alfredo
#-------------------------------------------------------------

import base64
import sys, getopt, argparse
import requests
import json

GrFN_API_ENDPOINT = 'http://hopper.sista.arizona.edu/api/v1/translate'
EXPTREE_API_ENDPOINT = 'http://hopper.sista.arizona.edu/api/v1/extract/expr_trees'
API_KEY = 'kZNp8uFllb3MWKFfXqMhFCa2'
PORT = '8080'
#PORT = '10800'
SM_BASE_MODEL_ENDPOINT = 'http://localhost:' + PORT + '/SemanticAnalysis/generateBaseModel'
SM_MODEL_ENDPOINT =      'http://localhost:' + PORT + '/SemanticAnalysis/generateAnnotationsModel'
SM_QUERY_ENDPOINT =      'http://localhost:' + PORT + '/SemanticAnalysis/queryService'

def performSemanticAnalysis(outputfile):
    with open(outputfile + '.json', 'rb') as grfnfile:
        grfn_payload = {'file' : grfnfile}

        headers = {'accept': 'text/plain'}

        # Request base model
        responseBaseSADL = requests.post(SM_BASE_MODEL_ENDPOINT, files = grfn_payload, headers=headers)
        print('Semantic analysis base model service response: ', "OK" if responseBaseSADL.ok else "Error"),

        # If all is well, save the file
        if responseBaseSADL.ok:
            print(' saving ' + outputfile + '_Base.sadl')
            with open(outputfile + '_Base.sadl', 'w') as sadlfile:
                sadlfile.write(responseBaseSADL.text)

        # Reset the input file!!!
        grfnfile.seek(0)
                
        # Request semantic analysis query
        responseQuery = requests.post(SM_QUERY_ENDPOINT, files = grfn_payload, headers=headers)
        print('Semantic analysis query service response: ', "OK" if responseQuery.ok else "Error"),

        # If all is well, save the file
        if responseQuery.ok:
            print(' saving ' + outputfile + '.csv' + ' and ' + 'SemAnnotation.csv')
            with open(outputfile + '.csv', 'w') as csvfile:
                csvfile.write(responseQuery.text)
            #Output also into a file call SemAnnotation.csv for the Ghidra visualization
            with open('SemAnnotation.csv', 'w') as csvfile:
                csvfile.write(responseQuery.text)
        else:
            print('\nQuery service returned:')
            print(responseQuery.text)

        # Reset the input file!!!
        grfnfile.seek(0)

        # Request semantic analysis model
        responseAnnotSADL = requests.post(SM_MODEL_ENDPOINT, files = grfn_payload, headers=headers)
        print('Semantic analysis annotations model service response: ', "OK" if responseAnnotSADL.ok else "Error"),

        # If all is well, save the file
        if responseAnnotSADL.ok:
            print(' saving ' + outputfile + '_SemAnalysis.sadl')
            with open(outputfile + '_SemAnalysis.sadl', 'w') as sadlfile:
                sadlfile.write(responseAnnotSADL.text)

def generateJsons(inputfile, outputfile):
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

    #print('GrFN service payload: ', json.dumps(payload))

    response = requests.post(GrFN_API_ENDPOINT, headers = headers, data = json.dumps(payload))

    # print('GrFN service request: ', response.request.body)

    print('GrFN service response: ', response.reason)

    if response.ok:
        grfn_json_orig = json.loads(response.text)

        # Our service takes the the top level 'grfn' value as input, so grab that
        grfn_json = grfn_json_orig['grfn']
        
        # Save the GrFN json
        with open(outputfile + '_GrFN.json', 'w') as grfnfile:
            #json.dump(grfn_json, grfnfile)
            json.dump(grfn_json_orig, grfnfile)


        #generateSemanticAnnotationModel(outputfile + '_GrFN')


        # Next, generate ExpTree SADL

        # Get exp tree json
        responseExpTreeSADL = requests.post(EXPTREE_API_ENDPOINT, headers = headers, data = json.dumps(grfn_json_orig))

        print('ExpTree service response: ', responseExpTreeSADL.reason)

        if responseExpTreeSADL.ok:
            exptree_json = json.loads(responseExpTreeSADL.text)

        # Save the ExpTree json
        with open(outputfile + '_ExpTree.json', 'w') as grfnfile:
            json.dump(exptree_json, grfnfile)

    return grfn_json, exptree_json

def main(inputFiles):

    """
    print(len(inputFiles))
    for f in inputFiles:
        print(f)
    return
    """
    #print(inputFiles[0].endswith('.c'))

    cFile = ''
    json1 = json2 = ''
    
    if(inputFiles[0].endswith('.c')):
        if(len(inputFiles) < 2):
            cFile = inputFiles[0]
        else:
            print('Only 1 c file should be provided')
            return
    elif(len(inputFiles) == 2):
        if(inputFiles[0].endswith('.json') and inputFiles[1].endswith('.json')):
            json1, json2 = inputFiles 
        else:
            print('json input filenames must have extension .json')
            return
    else:
        print('script arguments should be 1 c file or 2 json files')
        return

    outputfile=inputFiles[0].replace('.c','').replace('.json','')


    if(cFile != ''):
        grfn_json, exptree_json = generateJsons(cFile, outputfile)
    else:
        with open(json1, 'r') as j1:
            grfn_json = json.load(j1)
            
        with open(json2, 'r') as j2:
            exptree_json = json.load(j2)
    
            
    combined_json = {'grfn': grfn_json,
                     'expTreeArray' : exptree_json}

    # Save the combined json
    with open(outputfile + '.json', 'w') as grfnfile:
        json.dump(combined_json, grfnfile)
            
    performSemanticAnalysis(outputfile)


if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument('-i', '--inputFiles', help='a C source file or a pair of Json files', type=str, nargs='+')
   args = parser.parse_args()
   main(args.inputFiles)

