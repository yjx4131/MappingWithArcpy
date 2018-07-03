#######################################################
# Name: GA_IDW for EPRI
# Objective: spatial interpolation with automatic optimization of IDW power parameter
# Author: Jianxin Yang
# Date: 5/4/2018
## important: no space should appear in the names of input featureclasses
################################################################
import arcpy
from arcpy import env
import os
import shutil
import time
# import csv

# set geoprocessing environment parameters
env.outputCoordinateSystem = arcpy.SpatialReference("North America Albers Equal Area Conic")
env.cellsize = 1
arcpy.env.overwriteOutput = True

# set input data and output directory
inputDir = r"C:\Users\jyang71\Google Drive\PyCharmProject\EpriMapping2018\smallTest\input"
outputDir = inputDir.replace("input", "output")
if os.path.exists(outputDir):
    shutil.rmtree(outputDir)
os.mkdir(outputDir)
optimizedOutModel = os.path.join(outputDir, "optimizedIdwModel")
optimizedOutLyr = os.path.join(outputDir, "optimizedOutIdwLyr")
outIdwRasDir = os.path.join(outputDir, "outIdwRas")
os.mkdir(optimizedOutModel)
os.mkdir(optimizedOutLyr)
os.mkdir(outIdwRasDir)

# set raster mask
maskDic = {}
keyValueLst = []
boundaryDir = os.path.join(inputDir, "boundaries_Shp")
env.workspace = boundaryDir
boundaryLst = arcpy.ListFeatureClasses()
for bound in boundaryLst:
    desc = arcpy.Describe(bound)
    key = desc.basename[:4]
    value = os.path.join(boundaryDir, bound)
    keyValueLst.append((key, value))
maskDic = dict(keyValueLst)

# set Neighborhood Parameters for IDW
majSemiaxis = 500
minSemiaxis = 500
angle = 0
maxNeighbors = 15
minNeighbors = 10
sectorType = "ONE_SECTOR"

# IDW input feature class
soilSampFolder = os.path.join(inputDir, "Projected_Fc")

env.workspace = soilSampFolder
soliSampLst = arcpy.ListFeatureClasses()
arcpy.CheckOutExtension("GeoStats")
arcpy.CheckOutExtension("Spatial")
# IDW interpolation
totalTime = 0
mapId = 1
for samp in soliSampLst:
    print "Deal with the %s th idw layer" % mapId
    mapId += 1
    startTime = time.time()
    #print samp
    #nrows = arcpy.GetCount_management(samp)
    #maxNeighbors = nrows
    #minNeighbors = nrows
    #print maxNeighbors, minNeighbors
    searchNeighbourhood = arcpy.SearchNeighborhoodStandard(majSemiaxis, minSemiaxis, angle, maxNeighbors, minNeighbors,
                                                           sectorType)
    desc = arcpy.Describe(samp)
    baseName = desc.basename
    if "Bottom" in baseName:
        depth = "Bottom"
    else:
        depth = "Top"
    newSampName = baseName[:4] + "_" + depth
    env.extent = maskDic[baseName[:4]]
    env.mask = maskDic[baseName[:4]]

    for metal in ["Zinc", "Steel", "Copper"]:
        out_idw_model_Lyr = newSampName + "_ModelLyr_" + metal + ".lyr"
        # get optimized  parameters for IDW
        arcpy.IDW_ga(in_features=samp, z_field=metal, out_ga_layer=out_idw_model_Lyr, cell_size="5",
                     search_neighborhood=searchNeighbourhood)
        optimized_out_idw_model_Xml = os.path.join(optimizedOutModel,
                                                   newSampName + "_OptimizedModelLyr_" + metal + ".xml")
        arcpy.GASetModelParameter_ga(out_idw_model_Lyr,
                                     "/model[@name='IDW']/value[@name='Power']/@auto; /model[@name='IDW']/model[@name='NeighbourSearch']/value[@name='MajorSemiaxis']/@auto; /model[@name='IDW']/model[@name='NeighbourSearch']/value[@name='MinorSemiaxis']/@auto",
                                     in_param_value="true;true;true", out_ga_model=optimized_out_idw_model_Xml)

# important: no space should appear in the name of input featureclass
        #idw_dataset = samp + " " + "X=Shape Y=Shape F1=" + str(metal)
        #print "idw input dataset: ", type(idw_dataset),idw_dataset
        geo_dataset_idw = arcpy.GeostatisticalDatasets(optimized_out_idw_model_Xml)
        geo_dataset_idw.dataset1 = samp
        geo_dataset_idw.dataset1Field = metal
        outLayer_idw_optimized = os.path.join(optimizedOutLyr, newSampName + "_optimizedLyr" + metal + ".lyr")

        arcpy.GACreateGeostatisticalLayer_ga(in_ga_model_source=optimized_out_idw_model_Xml,in_datasets=geo_dataset_idw, out_layer=outLayer_idw_optimized)

        power = arcpy.GAGetModelParameter_ga(outLayer_idw_optimized, "/model[@name='IDW']/value[@name='Power']")
        #print type(str(power.getOutput(0))), power.getOutput(0)

        if float(str(power.getOutput(0))[:5]) >= 4:
            print "WARNING: Optimized power %s bigger than 4, then use 2" %str(power.getOutput(0))[:5]
            arcpy.GASetModelParameter_ga(out_idw_model_Lyr,"/model[@name='IDW']/value[@name='Power']; /model[@name='IDW']/model[@name='NeighbourSearch']/value[@name='MajorSemiaxis']/@auto; /model[@name='IDW']/model[@name='NeighbourSearch']/value[@name='MinorSemiaxis']/@auto",
                                         in_param_value="2;true;true", out_ga_model=optimized_out_idw_model_Xml)
            arcpy.GACreateGeostatisticalLayer_ga(in_ga_model_source=optimized_out_idw_model_Xml,in_datasets=geo_dataset_idw, out_layer=outLayer_idw_optimized)

        parameters = arcpy.GAGetModelParameter_ga(outLayer_idw_optimized,
                                                      "/model[@name='IDW']/value[@name='Power']; /model[@name='IDW']/model[@name='NeighbourSearch']/value[@name='MajorSemiaxis']; /model[@name='IDW']/model[@name='NeighbourSearch']/value[@name='MinorSemiaxis']")


        print "idw interpolation using dataset: %s" %samp, "\n","metal: %s" %metal, "\n","parameters uese: " "\n","\t", "power; majSemiaxis; minSemiaxis:" ,parameters
        print "\n","-----------------------------------------------------"
        #print "test",type(parameters.getOutput(0)),parameters.getOutput(0)
        IdwReslutLyr = os.path.join(optimizedOutLyr, newSampName + "_IDW_" + metal + ".lyr")
        arcpy.SaveToLayerFile_management(outLayer_idw_optimized, IdwReslutLyr, 'ABSOLUTE')
        outIdwRas = os.path.join(outIdwRasDir, baseName + "_" + depth + "_IDW_" + metal + ".tif")

        outCellSize = 1
        arcpy.GALayerToGrid_ga(IdwReslutLyr, outIdwRas, outCellSize, "1", "1")
        endTime = time.time()
        runningTime = endTime - startTime
        totalTime = runningTime + totalTime
        print "Time: %.2f" %runningTime
print "Total Time: %.2f" %totalTime