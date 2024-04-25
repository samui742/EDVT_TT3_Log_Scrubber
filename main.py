import re
import requests
import os
import pyautogui
from art import text2art
from bs4 import BeautifulSoup


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
def extract_uut_list(html):
    uut_match = re.findall(r'UUT\d+ </span></td>', html)
    uut_list = []

    for match in uut_match:
        uut_id = re.search(r'\d+', match).group(0)
        if uut_id not in uut_list:
            uut_list.append(uut_id)
    return uut_list
def extract_corner_ids(html):
    # print(html)
    corner_match = re.findall(r'data-cornerid="\d+"', html)
    corner_list = []
    for match in corner_match:
        corner_id = re.search(r'\d+', match).group(0)
        if corner_id not in corner_list:
            corner_list.append(corner_id)

    corner_name_match = re.findall(r'data-cornername=".*', html)
    corner_name_list = []
    for match in corner_name_match:
        corner_name = re.search(r'"(.*?)"', match).group(1).strip("Test").strip(" ")
        # corner_name = corner_name.strip(" Test")
        if corner_name not in corner_name_list:
            corner_name_list.append(corner_name)

    # print("corner_list", *corner_list)
    # print("corner_name_list", *corner_name_list)
    corner_dict = {id: corner for id, corner in zip(corner_list, corner_name_list)}
    # print("corner_dict", corner_dict)

    return corner_list, corner_dict
def parse_jobids(jobids_input):
    jobid_list = []

    if "," in str(jobids_input):
        jobid_list.extend(jobids_input.split(','))
        # jobid_list = list(jobids_input)
        jobid_list = [item.strip() for item in jobid_list]
    else:
        jobid_list.append(str(jobids_input))

    # print(jobid_list)
    return jobid_list
def parse_keywords(keywords_input):
    keyword_list = []

    if "," in str(keywords_input):
        keyword_list = keywords_input.split(',')
        keyword_list = [item.strip() for item in keyword_list]
    else:
        keyword_list.append(str(keywords_input).strip())

    # Add to support comma search. User has to input as semicolon
    for i in range(len(keyword_list)):
        if ";" in keyword_list[i]:
            x = keyword_list[i].replace(";",",")
            # print(keyword_list[i])
            keyword_list[i] = x

    return keyword_list

def parse_corners(corners_list, corner_select):
    corner_map = []
    corner_select = corner_select.replace(",", "")

    for item in corner_select:
        corner_map.append(corners_list[int(item) - 1])

    return corner_map

def parse_uuts(uut_list, uut_select):
    uut_map = []
    uut_select = uut_select.replace(",", "")

    for item in uut_select:
        uut_map.append(uut_list[int(item) - 1])

    return uut_map

def grab_switch_logs(corner, uut, jobid, username, password):

    local_log = "no"
    url = f"https://wwwin-testtracker3.cisco.com/trackerApp/oneviewlog/switch{uut}.log?page=1&corner_id={corner}"

    response = requests.get(url, auth=(username, password))
    response.close()
    html_log = response.text

    # Create a local log file
    html_log_name = f"{jobid}_{corner}_uut{uut}_html_log.txt"
    # print(html_log_name)

    try:
        #content = html_log[html_log.index("TESTCASE START"):html_log.index("Corner - runSwitch")]
        content = html_log[html_log.index("Total testcases to execute"):html_log.index("Corner - runSwitch")]
    except ValueError:
        # print(f"no log found on uut{uut}. The unit might be the link partner")
        content = "unit " + str(uut) + (" has no log file or uncompleted. Must be a link partner unit or corner was aborted")

    # To add option if need a local html log
    if local_log == "yes":
        with open(html_log_name, "w") as local_log:
            # local_log.write(html_log)
            local_log.write(content)

    return content, url
