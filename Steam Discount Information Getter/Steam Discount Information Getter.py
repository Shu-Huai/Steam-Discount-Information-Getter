import docx
import requests
from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Pt
from docx.enum.dml import MSO_THEME_COLOR_INDEX
from urllib import request
import os


def GetMaxPage():
    url = list([])
    url.append("https://store.steampowered.com/search/?specials=1&page=1")
    soup = GetSoup(GetUrlContents(url))
    node = soup[0].find_all("div", class_="search_pagination_right")
    return int(node[0].contents[5].contents[0])


def CreateUrls(pages):
    urls = []
    for i in range(pages):
        urlExample = "https://store.steampowered.com/search/?specials=1&page={}".format(i + 1)
        urls.append(urlExample)
    return urls


def GetUrlContents(urls):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_16_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/ 90.0.4430.93 Safari/605.1.15'}
    responseList = []
    contentList = []
    for i in range(len(urls)):
        try:
            responseList.append(requests.get(urls[i], headers=headers))
        except ConnectionError:
            break
        contentList.append(responseList[i].text)
    return contentList


def GetSoup(contentList):
    soup = []
    for i in range(len(contentList)):
        soup.append(BeautifulSoup(contentList[i], "html.parser"))
    return soup


def GetGameNames(contentList):
    names = []
    soup = GetSoup(contentList)
    for i in range(len(contentList)):
        names.extend(soup[i].find_all("span", class_="title"))
    for i in range(len(names)):
        names[i] = names[i].string
    return names


def GetGameUrls(contentList):
    urls = []
    soup = GetSoup(contentList)
    urlPrefix = "https://store.steampowered.com/"
    for i in range(len(contentList)):
        for node in soup[i].find_all("a"):
            temp = node.get("href")
            if (urlPrefix + "app/" in temp or urlPrefix + "bundle/" in temp or urlPrefix + "sub/" in temp) and "view" not in temp:
                urls.append(node.get("href"))
    return urls


def GetPrices(contentList):
    previousPrices = []
    nowPrices = []
    discounts = []
    soup = GetSoup(contentList)
    for i in range(len(contentList)):
        count = 0
        unpurchaseableIndex = []
        for node in soup[i].find_all("div", class_="col search_discount responsive_secondrow"):
            discount = node.text.strip("\n")
            if discount == "":
                discounts.append("0")
                unpurchaseableIndex.append(count)
            else:
                discounts.append(discount)
            count += 1
        for node in soup[i].find_all("div", class_="col search_price discounted responsive_secondrow"):
            previousPrices.append(node.contents[1].contents[0].contents[0])
            nowPrices.append(node.contents[3].strip())
        for j in unpurchaseableIndex:
            previousPrices.insert(i * 25 + j, "Unpurchasable")
            nowPrices.insert(i * 25 + j, "Unpurchasable")
    return previousPrices, nowPrices, discounts


def DeleteGameCovers(path):
    for i in os.listdir(path):
        file = path + "\\" + i
        if os.path.isfile(file):
            os.remove(file)
        else:
            DeleteGameCovers(file)


def GetGameCovers(contentList):
    if not os.path.exists("Game Cover"):
        os.makedirs("Game Cover")
    DeleteGameCovers("Game Cover")
    soup = GetSoup(contentList)
    count = 0
    for i in range(len(contentList)):
        for node in soup[i].find_all("div", class_="col search_capsule"):
            request.urlretrieve(node.contents[0].attrs["src"], "Game Cover" + "\\" + str(count) + ".png")
            count += 1


def Merge(names, urls, previousPrices, nowPrices, discounts):
    games = []
    for i in range(len(names)):
        diction = dict(gameName=names[i], gameUrl=urls[i], previousPrice=previousPrices[i], nowPrice=nowPrices[i], discount=discounts[i], gameCoverNumber=i)
        games.append(diction)
    return games


