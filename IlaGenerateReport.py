import base64
from bs4 import BeautifulSoup
import datetime
import smtplib
import json
from datetime import date
from email.message import EmailMessage
from email.utils import make_msgid
import numpy as np
import matplotlib.pyplot as plt

# files used
BH_report = 'HTML Files/reportBH.html'
JO_report = 'HTML Files/reportJO.html'
Bar_graph = 'Generated Graphs/output.jpg'
BH_JSON_name = 'JSON Files/BH_JSON.json'
JO_JSON_name = 'JSON Files/JO_JSON.json'

# -------------------- Vriables ---------------

day = datetime.datetime.now()
Today_Date = str(date.today()) + ' ' + day.strftime("%a")


# image section
def createImageTag(file_name):
    data_uri = base64.b64encode(open(file_name, 'rb').read()).decode('utf-8')
    img_tag = '<img src="data:image/png;base64,{0}" style="height: 300px;width: 700px;">'.format(data_uri)
    return img_tag


# total, pass, fail values from HTML
def getcount(file_name):
    with open(file_name) as f:
        html_doc = f.read()
    soup = BeautifulSoup(html_doc, 'html.parser')
    scenario_total_count = len(soup.find_all('div', attrs={'class': 'card iteration-0'}))
    scenario_fail_count = int(soup.find('a', {'id': 'pills-failed-tab'}).find('span', {'class': 'badge'}).text)
    scenario_pass_count = scenario_total_count - scenario_fail_count

    # Get failed scenarios:
    failure_list = []
    for sp in soup.find_all("div", class_="card iteration-0"):
        for danger in sp.findChildren("div", class_="bg-danger"):
            for failure in danger.findChildren("a"):
                # print(failure.text.strip().replace("Iteration: 1 - ", ""))
                failure_list.append(failure.text.strip().replace("Iteration: 1 - ", ""))

    if len(failure_list) < 1:
        failure_list.append("No failed cases")

    return scenario_total_count, scenario_pass_count, scenario_fail_count, failure_list


# Create DICTIONARY OF Pass, fail and total
def createDict(filee_name):
    total, passed, failed, failed_scenarios = getcount(filee_name)
    new_dict = {
        'Total': total,
        'Pass': passed,
        'Fail': failed,
        'Failed Scenarios': failed_scenarios
    }
    return new_dict


# update json
def createUpdateJSON(json_filee_name, html_file_name):
    new_key = Today_Date
    new_value = createDict(html_file_name)
    with open(json_filee_name, 'r') as f:
        data = json.load(f)
        data[new_key] = new_value
    with open(json_filee_name, 'w') as f:
        json.dump(data, f, indent=2)


def openJSONFile(file_name):
    with open(file_name, 'r') as BH:
        data = json.load(BH)
    return data


def substitueValues(data_file, subValue):
    value_data = np.array(list(data_file.values()))
    subVal = [sub[subValue] for sub in value_data]
    return subVal


def doreplace(text):
    for char in ["[", "]", "'"]:
        # replace() "returns" an altered string
        text = text.replace(char, "")
    return text


def createTableForDetailedTRENDS(json_file_BH, json_file_JO):
    html = "<table>"
    html += "<tr style='background-color: #305496;'><th colspan='3' style='color: azure; border-color: black; font-size: medium;'> Detailed Execution trend - last 7 days </th></tr><tr style='background-color: #8EA9DB;'><th style='font-size: small;'> Dates </th> <th style='font-size: small;'> Bahrain </th> <th style='font-size: small;'> Jordan </th></tr>"

    BH_data = openJSONFile(json_file_BH)
    JO_data = openJSONFile(json_file_JO)
    dates = list(BH_data.keys())
    BH_FAILURES = substitueValues(BH_data, 'Failed Scenarios')
    JO_FAILURES = substitueValues(JO_data, 'Failed Scenarios')

    for i in range(0, 7):

        if i in (0, 2, 4, 6):
            Dcolor = "#B4C6E7"
            Pcolor = "#C6E0B4"
            Fcolor = "#E81828"
        else:
            Dcolor = "#D9E1F2"
            Pcolor = "#A9D08E"
            Fcolor = "#ED1C24"

        BHval = "<td style = 'background-color:" + Fcolor + ";text-align: left;'>" + doreplace(
            str(BH_FAILURES[i])) + "</td>"
        JOval = "<td style = 'background-color:" + Fcolor + ";text-align: left;'>" + doreplace(
            str(JO_FAILURES[i])) + "</td>"

        if "No failed" in BHval:
            BHval = "<td style = 'background-color:" + Pcolor + ";'>" + doreplace(str(BH_FAILURES[i])) + "</td>"
        elif "No failed" in JOval:
            JOval = "<td style = 'background-color:" + Pcolor + ";'>" + doreplace(str(JO_FAILURES[i])) + "</td>"

        html += "<tr><td style = 'background-color:" + Dcolor + ";text-align: center;'>" + str(
            dates[i]) + "</td>" + BHval + " " + JOval + "</tr>"

    html += "</table>"
    return html