def switch_log_request(jobids_input, keywords_input, username, password, option):

    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    allow_duplicate = "yes"
    jobid_list = parse_jobids(jobids_input)
    print("jobIDs to proceed = ", jobid_list)

    keyword_list = parse_keywords(keywords_input)
    print("Keywords to search = ", keyword_list)

    for jobid in jobid_list:
        #Send HTTP Request with TT3 credentials
        url = f"https://wwwin-testtracker3.cisco.com/trackerApp/cornerTest/{jobid}"
        response = requests.get(url, auth=(username, password))
        response.close()
        html = response.text

        # corner_list = extract_corner_ids(html)
        corner_list, corner_dict = extract_corner_ids(html)
        uut_list = extract_uut_list(html)
        len_corner = len(corner_list)
        print(f'JOBID# {jobid} has total {len(corner_list)} corners.' + 'Corner number: ', ','.join(map(str, range(1, len_corner + 1))))
        corner_select = input(f'Press enter to search all or specify corner number (using comma if there are multiples): ')
        print(f'There are total {len(uut_list)} units.' + 'Unit number: ', ','.join(map(str, uut_list)))
        uut_select = input(f'Press enter to search all or specify unit number (using comma if there are multiples): ')

        if len(corner_select) == 0:
            pass
        else:
            corner_list = parse_corners(corner_list, corner_select)

        if len(uut_select) == 0:
            pass
        else:
            uut_list = parse_uuts(uut_list, uut_select)

        for uut in uut_list:
            result_file = f"{jobid}_uut{uut}_{option}_result.txt"
            with open(result_file, "w") as result_file:
                for corner in corner_list:
                    content, url = grab_switch_logs(corner, uut, jobid, username, password)
                    # Process content starts from here
                    if len(keywords) != 0:
                        print("="*100)
                        print(f'jobid={jobid} cornerid={corner} uut={uut}')
                        # print(f'jobid= {jobid} cornerid= {corner} cornername= {corner_dict[corner]} uut= {uut}')
                        print("Keywords to search = ", keyword_list)
                        print(f'{url}')
                        print("="*100)
                        result_file.write("="*100 + "\n")
                        result_file.write(f'jobid={jobid} cornerid={corner} uut={uut}' + "\n")
                        # result_file.write(f'jobid={jobid} cornerid={corner} cornername= {corner_dict[corner]} uut={uut}' + "\n")
                        result_file.write(f"URL: {url}" + "\n")
                        result_file.write("="*100 + "\n")
                        lines = content.splitlines()
                        line_with_keyword_list = []

                        for line in lines:
                            # To handle crashed corner
                            if f'REMOVING switch{uut} FROM CURRENT CORNER - JOB' in line:
                                print(f'{bcolors.BOLD}{bcolors.WARNING} *** Corner is NOT completed, switch is removed from the current corner ***{bcolors.ENDC}')
                                result_file.write(
                                    '\nCorner is NOT completed, switch is removed from the current corner\n\n')
                            # To handle link partner unit which does not have log file
                            if 'has no log file or uncompleted. Must be a link partner unit or corner was aborted' in line:
                                # print(f'{bcolors.BOLD}{bcolors.WARNING} *** has no log file match. Could be a link partner unit ***{bcolors.ENDC}')
                                print(f'{bcolors.BOLD}{bcolors.WARNING}*** {line} ***{bcolors.ENDC}')
                                result_file.write(line + "\n")

                            for keyword in keyword_list:
                                if keyword in line:
                                    if allow_duplicate == "yes":
                                        line_with_keyword_list.append(line)
                                        # To display testcase names on the report
                                        if "TESTCASE START" in line:
                                            print("\t" + f'{bcolors.OKBLUE}{line}{bcolors.ENDC}')
                                            result_file.write("\t" + line + "\n")
                                        else:
                                            print("\t\t\t" + f'{bcolors.FAIL}{line}{bcolors.ENDC}')
                                            result_file.write("\t\t\t" + line + "\n")
                                    else:
                                        if line not in line_with_keyword_list:
                                            line_with_keyword_list.append(line)
                                            if "TESTCASE START" in line:
                                                print("\t" + f'{bcolors.OKBLUE}{line}{bcolors.ENDC}')
                                                result_file.write("\t" + line + "\n")
                                            else:
                                                print("\t\t\t" + f'{bcolors.FAIL}{line}{bcolors.ENDC}')
                                                result_file.write("\t\t\t" + line + "\n")
            result_file.close()
