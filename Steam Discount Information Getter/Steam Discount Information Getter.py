import sys
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QApplication, QMainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import docx
import requests
from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Pt
from docx.enum.dml import MSO_THEME_COLOR_INDEX
from urllib import request
import os


class SteamDiscountInformationGetter(object):
    def __init__(self) -> None:
        super().__init__()

    def GetMaxPage(self):
        url = []
        url.append("https://store.steampowered.com/search/?specials=1&page=1")
        soup = self.GetSoup(self.GetUrlContents(url))
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
                response = requests.get(urls[i], headers=headers)
            except requests.exceptions.ConnectionError:
                MainWindow.EjectConnectionErrorDialog(MainWindow)
                exit()
            responseList.append(response)
            contentList.append(responseList[i].text)
        return contentList

    def GetSoup(contentList):
        soup = []
        for i in range(len(contentList)):
            soup.append(BeautifulSoup(contentList[i], "html.parser"))
        return soup

    def GetGameNames(self, contentList):
        names = []
        soup = self.GetSoup(contentList)
        for i in range(len(contentList)):
            names.extend(soup[i].find_all("span", class_="title"))
        for i in range(len(names)):
            names[i] = names[i].string
        return names

    def GetGameUrls(self, contentList):
        urls = []
        soup = self.GetSoup(contentList)
        urlPrefix = "https://store.steampowered.com/"
        for i in range(len(contentList)):
            for node in soup[i].find_all("a"):
                temp = node.get("href")
                if (urlPrefix + "app/" in temp or urlPrefix + "bundle/" in temp or urlPrefix + "sub/" in temp) and "view" not in temp:
                    urls.append(node.get("href"))
        return urls

    def GetPrices(self, contentList):
        previousPrices = []
        nowPrices = []
        discounts = []
        soup = self.GetSoup(contentList)
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

    def DeleteGameCovers(self, path):
        for i in os.listdir(path):
            file = path + "\\" + i
            if os.path.isfile(file):
                os.remove(file)
            else:
                self.DeleteGameCovers(file)

    def GetGameCovers(self, contentList):
        if not os.path.exists("Game Cover"):
            os.makedirs("Game Cover")
        self.DeleteGameCovers(self, "Game Cover")
        soup = self.GetSoup(contentList)
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
            r = docx.oxml.shared.OxmlElement('w:r')
            rPr = docx.oxml.shared.OxmlElement('w:rPr')
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


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Steam Discount Information Getter")
        self.setWindowIcon(QtGui.QIcon("Steam Discount Information Getter.png"))
        self.setObjectName("mainWindow")
        self.resize(1500, 500)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName("centralWidget")
        self.InitializeTitleLabel()
        self.InitializePageNumberLabel()
        self.InitializePageNumberEdit()
        self.InitializeOkButton()
        self.InitializeCloseButton()
        self.InitializeSortRuleGroup()
        self.InitializeSaveCheckBox()
        self.InitializeResultTextBrowser()
        self.InitializeClearButton()
        self.pageNumberLabel.raise_()
        self.okButton.raise_()
        self.titleLabel.raise_()
        self.pageNumberEdit.raise_()
        self.closeButton.raise_()
        self.setCentralWidget(self.centralWidget)
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

    def InitializeTitleLabel(self):
        self.titleLabel = QtWidgets.QLabel("Steam Discount Information Getter", self.centralWidget)
        self.titleLabel.setGeometry(QtCore.QRect(170, 50, 391, 21))
        self.titleLabel.setObjectName("titleLabel")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(20)
        self.titleLabel.setFont(font)

    def InitializePageNumberLabel(self):
        pages = SteamDiscountInformationGetter.GetMaxPage(SteamDiscountInformationGetter)
        self.pageNumberLabel = QtWidgets.QLabel("Please input the pages you want:             /" + str(pages), self.centralWidget)
        self.pageNumberLabel.setGeometry(QtCore.QRect(170, 110, 281, 21))
        self.pageNumberLabel.setObjectName("pageNumberLabel")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.pageNumberLabel.setFont(font)

    def InitializePageNumberEdit(self):
        self.pageNumberEdit = QtWidgets.QLineEdit(self.centralWidget)
        self.pageNumberEdit.setGeometry(QtCore.QRect(370, 110, 41, 21))
        self.pageNumberEdit.setObjectName("pageNumberEdit")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.pageNumberEdit.setFont(font)

    def InitializeOkButton(self):
        self.okButton = QtWidgets.QPushButton("Ok", self.centralWidget)
        self.okButton.setGeometry(QtCore.QRect(390, 310, 75, 24))
        self.okButton.setObjectName("okButton")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.okButton.setFont(font)
        self.okButton.clicked.connect(self.OkButtonClicked)

    def InitializeCloseButton(self):
        self.closeButton = QtWidgets.QPushButton("Close", self.centralWidget)
        self.closeButton.setGeometry(QtCore.QRect(480, 310, 75, 24))
        self.closeButton.setObjectName("closeButton")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.closeButton.setFont(font)
        self.closeButton.clicked.connect(self.close)

    def InitializeSortRuleGroup(self):
        self.sortRuleGroup = QtWidgets.QGroupBox("Sort rule:", self.centralWidget)
        self.sortRuleGroup.setGeometry(QtCore.QRect(170, 160, 391, 80))
        self.sortRuleGroup.setObjectName("sortRuleGroup")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.sortRuleGroup.setFont(font)
        self.InitializeGameNameRadio()
        self.InitializePreviousPriceRadio()
        self.InitializeNowPriceRadio()
        self.InitializeDiscountRadio()
        self.InitializeGameCoverNumberRadio()

    def InitializeGameNameRadio(self):
        self.gameNameRadio = QtWidgets.QRadioButton("Game name", self.sortRuleGroup)
        self.gameNameRadio.setGeometry(QtCore.QRect(10, 20, 95, 20))
        self.gameNameRadio.setObjectName("gameNameRadio")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.gameNameRadio.setFont(font)
        self.gameNameRadio.clicked.connect(self.GameNameRadioChecked)

    def InitializePreviousPriceRadio(self):
        self.previousPriceRadio = QtWidgets.QRadioButton("Previous price", self.sortRuleGroup)
        self.previousPriceRadio.setGeometry(QtCore.QRect(140, 20, 111, 20))
        self.previousPriceRadio.setObjectName("previousPriceRadio")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.previousPriceRadio.setFont(font)
        self.previousPriceRadio.clicked.connect(self.PreviousPriceRadioChecked)

    def InitializeNowPriceRadio(self):
        self.nowPriceRadio = QtWidgets.QRadioButton("Now price", self.sortRuleGroup)
        self.nowPriceRadio.setGeometry(QtCore.QRect(270, 20, 95, 20))
        self.nowPriceRadio.setObjectName("nowPriceRadio")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.nowPriceRadio.setFont(font)
        self.nowPriceRadio.clicked.connect(self.NowPriceRadioChecked)

    def InitializeDiscountRadio(self):
        self.discountRadio = QtWidgets.QRadioButton("Discount", self.sortRuleGroup)
        self.discountRadio.setGeometry(QtCore.QRect(10, 50, 95, 20))
        self.discountRadio.setObjectName("discountRadio")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.discountRadio.setFont(font)
        self.discountRadio.setChecked(True)
        self.discountRadio.clicked.connect(self.DiscountRadioChecked)

    def InitializeGameCoverNumberRadio(self):
        self.gameCoverNumberRadio = QtWidgets.QRadioButton("Game cover number", self.sortRuleGroup)
        self.gameCoverNumberRadio.setGeometry(QtCore.QRect(140, 50, 171, 20))
        self.gameCoverNumberRadio.setObjectName("gameCoverNumberRadio")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.gameCoverNumberRadio.setFont(font)
        self.gameCoverNumberRadio.clicked.connect(self.GameCoverNumberRadioChecked)

    def InitializeSaveCheckBox(self):
        self.saveCheckBox = QtWidgets.QCheckBox("Save result into docx", self.centralWidget)
        self.saveCheckBox.setGeometry(QtCore.QRect(180, 260, 221, 20))
        self.saveCheckBox.setObjectName("saveCheckBox")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.saveCheckBox.setFont(font)
        self.saveCheckBox.setChecked(True)

    def InitializeResultTextBrowser(self):
        self.resultTextBrowser = QtWidgets.QTextBrowser(self.centralWidget)
        self.resultTextBrowser.setGeometry(QtCore.QRect(630, 60, 791, 271))
        self.resultTextBrowser.setObjectName("resultTextBrowser")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.resultTextBrowser.setFont(font)
        self.resultTextBrowser.setOpenExternalLinks(True)

    def InitializeClearButton(self):
        self.clearButton = QtWidgets.QPushButton("Clear", self.centralWidget)
        self.clearButton.setGeometry(QtCore.QRect(630, 350, 75, 24))
        self.clearButton.setObjectName("clearButton")
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.clearButton.setFont(font)
        self.clearButton.clicked.connect(self.resultTextBrowser.clear)

    def GetSortRule(self):
        if self.gameNameRadio.isChecked():
            return "gameName"
        if self.previousPriceRadio.isChecked():
            return "previousPrice"
        if self.nowPriceRadio.isChecked():
            return "nowPrice"
        if self.discountRadio.isChecked():
            return "discount"
        if self.gameCoverNumberRadio.isChecked():
            return "gameCoverNumber"

    def EjectConnectionErrorDialog(self):
        errorDialog = QDialog()
        errorDialog.resize(260, 100)
        errorDialog.setWindowTitle("Error")
        errorDialog.setWindowIcon(QtGui.QIcon("Steam Discount Information Getter Error.png"))
        errorLabel = QLabel("Error connection.\nPlease check Internet connection.", errorDialog)
        errorLabel.move(30, 10)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        errorLabel.setFont(font)
        okButton = QPushButton('Ok', errorDialog)
        okButton.move(110, 60)
        okButton.setFont(font)
        okButton.clicked.connect(errorDialog.close)
        errorDialog.exec_()

    def EjectPageNumberErrorDialog(self):
        errorDialog = QDialog()
        errorDialog.resize(180, 100)
        errorDialog.setWindowTitle("Error")
        errorDialog.setWindowIcon(QtGui.QIcon("Steam Discount Information Getter Error.png"))
        errorLabel = QLabel("Error page number.\nPlease input again.", errorDialog)
        errorLabel.move(30, 10)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        errorLabel.setFont(font)
        okButton = QPushButton('Ok', errorDialog)
        okButton.move(50, 60)
        okButton.setFont(font)
        okButton.clicked.connect(errorDialog.close)
        errorDialog.exec_()

    def OkButtonClicked(self):
        if self.pageNumberEdit.text() == "":
            self.pageNumberEdit.setText("5")
        try:
            pages = int(self.pageNumberEdit.text())
        except ValueError:
            self.EjectPageNumberErrorDialog()
            self.pageNumberEdit.clear()
            self.pageNumberEdit.setFocus()
            return
        if pages < 0 or pages > int(self.pageNumberLabel.text().strip("Please input the pages you want:             /")):
            self.EjectPageNumberErrorDialog()
            self.pageNumberEdit.clear()
            self.pageNumberEdit.setFocus()
            return
        urls = SteamDiscountInformationGetter.CreateUrls(pages)
        contentList = SteamDiscountInformationGetter.GetUrlContents(urls)
        gameNames = SteamDiscountInformationGetter.GetGameNames(SteamDiscountInformationGetter, contentList)
        gameUrls = SteamDiscountInformationGetter.GetGameUrls(SteamDiscountInformationGetter, contentList)
        previousPrices, nowPrices, discounts = SteamDiscountInformationGetter.GetPrices(SteamDiscountInformationGetter, contentList)
        SteamDiscountInformationGetter.GetGameCovers(SteamDiscountInformationGetter, contentList)
        games = SteamDiscountInformationGetter.Merge(gameNames, gameUrls, previousPrices, nowPrices, discounts)
        games = SteamDiscountInformationGetter.Sort(games, sortRule=self.GetSortRule())
        self.resultTextBrowser.clear()
        for i in range(len(games)):
            self.resultTextBrowser.append("Game: %s." % (games[i]["gameName"]))
            self.resultTextBrowser.append('Link: <a href=%s>%s</a>.' % (games[i]["gameUrl"], games[i]["gameUrl"]))
            self.resultTextBrowser.append("Discount: %s, Price: %s, Previous Price: %s.\n" % (games[i]["discount"], games[i]["nowPrice"], games[i]["previousPrice"]))
            self.resultTextBrowser.insertHtml('<img src="Game Cover\%d.png"/>' % i)
            self.resultTextBrowser.append("")
        if self.saveCheckBox.isChecked():
            SteamDiscountInformationGetter.SaveToDocx(games)
        completeDialog = QDialog()
        completeDialog.resize(180, 100)
        completeDialog.setWindowTitle("Complete")
        completeDialog.setWindowIcon(QtGui.QIcon("Steam Discount Information Getter Complete.png"))
        completeLabel = QLabel("Completed getting\nsteam discount information.", completeDialog)
        completeLabel.move(10, 10)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        completeLabel.setFont(font)
        okButton = QPushButton('Ok', completeDialog)
        okButton.move(50, 60)
        okButton.setFont(font)
        okButton.clicked.connect(completeDialog.close)
        completeDialog.exec_()

    def GameNameRadioChecked(self):
        self.previousPriceRadio.setChecked(False)
        self.nowPriceRadio.setChecked(False)
        self.discountRadio.setChecked(False)
        self.gameCoverNumberRadio.setChecked(False)

    def PreviousPriceRadioChecked(self):
        self.gameNameRadio.setChecked(False)
        self.nowPriceRadio.setChecked(False)
        self.discountRadio.setChecked(False)
        self.gameCoverNumberRadio.setChecked(False)

    def NowPriceRadioChecked(self):
        self.gameNameRadio.setChecked(False)
        self.previousPriceRadio.setChecked(False)
        self.discountRadio.setChecked(False)
        self.gameCoverNumberRadio.setChecked(False)

    def DiscountRadioChecked(self):
        self.gameNameRadio.setChecked(False)
        self.previousPriceRadio.setChecked(False)
        self.nowPriceRadio.setChecked(False)
        self.gameCoverNumberRadio.setChecked(False)

    def GameCoverNumberRadioChecked(self):
        self.gameNameRadio.setChecked(False)
        self.previousPriceRadio.setChecked(False)
        self.nowPriceRadio.setChecked(False)
        self.discountRadio.setChecked(False)


application = QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(application.exec_())