def plotBarGraph(json_file_BH, json_file_JO, division):
    width = 0.4
    img_location = "Graphs/" + division + ".jpg"

    BH_data = openJSONFile(json_file_BH)
    JO_data = openJSONFile(json_file_JO)

    dates = list(BH_data.keys())

    # sub-dividing the values
    BH_pass_list = substitueValues(BH_data, 'Pass')
    BH_fail_list = substitueValues(BH_data, 'Fail')
    JO_pass_list = substitueValues(JO_data, 'Pass')
    JO_fail_list = substitueValues(JO_data, 'Fail')
    jototal = substitueValues(JO_data, 'Total')
    bhtotal = substitueValues(BH_data, 'Total')

    lastSevenDates = dates[-7:]
    bh_pass_data = BH_pass_list[-7:]
    bh_fail_data = BH_fail_list[-7:]
    jo_pass_data = JO_pass_list[-7:]
    jo_fail_data = JO_fail_list[-7:]
    jototoaldata = jototal[-7:]
    bhtotaldata = bhtotal[-7:]

    maxTotal = max(jototoaldata, bhtotaldata)

    barvalues = np.arange(len(lastSevenDates))
    bars = [i + width for i in barvalues]

    shortDates = ''
    for i in lastSevenDates:
        shortDates += str(i.replace('2023-', ''))[:-3] + '    '

    b1 = plt.bar(lastSevenDates, bh_pass_data, width, color='green', edgecolor='black', linewidth=1, label='Pass')
    b2 = plt.bar(barvalues, bh_fail_data, width, bottom=bh_pass_data, color='red', edgecolor='black', linewidth=1,
                 label='Fail')

    b3 = plt.bar(bars, jo_pass_data, width, color='green', edgecolor='black', linewidth=1)
    b4 = plt.bar(bars, jo_fail_data, width, bottom=jo_pass_data, color='red', edgecolor='black', linewidth=1)

    for rect1, rect2 in zip(b1, b2):
        height1 = rect1.get_height()
        height2 = rect2.get_height()
        plt.text(rect1.get_x() + rect1.get_width() / 2., height1 / 2.,
                 '%d' % int(height1), ha='center', va='bottom')
        plt.text(rect2.get_x() + rect2.get_width() / 2., height1 + height2 / 2.,
                 '%d' % int(height2), ha='center', va='bottom')
    for rect1, rect2 in zip(b3, b4):
        height1 = rect1.get_height()
        height2 = rect2.get_height()
        plt.text(rect1.get_x() + rect1.get_width() / 2., height1 / 2.,
                 '%d' % int(height1), ha='center', va='bottom')
        plt.text(rect2.get_x() + rect2.get_width() / 2., height1 + height2 / 2.,
                 '%d' % int(height2), ha='center', va='bottom')

    plt.xlabel(shortDates)
    my_xticks = ['  BH   JO', '  BH   JO', '  BH   JO', '  BH   JO', '  BH   JO', '  BH   JO', '  BH   JO']
    plt.xticks(barvalues, my_xticks)
    plt.ylabel("PASS/ FAIL STATUS")
    plt.legend()
    plt.ylim(0, max(maxTotal) + 10)
    plt.title("Execution Trends For Last 7 Days - BH and JO")
    plt.savefig(img_location)
    img_tg = createImageTag(img_location)
    return img_tg


