#應數15 顏友君(111652042)

import pyautogui
import time

#Fail-Safe
pyautogui.FailSafeException == True

global maxLen
global maxLenPositions
dx = [-1, 0, 1, 1, 1, 0, -1, -1]
dy = [1, 1, 1, 0, -1, -1, -1, 0]
beginX = 730
beginY = 390
offset = 60

#Determine the color of the ball and convert it into a 6x6 matrix.
def createColorMatrix():
    colorMatrix = [[None for _ in range(6)] for _ in range(6)]
    for i in range(6):
        for j in range(6):
            if pyautogui.pixel(beginX + offset*j, beginY + offset*i) == (255, 0, 29):  #Red
                colorMatrix[i][j] = 1
            elif pyautogui.pixel(beginX + offset*j, beginY + offset*i) == (249, 140, 41):  #Orange
                colorMatrix[i][j] = 2
            elif pyautogui.pixel(beginX + offset*j, beginY + offset*i) == (77, 186, 48):  #Green
                colorMatrix[i][j] = 3
            elif pyautogui.pixel(beginX + offset*j, beginY + offset*i) == (82, 130, 246):  #Blue
                colorMatrix[i][j] = 4
            elif pyautogui.pixel(beginX + offset*j, beginY + offset*i) == (150, 43, 235):  #Purple
                colorMatrix[i][j] = 5
    return colorMatrix

#Determine if the position is inside the color matrix
def isIn(i, j):
    if i < 0 or i >= 6:
        return False
    if j < 0 or j >= 6:
        return False
    return True

#Find the longest path in the connection
def dfs(positionList, curI, curJ):
    global maxLen
    global maxLenPositions

    curColor = colorMatrix[curI][curJ]
    positionList.append((curI, curJ))
    if len(positionList) > maxLen:
        maxLen = len(positionList)
        maxLenPositions = positionList[:]

    for d in range(8):
        ni = curI + dx[d]
        nj = curJ + dy[d]
        if isIn(ni, nj):
            if colorMatrix[ni][nj] == curColor and (ni, nj) not in positionList:
                dfs(positionList, ni, nj)
    positionList.pop()

#Convert the vertices on the longest path to absolute coordinates.
def obsPosition():
    global maxLen
    global maxLenPositions
    maxLenObsPosition = []
    for i in (maxLenPositions[:min(8,maxLen)]):
        maxLenObsPosition.append((beginX+offset*i[1], beginY+offset*i[0]))
    return maxLenObsPosition

#Connect the longest path
def connet(maxLenObsPosition):
    pyautogui.mouseDown(maxLenObsPosition[0][0], maxLenObsPosition[0][1])
    for i in (maxLenObsPosition):
        pyautogui.moveTo(i[0], i[1], duration=0.2)
    time.sleep(0.1)
    pyautogui.mouseUp()

# main
# open game
pyautogui.rightClick(980, 1060)
time.sleep(0.1)
pyautogui.click(980, 900)
time.sleep(0.5)
pyautogui.typewrite('https://www.crazygames.com/game/collect-em-all', interval=0.01)
pyautogui.press('enter')
time.sleep(5)

#start game
while True:
    global maxLenPositions
    global maxLen
    maxLenPositions = []
    maxLen = 0

    #Ended condition
    if pyautogui.pixel(985, 365) == (255, 255, 255):
        pyautogui.click(985, 365)
        break

    colorMatrix = createColorMatrix()
    for i in range(6):
        for j in range(6):
            positionList = []
            dfs(positionList, i, j)
    connet(obsPosition())
    time.sleep(1.5)

#Close window
pyautogui.click(1910, 10)