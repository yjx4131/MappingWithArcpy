#######################################################
# Name: GA_IDW for EPRI
# Objective: automatically map IDW layers
# Author: Jianxin Yang
# Date: 5/4/2018
##
################################################################
import arcpy
from arcpy import env
from arcpy import mapping
import os
import shutil

arcpy.env.overwriteOutput = True
# set input data path
outMapDir = os.path.join("C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\output","maps")
if os.path.exists(outMapDir):
    shutil.rmtree(outMapDir)
else:
    os.mkdir(outMapDir)
IdwRasDir = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\output\outIdwRas"
SoilSamPointDir = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input\Projected_Fc"
BoundaryDir = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input\boundaries_Shp"
MxdTemplateDir = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input\MXD_Template"
# set layer template path
idwRasTemplate = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input\LyrTemplate\IDW.lyr"
soilSampTemplate = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input\LyrTemplate\soilPoint.lyr"
boundaryTemplate = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input\LyrTemplate\boundary.lyr"
BaseMapLyr = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input\BasemapLyr\basemap.lyr"
mxd = arcpy.mapping.MapDocument(
    r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input\MXD_Template\DecaturParkSolar_Bottom_Steel.mxd")
df = arcpy.mapping.ListDataFrames(mxd, "")[0]
df.spatialReference =  arcpy.SpatialReference("North America Albers Equal Area Conic")
# df.scale = 16887.00
lyrLst = arcpy.mapping.ListLayers(mxd, "", df)


# create a dictionary to store soil samples and PV farm boundaries
def createDict(workspace, wild_card):
    fileList = []
    env.workspace = workspace
    files = arcpy.ListFiles(wild_card)
    for fi in files:
        if "Bottom" in fi:
            depth = "_Bottom"
        elif "Top" in fi:
            depth = "_Top"
        else:
            depth = ""
        key = fi[:4] + depth
        value = os.path.join(workspace, fi)
        fileList.append((key, value))
    fileDict = dict(fileList)
    # print fileDict
    return fileDict


soilPointDict = createDict(SoilSamPointDir, "*.shp")
boundaryDict = createDict(BoundaryDir, "*.shp")

# defined symbology breakvalue list for IDW layer
zinkValueBreak = [0.039, 0.181, 0.380, 0.583, 0.787, 1.109, 1.698, 2.653, 4.432, 9.110]
zinkBreakLabels = ["0.039 - 0.181", "0.181 - 0.380", "0.380 - 0.583", "0.583 - 0.787", "0.787 - 1.109", "1.109 - 1.698",
                   "1.698 - 2.653", "2.653 - 4.432", "4.432 - 9.110"]
copperValueBreak = [0.026, 0.116, 0.199, 0.287, 0.350, 0.436, 0.523, 0.718, 1.010, 1.720]
copperBreakLabels = ["0.026 - 0.116", "0.116 - 0.199", "0.199 - 0.287", "0.287 - 0.350", "0.350 - 0.436",
                     "0.436 - 0.523", "0.523 - 0.718", "0.718 -1.010", "1.010 - 1.720"]
steelValueBreak = [0.054, 0.177, 0.307, 0.549, 0.771, 1.035, 1.700, 2.466, 3.364, 6.467]
steelBreakLabels = ["0.054 - 0.177", "0.177 - 0.307", "0.307 - 0.549", "0.549 - 0.771", "0.771 - 1.035",
                    "1.035 - 1.700", "1.700 - 2.466", "2.466 - 3.364", "3.364 - 6.467"]
# create a dictionary to look up value breaks and labels
ValueBreakDict = {"Zinc": {"break": zinkValueBreak, "label": zinkBreakLabels},
                  "Copper": {"break": copperValueBreak, "label": copperBreakLabels},
                  "Steel": {"break": steelValueBreak, "label": steelBreakLabels}}

# start mapping
env.workspace = IdwRasDir
IdwRasLst = arcpy.ListRasters("", "TIF")
mapId = 1
for idwras in IdwRasLst:
    print "Mapping the %sth idw layer"%mapId
    mapId += 1
    descRas = arcpy.Describe(idwras)
    baseName = descRas.basename
    print "Mapping: %s" %baseName
    key1 = baseName[:4] # dictionary key for boundary files
    if "Bottom" in baseName:
        depth = "_Bottom"
    elif "Top" in baseName:
        depth = "_Top"
    else:
        depth = ""
    key2 = key1 + depth # dictionary key for soil sample files
    descBoundary = arcpy.Describe(boundaryDict[key1])
    fcExtent = descBoundary.extent

# create layer file
    outIdwLyr = baseName + "_idwLyr"
    outSoilPointLyr = baseName + "_SoilPointLyr"
    ourBoundaryLyr = baseName + "_BoundaryLyr"
    arcpy.MakeRasterLayer_management(idwras, outIdwLyr, "", fcExtent, "1")
    arcpy.MakeFeatureLayer_management(boundaryDict[key1], ourBoundaryLyr, "", "", "")
    arcpy.MakeFeatureLayer_management(soilPointDict[key2], outSoilPointLyr, "", "", "")
# create layer object
    addIdwLyr = mapping.Layer(outIdwLyr)
    addBoundaryLyr = mapping.Layer(ourBoundaryLyr)
    addSoilPointLyr = mapping.Layer(outSoilPointLyr)
    addSoilPointLyr.name = "Soil Sample"
# create layer object for template layer
    idwTemp = mapping.Layer(idwRasTemplate)
    boundaryTemp = mapping.Layer(boundaryTemplate)
    soilSampTemp = mapping.Layer(soilSampTemplate)

    baseLayer = mapping.Layer(BaseMapLyr)
    addIdwLyr.transparency = 30
# apply layer template so as to render layers
    arcpy.mapping.UpdateLayer(df, addIdwLyr, idwTemp, True)
    arcpy.mapping.UpdateLayer(df, addBoundaryLyr, boundaryTemp, True)
    arcpy.mapping.UpdateLayer(df, addSoilPointLyr, soilSampTemp, True)
# set symbology property for idw layers. Grouping values
    if addIdwLyr.symbologyType == "RASTER_CLASSIFIED":
        addIdwLyr.symbology.classBreakValues = ValueBreakDict[baseName.split("_")[-1]]["break"]
        addIdwLyr.symbology.classBreakLabels = ValueBreakDict[baseName.split("_")[-1]]["label"]
    addIdwLyr.save()
# pan data frame to the extent of idw layer of interest
    mapExtent = addIdwLyr.getExtent()
    df.panToExtent(mapExtent)
# set legend. Two legends are added in the mxd template
    legend1 = mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT", "Legend1")[0]
    legend2 = mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT", "Legend2")[0]
    legend1.autoAdd = True
    legend2.autoAdd = False
    mapping.AddLayer(df, addIdwLyr, "AUTO_ARRANGE")
    legend1.autoAdd = False
    legend2.autoAdd = True
    mapping.AddLayer(df, addSoilPointLyr, "AUTO_ARRANGE")
    legend1.autoAdd = False
    legend2.autoAdd = False
    mapping.AddLayer(df, addBoundaryLyr, "AUTO_ARRANGE")
    arcpy.mapping.AddLayer(df, baseLayer, "BOTTOM")
# set name of legends
    legend1.title = baseName.split("_")[-1] + " Corrosion Rate (mils/year)"
    legend2.title = ""
    styleItem = mapping.ListStyleItems("ESRI.style", "Legend Items", "Horizontal Single Symbol Label Only")[0]
# set layer style
    for lyr in legend1.listLegendItemLayers():
        legend1.updateItem(lyr, styleItem)
    legend1.adjustColumnCount(3)
    for lyr in legend2.listLegendItemLayers():
        legend2.updateItem(lyr, styleItem)
# print map

    outMapName = baseName.split("_")[0] + depth + baseName.split("_")[-1]
    outMap = os.path.join(outMapDir, outMapName)
    mapping.ExportToPNG(mxd,outMap,resolution=300)
# clear up layers that added to the mxd template so as to get prepared for mapping the next idw layer
    for lyr in arcpy.mapping.ListLayers(mxd, "", df):
        arcpy.mapping.RemoveLayer(df, lyr)
    print "Mapping Done"

mxd.save()
del mxd
