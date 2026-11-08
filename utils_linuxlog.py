import sys
import json
import pymysql
import random
import datetime
import csv
from pathlib import Path
from pymysql.cursors import DictCursor
import config_store


settingsDict = {}


def ensure_settings_loaded():
    global settingsDict
    if not settingsDict:
        settingsDict = load_settings()
    return settingsDict


def reset_country_file(country_dict=None):
    if country_dict is None:
        country_dict = {
            'Ukraine': {'prefix': ['UR', 'UT', 'UX', 'EM', 'EN'],
                        'itu': '29',
                        'cq-zone': '16'},
            'Botswana': {'prefix': ['A2'],
                         'itu': '57',
                         'cq-zone': '38'},
            'Tonga Isl.': {'prefix': ['A3'],
                           'itu': '62',
                           'cq-zone': '32'},
            'Oman & Muscat': {'prefix': ['A4'],
                              'itu': '39',
                              'cq-zone': '21'},
            'Bhutan': {'prefix': ['A5'],
                       'itu': '41',
                       'cq-zone': '22'},
            'UAE': {'prefix': ['A6'],
                    'itu': '39',
                    'cq-zone': '21'},
            'Qatar': {'prefix': ['A7'],
                      'itu': '39',
                      'cq-zone': '21'},
            'Bahrain': {'prefix': ['A9'],
                        'itu': '39',
                        'cq-zone': '21'},
            'Pakistan': {'prefix': ['AP', 'AS'],
                         'itu': '41',
                         'cq-zone': '21'},
            'Scarb. Reef': {'prefix': ['BS7'],
                            'itu': '50',
                            'cq-zone': '27'},
            'Taiwan': {'prefix': ['BV'],
                       'itu': '44',
                       'cq-zone': '24'},
            'Pratas': {'prefix': ['BV9P'],
                       'itu': '44',
                       'cq-zone': '24'},
            'China': {'prefix': ['BX', 'BZ'],
                      'itu': '42, 43, 44',
                      'cq-zone': '23, 24'},
            'Rep.of Nauru': {'prefix': ['C2'],
                             'itu': '65',
                             'cq-zone': '31'},
            'Andorra': {'prefix': ['C3'],
                        'itu': '27',
                        'cq-zone': '14'},
            'Gambia': {'prefix': ['C5'],
                       'itu': '46',
                       'cq-zone': '35'},
            'Bahamas': {'prefix': ['C6'],
                        'itu': '11',
                        'cq-zone': '08'},
            'Mozambique': {'prefix': ['C9'],
                           'itu': '53',
                           'cq-zone': '37'},
            'Chili': {'prefix': ['CE'],
                      'itu': '14,15,16',
                      'cq-zone': '12'},
            'Antarctica': {'prefix': ['CE9', 'KC4'],
                           'itu': '73',
                           'cq-zone': '13'},
            'Cuba': {'prefix': ['CM', 'CO'],
                     'itu': '11',
                     'cq-zone': '08'},
            'Morocco': {'prefix': ['CN'],
                        'itu': '37',
                        'cq-zone': '33'},
            'Gambia': {'prefix': ['C5'],
                       'itu': '46',
                       'cq-zone': '35'},
            'Bolivia': {'prefix': ['CP'],
                        'itu': '12,13,14',
                        'cq-zone': '12'},
        }

    settings = ensure_settings_loaded()
    country_path = Path(__file__).parent / settings['country-file']
    with country_path.open('w', encoding='utf-8') as f:
        json.dump(country_dict, f)

def csv_to_json_country(csv_file):
    """
    need CSV file with format:
                    "pfx,pfx;country;cq-zone;itu"
    :return: convert CSV to JSON and create file and settingsDict['country-file']
    """
    object_to_json = {}
    csv_path = Path(__file__).parent / csv_file
    with csv_path.open('r', encoding='utf-8', newline='') as country_file:
        for row in csv.reader(country_file, delimiter=';'):
            if len(row) < 4:
                continue
            prefixes, country, cq_zone, itu = (value.strip() for value in row[:4])
            if not country:
                continue
            object_to_json[country] = {
                'prefix': [prefix.strip() for prefix in prefixes.split(',') if prefix.strip()],
                'itu': itu,
                'cq-zone': cq_zone,
            }

    reset_country_file(object_to_json)
    #print("Full Object", object_to_json)