def command_output_request(jobids_input, command_user, username, password, option):

    jobid_list = parse_jobids(jobids_input)
    print("User input these jobIDs = ", jobid_list)

    for jobid in jobid_list:
        #Send HTTP Request with TT3 credentials
        url = f"https://wwwin-testtracker3.cisco.com/trackerApp/cornerTest/{jobid}"
        response = requests.get(url, auth=(username, password))
        response.close()
        html = response.text
        # corner_list = extract_corner_ids(html)
        # corner_list, corner_dict = extract_corner_ids(html)
        # uut_list = extract_uut_list(html)
        # html = response.text
        # corner_list = extract_corner_ids(html)
        corner_list, corner_dict = extract_corner_ids(html)
        uut_list = extract_uut_list(html)

        len_corner = len(corner_list)
        print(f'JOBID#{jobid} has total {len(corner_list)} corners.' + 'Corner number: ',
              ','.join(map(str, range(1, len_corner + 1))))
        corner_select = input(
            f'Press enter to search all or specify corner number (using comma if there are multiples): ')
        print(f'There are total {len(uut_list)} units.' + 'Unit number: ', ','.join(map(str, uut_list)))
        uut_select = input(f'Press enter to search all or specify unit number (using comma if there are multiples): ')

        if len(corner_select) == 0:
            pass
        else:
            corner_list = parse_corners(corner_list, corner_select)

        if len(uut_select) == 0:
            pass
        else:
            uut_list = parse_uuts(uut_list, uut_select)

        # for uut in uut_list:
        #
        # corner_select = input(f'There are total {len(corner_list)} corners. Corner number: {corner_list}'
        #                       f'\nPress enter to search on all corners or specific corner by using comma: ')
        #
        # if len(corner_select) == 0:
        #     pass
        # else:
        #     corner_list = parse_corners(corner_list, corner_select)

        for uut in uut_list:
            output_file = f"{jobid}_uut{uut}_command_output_result.txt"
            with open(output_file, "w") as output_file:
                for corner in corner_list:
                    start_list = []
                    stop_list = []
                    content, url = grab_switch_logs(corner, uut, jobid, username, password)
                    print("="*100)
                    print(f'jobid={jobid} cornerid={corner} uut={uut}')
                    # print(f'jobid= {jobid} cornerid= {corner} cornername= {corner_dict[corner]} uut= {uut}')

                    print(f'{url}')
                    print("="*100)
                    output_file.write("="*100 + "\n")
                    output_file.write(f'jobid={jobid} cornerid={corner} uut={uut}' + "\n")
                    # output_file.write(f'jobid={jobid} cornerid={corner} cornername= {corner_dict[corner]} uut={uut}' + "\n")
                    output_file.write(f"URL: {url}" + "\n")
                    output_file.write("="*100 + "\n")

                    # To specify stop point of each command output
                    # TT3 might change the print out which will affect the code here
                    stop_keyword = "platform"  # old test effort
                    # stop_keyword = "*****************************************************************************************************************" # new test effort from Apr'24

                    lines = content.split('\n')
                    for i in range(len(lines)):
                        if command_user in lines[i]:
                            start_list.append(i)

                    # START SEARCHING FOR STOP POINT FROM WHERE THE COMMAND IS FOUND THEN BREAK ONCE FOUND
                    for item in start_list:
                        for i in range(item, len(lines)):
                            if stop_keyword in lines[i]:
                                stop_list.append(i)
                                break

                    # MAPPING BETWEEN START AND STOP POINT LIST
                    mapped = list(zip(start_list, stop_list))
                    # print(*mapped, sep="\n")

                    # WRITE RESULT INTO TEXT FILE
                    command_output = []
                    for (command_user_index, stop_keyword_index) in mapped:
                        for line in lines[command_user_index - 1:stop_keyword_index + 1]:
                            # if "Tune timeout on SerDes" not in line and "platform" not in line:
                            if "Tune timeout on SerDes" not in line:
                                command_output.append(line)
                                print(line)
                                output_file.write(line + '\n')
                output_file.close()


def statshow_diag_scrub(jobids_input, command_user, username, password, option):

    jobid_list = parse_jobids(jobids_input)
    print("User input these jobIDs = ", jobid_list)

    for jobid in jobid_list:
        #Send HTTP Request with TT3 credentials
        url = f"https://wwwin-testtracker3.cisco.com/trackerApp/cornerTest/{jobid}"
        response = requests.get(url, auth=(username, password))
        response.close()
        html = response.text
        # corner_list = extract_corner_ids(html)
        # uut_list = extract_uut_list(html)

        # html = response.text

        # corner_list = extract_corner_ids(html)
        corner_list, corner_dict = extract_corner_ids(html)
        uut_list = extract_uut_list(html)
        len_corner = len(corner_list)
        print(f'JOBID# {jobid} has total {len(corner_list)} corners.' + 'Corner number: ',
              ','.join(map(str, range(1, len_corner + 1))))
        corner_select = input(
            f'Press enter to search all or specify corner number (using comma if there are multiples): ')
        print(f'There are total {len(uut_list)} units.' + 'Unit number: ', ','.join(map(str, uut_list)))
        uut_select = input(f'Press enter to search all or specify unit number (using comma if there are multiples): ')

        if len(corner_select) == 0:
            pass
        else:
            corner_list = parse_corners(corner_list, corner_select)

        if len(uut_select) == 0:
            pass
        else:
            uut_list = parse_uuts(uut_list, uut_select)

        # for uut in uut_list:
        #
        #
        # corner_select = input(f'There are total {len(corner_list)} corners. Corner number: {corner_list}'
        #                       f'\nPress enter to search on all corners or specific corner by using comma: ')
        #
        # if len(corner_select) == 0:
        #     pass
        # else:
        #     corner_list = parse_corners(corner_list, corner_select)

        for uut in uut_list:
            output_file = f"{jobid}_uut{uut}_command_output_result.txt"
            with open(output_file, "w") as output_file:

                for corner in corner_list:
                    start_list = []
                    stop_list = []

                    content, url = grab_switch_logs(corner, uut, jobid, username, password)
                    print("="*100)
                    print(f'jobid={jobid} cornerid={corner} uut={uut}')
                    # print(f'jobid={jobid} cornerid={corner} cornername={corner_dict[corner]} uut={uut}')
                    print(f'{url}')
                    print("="*100)
                    output_file.write("="*100 + "\n")
                    output_file.write(f'jobid={jobid} cornerid={corner} uut={uut}' + "\n")
                    output_file.write(f"URL: {url}" + "\n")
                    output_file.write("="*100 + "\n")

                    # IN THE FUTURE COULD ASK TT3 TO ADD A BETTER MESSAGE
                    stop_keyword = "platform"
                    # stop_keyword = "*****************************************************************************************************************" # new test effort from Apr'24


                    # COVERT STRING INTO LIST
                    lines = content.split('\n')
                    # RETURN LIST INDEX WHEN COMMAND IS FOUND
                    for i in range(len(lines)):
                        if command_user in lines[i]:
                            start_list.append(i)

                    # START SEARCHING FOR STOP POINT FROM WHERE THE COMMAND IS FOUND THEN BREAK ONCE FOUND
                    for item in start_list:
                        for i in range(item, len(lines)):
                            if stop_keyword in lines[i]:
                                stop_list.append(i)
                                break

                    # MAPPING BETWEEN START AND STOP POINT LIST
                    mapped = list(zip(start_list, stop_list))
                    # print(*mapped, sep="\n")

                    # WRITE RESULT INTO TEXT FILE
                    command_output = []
                    for (command_user_index, stop_keyword_index) in mapped:
                        statshow_list = lines[command_user_index - 1:stop_keyword_index + 1]
                        # print(statshow_list)
                        statshow_error(statshow_list)
                        for line in lines[command_user_index - 1:stop_keyword_index + 1]:
                            # if "Tune timeout on SerDes" not in line and "platform" not in line:
                            if "Tune timeout on SerDes" not in line:
                                command_output.append(line)
                                # print(line)
                                output_file.write(line + '\n')
                output_file.close()