def FormatSortRule(sortRule):
    inputError = bool(0)
    if sortRule == "A" or sortRule == "a" or sortRule == "0":
        sortRule = "gameName"
    elif sortRule == "B" or sortRule == "b" or sortRule == "1":
        sortRule = "previousPrice"
    elif sortRule == "C" or sortRule == "c" or sortRule == "2":
        sortRule = "nowPrice"
    elif sortRule == "D" or sortRule == "d" or sortRule == "3":
        sortRule = "discount"
    elif sortRule == "E" or sortRule == "e" or sortRule == "4":
        sortRule = "gameCoverNumber"
    else:
        inputError = 1
    return sortRule, inputError


def Sort(games, sortRule):
    for i in range(len(games)):
        games[i]["previousPrice"] = float(games[i]["previousPrice"].strip("¥"))
        games[i]["nowPrice"] = float(games[i]["nowPrice"].strip("¥"))
        games[i]["discount"] = float(games[i]["discount"].strip("%"))
    games = sorted(games, key=lambda x: (x[sortRule], x["gameName"]))
    for i in range(len(games)):
        games[i]["previousPrice"] = "¥ " + str(games[i]["previousPrice"])
        games[i]["nowPrice"] = "¥ " + str(games[i]["nowPrice"])
        games[i]["discount"] = str(games[i]["discount"]) + "%"
    return games


def SaveToDocx(games):
    docxFile = Document()
    docxFile.styles["Normal"].font.name = "Times New Roman"
    docxFile.styles["Normal"].font.size = Pt(12)
    docxFile.add_paragraph().add_run("Here is the Steam discount information for this week.").font.bold = True
    for i in range(len(games)):
        paragraph = docxFile.add_paragraph()
        paragraph.add_run("Game: %s.\n" % games[i]["gameName"]).font.bold = True
        paragraph.add_run("Link: ")
        part = paragraph.part
        ralationId = part.relate_to(games[i]["gameUrl"], docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
        hyperLink = docx.oxml.shared.OxmlElement("w:hyperlink")
        hyperLink.set(docx.oxml.shared.qn("r:id"),
            ralationId,)
        r = docx.oxml.shared.OxmlElement("w:r")
        rPr = docx.oxml.shared.OxmlElement("w:rPr")
        r.append(rPr)
        r.text = games[i]["gameUrl"]
        hyperLink.append(r)
        run = paragraph.add_run()
        run._r.append(hyperLink)
        run.font.color.theme_color = MSO_THEME_COLOR_INDEX.HYPERLINK
        run.font.underline = True
        paragraph.add_run("\nDiscount: %s, " % games[i]["discount"])
        paragraph.add_run("Price: %s, Previous Price: %s." % (games[i]["nowPrice"], games[i]["previousPrice"]))
        docxFile.add_picture("Game Cover" + "\\" + str(games[i]["gameCoverNumber"]) + ".png")
    docxFile.save("Steam Discount Information.docx")


pages = input("Please input the pages you want, min is 1, max is %d, default is 5: " % GetMaxPage())
try:
    pages = int(pages)
except ValueError:
    pages = 5
inputError = bool(1)
while inputError:
    print("A/a/0 represents game name.\nB/b/1 represents previous price.\nC/c/2 represents now price.")
    print("D/d/3 represents discount.\nE/e/4 represents the original order.")
    sortRule = input("Please input the sort rule: ")
    sortRule, inputError = FormatSortRule(sortRule)
    if inputError:
        print("Input error, please input again.")
urls = CreateUrls(pages)
contentList = GetUrlContents(urls)
gameNames = GetGameNames(contentList)
gameUrls = GetGameUrls(contentList)
previousPrices, nowPrices, discounts = GetPrices(contentList)
GetGameCovers(contentList)
games = Merge(gameNames, gameUrls, previousPrices, nowPrices, discounts)
games = Sort(games, sortRule)
for i in range(len(games)):
    print("Game: %s.\nLink: %s." % (games[i]["gameName"], games[i]["gameUrl"]))
    print("Discount: %s, " % games[i]["discount"], end="")
    print("Price: %s, Previous Price: %s.\n" % (games[i]["nowPrice"], games[i]["previousPrice"]))
SaveToDocx(games)