def delete_all_qso(table_name):
    if isinstance(table_name, (list, tuple)):
        table_name = table_name[0] if table_name else ''
    table_name = str(table_name)
    if not table_name or "\x00" in table_name:
        raise ValueError("Invalid database table name")
    quoted_table_name = "`" + table_name.replace("`", "``") + "`"

    settings = ensure_settings_loaded()
    connection = pymysql.connect(
        host=settings['db-host'],
        user=settings['db-user'],
        password=settings['db-pass'],
        db=settings['db-name'],
        charset=settings['db-charset'],
        cursorclass=DictCursor
    )
    try:
        with connection.cursor() as cursor:
            result = cursor.execute(f"DELETE FROM {quoted_table_name}")
        connection.commit()
    finally:
        connection.close()
    print("Result clear operation for", table_name, ":", result)

def _adi_field(name, value):
    value = str(value)
    return f"<{name}:{len(value)}>{value}"


def generate_adif(count, name_file):
    settings = ensure_settings_loaded()
    if not str(count).isdigit():
        return

    letters = 'ABCDEFGHIKLMNOPQRSTVXYZ'
    digits = '1234567890'
    records = []
    for _ in range(int(count)):
        call = ''.join(random.choice(letters) for _ in range(2))
        call += random.choice(digits)
        call += ''.join(random.choice(letters) for _ in range(3))
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        record = {
            'BAND': '15M',
            'CALL': call,
            'FREQ': '21.17',
            'MODE': 'SSB',
            'OPERATOR': settings.get('my-call', ''),
            'QSO_DATE': datetime.date.today().strftime('%Y%m%d'),
            'TIME_ON': timestamp.strftime('%H%M%S'),
            'RST_RCVD': '59',
            'RST_SENT': '59',
            'NAME': 'Nam',
            'QTH': 'qth',
            'COMMENTS': 'comment',
            'TIME_OFF': timestamp.strftime('%H%M%S'),
            'EQSL_QSL_SENT': 'N',
            'CLUBLOG_QSO_UPLOAD_STATUS': 'N',
        }
        records.append(''.join(_adi_field(field, value) for field, value in record.items()) + '<EOR>\n')

    now = datetime.datetime.now()
    header = (
        'ADIF from LinuxLog Generator ADIF v.0.1\n'
        f'Copyright 2019-{now.year}  Baston V. Sergey\n'
        f"Header generated on {now} by {settings.get('my-call', '')}\n"
        'File output restricted to QSOs by : All Operators - All Bands - All Modes\n'
        '<PROGRAMID:8>LinuxLog\n'
        '<PROGRAMVERSION:3>0.1\n'
        '<EOH>\n\n'
    )
    output_path = Path(__file__).parent / name_file
    with output_path.open('w', encoding='utf-8') as output_file:
        output_file.write(header)
        output_file.writelines(records)

def load_settings():
    return config_store.load_settings()


def main(argv=None):
    global settingsDict
    arguments = sys.argv[1:] if argv is None else argv
    if not arguments:
        print("Use 'help' to list commands")
        return 1

    parameter = arguments[0]
    settingsDict = load_settings()
    if parameter == 'reset-country':
        reset_country_file()
    elif parameter == 'csv-country':
        if len(arguments) < 2:
            print("CSV filename is required")
            return 1
        csv_to_json_country(arguments[1])
    elif parameter == 'clear-log':
        if len(arguments) < 2:
            print("Incorrect name table\nUse utils_linuxlog.py clear-log <table-name>")
            return 1
        delete_all_qso(arguments[1])
    elif parameter == 'generate-adif':
        if len(arguments) < 3 or not arguments[1].isdigit():
            print("Usage: utils_linuxlog.py generate-adif <count> <output-file>")
            return 1
        generate_adif(arguments[1], arguments[2])
    elif parameter == 'help':
        print("RESET COUNTRY\nCommand: python3 utils_linuxlog.py reset-country")
        print("Create the country file in JSON format.")
        print("\nCSV COUNTRY\nCommand: python3 utils_linuxlog.py csv-country <csv-file.csv>")
        print("Convert a semicolon-separated country CSV file to JSON.")
        print("\nCLEAR LOG\nCommand: python3 utils_linuxlog.py clear-log <table-name>")
        print("Delete all records (QSOs) from a MySQL table.")
        print("\nGENERATE ADIF\nCommand: python3 utils_linuxlog.py generate-adif <count> <output-file>")
        print("Generate random QSOs in an ADIF file.")
    else:
        print(f"Unknown command: {parameter}")
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
