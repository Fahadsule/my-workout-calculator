import pandas as pd
from datetime import date

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


df['calorie_type'] = 'maintainance'  # default value
df.loc[df['calorie_difference'] > 0, 'calorie_type'] = 'calorie_surplus'
df.loc[df['calorie_difference'] < 0, 'calorie_type'] = 'calorie_deficit'
print(df)

def get_maintainance():
    today_str = today.strftime('%Y-%m-%d')  # Will be '2026-02-09'
    today_row = df[df['date'] == today_str]
    
    if not today_row.empty:
        return today_row['maintainance_calories'].values[0]
    else:
        print(f"No entry found for {today_str}")
        return None
    