def createOverallExecutionTable(BH_JSON_nam, JO_JSON_nam):
    BH_data = openJSONFile(BH_JSON_nam)
    JO_data = openJSONFile(JO_JSON_nam)

    BH_pass_list = substitueValues(BH_data, 'Pass')
    BH_fail_list = substitueValues(BH_data, 'Fail')
    JO_pass_list = substitueValues(JO_data, 'Pass')
    JO_fail_list = substitueValues(JO_data, 'Fail')
    BH_Total_list = substitueValues(BH_data, 'Total')
    JO_Total_list = substitueValues(JO_data, 'Total')

    revisedScope = 800
    totalTCs = sum(BH_Total_list) + sum(JO_Total_list)
    totalPassTCs = sum(BH_pass_list) + sum(JO_pass_list)
    totalFailTCs = sum(BH_fail_list) + sum(JO_fail_list)
    tcPerc = round((totalTCs / revisedScope) * 100, 2)
    passPerc = round((totalPassTCs / totalTCs) * 100, 2)
    failPerc = round((totalFailTCs / totalTCs) * 100, 2)
    execPending = revisedScope - totalTCs
    excPerc = round((execPending / revisedScope) * 100, 2)

    html = "<table style='height: 163px;'><tr><th colspan='3' style='background-color: #305496; color: azure; border-color: black; font-size: small; '>Overall Execution Status </th> </tr> <tr> <th style='background-color: #8EA9DB; border-color: black; text-align: left; width: 25%;'>   Revised Scope</th><td style='background-color: #70AD47;'>" + str(
        revisedScope) + "</td><th style='background-color: #305496; color: azure; border-color: black; '>  Progress in %</th></tr><tr><th style='background-color: #8EA9DB; border-color: black; text-align: left;'>   Total TCs Executed</th><td style = 'background-color:#C6E0B4'>" + str(
        totalTCs) + " </td><td style = 'background-color:#C6E0B4'> " + str(
        tcPerc) + " %</td></tr><tr><th style='background-color: #8EA9DB; border-color: black; text-align: left;'>   TCs Passed</th><td style = 'background-color:#A9D08E'> " + str(
        totalPassTCs) + "  </td><td style = 'background-color:#A9D08E'> " + str(
        passPerc) + " %</td></tr><tr><th style='background-color: #8EA9DB; border-color: black; text-align: left;'>   TCs Failed</th><td style = 'background-color:#C6E0B4'>  " + str(
        totalFailTCs) + " </td><td style = 'background-color:#C6E0B4'>  " + str(
        failPerc) + " %</td></tr><tr><th style='background-color: #8EA9DB; border-color: black; text-align: left;'>   Execution Pending</th><td style = 'background-color:#A9D08E; color: #E81828; font-size: small;' > " + str(
        execPending) + " </td><td style = 'background-color:#A9D08E; color: #E81828; font-size: small;'> " + str(
        excPerc) + " %</td></tr></table> "

    return html


