#Ce script est un code Python qui produit des fichiers, pouvant être affichés sur Arcgis Pro.
#Les fichiers avec symbologies permettent de visualiser les zones d'inondations de la Baie d'Authie, les zones où le risque d'inondation est fort et les classes d'occupation du sol
#2 tables sont aussi créés contenant le nombre de batiments en zones inondés et les surfaces inondés par classe d'occupation

import arcpy, os # importation de la bibliothèque arcpy d'arcgis contenant l'ensemble des toolboxes et de la bibliothèque os de l'ordinateur
from arcpy import env # importation d'un workspace
from arcpy.sa import *

env.overwriteOutput = True

#Définition des environnements
print("Définition des environnements")
input_path = r"C:\Users\HP\OneDrive\Documents\Unilasalle cours\4eme année\Système géographique avancé\Projet Arcgis\projet_Baie_dAuthie\Projet_baie_authie_input_data.gdb"

#Creation gdb
#dem_gdb = input('Voulez vous creer la gdb ? O/N \n')
#if dem_gdb == 'O' or dem_gdb == 'o':
print ("on créer notre gdp")
output_path = r"C:\Users\HP\OneDrive\Documents\Unilasalle cours\4eme année\Système géographique avancé\Projet Arcgis\projet_Baie_dAuthie"
out_name = "Projet_baie_authie_resultats.gdb"
if arcpy.Exists(os.path.join(output_path, out_name)):
    arcpy.management.Delete(os.path.join(output_path, out_name))
    print("Ancienne gdb supprimée")
arcpy.management.CreateFileGDB(output_path, out_name, "")
print ("Nouvelle gdp créée")

#Définition des environnements 2
print("Suite définition des environnements")
output_path = r"C:\Users\HP\OneDrive\Documents\Unilasalle cours\4eme année\Système géographique avancé\Projet Arcgis\projet_Baie_dAuthie\Projet_baie_authie_resultats.gdb"
arcpy.env.workspace = output_path

#Définition des variables
print("Définition des variables")
nom_cadastre80batiments = "cadastre80batiments"
nom_Communes_France = "Communes_France"
nom_MNT_RGF93_5m = "MNT_RGF93_5m"
nom_occup_sol = "occup_sol"
ask_chem = input("Voulez vous entrer vous-même les chemins d'accés des fichiers ? O/N \n")
if ask_chem ==  "O" :
    path_cadastre80batiments = input("Donnez ci dessous le chemin d'accés du fichier 'cadastre80batiments'") 
    path_Communes_France = input("Donnez ci dessous le chemin d'accés du fichier 'Commune_France'")
    path_MNT_RGF93_5m = input("Donnez ci dessous le chemin d'accés du fichier 'MNT_RGF93_5m'")
    path_occup_sol = input("Donnez ci dessous le chemin d'accés du fichier issue de la télédétéction")

else :
    path_cadastre80batiments = f"{input_path}\{nom_cadastre80batiments}"
    path_Communes_France = f"{input_path}\{nom_Communes_France}"
    path_MNT_RGF93_5m = f"{input_path}\{nom_MNT_RGF93_5m}"
    path_occup_sol = f"{input_path}\{nom_occup_sol}"
print("Variables définits")


#Conversion vers la gdb de travail
print("Conversion vers la gdb de travail")
#dem_conv = input('Voulez vous reconvertir les données vers la gdb resultats ? O/N \n')
#if dem_conv == 'O' or dem_conv == 'o' :
arcpy.conversion.FeatureClassToGeodatabase([path_cadastre80batiments, path_Communes_France, path_occup_sol], output_path)
print("Vecteur convertit")
if not arcpy.Exists(os.path.join(output_path, nom_MNT_RGF93_5m)): # Cette condition ne sert à rien mais je l'ai laissé car j'avais mit du temps à la trouver
    arcpy.conversion.RasterToGeodatabase(path_MNT_RGF93_5m, output_path)
    print("Raster convertit")
else:
    print(f"Le fichier raster {nom_MNT_RGF93_5m} existe déjà dans la géodatabase de sortie.")

    

#Changement SRC
print("Changement SRC")
#dem_src = input('Voulez vous rechanger le SRC de la couche batiment ? O/N \n')
#if dem_src == 'O' or dem_src == 'o':
coor_system = arcpy.SpatialReference(2154)
nom_batiments80_L93 = "batiments80_L93"
arcpy.management.Project(nom_cadastre80batiments, nom_batiments80_L93, coor_system)
print("SRC changé")

