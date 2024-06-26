import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import locale
from string import ascii_uppercase
from itertools import pairwise
from openpyxl import load_workbook
import pandas as pd
import os
import re
def concat_and_sort(x):
        grouped_df = x[x['secteur'] != 5].groupby('secteur')['SAU(ha)'].sum()
        df_from_grouped = grouped_df.reset_index()
        df_from_grouped.columns = ['secteur', 'SAU(ha)']
        
        df2 = x[x['secteur'] == 5][["secteur","SAU(ha)"]]
        df2.reset_index(drop=True, inplace=True)
        
        concatenated_df = pd.concat([df_from_grouped, df2])
        sorted_df = concatenated_df.sort_values(by='secteur')
        sorted_df.reset_index(drop=True, inplace=True)
        sorted_df["serre"]=[i for i in range(1,8)]
        return sorted_df
class ExcelDataExtractor:
    def __init__(self, file_path,folder_path ):
        self.file_path = file_path
        self.folder_path= folder_path
    


    def get_next_code(self, code):
        '''
        returns next column letter given existing one
        input: 'AA', output: 'AB'
        input: 'AB', output: 'AC'
        '''
        letter_map = {a: b for a, b in pairwise(ascii_uppercase)}
        code = list(code)
        i = -1
        while True:
            if code[i] == 'Z':
                code[i] = 'A'
                i -= 1
                if abs(i) > len(code):
                    return 'A' + ''.join(code)
            else:
                code[i] = letter_map[code[i]]
                return ''.join(code)

    def snap_table(self, sheet, topleft, num_columns, num_rows):
        '''
        input:
            sheet: the Excel sheet we want
            topleft: coordinates of topleft coordinate eg. 'B2'
            num_columns: number of columns in table
            num_rows: number of rows in table
        output:
            pandas dataframe representing table
        '''
        try:
            col = re.findall('[a-zA-Z]+', topleft)[0]
            num = int(re.findall('[0-9]+', topleft)[0])

            columns = [col]
            for i in range(num_columns - 1):
                columns.append(self.get_next_code(columns[-1]))
            numbers = [n for n in range(num, num + num_rows)]

            data = []
            for n in numbers:
                row = []
                for c in columns:
                    code = c + str(n)
                    row.append(sheet[code].value or sheet[code].value)
                data.append(row)
            return pd.DataFrame(data[1:], columns=data[0])
        except Exception as e:
            return pd.DataFrame()

    def extract_data(self):
        workbook = load_workbook(self.file_path)
        sheet1 = workbook['latest inputs']
        sheet2 = workbook['Indices']
        sheet3 = workbook['Simulation']
        df_price = self.snap_table(sheet1, 'B10', 91, 3)
        df_prod = self.snap_table(sheet1, 'B17', 45, 16)
        df_chargesvar = self.snap_table(sheet1, 'B38', 8, 16)
        df_plantation = self.snap_table(sheet2, 'J52', 3, 11)
        # df_month_index = self.snap_table(sheet2, 'L3', 2, 25)
        df_sim = self.snap_table(sheet3, 'B22', 3, 25)

          # Default folder path
        os.makedirs(self.folder_path, exist_ok=True)  # Create the folder if it doesn't exist

        # Export DataFrames with full path
        df_price.to_csv(os.path.join(self.folder_path, "Prices.csv"), index=False)
        df_chargesvar.to_csv(os.path.join(self.folder_path, "Charges_var.csv"), index=False)
        df_prod.to_csv(os.path.join(self.folder_path, "Production.csv"), index=False)
        df_plantation.to_csv(os.path.join(self.folder_path, "plantation.csv"), index=False)
        df_sim_bis=concat_and_sort(df_sim)
        df_sim_bis.to_csv(os.path.join(self.folder_path, "Simulation.csv"), index=False)
        df_price.to_csv(os.path.join(self.folder_path + " copy", "Prices.csv"), index=False)
        df_chargesvar.to_csv(os.path.join(self.folder_path + " copy", "Charges_var.csv"), index=False)
        df_prod.to_csv(os.path.join(self.folder_path + " copy", "Production.csv"), index=False)
        df_plantation.to_csv(os.path.join(self.folder_path + " copy", "plantation.csv"), index=False)
        df_sim_bis.to_csv(os.path.join(self.folder_path + " copy", "Simulation.csv"), index=False)

        print(f"DataFrames saved to folder: {self.folder_path}")
