import time
from datetime import date
import pymysql
import requests
from bs4 import BeautifulSoup

url = 'https://www.indeed.com/jobs?q=software+developer&start='
baseURL = 'https://www.indeed.com'

jobs = []

DB_Identifier = None

host_name = 'REDACTED'

db_username = 'REDACTED'

db_password = 'REDACTED'
# db = pymysql.connect(host_name)

db = pymysql.connect(host=host_name,

                     user=db_username,

                     password=db_password,

                     database=DB_Identifier,

                     charset='utf8mb4',

                     cursorclass=pymysql.cursors.DictCursor)

print(db)

cursor = db.cursor()

print(cursor)
sql = '''use JobInsights'''

cursor.execute(sql)


class jobListing:
    title = ""
    company = ""
    fullHTML = ""
    descHTML = ""
    descRefined = ""
    listingURL = ""
    href = ""
    dateFound = ""

    def __init__(self, href):
        self.href = href
        dateFound = date.today()
        # print(dateFound)
        # The following code will run every time a new job is added
        # It will grab the title and html of the description
        base_url = "https://www.indeed.com"
        with requests.get(base_url + self.href) as response:
            # print("Going to job")
            # print(base_url + href)
            self.fullHTML = response.text
            if response.status_code != 200:
                print("FAILURE::{0}".format(url))

            info = BeautifulSoup(response.content, "html.parser")
            jobTitle = info.find("h1", class_="icl-u-xs-mb--xs icl-u-xs-mt--none jobsearch-JobInfoHeader-title")
            try:
                self.company = info.find(class_="icl-u-lg-mr--sm icl-u-xs-mr--xs").next_element.text
            except:
                self.company = "---ERROR---"
            self.descHTML = info.find(id="jobDescriptionText")
            # print(job_desc)
            try:
                self.title = jobTitle.text
                # print(jobTitle.text)
            except:
                # print("-No Title-")
                self.title = "-No Title-"
        try:
            self.descRefined = refineDesc(self.descHTML)
        except:
            self.descRefined = ""

        if len(self.company) > 64:
            self.company = self.company[:63]
        # print(self.descRefined)
        if self.descRefined == "" or self.descRefined == "\n":
            print("empty, not adding to DB " + (base_url + self.href))
        else:
            # print(self.title)
            # print(self.company)
            print(base_url + self.href)
            # print(self.descHTML)
            # print(self.descRefined)
            sql = ("SELECT * FROM companies WHERE company_name = %s")
            cursor.execute(sql, (self.company))
            results = cursor.fetchall()
            if not results:
                print("Company not yet added")
                cursor.execute("BEGIN;")
                print(cursor.execute("INSERT IGNORE INTO companies (company_name) VALUES(%s);", (self.company)))
                cursor.execute("COMMIT;")
                print("Added")
            else:
                print("In Database")

            cursor.execute("BEGIN;")
            sql = "SELECT company_id FROM companies WHERE company_name = %s;"
            cursor.execute(sql, (self.company))
            company_id = 0
            company_id = cursor.fetchone()
            print(company_id)

            sql = "SELECT job_title FROM postings WHERE posting_id = %s;"
            cursor.execute(sql, (self.href))
            res = cursor.fetchall()
            if not res:
                sql = "INSERT IGNORE INTO postings (posting_id, job_title, company_id, job_description) VALUES(%s,%s,%s,%s);"
                print(cursor.execute(sql, (self.href, self.title, company_id['company_id'], self.descRefined)))
                cursor.execute("COMMIT;")
                time.sleep(.1)
            else:
                print("already added")


def getResultsFromPage(pageNumber):
    currentPageUrl = url + (pageNumber * 10).__str__()

    try:
        page = requests.get(currentPageUrl)
    except:
        return
    soup = BeautifulSoup(page.content, "html.parser")

    # if soup.findAll(class_='h-captcha'):
    #     print(soup.find(class_='h-captcha'))
    #     print("\nFound Captcha\nPlease Solve and continue by entering any value\n")
    #     webbrowser.open(currentPageUrl)
    #     input()
    #     time.sleep(4)

    results = soup.find(id="mosaic-provider-jobcards")

    # print(results.prettify())

    if results is None:
        print("Failed Getting page " + str(pageNumber))
        time.sleep(3)
        return

    for a in results.find_all('a', href=True):

        if "clk?" in a['href']:
            if "pagead" not in a['href']:
                # print("Found the URL:", a['href'])
                jobs.append(jobListing(a['href']))
                time.sleep(.4)

    # print(hrefs)


def refineDesc(desc):
    keywords = ["responsibilities", "qualifications", "duties", "requirements", "skills", "knowledge", "functions"]
    results = []
    descList = ""
    # print(desc)

    for a in desc.find_all('p' or 'b'):

        # print(a)
        try:
            for keyword in keywords:
                if (str(a)).lower().find(keyword) == -1:
                    continue
                else:
                    # print(a)
                    element = a
                    descList = descList + "/" + keyword + "/\n"
                    match = desc.find('p', text=a.text)
                    # print("------from html-----")
                    # print(match.text)
                    # print("next----")
                    # print(match.next_sibling)
                    if "<ul>" in str(match.next_sibling):
                        # print("in list")
                        # print(match.next_sibling.prettify())
                        descList = descList + match.next_sibling.prettify() + "\n"
                    elif "<ul>" in str(match.next_sibling.next_sibling):
                        descList = descList + match.next_sibling.next_sibling.prettify() + "\n"
                    else:
                        # print("not in list")
                        descList = descList + "/" + keyword + "/" + str(match).lstrip("<p>").rstrip("</p>")
                        descList = descList + "/" + keyword + "/" + str(match).lstrip("<b>").rstrip("</b>")
                    # print(descList)



        except:
            descList = ""
    # print(descList)
    # print(descList.children)
    f = ""
    try:
        lines = descList.split("\n")
        for line in lines:
            if line.count("<") == 0:
                f = f + "\n" + line
        print(f)
        return f
    except:
        # print("FAIL")

        # print(descList)
        return descList


def run():
    pageNum = 1

    while True:

        print("started page " + str(pageNum))

        cursor.execute("BEGIN;")

        (cursor.execute("SELECT COUNT(company_id) FROM companies;"))
        numComp = cursor.fetchone()
        (cursor.execute("SELECT COUNT(posting_id) FROM postings;"))
        numList = cursor.fetchone()
        cursor.execute("COMMIT;")
        print("Number of Companies: " + str(numComp['COUNT(company_id)']))
        print("Number of Postings: " + str(numList['COUNT(posting_id)']))

        getResultsFromPage(pageNum)

        pageNum = pageNum + 1
        if pageNum == 150:
            break

    # print(jobs.__len__())
    # print(jobs[1].href)


run()