def statshow_error(statshow_list):

    start_index = statshow_list.index("   P#   Transmit      TxBytes     TxErr  Receive      RxBytes     RxFcs RxIpg RxCol OvrSz UndSz RxSym OvRun\r")
    # stop_index = statshow_list.index("Traf&gt; platform : 9300")
    stop_index = statshow_list.index("*************")
    lines = statshow_list[start_index:stop_index - 1]

    for line in lines:
        line.strip('\r')
        line.lstrip(' ')

    for line in lines:
        if "----" in line:
            lines.remove(line)

    for line in lines:
        if "P#   Transmit" in line:
            lines.remove(line)

    list_of_dict = []
    non_zero_error_portlist = []
    for line in lines:
        data = {}
        (data['P#'], data['Transmit'], data['TxBytes'], data['TxErr'], data['Receive'], data['RxBytes'], data['RxFcs'],
         data['RxIpg'], data['RxCol'], data['OvrSz'], data['UndSz'], data['RxSym'], data['OvRun']) = line.split()

        list_of_dict.append(data)

    for item in list_of_dict:
        if item["RxFcs"] != '00000' or item["RxIpg"] != '00000' or item["RxCol"] != '00000' or item["OvrSz"] != '00000' or item["UndSz"] != '00000' or item["RxSym"] != '00000' or item["OvRun"] != '00000':
            print(
                f'{bcolors.WARNING}{item["P#"]:<10} {item["Transmit"]:<10} {item["TxBytes"]:<10} {item["TxErr"]:<10} {item["Receive"]:<10} {item["RxBytes"]:<10} {item["RxFcs"]:<10} {item["RxIpg"]:<10} {item["RxCol"]:<10} {item["OvrSz"]:<10} {item["UndSz"]:<10} {item["RxSym"]:<10} {item["OvRun"]:<10} {bcolors.ENDC}')
            non_zero_error_portlist.append(item["P#"])

    print("non_zero_error_portlist", non_zero_error_portlist)
    if len(non_zero_error_portlist) == 0:
        print('all error counters are zero'.upper())
        print(f'{bcolors.BOLD}{bcolors.OKBLUE}{"P#":<10} {"Transmit":<10} {"TxBytes":<10} {"TxErr":<10} {"Receive":<10} {"RxBytes":<10} {"RxFcs":<10} {"RxIpg":<10} {"RxCol":<10} {"OvrSz":<10} {"UndSz":<10} {"RxSym":<10} {"OvRun":<10} {bcolors.ENDC}')

        for item in list_of_dict:
            print(
                f'{bcolors.OKGREEN}{item["P#"]:<10} {item["Transmit"]:<10} {item["TxBytes"]:<10} {item["TxErr"]:<10} {item["Receive"]:<10} {item["RxBytes"]:<10} {item["RxFcs"]:<10} {item["RxIpg"]:<10} {item["RxCol"]:<10} {item["OvrSz"]:<10} {item["UndSz"]:<10} {item["RxSym"]:<10} {item["OvRun"]:<10} {bcolors.ENDC}')
    else:
        print(f'{bcolors.BOLD}{bcolors.OKBLUE}{"P#":<10} {"Transmit":<10} {"TxBytes":<10} {"TxErr":<10} {"Receive":<10} {"RxBytes":<10} {"RxFcs":<10} {"RxIpg":<10} {"RxCol":<10} {"OvrSz":<10} {"UndSz":<10} {"RxSym":<10} {"OvRun":<10} {bcolors.ENDC}')
        for port in non_zero_error_portlist:
            print(port)
            if item in list_of_dict:
                print(f'{bcolors.WARNING}{item["P#"]:<10} {item["Transmit"]:<10} {item["TxBytes"]:<10} {item["TxErr"]:<10} {item["Receive"]:<10} {item["RxBytes"]:<10} {item["RxFcs"]:<10} {item["RxIpg"]:<10} {item["RxCol"]:<10} {item["OvrSz"]:<10} {item["UndSz"]:<10} {item["RxSym"]:<10} {item["OvRun"]:<10} {bcolors.ENDC}')