class DataProcessor:
    def __init__(self, folder_path, premium):
        self.folder_path = folder_path
        self.premium=premium
        self.df_price = None
        self.df_chargesvar = None
        self.df_prod = None
        self.df_plantation = None
        # self.df_month_index = None
        self.df_sim = None
        self.counts=None
        self.variety_scenario_dict = None
        self.scenario_variety_mapping = None
        self.serre_sau_dict = None
        self.scenario_prod = None
        self.month_to_week_indices = None
        self.scenario_cmo = None
        self.scenario_vitesse = None
        self.scenario_cv = None
        self.scenario_delai_dict = None
        self.scenario_duree_dict = None
        self.scenario_mois_dict = None
        self.scenario_culture = None
        self.secteur_serre_dict = None
        self.serre_secteur_dict = None
        self.price = None
        self.scenarios = None
        self.num_serre = None
        self.num_sect = None
        self.prod = None
        self.prod_mat = None
        self.serre_sau_dict=None
        self.scenario_couple=None
    
    def get_data(self):
        self.df_price = pd.read_csv(os.path.join(self.folder_path, "Prices.csv")).fillna(0)
        self.df_chargesvar = pd.read_csv(os.path.join(self.folder_path, "Charges_var.csv"))
        self.df_prod = pd.read_csv(os.path.join(self.folder_path, "Production.csv")).fillna(0)
        self.df_plantation = pd.read_csv(os.path.join(self.folder_path, "plantation.csv"))
        # self.df_month_index = pd.read_csv(os.path.join(self.folder_path, "month_index.csv"))
        self.df_sim = pd.read_csv(os.path.join(self.folder_path, "Simulation.csv"))
        
    def get_dict(self):
        serre_sau_dict = self.df_sim.set_index('serre')['SAU(ha)'].to_dict()
        self.serre_sau_dict=serre_sau_dict
        scenario_variety_mapping = self.df_prod[['Scénario', 'variété 23-24']]
        sum_last_37 = self.df_prod.iloc[:, -37:].sum(axis=1)
        variety_scenario_dict = {}
        scenario_prod = dict(zip(self.df_prod['Scénario'], sum_last_37))
        
        for _, row in scenario_variety_mapping.iterrows():
            scenario = row['Scénario']
            variety = row['variété 23-24']
            if variety not in variety_scenario_dict:
                variety_scenario_dict[variety] = []
            variety_scenario_dict[variety].append(scenario)
        
        self.variety_scenario_dict = variety_scenario_dict
        self.scenario_variety_mapping = scenario_variety_mapping
        self.serre_sau_dict = serre_sau_dict
        self.scenario_prod = scenario_prod
        
    def month_week_dict(self):
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        start_date = datetime(2024, 1, 1)
        data = []
        months = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        num_weeks = 84
        
        for index in range(1, num_weeks + 1):
            month_index = start_date.month
            month_name = months[month_index - 1]
            month = month_name.capitalize()
            month_index = self.get_month_index(month)
            data.append([month, start_date.strftime('%d/%m/%Y'), month_index, index])
            start_date += timedelta(weeks=1)
        
        df_week_index = pd.DataFrame(data, columns=['Month', 'Date', 'Month Index', 'Week Index'])
        month_to_week_indices = {}
        
        for index, row in df_week_index.iterrows():
            month = row['Month']
            week_index = row['Week Index']
            if month not in month_to_week_indices:
                month_to_week_indices[month] = []
            month_to_week_indices[month].append(week_index)
        
        self.month_to_week_indices = month_to_week_indices
    
    def get_month_index(self, month):
        month_dict = {
            'Janvier': 1,
            'Février': 2,
            'Mars': 3,
            'Avril': 4,
            'Mai': 5,
            'Juin': 6,
            'Juillet': 7,
            'Aout': 8,
            'Septembre': 9,
            'Octobre': 10,
            'Novembre': 11,
            'Décembre': 12
        }
        return month_dict[month]
    
    def extract_scenario_charges(self):
        scenario_cmo = {}
        scenario_vitesse = {}
        scenario_cv = {}
        
        for _, row in self.df_chargesvar.iterrows():
            scenario = row['Scénario']
            cmo = row["Coûts de Main d'œuvre par kg de production"]
            vitesse = row["Vitesse de main d'œuvre kg/personne/jour"]
            cv = row["Coûts variable par hectar"]
            scenario_cmo[scenario] = cmo
            scenario_vitesse[scenario] = vitesse
            scenario_cv[scenario] = cv
            
        self.scenario_cmo = scenario_cmo
        self.scenario_vitesse = scenario_vitesse
        self.scenario_cv = scenario_cv
    
    def extract_scenario_production(self):
        scenario_delai_dict = {}
        scenario_duree_dict = {}
        scenario_mois_dict = {}
        scenario_culture = {}
        scenario_couple={}
        for _, row in self.df_prod.iterrows():
            scenario = row['Scénario']
            delai = row['Délai pour début de production']
            duree = row['Durée de production en semaine']
            mois = row['Mois']
            couple=row['Couple']
            culture = row['Culture']
            
            scenario_delai_dict[scenario] = delai
            scenario_duree_dict[scenario] = duree
            scenario_mois_dict[scenario] = mois
            scenario_culture[scenario] = culture
            scenario_couple[scenario]=couple
        
        self.scenario_delai_dict = scenario_delai_dict
        self.scenario_duree_dict = scenario_duree_dict
        self.scenario_mois_dict = scenario_mois_dict
        self.scenario_culture = scenario_culture
        self.scenario_couple=scenario_couple
        self.scenario_chosen=None
        self.semaines_chosen=None
    def extract_sim_data(self):
        secteur_serre_dict = {}
        
        for _, row in self.df_sim.iterrows():
            secteur = row['secteur']
            serre = row['serre']
            if secteur not in secteur_serre_dict:
                secteur_serre_dict[int(secteur)] = [int(serre)]
            else:
                secteur_serre_dict[int(secteur)].append(int(serre))
        
        serre_secteur_dict = {serre: secteur for secteur, serres in secteur_serre_dict.items() for serre in serres}
        
        self.secteur_serre_dict = secteur_serre_dict
        self.serre_secteur_dict = serre_secteur_dict
    
    def extract_price_data(self):
        price = {}
        price["Framboise"] = np.array(self.df_price.iloc[0, 1:])
        price["Mure"] = np.array(self.df_price.iloc[1, 1:])
        multiplier =(price["Framboise"] > 0).astype(int)
        price["Adelita"] =price["Framboise"]+multiplier*self.premium
        self.price = price
    def filter_elements_less_than(self,array, horizon):
        filtered_array = [x for x in array if x <= horizon]
        return filtered_array
    def filter_elements_more_than(self,array, horizon):
        filtered_array = [x for x in array if x > horizon]
        return filtered_array

    def other_data(self):
        scenarios = list(self.scenario_culture.keys())
        num_serre = self.df_sim.shape[0]
        num_sect = len(self.secteur_serre_dict)
        
        self.scenarios = scenarios
        self.num_serre = num_serre
        self.num_sect = num_sect
        counts={}
        for i in range(num_serre):
            s=0
            if i+1 in self.secteur_serre_dict[5]:
                for j in scenarios:
                    if j not in [4,5]:
                        if j in self.variety_scenario_dict["Clara"] or j  in self.variety_scenario_dict["LAURITA"]:
                            if self.serre_sau_dict[i+1] < 2.87:
                                for t in self.month_to_week_indices[self.scenario_mois_dict[j]]:
                                    s+=1
                        else:
                            for t in self.month_to_week_indices[self.scenario_mois_dict[j]]:
                                s+=1
            elif i+1 in self.secteur_serre_dict[6]:
                for j in scenarios:
                    if j not in self.variety_scenario_dict["Clara"] and j not in self.variety_scenario_dict["LAURITA"]:
                        for t in self.month_to_week_indices[self.scenario_mois_dict[j]]:
                            s+=1
            else:
                for j in scenarios:
                    if j not in [4,5] and j not in self.variety_scenario_dict["Clara"] and j not in self.variety_scenario_dict["LAURITA"]:
                        for t in self.month_to_week_indices[self.scenario_mois_dict[j]]:
                            s+=1 
            counts[i]=s    
        self.counts=counts

    def padded_dot(self, a, b):
        len_a = a.shape[1]
        len_b = b.shape[1]
        max_len = max(len_a, len_b)
        a_padded = np.pad(a, ((0, 0), (0, max_len - len_a)), mode='constant', constant_values=0)
        b_padded = np.pad(b, ((0, 0), (0, max_len - len_b)), mode='constant', constant_values=0)
        result = np.dot(a_padded, b_padded.T)
        return result
    
    def compute_tensor(self):
        prod_mat = np.matrix(self.df_prod.iloc[:, 8:])
        prod = {}
        
        for i in range(self.num_serre):
            for j in self.scenarios:
                for t in self.month_to_week_indices[self.scenario_mois_dict[j]]:
                    if j in self.variety_scenario_dict["Adelita"]:
                        price_array = np.array(self.price["Adelita"][t -1+ self.scenario_delai_dict[j] :])
                        prod_mat_array = np.array(prod_mat[self.scenarios.index(j), :])
                        prod[(i, j, t)] = self.serre_sau_dict[i + 1] * self.padded_dot(
                            price_array.reshape(1, -1),
                            prod_mat_array.reshape(1, -1)
                        )[0][0]
                    else:
                        price_array = np.array(self.price[self.scenario_culture[j]][t-1 + self.scenario_delai_dict[j]:])
                        prod_mat_array = np.array(prod_mat[self.scenarios.index(j),:])
                        prod[(i, j, t)] = self.serre_sau_dict[i + 1] * self.padded_dot(
                            price_array.reshape(1, -1),
                            prod_mat_array.reshape(1, -1)
                        )[0][0]
        self.prod = prod
        self.prod_mat = prod_mat
    def get_assets(self):
        self.get_data()
        self.get_dict()
        self.month_week_dict()
        self.extract_scenario_charges()
        self.extract_scenario_production()
        self.extract_sim_data()
        self.extract_price_data()
        self.other_data()
        self.compute_tensor()
    def get_random_price(self, folder_path_rob,sim):
        self.folder_path=folder_path_rob
        self.get_data()
        self.get_dict()
        self.month_week_dict()
        self.extract_scenario_charges()
        self.extract_scenario_production()
        self.extract_sim_data()
        random_prices(folder_path_rob,sim)
        self.get_data()
        self.extract_price_data()
        self.other_data()
        self.compute_tensor()
    def display(self, loop=False, alternative = False, semaines_chosen=[],scenario_chosen=[]):
        if not alternative:

            if loop:
                scenario_chosen=self.scenario_chosen_top
                semaines_chosen=self.semaines_chosen_top
            else:
                semaines_chosen=self.semaines_chosen
                scenario_chosen=self.scenario_chosen

        data_dict = self.scenario_variety_mapping.to_dict(orient='records')
        data_dict = {entry['Scénario']: entry['variété 23-24'] for entry in data_dict}

        data = {
            "Secteur": list(self.serre_secteur_dict[i] for i in range(1, self.num_serre+1)),
            "Serre": list(range(1, self.num_serre + 1)),
            "Sau": list(self.serre_sau_dict.values()),
            "Scenario_index": scenario_chosen,
            "Variété": [data_dict[scenario] for scenario in scenario_chosen],
            "Scenario":[self.scenario_couple[i] for i in scenario_chosen],
            "Scenario Mois":[get_month_from_week_index(i) for i in semaines_chosen],
            
            "Cout variables": [self.scenario_cv[i] for i in scenario_chosen],
            "Vitesse de récolte": [self.scenario_vitesse[i] for i in scenario_chosen],
            
            "Week of plantation": semaines_chosen,
            
            
            "Weeks to debut plantation":[self.scenario_delai_dict[i] for i in scenario_chosen]

            }
        df = pd.DataFrame(data)
        return df
    def summarize(self, dict_CA_values,dict_CMO_values,dict_CV_values,scenario_dict):

        data = {
                "Scenario index": list(set(self.scenario_chosen_top)),
                "Scenario": [self.scenario_couple[i] for i in list(set(self.scenario_chosen_top))],
                "Mois": [self.scenario_mois_dict[i] for i in list(set(self.scenario_chosen_top))],
                "Semaines": [', '.join(map(str, list(set(scenario_dict[i])))) for i in list(set(self.scenario_chosen_top))],
                "Hectars": [
                    int(100*np.dot(
                        [1 if i == self.scenario_chosen_top[value] else 0 for value in range(self.num_serre)],
                        np.array(list(self.serre_sau_dict.values()))
                    ))/100
                    for i in list(set(self.scenario_chosen_top))
                ],
                 "Chiffre d'affaire": ["{:,.0f}".format(dict_CA_values[j]) for j in list(set(self.scenario_chosen_top))],
             "Marge": ["{:,.0f}".format(dict_CA_values[j]-dict_CV_values[j]-dict_CMO_values[j]) for j in list(set(self.scenario_chosen_top))],
             "Taux de marge":[int(100*(dict_CA_values[j]-dict_CV_values[j]-dict_CMO_values[j])/dict_CA_values[j])
                            for j in list(set(self.scenario_chosen_top))]

            }
        df=pd.DataFrame(data)
        return df
    
    def marge(self,scenario_chosen, semaines_chosen):
        CA=sum([self.prod[(i, j, t)] 
                                    for i,j,t in zip(range(self.num_serre), scenario_chosen, semaines_chosen)
                               
                                     ])
        CV=sum([self.serre_sau_dict[i+1] * self.scenario_cv[j] 
                                     for i,j in zip(range(self.num_serre), scenario_chosen)])
        return CA-CV
        