#Select by attribute communes
print("Séléction des communes")
arcpy.management.MakeFeatureLayer("Communes_France", "Communes_France_lyr")
'''val = ["Quend", "Saint-Quentin-en-Tourmont", "Rue", "Fort-Mahon", "Le Crotoy"]
selection = str(""" "nom" = '""" + val + "'")'''

val = ["Quend", "Saint-Quentin-en-Tourmont", "Rue", "Fort-Mahon-Plage", "Le Crotoy"]
selection = "nom IN ('" + "','".join(val) + "')"
arcpy.management.SelectLayerByAttribute("Communes_France_lyr", "NEW_SELECTION", selection)
Communes_baie_authie = "Communes_baie_authie"
arcpy.management.CopyFeatures("Communes_France_lyr", Communes_baie_authie)
print(f'{Communes_baie_authie} créé')
#arcpy.management.MakeFeatureLayer("cadastre80batiments", "cadastre80batiments_lyr")


#Dimensionnement des données
print("Dimensionnement des données")
print("  Extract by mask")
outExtractByMask = ExtractByMask(nom_MNT_RGF93_5m, Communes_baie_authie)
MNT_5m_baie_authie = "MNT_5m_baie_authie"
outExtractByMask.save(MNT_5m_baie_authie)


#Définition zones inondation
print("Définition des zones d'inondation")

  #Minus
print("  Creation minus")
niv_eau_init = float(input("Veuillez saisir la valeur du niveau d'eau initial en mètres NGF : "))
print(f'Votre valeur {niv_eau_init} mètres NGF')
calcul_minus = arcpy.ia.Minus(MNT_5m_baie_authie, niv_eau_init)
minus = "MNT_baie_authie_minus"
calcul_minus.save(minus)

print("  Minus créé")

  #Reclassify
print("  Reclassify")

calcul_reclass = Reclassify(minus, "VALUE", RemapRange([[-1000, -2, 1],
                                                        [-2, -1, 2],
                                                        [-1, -0.5, 3],
                                                        [-0.5, 0, 4],
                                                        [0, 1000, 5]]), "")

reclass = "MNT_baie_authie_reclass"
calcul_reclass.save(reclass)
print("  Reclassify fait")

  #Raster to polygon
print("  Raster to polygon")
reclass_shp = "SHP_baie_authie_reclass"
arcpy.conversion.RasterToPolygon(reclass, reclass_shp)
print("  Raster to polygon Fait")

 #Symbologie
print("  Application de la symbologie")
ask_chem = input("Voulez vous entrer vous-même les chemins d'accés de la symbologie ? O/N \n")
if ask_chem ==  "O" :
    SHP_baie_authie_reclass_lyrx = input("Indiquez ci-dessous le chemin d'accés au fichier symbology_shp_baie_authie.lyrx")
else :
    SHP_baie_authie_reclass_lyrx = r"C:\Users\HP\OneDrive\Documents\Unilasalle cours\4eme année\Système géographique avancé\Projet Arcgis\projet_Baie_dAuthie\symbology_shp_baie_authie.lyrx"

symbologie_fields = [["VALUE_FIELD", "gridcode", "gridcode"]]
arcpy.management.ApplySymbologyFromLayer(reclass_shp, SHP_baie_authie_reclass_lyrx,symbologie_fields)
SHP_baie_authie_avec_symb = "SHP_baie_authie_reclass_avec_symb"
arcpy.management.SaveToLayerFile(reclass_shp, SHP_baie_authie_avec_symb)
print("  Symbologie appliquée")


#Selection zones inondation > 1m
print("Selection zones inondation > 1m")
reclass_shp_lyr = "SHP_baie_authie_reclass_lyr"
#arcpy.management.MakeFeatureLayer(reclass_shp, reclass_shp_lyr)
arcpy.management.SelectLayerByAttribute(reclass_shp, "NEW_SELECTION", "gridcode = 1 Or gridcode = 2")
zones_innon_sup_1m = "zones_innon_sup_1m"   
arcpy.management.CopyFeatures(reclass_shp, zones_innon_sup_1m)
print("SHP zones inondation > 1m créé")
                                         
  #Symbologie
print("  Application de la symbologie")
symbologie_fields = [["VALUE_FIELD", "gridcode", "gridcode"]]