def diag_sfp_report(jobids, keywords, username, password, option):

    jobID_list = []
    for i in jobids.split(','):
        jobID_list.append(i.strip())
    print("USER INPUT: ", jobID_list)

    for jobid in jobID_list:
        sfp_type_result = []
        sfpeeprom_csv_file, total_corner, total_uut = sfp_tt3_log_request(jobid, username, password)

        print("sfpeeprom_csv_file", sfpeeprom_csv_file)
        print("total_corner", total_corner)
        print("total_uut", total_uut)

        for uut in total_uut:
            sfp_file_result = f'{jobid}_switch{uut}_sfp_result.txt'
            for corner in total_corner:
                list_of_port_dict, sfp_type_result = create_list_dict_sfp(sfpeeprom_csv_file, total_corner, uut, sfp_type_result)

                print(f"\nPROCESSING ON JOBID: {jobid} CORNERID: {corner} UNIT: {uut}")
                fail_port_single = check_sfp_diag_traffic(jobid, corner, uut, username, password)
                print_sfp_result(list_of_port_dict, fail_port_single, sfp_file_result, jobid, corner, uut)

        print_sfp_summary(jobid, sfp_type_result)


def sfp_tt3_log_request(jobid, username, password):
    "Retrieve SFP data from the the user-provided jobID list by making a request to TT3 \
    The SFP data will only come from the first corner of each JobID \
    then filter out all the unnecessary text then print out the table format"

    file_list = []
    first_cornerID, total_corner, total_uut = find_first_corner(jobid, username, password)

    # Request SFP data from the first CornerID
    sfpeeprom_csv_file = f"{jobid}_{first_cornerID}_SFEEPROM.csv"
    working_directory = str(os.getcwd())
    url = f"https://wwwin-testtracker3.cisco.com/trackerApp/oneviewlog/opticalData.csv?page=1&corner_id={first_cornerID}"

    # 1. Send HTTP Request with TT3 credentials
    response = requests.get(url, auth=(username, password))
    response.close()

    # 2. Use BeautifulSoup to extract text
    html = response.text
    soup = BeautifulSoup(html, features='html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    # Strip out space and double space
    lines = (line.strip() for line in text.splitlines())
    # Fix strange character from various sfp type
    lines = (line.replace("  (", " (") for line in lines)
    lines = (line.replace("],", ",") for line in lines)
    lines = (line.replace(",INC,", ",") for line in lines)
    lines = (line.replace(",0x10  -- unrecognized compliance code.,", ",0x10 unrecognized,") for line in lines)
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    # Strip off unnecessary text but keep SFPEEPROM data table
    stri = text[text.index('+++'):text.index('Show\n')]
    sections = re.split(r"\s*\+{10,}\s*", stri)
    # To strip blank element
    section_headers = [section.strip() for section in sections if section.strip()]

    for header in section_headers[::2]:
        # table_list.append(header)
        # Generate CSV file for SFEEPROM only
        if header == "SFEEPROM":
            table_name_file = os.path.join(working_directory, sfpeeprom_csv_file)
            file_list.append(table_name_file)

    # Map header and date into the generated csv file
    # writing sfp table  into a csv file
    for header, section_data in zip(section_headers[::2], section_headers[1::2]):
        for i in range(0, len(file_list)):
            if header in file_list[i]:
                # print('separating', header, 'table into a file')
                # file = open(file_list[i], "a")
                file = open(file_list[i], "w")
                file.write('+' * 35 + ' ' + header + ' ' + '+' * 35 + '\n')
                file.write(section_data)
                file.close()
    file_list = []

    return sfpeeprom_csv_file, total_corner, total_uut

def create_list_dict_sfp(sfpeeprom_csv_file, total_corner, unit, sfp_type_result):

    # sfp_type_result = []

    with open(sfpeeprom_csv_file, 'r') as input_file:
        lines = input_file.readlines()
        lines = lines[2:]

    # uut_list = []
    list_of_port_dict = []
    for line in lines:
        if "switch" + unit in line:
            s = {}
            (s["jobid"], s["cornerid"], s["uut"], s["port"], s["type"], s["vendor"], s["mfg"], s["sn"], s["create"],
             s["create_date"], s["update"], s["update_date"], s["slot"]) = line.split(",")

            # To add s["pid"] here
            # add a function to find pid from mfg number
            s["pid"] = find_pid_by_mfg(s["mfg"])
            s["port"] = s["port"].zfill(2)

            # This part is database mapping to find out type from mfg partnumber
            # print(s["type"])
            if s["type"] == "Data unavailable" or s["type"] == "0x0 (Non Standard)" or s["type"] == "0x80 (Unknown)" or \
                    s["type"] == "0x10 unrecognized":
                s["type"] = find_type_by_mfg(s["mfg"])
            else:
                s["type"] = re.search(r"\((.*?)\)", s["type"]).group(1)
                # TRY OVERWRITE TYPE IF MFG AVAILABLE IN DATABASE
                s["type"] = find_type_by_mfg(s["mfg"])

            if (s['type'], s['vendor'], s['mfg'], s['pid']) not in sfp_type_result:
                sfp_type_result.append((s['type'], s['vendor'], s['mfg'], s['pid']))

            # if s["vendor"] == "CISCO":8
            #     s["vendor"] = find_vendor_by_mfg(s["mfg"])

            s["vendor"] = find_vendor_by_mfg(s["mfg"])

            list_of_port_dict.append(s)

    input_file.close()
    return list_of_port_dict, sfp_type_result

def find_first_corner(jobid, username, password):
    "Find the first corner ID from the user-provided jobID list by making a request to TT3 \
    then filter out all the unnecessary text then return the first cornerID"

    url = f"https://wwwin-testtracker3.cisco.com/trackerApp/cornerTest/{jobid}"

    # 1. Send HTTP Request with TT3 credentials
    response = requests.get(url, auth=(username, password))
    response.close()

    # 2. Use BeautifulSoup to extract text
    html = response.text

    total_corner = extract_total_corner(html)
    total_uut = extract_total_uut(html)

    soup = BeautifulSoup(html, features='html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()

    # Fix double space has issue
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    # Remove all the other sting but first cornerID
    stri = text[text.index('Select Corners to delete:'):text.index(
        '* Press Submit to Delete the Corners, Cancel to Return')]
    cornerID_list = list(stri.split('\n'))
    cornerID_list.remove('Select Corners to delete:')
    first_CornerID = cornerID_list[0]

    return first_CornerID, total_corner, total_uut

def find_type_by_mfg(lookup_mfg):
    input_file = open('SFPs_Database.csv')
    for line in input_file:
        data = {}
        (data['type'], data['vendor'], data['mfg'], data['pid'], data['sn']) = line.split(',')
        if data['mfg'] == lookup_mfg:
            input_file.close()
            return data["type"]
    input_file.close()
    return "Not in Database"

def find_pid_by_mfg(lookup_mfg):
    input_file = open('SFPs_Database.csv')
    for line in input_file:
        data = {}
        # print(line) # Debug not enough values to unpack.
        # Most of the time caused from extra blank line in SFP database txt file
        (data['type'], data['vendor'], data['mfg'], data['pid'], data['sn']) = line.split(',')
        if data['mfg'] == lookup_mfg:
            input_file.close()
            return data["pid"]
    input_file.close()
    return "Not in Database"

def find_vendor_by_mfg(lookup_mfg):
    input_file = open('SFPs_Database.csv')
    for line in input_file:
        data = {}
        (data['type'], data['vendor'], data['mfg'], data['pid'], data['sn']) = line.split(',')
        if data['mfg'] == lookup_mfg:
            input_file.close()
            return data["vendor"]
    input_file.close()
    return "Not in Database"

def extract_total_uut(html):
    uut_match = re.findall(r'UUT\d+ </span></td>', html)
    total_uut = []

    for match in uut_match:
        uut_id = re.search(r'\d+', match).group(0)
        if uut_id not in total_uut:
            total_uut.append(uut_id)
    return total_uut

def extract_total_corner(html):
    corner_match = re.findall(r'data-cornerid="\d+"', html)
    total_corner = []

    for match in corner_match:
        corner_id = re.search(r'\d+', match).group(0)
        if corner_id not in total_corner:
            total_corner.append(corner_id)
    return total_corner

def check_sfp_diag_traffic(jobid, corner, uut, username, password):

    result = []

    url = f"https://wwwin-testtracker3.cisco.com/trackerApp/oneviewlog/switch{uut}.log?page=1&corner_id={corner}"
    print(f'\nJobID:{jobid} CornerID:{corner} switch{uut}\n{url}')

    response = requests.get(url, auth=(username, password))
    response.close()
    html_log = response.text

    html_log_name = f"{jobid}_{corner}_uut{uut}_html_log.txt"
    data = {"cornerid": corner, "uut": uut, "logfile": html_log_name, "failures": [], "uutinfo": []}
    result.append(data)
    content = html_log[html_log.index("TESTCASE START"):html_log.index(f"{corner} Complete")]

    # To add option if need a local html log
    with open(html_log_name, "w") as local_log:
        local_log.write(content)

    for item in result:
        f = open(item["logfile"], "r")
        text = f.read()
        content = text[text.index("TESTCASE START"):text.index("Corner - runSwitch")]
        lines = content.splitlines()
        for line in lines:
            if "SYSTEM_SERIAL_NUM" in line:
                if line not in item['uutinfo']:
                    item['uutinfo'].append(line.strip())

            # SEARCH FOR FAILED PORTS
            if re.search(r'FAIL\*\*\s+[a-zA-Z]', line):
                data = {}
                if line not in item['failures']:
                    item['failures'].append(line)
        f.close()
    os.remove(item["logfile"])

    # Find failed traffic combination
    traf_failures = []
    traffic_failed_combination_list = []

    for item in result:
        switch_number = 'switch' + item['uut']

        for info in item['uutinfo']:
            if "SYSTEM_SERIAL" in info:
                serial_number = info
                print(f"{serial_number}")

        for failure in item['failures']:
            print(failure)
            if "Ext" in failure:
                data = {}
                (data['conver'], data['portpair'], data['iter'], data['duration'], data['status'], data['error'],
                 data['duration'], data['portresult'], data['traftype'], data['speed'], data['size']) = failure.split()
                traf_failures.append(data)

    for item in traf_failures:
        for key in ["conver", "iter", "duration", "status", "portresult"]:
            item.pop(key)
        if item not in traffic_failed_combination_list:
            traffic_failed_combination_list.append(item)

    # Find failed portpair and convert into single port list
    fail_portpair = []
    fail_port_single = []
    for item in traffic_failed_combination_list:
        if item["portpair"] not in fail_portpair:
            fail_portpair.append(item["portpair"])

            # To create a new list with a single port to map with the SFP list in the future
            first_port, second_port = item["portpair"].split('/')
            if first_port not in fail_port_single or second_port not in fail_port_single:
                fail_port_single.append(first_port.zfill(2))
                fail_port_single.append(second_port.zfill(2))
    fail_port_single.sort()

    # Find failed speeds - for future report
    fail_speed = []
    for item in traffic_failed_combination_list:
        if item["speed"] not in fail_speed:
            fail_speed.append(item["speed"])
    # print("failed speeds are : ", *fail_speed, sep='\n\t')

    # Find failed sizes - for future report
    fail_size = []
    for item in traffic_failed_combination_list:
        if item["size"] not in fail_size:
            fail_size.append(item["size"])
    # print("failed size are : ", *fail_size, sep='\n\t')

    return fail_port_single

def print_sfp_result(list_of_port_dict, failed_port_single, sfp_file_result, jobid, corner, uut):
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    # Add to write result in file
    with open(sfp_file_result, "a") as sfp_file_result:

        sfp_file_result.write('\n' + f'JobID:{jobid} CornerID:{corner} switch{uut}' + '\n')
        print(f'{bcolors.BOLD}{bcolors.OKBLUE}-{bcolors.ENDC}' * 150)
        sfp_file_result.write('-' * 150 + '\n')

        print(f'{bcolors.BOLD}{bcolors.OKBLUE}{"port":<10} {"sfp_type":<20} {"Cisco PID":<20} {"sfp_vendor":<20} {"mfg_number":<20} {"serial_number":<20} {"port_result"}{bcolors.ENDC}')
        sfp_file_result.write(f'{"port":<10} {"sfp_type":<20} {"Cisco PID":<20} {"sfp_vendor":<20} {"mfg_number":<20} {"serial_number":<20} {"port_result"}' + '\n')
        print(f'{bcolors.BOLD}{bcolors.OKBLUE}-{bcolors.ENDC}' * 150)
        sfp_file_result.write('-' * 150+ '\n')

        # print(list_of_port_dict)
        list_of_port_dict = sorted(list_of_port_dict, key=lambda k: k['port'])

        for item in list_of_port_dict:
            item.update(port_result="pass")

            for failed_port in failed_port_single:
                if item["port"] == failed_port:
                    item.update(port_result="fail")

            if item["port_result"] == "fail":
                print(
                    f'{bcolors.FAIL}{item["port"].strip("]"):<10} {item["type"]:<20} {item["pid"]:<20} {item["vendor"]:<20} {item["mfg"]:<20} {item["sn"]:<20} {item["port_result"]:<20}{bcolors.ENDC}')
                sfp_file_result.write(f'{item["port"].strip("]"):<10} {item["type"]:<20} {item["pid"]:<20} {item["vendor"]:<20} {item["mfg"]:<20} {item["sn"]:<20} {item["port_result"]} ***' + "\n")
            else:
                print(
                    f'{bcolors.OKGREEN}{item["port"].strip("]"):<10} {item["type"]:<20} {item["pid"]:<20} {item["vendor"]:<20} {item["mfg"]:<20} {item["sn"]:<20} {item["port_result"]:<20}{bcolors.ENDC}')
                sfp_file_result.write(f'{item["port"].strip("]"):<10} {item["type"]:<20} {item["pid"]:<20} {item["vendor"]:<20} {item["mfg"]:<20} {item["sn"]:<20} {item["port_result"]:<20}' + '\n')

    sfp_file_result.close()

def print_sfp_summary(jobid, sfp_type_result):

    with open(f"{jobid}_sfps_types_summary.txt", "w") as output_file:
        # PRINT CSV SUMMARY
        print("\n--------------------------------------------")
        output_file.write("\n--------------------------------------------\n")
        print(f"RESULT THERE ARE TOTAL {len(sfp_type_result)} VARIATIONS OF SFPS")
        output_file.write(f"RESULT THERE ARE TOTAL {len(sfp_type_result)} VARIATIONS OF SFPS\n")
        print("--------------------------------------------")
        output_file.write("--------------------------------------------\n")

        print(f'NO,TYPE,PID,VENDOR,MFG_PARTNUM')
        output_file.write(f'NO,TYPE,PID,VENDOR,MFG_PARTNUM\n')

        for index, item in enumerate(sfp_type_result, 1):
            item_list = list(item)
            print(f'{index},{item_list[0]},{item_list[3]},{item_list[1]},{item_list[2]}')
            output_file.write(f'{index},{item_list[0]},{item_list[3]},{item_list[1]},{item_list[2]}' + '\n')

        # JUST IN CASE NEED TO PRINT TEXT SUMMARY
        # print("\n----------------------------------")
        # print(f"RESULT THERE ARE TOTAL {len(sfp_type_result)} VARIATIONS")
        # print("----------------------------------")
        # for index, item in enumerate(sfp_type_result):
        #     print(f"\nITEM# {index}")
        #     print("----------------------------------")
        #     item_list = list(item)
        #     print("TYPE: " + item_list[0])
        #     print("VENDOR: " + item_list[1])
        #     print("MFG PARTNUM: " + item_list[2])
        #     print("CISCO PID: " + item_list[3])

    output_file.close()

############ MAIN ################

if __name__ == '__main__':

    banner = text2art("EDVT \nLog Scrubber", space=1)
    print("\n" + banner + "\n")

    print('Enter CEC username and password in the popup window')
    username = pyautogui.prompt('input your cec username: ')
    password = pyautogui.password('input your password: ')
    if len(username) == 0 or len(password) == 0:
        print("Username and Password can't be blank. Please restart the program")
        quit()

    jobids = input("Enter JOBID (separate by comma for multiples): ")

    options = input(f'\nSelect from options below \n\
    \n\
    1 - search by keywords \n\
    2 - filter specific command output \n\
    3 - ixia diag failure \n\
    4 - istardust diag traffic failure \n\
    5 - istardust poe diag traffic failure \n\
    6 - diag traffic failure \n\
    7 - arcadecr vdd_avs check \n\
    8 - pwrcycle diag suite \n\
    9 - diag traffic sfp report \n\
    \n\
    Please enter the number: ')

    if options == "1":
        # keywords = " MODEL_NUM,  SYSTEM_SERIAL, Test(s) failed:, test(s) failed"
        option = "keyword_search"
        keywords = input("Enter keywords separate by comma: ")
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "2":
        option = "command_output"
        command = input("Enter the command: ")
        command = "command is : {" + command
        command_output_request(jobids, command, username, password, option)

    elif options == "3":
        option = "ixia_diag"
        command = "statshow"
        command = "command is : {" + command
        statshow_diag_scrub(jobids, command, username, password, option)

    elif options == "4":
        option = "istardust_traffic"
        keywords = "TESTCASE START -, FAILED VALIDATION -, Pass Fail, Fail Pass, Fail Fail, Status: Failed, ERROR DOYLE_FPGA, FAILED: Timeout,  ERROR: Leaba_Err"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "5":
        option = "istardust_poe_traffic"
        # keywords = "TESTCASE START -, FAILED VALIDATION -, 0W; 0W; 0W,Pass Fail, Fail Pass, Fail Fail, Status: Failed, ERROR DOYLE_FPGA, FAILED: Timeout,  ERROR: Leaba_Err"
        keywords = "TESTCASE START -, FAILED VALIDATION -, FAILED VALIDATION while, Pass Fail, Fail Pass, Fail Fail, Status: Failed, ERROR DOYLE_FPGA, FAILED: Timeout,  ERROR: Leaba_Err"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "6":
        option = "diag_traffic"
        keywords = "FAILED VALIDATION while, FAILED VALIDATION -, FAIL**  E, FAIL**  P, TESTCASE START -"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "7":
        option = "vdd_avs_search"
        keywords = "SYSTEM_SERIAL_NUM, VDD_AVS |"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "8":
        option = "pwrcycle_diag_suite"
        keywords = "Test(s) failed:,  FAILED VALIDATION -, FAILED: Timeout, TESTCASE START -, FAIL*"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "9":
        option = "diag_traffic_sfp_report"
        keywords = "FAILED VALIDATION while, FAILED VALIDATION -, FAIL**  E, FAIL**  P, TESTCASE START -"
        diag_sfp_report(jobids, keywords, username, password, option)

