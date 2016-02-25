#coding: utf-8
import csv
import json
import sys

def jsonToCsv(jsonFilePath, csvFilePath):
    with open(jsonFilePath, 'r') as jsonfile:
        jsonData = json.loads(jsonfile.read(), encoding='utf-8')

    with open(csvFilePath, "wb+") as csvFile:
        csvFile.write('\xEF\xBB\xBF') 
        f = csv.writer(csvFile)
        
        for i in range(0, len(jsonData), 1):
            rowData = []
            for key in jsonData[i].keys():
                rowData.append(json.dumps(jsonData[i][key], ensure_ascii = False).encode("utf8"))
            f.writerow(rowData)
            sys.stdout.write("\r%d%%" % (float(i) / (len(jsonData) - 1) * 100.0))
            sys.stdout.flush()

        print(u"\n檔案輸出至" + csvFilePath);
'''
def csvToJson(csvFilePath, jsonFilePath):
    print("[csvToJson] Not implemented!")
'''

def main():
    if(len(sys.argv) < 2):
        print('請輸入要轉換的檔案路徑!')
    else:
        inputPath = sys.argv[1]
        
        if(inputPath.find(".json") > 0):
            outputPath = inputPath[0:inputPath.find(".json")-1] + ".csv"
            jsonToCsv(inputPath, outputPath)
        '''
        elif(inputPath.find(".csv") > 0):
            outputPath = inputPath[0:inputPath.find(".csv")-1] + ".json"
            csvToJson(inputPath, outputPath)
            print(outputPath)
        '''
        else:
            print("輸入檔案的副檔名必須是.json")
    return

if __name__ == '__main__':
    main()