start_date = datetime(2024, 1, 1)

# Dictionary of French month names
french_months = {
    1: 'Janvier',
    2: 'Février',
    3: 'Mars',
    4: 'Avril',
    5: 'Mai',
    6: 'Juin',
    7: 'Juillet',
    8: 'Août',
    9: 'Septembre',
    10: 'Octobre',
    11: 'Novembre',
    12: 'Décembre'
}
def get_month_from_week_index(week_index):
    # Calculate the date corresponding to the week index
    target_date = start_date + timedelta(weeks=week_index - 1)

# Get the month index from the target date
    month_index = target_date.month

# Get the French month name from the month index using the dictionary
    month_name = french_months[month_index]

    return month_name
def random_prices(path,i):
    index = np.arange(1, 91)
    

# Replace values from 1 to 19 with the provided values
#     L1= np.array([
#     49.315889816078794, 51.3279931628088, 54.42024927724581, 57.58244703692335, 59.502598332442545,
#     58.544193838681565, 58.51125324477548, 59.380443622929086, 61.00327865668225, 60.952787393320286,
#     60.171619735606356, 57.37187363319658, 55.81035497912603, 48.79385843044139, 43.21042621437749,
#     43.6494762927753, 37.6814863923284, 34.66737695883439, 29.881550874132962, 29.881550874132962
# ])
#     L2 = np.array([
#     75.0, 75.0, 75.0, 74.0, 74.0, 68.82271963729504, 53.89713681841958, 45.87490940587012,
#     56.59155775366881, 59.3818470376119, 62.355749216862904, 65.62231522026549, 65.35340883617472,
#     58.51812703133646, 58.8288348738439, 59.46145612165989, 57.009992985823544, 51.345258383513055,
#     51.98029609778864,51.98029609778864
# ])
    mat1=np.load("forecast_prices_framboise.npy")
    mat2=np.load("forecast_prices_mure.npy")
    mat1[mat1 < 0] = 0
    mat2[mat2 < 0] = 0
    l1_bis=mat1[:,i]
    l2_bis=mat2[:,i]
    
    L11=np.squeeze(l1_bis)
   
    L22=np.squeeze(l2_bis)
    data = {
    'Framboise':L11,
    'Mure':L22
}
# Create DataFrame
    df = pd.DataFrame(data, index=index).transpose()
    df.to_csv(path+"\Prices.csv")
