#Ce script est un code Python qui produit des fichiers, pouvant être affichés sur Arcgis Pro.
#Les fichiers avec symbologies permettent de visualiser les zones d'inondations de la Baie d'Authie, les zones où le risque d'inondation est fort et les classes d'occupation du sol
#2 tables sont aussi créés contenant le nombre de batiments en zones inondés et les surfaces inondés par classe d'occupation

import arcpy, os # importation de la bibliothèque arcpy d'arcgis contenant l'ensemble des toolboxes et de la bibliothèque os de l'ordinateur
from arcpy import env # importation d'un workspace
from arcpy.sa import *

env.overwriteOutput = True

input_path = arcpy.GetParameterAsText(0)
nom_cadastre80batiments = arcpy.GetParameterAsText(1)
nom_Communes_France = arcpy.GetParameterAsText(2)
nom_MNT_RGF93_5m = arcpy.GetParameterAsText(3)
nom_occup_sol = arcpy.GetParameterAsText(4)
niv_eau_init = float(arcpy.GetParameterAsText(5))
output_f_path = arcpy.GetParameterAsText(6)
output_name = arcpy.GetParameterAsText(7)
SHP_baie_authie_reclass_lyrx = arcpy.GetParameterAsText(8)
occup_sol_lyrx = arcpy.GetParameterAsText(9)

if arcpy.Exists(os.path.join(output_f_path, output_name)):
    arcpy.management.Delete(os.path.join(output_f_path, output_name))

arcpy.management.CreateFileGDB(output_f_path, output_name, "")


output_path = f'{output_f_path}/{output_name}'
arcpy.env.workspace = output_path

path_cadastre80batiments = f"{input_path}\{nom_cadastre80batiments}"
path_Communes_France = f"{input_path}\{nom_Communes_France}"
path_MNT_RGF93_5m = f"{input_path}\{nom_MNT_RGF93_5m}"
path_occup_sol = f"{input_path}\{nom_occup_sol}"
    

arcpy.conversion.FeatureClassToGeodatabase([path_cadastre80batiments, path_Communes_France, path_occup_sol], output_path)
arcpy.conversion.RasterToGeodatabase(path_MNT_RGF93_5m, output_path)

coor_system = arcpy.SpatialReference(2154)
nom_batiments80_L93 = "batiments80_L93"
arcpy.management.Project(nom_cadastre80batiments, nom_batiments80_L93, coor_system)

arcpy.management.MakeFeatureLayer("Communes_France", "Communes_France_lyr")

val = ["Quend", "Saint-Quentin-en-Tourmont", "Rue", "Fort-Mahon-Plage", "Le Crotoy"]
selection = "nom IN ('" + "','".join(val) + "')"
arcpy.management.SelectLayerByAttribute("Communes_France_lyr", "NEW_SELECTION", selection)
Communes_baie_authie = "Communes_baie_authie"
arcpy.management.CopyFeatures("Communes_France_lyr", Communes_baie_authie)
print(f'{Communes_baie_authie} créé')

outExtractByMask = ExtractByMask(nom_MNT_RGF93_5m, Communes_baie_authie)
MNT_5m_baie_authie = "MNT_5m_baie_authie"
outExtractByMask.save(MNT_5m_baie_authie)


calcul_minus = arcpy.ia.Minus(MNT_5m_baie_authie, niv_eau_init)
minus = "MNT_baie_authie_minus"
calcul_minus.save(minus)

calcul_reclass = Reclassify(minus, "VALUE", RemapRange([[-1000, -2, 1],
                                                        [-2, -1, 2],
                                                        [-1, -0.5, 3],
                                                        [-0.5, 0, 4],
                                                        [0, 1000, 5]]), "")

reclass = "MNT_baie_authie_reclass"
calcul_reclass.save(reclass)

reclass_shp = "SHP_baie_authie_reclass"
arcpy.conversion.RasterToPolygon(reclass, reclass_shp)

