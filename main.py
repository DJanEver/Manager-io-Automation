import requests
import json
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, Frame
from reportlab.lib.colors import HexColor
import numpy as np
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.units import inch
from heroku import *
import datetime
import sys


API_LIST_FILENAME = "api-list.json"
API_KEY_JSON = API_KEY + ".json"
PAYSLIP_LIST_FILENAME = "payslip-list.json"
PAYROLL_DATE=datetime.datetime.today()


def fetchApiList():
    response = requests.get(f"https://{COMPANY_NAME}/api/{API_KEY_JSON}", auth=(USERNAME, PASSWORD))
    print(response)
    return response


def createApiList():
    with open(API_LIST_FILENAME, "wb") as file:
        file.writelines(fetchApiList())


def searchMainApiList(itemValue, fileName, key):
    jsonFile = open(fileName)
    jsonData = json.load(jsonFile)

    for keyVey in jsonData:
        if (itemValue == keyVey[key]):
            return keyVey["Key"]

    print("No Payslips")
    os.remove(API_LIST_FILENAME)
    sys.exit()


createApiList()
EMP_LIST_KEY = searchMainApiList("Employee", API_LIST_FILENAME, "Name")
PAYSLIP_LIST_KEY = searchMainApiList("Payslip", API_LIST_FILENAME, "Name")


def fetchEmpInfo(empKey):
    empKeyJson = empKey + ".json"
    response = requests.get(f"https://{COMPANY_NAME}/api/{API_KEY}/{EMP_LIST_KEY}/{empKeyJson}",
                            auth=(USERNAME, PASSWORD))
    return response


def fetchPayslipList():
    payslipListKey = PAYSLIP_LIST_KEY + ".json"
    response = requests.get(f"https://{COMPANY_NAME}/api/{API_KEY}/{payslipListKey}", auth=(USERNAME, PASSWORD))
    return response


def createPayslipList():
    with open(PAYSLIP_LIST_FILENAME, "wb") as file:
        file.writelines(fetchPayslipList())


createPayslipList()


def fetchPayslipKey(key):
    keyJson = key + ".json"
    response = requests.get(f"https://{COMPANY_NAME}/api/{API_KEY}/{PAYSLIP_LIST_KEY}/{keyJson}", auth=(USERNAME,
                                                                                                        PASSWORD))
    return response


def fetchPayslipItems(key, itemKey):
    itemJson = itemKey + ".json"
    response = requests.get(f"https://{COMPANY_NAME}/api/{API_KEY}/{PAYSLIP_LIST_KEY}/{key}/{itemJson}",
                            auth=(USERNAME, PASSWORD))

    return response


def populateDictionaries(keyTitle, supKey, key):
    value = fetchPayslipKey(key)
    data = dict(value.json())
    dataItemList = []
    if (checkForItem("employee", key)):
        if (checkForItem(keyTitle, key)):
            for keyVal in data.get(keyTitle):
                try:
                    keyValJson = keyVal["Item"] + ".json"
                    dataJson = dict(fetchPayslipItems(key, keyValJson).json())
                    dataItemList.append(dataJson.get("Name"))
                    rate = "{:,.2f}".format(keyVal[supKey])
                    dataItemList.append(rate)
                except:
                    print("Unable to append item for "+keyTitle + " with key=" + key)
            return dataItemList
        else:
            return dataItemList
    else:
        return dataItemList


def checkPayslipDate2(payslipData):
    payslipMonth = datetime.datetime.strptime(payslipData.get("Date"),'%Y-%m-%d').replace(day=1, hour=0, minute=0, second=0, microsecond=0) 
    currentMonth = PAYROLL_DATE.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    flag = False
    if payslipMonth == currentMonth:
        flag = True   
    return flag
    
    
def checkPayslipDate(payslipData):
    #payslipDate = payslipData.get("Date").split("-")
    payslipDate = payslipData.get("Date")
    print(payslipDate)
    print(PAYROLL_DATE)
    currentDate = PAYROLL_DATE #datetime.date.today()
    year = PAYROLL_DATE.year #currentDate.year
    month = PAYROLL_DATE.month #currentDate.month
    count = 0
    flag = False
    secFlag = False
    monthString = str(month)
    newMonthString = ""

    if(len(monthString) == 1):
        newMonthString = '0' + monthString
        secFlag = True
    while not flag:
        if payslipDate[count] == str(year):
            count += 1
            currentString = newMonthString if secFlag else monthString
            if payslipDate[count] == currentString:
                flag = True
            else:
                break
        else:
            break
    return flag


