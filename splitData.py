import arcpy
import os
workspace = r"C:\Users\jyang71\Desktop\EpriMapping2018\Project1"
arcpy.env.workspace = workspace
PvFarmFc = os.path.join(workspace,"PV_FarmData.shp")
splitedPvFc_Path = os.path.join(workspace,"spliedPcFarmFc")
os.mkdir(splitedPvFc_Path)
field = ["PV_Farm_La","Depth"]
Deli_PvFarm_La = arcpy.AddFieldDelimiters(PvFarmFc,"PV_Farm_La")
Deli_Depth = arcpy.AddFieldDelimiters(PvFarmFc,"Depth")
PvFarmFc_Sc = arcpy.da.SearchCursor(PvFarmFc,field)
Lables = []
Depth = []
for Fc in PvFarmFc_Sc:
    if not Fc[0] in Lables:
        Lables.append(Fc[0])
    if not Fc[1] in Depth:
        Depth.append(Fc[1])

for Dep in Depth:
    for Lable in Lables:
        SQL_expression  = Deli_PvFarm_La + "=" + Lable + "and" + Deli_Depth + "=" + Dep
        arcpy.FeatureClassToFeatureClass_conversion(PvFarmFc, splitedPvFc_Path, Lable + "_" + Dep + ".shp", SQL_expression)