'''symbologie_fields = [["VALUE_FIELD", "gridcode", "gridcode"]]
arcpy.management.ApplySymbologyFromLayer(reclass_shp, SHP_baie_authie_reclass_lyrx,symbologie_fields)
SHP_baie_authie_avec_symb = "SHP_baie_authie_reclass_avec_symb"
arcpy.management.SaveToLayerFile(reclass_shp, SHP_baie_authie_avec_symb)'''

reclass_shp_lyr = "SHP_baie_authie_reclass_lyr"
arcpy.management.MakeFeatureLayer(reclass_shp, reclass_shp_lyr)
arcpy.management.SelectLayerByAttribute(reclass_shp_lyr, "NEW_SELECTION", "gridcode = 1 Or gridcode = 2")
zones_innon_sup_1m = "zones_innon_sup_1m"   
arcpy.management.CopyFeatures(reclass_shp_lyr, zones_innon_sup_1m)

                                         

symbologie_fields = [["VALUE_FIELD", "gridcode", "gridcode"]]

arcpy.management.MakeFeatureLayer(zones_innon_sup_1m, "zones_innon_sup_1m_lyr")
if arcpy.Exists("zones_innon_sup_1m_lyr"):
    arcpy.management.ApplySymbologyFromLayer("zones_innon_sup_1m_lyr", SHP_baie_authie_reclass_lyrx, symbologie_fields)
    sup_1m_symbo = "sup_1m_symbo"
    arcpy.management.SaveToLayerFile("zones_innon_sup_1m_lyr", sup_1m_symbo)

else:
    print("La couche 'zones_innon_sup_1m' n'existe pas ou n'est pas accessible.")



batiments_baie_authie = "batiments_baie_authie"
arcpy.analysis.Clip(nom_batiments80_L93, Communes_baie_authie, batiments_baie_authie)

batiments_baie_authie_lyr = "batiments_baie_authie_lyr"
arcpy.management.MakeFeatureLayer(batiments_baie_authie, batiments_baie_authie_lyr)
arcpy.management.SelectLayerByLocation(batiments_baie_authie_lyr, "", zones_innon_sup_1m)
batiments_baie_authie_sup_1m ="batiments_baie_authie_sup_1m"
arcpy.management.CopyFeatures(batiments_baie_authie_lyr, batiments_baie_authie_sup_1m)


table_nb_bat_sup_1m = "table_nb_bat_sup_1m"
arcpy.management.CreateTable(output_path,table_nb_bat_sup_1m )
arcpy.management.AddField(table_nb_bat_sup_1m, "Commune","TEXT")
arcpy.management.AddField(table_nb_bat_sup_1m, "Nb_bat","SHORT")



result1 = arcpy.management.GetCount(batiments_baie_authie_sup_1m)

selection = "nom IN ('Quend')"
arcpy.management.SelectLayerByAttribute("Communes_France_lyr", "NEW_SELECTION", selection)
arcpy.management.CopyFeatures("Communes_France_lyr", "Quend_commune")
selection = "nom IN ('Saint-Quentin-en-Tourmont')"
arcpy.management.SelectLayerByAttribute("Communes_France_lyr", "NEW_SELECTION", selection)
arcpy.management.CopyFeatures("Communes_France_lyr", "Saint_Quentin_en_Tourmont_commune")
selection = "nom IN ('Rue')"
arcpy.management.SelectLayerByAttribute("Communes_France_lyr", "NEW_SELECTION", selection)
arcpy.management.CopyFeatures("Communes_France_lyr", "Rue_commune")
selection = "nom IN ('Fort-Mahon-Plage')"
arcpy.management.SelectLayerByAttribute("Communes_France_lyr", "NEW_SELECTION", selection)
arcpy.management.CopyFeatures("Communes_France_lyr", "Fort_Mahon_Plage_commune")
selection = "nom IN ('Le Crotoy')"
arcpy.management.SelectLayerByAttribute("Communes_France_lyr", "NEW_SELECTION", selection)
arcpy.management.CopyFeatures("Communes_France_lyr", "Le_Crotoy_commune")