def checkForItem(keyTitle, key):
    value = fetchPayslipKey(key)
    data = dict(value.json())
    if (data.get(keyTitle) is None):
        return False
    return True


def checkForEarnings(keyTitle, subKey, key):
    value = fetchPayslipKey(key)
    data = dict(value.json())
    for keyVal in data.get(keyTitle):
        if (dict(keyVal).get("Item") is None or dict(keyVal).get(subKey) is None or len(list(keyVal)) == 0):
            return False
    return True


def populateEmpDictionaries(keyTitle, supKey, key):
    value = fetchPayslipKey(key)
    data = dict(value.json())
    dataItemList = []
    if (checkForItem("employee", key)):
        if (checkForItem(keyTitle, key)):
            for keyVal in data.get(keyTitle):
                keyValJson = keyVal["Item"] + ".json"
                dataJson = dict(fetchPayslipItems(key, keyValJson).json())
                dataItemList.append(dataJson.get("Name"))
                rate = "{:,.2f}".format(keyVal[supKey])
                dataItemList.append(rate)
            return dataItemList
        else:
            return dataItemList
    else:
        return dataItemList


def returnPayslipData(key):
    value = fetchPayslipKey(key)
    data = dict(value.json())
    return data


def getEmpFromPayslip(key):
    value = fetchPayslipKey(key)
    data = dict(value.json())
    empData = dict(fetchEmpInfo(data.get("employee")).json())
    return empData


def createEmpJson(payslipData, empData, key):
    empEList = populateEmpDictionaries("Earnings", "UnitPrice", key)
    empDecList = populateDictionaries("Deductions", "DeductionAmount", key)
    #if (len(empEList) != 0 and len(empDecList) != 0):
    if (len(empEList) != 0):
        creatingPdf(empData, payslipData, calEmpGross("Earnings", "UnitPrice", key),
                    deductionCal("Deductions", "DeductionAmount", key),
                    empEList, empDecList)
        emailingService(empData)
        # delEmpPayslip(key)
        delFiles(empData.get("Name") + "_payslip.pdf")


def pdfTableFormat(empEarningsList, empDecList, empGross, empNet):
    splitInto = len(empEarningsList) / 2
    splits = np.array_split(empEarningsList, splitInto)

    border = 2
    ePos = 0
    #
    empPayslipTable = [
        ["Description", "Total"]
    ]
    for array in splits:
        empPayslipTable.append(list(array))
        border += 1
        ePos += 1
    empPayslipTable.append(["Gross pay", empGross])
    
    
    splitIntoDec = len(empDecList) / 2
    
    try:
        splitsDec = np.array_split(empDecList, splitIntoDec)
    
        for array in splitsDec:
            empPayslipTable.append(list(array))
            border += 1
    except:
        print("Unable to append deductions to table")
        
        
    empPayslipTable.append(["Net pay", empNet])

    #
    num = 1
    flag = True
    borderStyles = [("BOX", (0, 0), (0, 0), 1, HexColor("#000000")), ("BOX", (1, 0), (1, 0), 1, HexColor("#000000")),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 7), ]

    while (num <= border):
        if (num == 1 and flag == True):
            borderStyles.append(("BOX", (1, num), (1, ePos), 1, HexColor("#000000")))
            borderStyles.append(("BOTTOMPADDING", (1, num), (1, ePos), 7))
            borderStyles.append(("RIGHTPADDING", (1, num), (1, ePos), 7))
            flag = False
        else:
            if (num > ePos):
                borderStyles.append(("BOX", (1, num), (1, num), 1, HexColor("#000000")))
                borderStyles.append(("BOTTOMPADDING", (1, num), (1, num), 7))
                borderStyles.append(("RIGHTPADDING", (1, num), (1, num), 7))
        num += 1

    borderStyles.append(("BOX", (0, 0), (0, ePos), 1, HexColor("#000000")))
    borderStyles.append(("ALIGN", (0, ePos + 1), (0, -1), "RIGHT"))
    borderStyles.append(("FONTNAME", (0, 0), (-1, -1), "Helvetica"))
    borderStyles.append(("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"))
    borderStyles.append(("FONTSIZE", (0, 0), (-1, -1), 10))
    borderStyles.append(("FONTNAME", (0, -1), (1, -1), "Helvetica-Bold"))
    borderStyles.append(("RIGHTPADDING", (0, 0), (0, 0), 400))
    borderStyles.append(("ALIGN", (1, 0), (1, -1), "RIGHT")),

    table = Table(empPayslipTable, style=borderStyles)

    return table


