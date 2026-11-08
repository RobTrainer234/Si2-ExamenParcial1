with open('database/fashionstore_complete_schema.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

sql = sql.replace("BOOLEAN DEFAULT '0'", "BOOLEAN DEFAULT FALSE")
sql = sql.replace("BOOLEAN DEFAULT '1'", "BOOLEAN DEFAULT TRUE")

with open('database/fashionstore_complete_schema.sql', 'w', encoding='utf-8') as f:
    f.write(sql)

print('Updated boolean defaults in SQL script!')