batiments_baie_authie_sup_1m_lyr = "batiments_baie_authie_sup_1m_lyr"
arcpy.management.MakeFeatureLayer(batiments_baie_authie_sup_1m, batiments_baie_authie_sup_1m_lyr)
arcpy.management.SelectLayerByLocation(batiments_baie_authie_sup_1m_lyr, "", "Quend_commune")
result2 = arcpy.management.GetCount(batiments_baie_authie_sup_1m_lyr)
print(f"   -{result2} dans la commune de Quend")
arcpy.management.SelectLayerByLocation(batiments_baie_authie_sup_1m_lyr, "", "Saint_Quentin_en_Tourmont_commune")
result3 = arcpy.management.GetCount(batiments_baie_authie_sup_1m_lyr)
print(f"   -{result3} dans la commune de Saint-Quentin-en-Tourmont")
arcpy.management.SelectLayerByLocation(batiments_baie_authie_sup_1m_lyr, "", "Rue_commune")
result4 = arcpy.management.GetCount(batiments_baie_authie_sup_1m_lyr)
print(f"   -{result4} dans la commune de Rue")
arcpy.management.SelectLayerByLocation(batiments_baie_authie_sup_1m_lyr, "", "Fort_Mahon_Plage_commune")
result5 = arcpy.management.GetCount(batiments_baie_authie_sup_1m_lyr)
print(f"   -{result5} dans la commune de Fort-Mahon-Plage")
arcpy.management.SelectLayerByLocation(batiments_baie_authie_sup_1m_lyr, "", "Le_Crotoy_commune")
result6 = arcpy.management.GetCount(batiments_baie_authie_sup_1m_lyr)
print(f"   -{result6} dans la commune de Le Crotoy")


count_value1 = int(result1.getOutput(0))
count_value2 = int(result2.getOutput(0))
count_value3 = int(result3.getOutput(0))
count_value4 = int(result4.getOutput(0))
count_value5 = int(result5.getOutput(0))
count_value6 = int(result6.getOutput(0))
myRows1 = ("France", count_value1)
myRows2 = ("Quend", count_value2)
myRows3 = ("Saint-Quentin-en-Tourmont", count_value3)
myRows4 = ("Rue", count_value4)
myRows5 = ("Fort-Mahon-Plage",count_value5)
myRows6 =  ("Le Crotoy", count_value6)
fields = ["Commune", "Nb_bat"]
with arcpy.da.InsertCursor(table_nb_bat_sup_1m,fields) as ins:
    ins.insertRow(myRows1)
    ins.insertRow(myRows2)
    ins.insertRow(myRows3)
    ins.insertRow(myRows4)
    ins.insertRow(myRows5)
    ins.insertRow(myRows6)
    

occup_sol_sup_1m = "occup_sol_sup_1m"
arcpy.analysis.Clip(nom_occup_sol, zones_innon_sup_1m, occup_sol_sup_1m)
arcpy.management.AddField(occup_sol_sup_1m, "surface", "DOUBLE")
exp = "!SHAPE.AREA@SQUAREMETERS! / 10000"
arcpy.CalculateField_management(occup_sol_sup_1m, "surface", exp, "PYTHON_9.3")

arcpy.management.AddField(occup_sol_sup_1m, "nom_gridcode", "TEXT")
exp = "'Eau' if !gridcode! == 10 else \
                ('Sable' if !gridcode! == 20 else \
                 ('Champs' if !gridcode! == 30 else \
                  ('Urbanisation' if !gridcode! == 40 else \
                   ('Forêt' if !gridcode! == 50 else None))))"
arcpy.management.CalculateField(occup_sol_sup_1m, "nom_gridcode", exp, "PYTHON_9.3")


arcpy.management.MakeFeatureLayer(occup_sol_sup_1m, "occup_sol_sup_1m_lyr")
arcpy.management.ApplySymbologyFromLayer("occup_sol_sup_1m_lyr", occup_sol_lyrx, symbologie_fields)
occup_sol_sup_1m_symbo = "occup_sol_sup_1m_symbo"

statsFields = [["surface", "SUM"]]
arcpy.analysis.Statistics(occup_sol_sup_1m, "table_occup_sol_sup_1m",  statsFields, "nom_gridcode")


print("End Script")