def creatingPdf(empData, payslipData, empGross, empDec, empElist, empDecList):
    imgFile = "solutech_logo.png"
    addX = 20
    addY = 746
    story = []
    frame = Frame(1.1 * inch, 1 * inch, 6 * inch, 8 * inch)
    empNet = empGross - empDec
    aEmpGross = "{:,.2f}".format(empGross)
    fEmpGross = str(aEmpGross)
    aEmpNet = "{:,.2f}".format(empNet)
    fEmpNet = str(aEmpNet)
    table = pdfTableFormat(empElist, empDecList, fEmpGross, fEmpNet)
    headerTable = addressTable(payslipData)
    pdfName = canvas.Canvas(empData.get("Name") + "_payslip.pdf")
    pdfName.setFont("Helvetica-Bold", 23)
    pdfName.drawString(20, 790, "Payslip")
    pdfName.drawImage(imgFile, 460, 770, width=105, preserveAspectRatio=True, mask='auto')
    pdfName.setFont("Helvetica-Bold", 9)
    pdfName.drawString(20, 760, empData.get("Name"))
    pdfName.setFont("Helvetica", 9)
    addSplit = str(empData.get("Address")).split("\n")
    for item in addSplit:
        pdfName.drawString(addX, addY, item)
        addY -= 15
    pdfName.setFont("Helvetica", 9)
    headerTable.wrapOn(pdfName, 100, 100)
    headerTable.drawOn(pdfName, 400, 710, )
    story.append(table)
    frame.addFromList(story, pdfName)
    pdfName.save()


def addressTable(payslipData):
    aTable = [
        ["Date", "Solutech Innovation Ltd."],
        [payslipData.get("Date"), "21 Connolley Drive"],
        ["", "Kingston 4"],

        ["", "TRN 002 082 080"],

    ]
    contentTable = Table(aTable, 60, 15, style=[
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (0, 0), "RIGHT"),

    ])
    return contentTable


def calEmpGross(keyTitle, supKey, key):
    valueNew = 0
    value = fetchPayslipKey(key)
    data = dict(value.json())
    for keyVal in data.get(keyTitle):
        valueNew = keyVal[supKey] + valueNew
    return valueNew




def deductionCal(keyTitle, supKey, key):
    valueNew = 0
    value = fetchPayslipKey(key)
    data = dict(value.json())
    for keyVal in data.get(keyTitle):
        try:
            valueNew = keyVal[supKey] + valueNew
        except:
            print("Unable to get "+keyTitle+" key="+supKey)
    return valueNew


def emailingService(empDictionary):
    empName = empDictionary.get("Name")
    pdfName = empName + "_payslip.pdf"
    subject = empName + "'s Payslip"
    empEmail = str(empDictionary.get("Email")).replace("\n", "")
    if empEmail == "None":
        print("Mail not sent")
        return

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = empEmail
    msg["Subject"] = subject

    msg.attach(MIMEText("PDF Documment", "plain"))
    # #
    binaryPdf = open(pdfName, "rb")
    payload = MIMEBase('application', 'octate-stream', Name=pdfName)
    payload.set_payload((binaryPdf).read())
    #
    encoders.encode_base64(payload)

    payload.add_header('Content-Decomposition',
                       'attachment', filename=pdfName)
    msg.attach(payload)

    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    session.login(EMAIL_ADDRESS, APP_KEY)

    text = msg.as_string()
    session.sendmail(FROM_EMAIL, empEmail, text)
    session.quit()
    print("Mail sent.")


def delEmpPayslip(key):
    keyJson = key + ".json"
    response = requests.delete(f"https://{COMPANY_NAME}/api/{API_KEY}/{PAYSLIP_LIST_KEY}/{keyJson}", auth=(USERNAME,
                                                                                                           PASSWORD))
    return response


def delFiles(empData):
    os.remove(empData)


def returnPayslipKey(fileName):
    jsonFile = open(fileName)
    jsonData = json.load(jsonFile)
    for keyVey in jsonData:
        key = keyVey["Key"]
        empData = getEmpFromPayslip(key)
        payslipData = returnPayslipData(key)
        # Check date here
        if (checkPayslipDate2(payslipData)):
            createEmpJson(payslipData, empData, key)
            print("Task Completed")


###################################################
# Main
###################################################
def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '-payrolldate':
        global PAYROLL_DATE
        PAYROLL_DATE=datetime.datetime.strptime(args[1],'%Y-%m-%d')
    returnPayslipKey(PAYSLIP_LIST_FILENAME)
    os.remove(PAYSLIP_LIST_FILENAME)
    os.remove(API_LIST_FILENAME)


main()
