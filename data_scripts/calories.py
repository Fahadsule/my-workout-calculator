import pandas as pd
from datetime import date


#get initial dieting states
def get_diet_phase():
    suitable_replies=['A','B','C']
    while True:
        input_variable = input("What phase of dieting are we in my boiii🤣\n\tchoose from the following...\n\t A FOR NONE\n\t B FOR BULK \n\t C FOR CUT   ").upper()
    
        if input_variable in suitable_replies:
            diet_phase = input_variable
            break
        else:
            print("Invalid response, try again!")


#Get my age
birthday = date(2006, 9, 20)  # Replace with your birthday (year, month, day)
today = date.today()
age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

#the model should hypotheticallty compute the daily maintainance calories(Miflin -St Joer, Male)
#load the data
df=pd.read_csv("data/daily.csv")
Height=177
df['BMR']=(10*df['Body_weight'])+(6.25*Height)-(5*age)+5
activity=1.6
df['maintainance_calories']=df['BMR']*activity
df['calorie_difference']=df['calories_taken']-df['maintainance_calories']

#Label the calorie_surplus and calorie_deficit groups.
df['calorie_type'] = 'maintainance'  # default value
df.loc[df['calorie_difference'] > 90, 'calorie_type'] = 'calorie_surplus'
df.loc[df['calorie_difference'] < 0, 'calorie_type'] = 'calorie_deficit'
df.loc[(df['calorie_difference'] > 0) & (df['calorie_difference'] <= 90), 'calorie_type'] = 'slight_calorie_surplus'

#Determine mass change from calorie difference
df['expected_mass_change']=str(0)+"kg "+"no_change"#default value
df.loc[df['calorie_type']=='calorie_surplus', 'expected_mass_change']=(df['calorie_difference']-90)/7700#7700 Kcal per kg of fat, 90 initial Kcal go to building muscle
df.loc[df['calorie_type']=='calorie_deficit', 'expected_mass_change']=df['calorie_difference']/7700
df.loc[df['calorie_type']=='slight_calorie_surplus', 'expected_mass_change']=df['calorie_difference']/3000#in slight surplus all go to muscle

df['expected_mass_change'] = pd.to_numeric(df['expected_mass_change'], errors='coerce').fillna(0)
df['actual_mass_change'] = df['Body_weight'].diff()

print(df)


def get_maintainance():
    today_str = today.strftime('%Y-%m-%d')  
    today_row = df[df['l_date'] == today_str]
    
    if not today_row.empty:
        return today_row['maintainance_calories'].values[0]
    else:
        print(f"No entry found for {today_str}")
        return None
    

def estimate_fat_loss(start_date,end_date):
    phase_df=df[df['l_date']>start_date]
    phase_df=phase_df[phase_df['l_date']<end_date]
    


