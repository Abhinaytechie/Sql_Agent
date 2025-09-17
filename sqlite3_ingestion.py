import sqlite3

## connect to sqlite3
connection=sqlite3.connect("Student.db")

cursor=connection.cursor()

table_info="""
create table STUDENT(Name Verchar(25),Class varchar(25),
Section varchar(25),Marks int)
"""

cursor.execute(table_info)

cursor.execute('''Insert Into STUDENT values('Abhinay','AIML','A',94)''')

cursor.execute('''Insert Into STUDENT values('Srutjih','DS','C',90)''')

cursor.execute('''Insert Into STUDENT values('Karthik','CSE','B',82)''')

cursor.execute('''Insert Into STUDENT values('Vineesh','IOT','A',76)''')

cursor.execute('''Insert Into STUDENT values('Teja','CS','B',58)''')

#Display
print("The inserted records are")
data=cursor.execute('''Select * from STUDENT''')
for row in data:
    print(row)

#commit changes in to the databse 
connection.commit()
#IMPPPPPP always close connection
connection.close()