def createExecutionStatus(json_file_BH, json_file_JO):
    BH_Total, BH_Pass, BH_Fail, BH_FAILURES = getcount(BH_report)
    JO_Total, JO_Pass, JO_Fail, JO_FAILURES = getcount(JO_report)

    if len(BH_FAILURES) > len(JO_FAILURES):
        for i in range(len(JO_FAILURES), len(BH_FAILURES)):
            JO_FAILURES.append("")
    else:
        for i in range(len(BH_FAILURES), len(JO_FAILURES)):
            BH_FAILURES.append("")

    html = "<table> <tr style='background-color: #305496;'> <th colspan='4'style='color: azure; border-color: black; font-size: medium;'> Daily Execution Report - " + Today_Date + " </th> </tr> <tr style='background-color: #8EA9DB;'><th colspan='2' style='border: 1px solid; font-size: small;'>Bahrain execution</th><th colspan ='2' style='font-size: small;'> Jordan Execution</th></tr> <tr><td style='background-color: #B4C6E7;'> Total TCs </td><td style='background-color: #C6E0B4;'>" + str(
        BH_Total) + "</td><td style='background-color: #B4C6E7;'> Total TCs </td><td style='background-color: #C6E0B4;'>" + str(
        JO_Total) + "</td></tr>  <tr><td style='background-color: #B4C6E7;'> Pass TCs </td><td style='background-color: #A9D08E;'>" + str(
        BH_Pass) + "</td><td style='background-color: #B4C6E7;'> Pass TCs </td><td style='background-color: #A9D08E;'>" + str(
        JO_Pass) + "</td></tr> <tr><td style='background-color: #B4C6E7;'> Failed TCs </td><td style='background-color: #C6E0B4; color: red; border-color: black;'>" + str(
        BH_Fail) + "</td><td style='background-color: #B4C6E7;'> Failed TCs </td><td style='background-color: #C6E0B4; color: red; border-color: black;'>" + str(
        JO_Fail) + "</td></tr> <tr><th colspan= '4' style='background-color: #305496; font-size: medium; color: azure; '> Failed Cases for today </th></tr> <tr style='background-color: #8EA9DB;'><th colspan='2' style='border: 1px solid; font-size: small;'>Bahrain execution</th><th colspan ='2' style='font-size: small;'> Jordan Execution</th></tr>"

    for i in range(0, len(BH_FAILURES)):
        if (i % 2) == 0 or i == 0:
            Pcolor = "#C6E0B4"
            Fcolor = "#E81828"
        else:
            Pcolor = "#A9D08E"
            Fcolor = "#ED1C24"

        BHval = "<td colspan='2' style = 'background-color:" + Fcolor + ";text-align: left;'>" + doreplace(
            str(BH_FAILURES[i])) + "</td>"
        JOval = "<td colspan='2' style = 'background-color:" + Fcolor + ";text-align: left;'>" + doreplace(
            str(JO_FAILURES[i])) + "</td>"

        if "No failed" in BHval:
            BHval = "<td colspan='2' style = 'background-color:" + Pcolor + ";' >" + doreplace(
                str(BH_FAILURES[i])) + "</td>"
        elif "No failed" in JOval:
            JOval = "<td colspan='2' style = 'background-color:" + Pcolor + ";'>" + doreplace(
                str(JO_FAILURES[i])) + "</td>"

        html += "<tr>" + BHval + " " + JOval + "</tr>"

    html += "</table>"
    return html


# for JSON updation
createUpdateJSON(BH_JSON_name, BH_report)
createUpdateJSON(JO_JSON_name, JO_report)


# HTML CODE
mssg = EmailMessage()
mssg['Subject'] = "ila Mobile Health Check Sanity Status - BH & JO - " + str(Today_Date)
asparagus_cid = make_msgid()
mssg.add_alternative("""\
<html lang="en">
<head>
    <style>
        table {
            font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
            font-size: smaller;
            table-layout: auto;

            border-collapse: collapse;
            border-color: black;
            white-space: nowrap;
        }
        tr {
            border: 1px solid;
            text-align: center;
        }
        th {
            height: 25px;
            border: 1px solid;
        }
        td {
            border: 1px solid;
            text-align: center;
            width: 350px;  
            border-color: black; 
        }
    </style>
</head>
<body>
    <div>
        <br>
        Hello Team, <br>
        Please find the following data attached for the todays execution.
        <br><br>
    </div>
    <table>
        <tr>
            <td style="width: 40%;vertical-align: top; border-color: white;">
            """ + createExecutionStatus(BH_report, JO_report) + """ <br/> 
            """ + createOverallExecutionTable(BH_JSON_name, JO_JSON_name) + """  


            </td>
            <td style="width: 60%;vertical-align: top; text-align: left;border-color: white;">
            """ + createTableForDetailedTRENDS(BH_JSON_name, JO_JSON_name) + """          
            <br/>
            """ + plotBarGraph(BH_JSON_name, JO_JSON_name, "BH and JO") + """        
            </td>
        </tr>        
    </table>
        <br>
        Warm Regards, <br>
        Tech Intervention Team.
        <br><br>

</body>
</html>
""".format(asparagus_cid=asparagus_cid[1:-1]), subtype='html')

# Mail-setup
smtp_server = 'smtp.office365.com'
smtp_port = 587
smtp_username = 'ilaapphealthcheck@maveric-systems.com'
smtp_password = 'Maveric@6781'
smtp_from = 'ilaapphealthcheck@maveric-systems.com'
smtp_to = ['akshaypa@maveric-systems.com']

# sending mail
mail_server = smtplib.SMTP(smtp_server, smtp_port)
mail_server.ehlo()
mail_server.starttls()
mail_server.login(smtp_username, smtp_password)
mail_server.sendmail(smtp_from, smtp_to, mssg.as_string())
# mail_server.send_message(mssg)
mail_server.quit()
