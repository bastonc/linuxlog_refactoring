# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8
from pathlib import Path


def parseStringAdi(string, adi_fields_standart, settings_dict):
    """
    This function recieving string from adi-file, and parse it.
    Function returning result in Phyton dictionary type, where key - it key from ADI-tag,
    value - information from ADI
    """

    print(string)
    counter = 0
    name = ''
    digitInTagString = ''
    digitInTagDigit = 0
    inTag = ''
    tags = {}
    counterChar = 0
    for i in string:
        try:
            if counter < len(string) - 1:
                counter = counter + 1


            if i == '<':
                counterChar = counter
                while string[counterChar] != ':':
                    name = name + string[counterChar]
                    #print(f"string {string} len string {len(string)} counter {counterChar}")
                    if str(name).upper() in ('EOR',     'EOH'):
                        break
                    counterChar = counterChar + 1
                if string[counterChar] == ':':
                    counterChar = counterChar + 1
                    while string[counterChar] != '>':
                        digitInTagString = digitInTagString + string[counterChar]
                        counterChar = counterChar + 1
                # digitInTagDigit=int(digitInTagString)
                while string[counterChar] != '<':
                    if string[counterChar] != ">":
                        inTag = inTag + string[counterChar]
                    if counterChar == len(string) - 1:
                        break
                    else:
                        counterChar = counterChar + 1
                tags.update({name: inTag})
                name = ''
                inTag = ''


        except Exception:
            print("Exception in parse")
        adi_normilzer(tags, adi_fields_standart, settings_dict)
    return tags

def adi_normilzer(tags: dict, fields_adi_standart: list, settings_dict):
    #print(tags)
    #for tag
    for field in fields_adi_standart:
        if tags.get(field) is not None:
            continue
        if field == "OPERATOR":
            tags[field] = settings_dict['my-call']
        else:
         tags[field]=""
    #print(f"Adi_normalizer. Output tags: {tags}")
    return tags





## Poles which used in programm (they will found into dictionary from file)
def getAllRecord(poles, filename, key=''):
    # poles=['QSO_DATE','TIME_ON','FREQ','CALL','MODE','RST_RCVD','RST_SENT','NAME','QTH']
    is_qso_string = False
    allrecord = []
    if key == "import":
        with open(Path(__file__).parent/filename, 'r', errors="ignore") as fin:
            lines = fin.readlines()
            with open(Path(__file__).parent/'import_tmp.adi', 'w', encoding='utf-8') as fout:
                fout.writelines(lines)
            filename = 'import_tmp.adi'
    else:
        pass
    file = open(Path(__file__).parent/filename, 'r', encoding="utf-8", errors='ignore')
    iterator_string_file = 0
    iterator_records = 0
    record = {}
    for string in file:  # read string from file
        ## For example using string
        # string='<BAND:3>20M <CALL:6>DL1BCL <CONT:2>EU <CQZ:2>14 <DXCC:3>230 <FREQ:9>14.000000 <ITUZ:2>28 <MODE:3>SSB <OPERATOR:6>UR4LGA <PFX:3>DL1 <QSLMSG:19>TNX For QSO TU 73!. <QSO_DATE:8:D>20131011 <TIME_ON:6>184700 <RST_RCVD:2>57 <RST_SENT:2>57 <TIME_OFF:6>184700 <eQSL_QSL_RCVD:1>Y <APP_LOGGER32_QSO_NUMBER:1>1 <EOR>'
        iterator_string_file += 1
        if is_qso_string and string != '\n':    # checked key by ready parsing processing (1-ready) and cheked on empty string
            tags = parseStringAdi(string)
            # calling function parse processing/ Function returning all tags from file in Python-Dictionary object
            print(f"tags: {tags}")
            if tags:
                for tag in tags.keys():
                        record.update({tag: str(tags[tag]).replace('\n', '')})
                if str(string).upper() == '<EOR>' or str(string).upper().find("<EOR>", -6) != -1:
                    iterator_records += 1
                    #tags.update({'string_in_file': str(iterator_string_file)})
                    #tags.update({'records_number': str(iterator_records)})

                    for tag in tags.keys():
                        record.update({str(tag).upper(): str(tags[tag]).replace('\n', '')})
                    for i in range(len(poles)):
                        if poles[i] in record.keys():  # chek all field in dictionary
                            print("poles[i]:", poles[i], record.keys())
                        else:
                            print("poles[i] ELSE:", poles[i], record.keys())
                            record.update({poles[i]: ' '})
                    allrecord.append(record)
                    record = {}

        if string.upper().find("<EOH>", -6) != -1:  # if we went to end by text header in ADI file (<EOH>) - set key by ready parsing in value = 1
            is_qso_string = True

    file.close()
    return allrecord