arcpy.management.MakeFeatureLayer(zones_innon_sup_1m, "zones_innon_sup_1m_lyr")
if arcpy.Exists("zones_innon_sup_1m_lyr"):
    arcpy.management.ApplySymbologyFromLayer("zones_innon_sup_1m_lyr", SHP_baie_authie_reclass_lyrx, symbologie_fields)
    sup_1m_symbo = "sup_1m_symbo"
    arcpy.management.SaveToLayerFile("zones_innon_sup_1m_lyr", sup_1m_symbo)
    print("  Symbologie appliquée")
else:
    print("La couche 'zones_innon_sup_1m' n'existe pas ou n'est pas accessible.")


#Selection batiments en zones inondation > 1m
print("Selection batiments en zones inondation > 1m")
print("  Clip")
batiments_baie_authie = "batiments_baie_authie"
arcpy.analysis.Clip(nom_batiments80_L93, Communes_baie_authie, batiments_baie_authie)

batiments_baie_authie_lyr = "batiments_baie_authie_lyr"
arcpy.management.MakeFeatureLayer(batiments_baie_authie, batiments_baie_authie_lyr)
arcpy.management.SelectLayerByLocation(batiments_baie_authie_lyr, "", zones_innon_sup_1m)
batiments_baie_authie_sup_1m ="batiments_baie_authie_sup_1m"
arcpy.management.CopyFeatures(batiments_baie_authie_lyr, batiments_baie_authie_sup_1m)

  #Creation table pour stocker stats
print("Creation table pour stocker stats")
table_nb_bat_sup_1m = "table_nb_bat_sup_1m"
arcpy.management.CreateTable(output_path,table_nb_bat_sup_1m )
arcpy.management.AddField(table_nb_bat_sup_1m, "Commune","TEXT")
arcpy.management.AddField(table_nb_bat_sup_1m, "Nb_bat","SHORT")


    
  #Nombre de batiments en zone innondation
result1 = arcpy.management.GetCount(batiments_baie_authie_sup_1m)
print(f"   Il y a, au total, {result1} batiments en zones inondation > 1m")

  #Nombre de batiments en zone innondation par communes
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

  #Ajout valeurs dans table
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
    
#Quantification de la surface totale d'occupation
print("Quantification de la surface total issue du fichier teledection")

print("  Rajout champ surface")
occup_sol_sup_1m = "occup_sol_sup_1m"
arcpy.analysis.Clip(nom_occup_sol, zones_innon_sup_1m, occup_sol_sup_1m)
arcpy.management.AddField(occup_sol_sup_1m, "surface", "DOUBLE")
exp = "!SHAPE.AREA@SQUAREMETERS! / 10000"
arcpy.CalculateField_management(occup_sol_sup_1m, "surface", exp, "PYTHON_9.3")
#arcpy.management.CalculateGeometryAttributes(occup_sol_sup_1m, ["surface", "AREA"])

print("  Rajout champ nom_gridcode")
arcpy.management.AddField(occup_sol_sup_1m, "nom_gridcode", "TEXT")
exp = "'Eau' if !gridcode! == 10 else \
                ('Sable' if !gridcode! == 20 else \
                 ('Champs' if !gridcode! == 30 else \
                  ('Urbanisation' if !gridcode! == 40 else \
                   ('Forêt' if !gridcode! == 50 else None))))"
arcpy.management.CalculateField(occup_sol_sup_1m, "nom_gridcode", exp, "PYTHON_9.3")

print("  Création du fichier avec symbologie")
ask_chem = input("Voulez vous entrer vous-même les chemins d'accés de la symbologie ? O/N \n")
if ask_chem ==  "O" :
    occup_sol_lyrx = input("Indiquez ci-dessous le chemin d'accés au fichier occup_sol.lyrx")
else :
    occup_sol_lyrx = r"C:\Users\HP\OneDrive\Documents\Unilasalle cours\4eme année\Système géographique avancé\Projet Arcgis\projet_Baie_dAuthie\occup_sol.lyrx"

arcpy.management.MakeFeatureLayer(occup_sol_sup_1m, "occup_sol_sup_1m_lyr")
arcpy.management.ApplySymbologyFromLayer("occup_sol_sup_1m_lyr", occup_sol_lyrx, symbologie_fields)
occup_sol_sup_1m_symbo = "occup_sol_sup_1m_symbo"
#arcpy.management.SaveToLayerFile("occup_sol_sup_1m_lyr", occup_sol_sup_1m_symbo)

print("  Création de la table avec valeurs de surface")
statsFields = [["surface", "SUM"]]
arcpy.analysis.Statistics(occup_sol_sup_1m, "table_occup_sol_sup_1m",  statsFields, "nom_gridcode")
print("Table créée")

print("End Script")
