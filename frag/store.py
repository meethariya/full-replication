import mysql.connector as MYSQL

def connector():
    conn = MYSQL.connect(host='localhost', username='root',password='root')
    cur = conn.cursor()
    return conn, cur

def record_counter():
    conn, cur = connector()
    cur.execute("SHOW DATABASES LIKE 'ads1_%';")
    db = cur.fetchall()
    records = 0
    for i in db:
        i = i[0]
        cur.execute(f"USE {i};")
        cur.execute("SELECT COUNT(id) FROM PRODUCT;")
        records += cur.fetchall()[0][0]
    return records

def horizontal_fragment(ratio,db1='ads2_1',db2='ads2_2'):
    # connecting to mysql
    conn, cur = connector()
    cur.execute("SHOW DATABASES LIKE 'ads2_%';")
    db = cur.fetchall()
    # if already 2 db, break
    if len(db)>=2:
        return {
            'alert' : True,
            'result' : "danger",
            'outcome' : "Failed",
            'outcome_message' : "Database already fragmented."}
    # find count of records
    cur.execute(f'USE {db1};')
    # finding seperating ratio
    cur.execute('SELECT COUNT(id) FROM product;')
    temp = int(cur.fetchone()[0]*int(ratio)/100)
    # seperating records according to ratio
    cur.execute(f"SELECT * FROM product WHERE id>{temp};")
    shifting_records = cur.fetchall()
    cur.execute(f"DELETE FROM product where id>{temp}")
    # creating second db
    cur.execute(f"CREATE DATABASE {db2};")
    cur.execute(f"USE {db2};")
    # creating table
    table = '''create table product(
    id int primary key auto_increment,
    name varchar(100) not null,
    price int not null,
    seller varchar(100) not null,
    category varchar(100) not null
    );'''
    val = "%s, %s, %s, %s, %s"
    cur.execute(table)
    # shifting records
    cur.executemany(f"INSERT INTO product values ({val});",shifting_records)
    conn.commit()
    return {
        'alert' : True,
        'result' : "success",
        'outcome' : "Success",
        'outcome_message' : "Database fragmented."}

def horizontal_merge(cur,db1,db2):
    # takes cursor object, and 2 databases. merges db1 in db2. db1 is then deleted
    cur.execute(f"select * from {db1}.product;")
    shifting_records = cur.fetchall()
    val = str("%s,"*len(shifting_records[0]))[:-1]
    # inserting data to db2
    cur.executemany(f"INSERT INTO {db2}.product values ({val});",shifting_records)
    # deleting db1
    cur.execute(f"DROP DATABASE {db1};")

def vertical_merge(cur,db1,db2):
    # takes cursor object, and 2 databases. merges db1 in db2 . db1 is then deleted
    val = "%s, %s, %s, %s, %s"
    table = f'''create table {db2}.product(
        id int primary key auto_increment,
        name varchar(100) not null,
        price int not null,
        seller varchar(100) not null,
        category varchar(100) not null
        );'''
    cur.execute(f"select p1.id, name, price, seller, category from {db2}.product as p1 inner join {db1}.product as p2 on p1.id = p2.id;")
    shifting_records = cur.fetchall()
    #deleting table and creating new schema
    cur.execute(f"DROP TABLE {db2}.product;")
    cur.execute(table)
    # inserting data to db2
    cur.executemany(f"INSERT INTO {db2}.product values ({val});",shifting_records)
    cur.execute(f"DROP DATABASE {db1};")

def reset_database():
    result = {
        'alert' : True,
        'result' : "success",
        'outcome' : "Success",
        'outcome_message' : "All Database reset."}
    # connecting to mysql server
    conn, cur = connector()
    cur.execute("SHOW DATABASES LIKE 'ads2_2';")
    op = cur.fetchone()
    if not op: # it means no fragmentation is done
        return result
    else: # either vertical or horizontal fragmentation is done
        cur.execute("use ads2_1;")
        cur.execute("desc product;")
        h_v = cur.fetchall()
        if len(h_v) < 5: # it mean it is vertically fragmented
            vertical_merge(cur, 'ads2_2', 'ads2_1')
        else: # it means it is horizontally fragmented
            horizontal_merge(cur, 'ads2_2', 'ads2_1')
    cur.execute('drop table if exists ads2_1.pro_replica;')
    conn.commit()
    return result

def vertical_fragment(ratio):
    # connecting to mysql
    conn, cur = connector()
    cur.execute("SHOW DATABASES LIKE 'ads2_%';")
    op = cur.fetchall()
    # if already 2 db, break
    if len(op)>=2:
        return {
            'alert' : True,
            'result' : "danger",
            'outcome' : "Failed",
            'outcome_message' : "Database already fragmented."}
    cur.execute("USE ads2_1;")
    # seperating data based on ratio given

    # frag1 is 1st table
    # table1 is query for creating table1
    # val1 are table1 attributes
    # frag2 is 2nd table
    # table2 is query for creating table2
    # val2 are table2 attributes
    if ratio == "n": # seperate id,name --- price,seller,category
        cur.execute("SELECT id, name from product;")
        frag1 = cur.fetchall()
        table1 = '''
            CREATE TABLE product(
                id int primary key auto_increment,
                name varchar(100) not null
            );
        '''
        val1 = "id,name"
        cur.execute("SELECT id, price, seller, category FROM product;")
        frag2 = cur.fetchall()
        table2 = '''
            create table product(
                id int primary key auto_increment,
                price int not null,
                seller varchar(100) not null,
                category varchar(100) not null
        );
        '''
        val2 = "id,price,seller,category"
    elif ratio == "p": # seperate id,name,price --- seller,category
        cur.execute("SELECT id, name, price from product;")
        frag1 = cur.fetchall()
        table1 = '''
            CREATE TABLE product(
                id int primary key auto_increment,
                name varchar(100) not null,
                price int not null
            );
        '''
        val1 = "id,name,price"
        cur.execute("SELECT `id`, `seller`, `category` FROM product;")
        frag2 = cur.fetchall()
        table2 = '''
            create table product(
                id int primary key auto_increment,
                seller varchar(100) not null,
                category varchar(100) not null
        );
        '''
        val2 = "id,seller,category"
    else: # seperate id,name,price,seller --- category
        cur.execute("SELECT id, name, price, seller from product;")
        frag1 = cur.fetchall()
        table1 = '''
            CREATE TABLE product(
                id int primary key auto_increment,
                name varchar(100) not null,
                price int not null,
                seller varchar(100) not null
            );
        '''
        val1 = "id,name,price,seller"
        cur.execute("SELECT id, category FROM product;")
        frag2 = cur.fetchall()
        table2 = '''
            create table product(
                id int primary key auto_increment,
                category varchar(100) not null
        );
        '''
        val2 = "id,category"
    # creating %s parameters based on num of columns
    temp1 = str('%s,'*len(frag1[0]))[:-1]
    temp2 = str('%s,'*len(frag2[0]))[:-1]
    # deleting previous table
    cur.execute("DROP TABLE product;")
    # creating new table
    cur.execute(table1)
    # filling data
    cur.executemany(f"INSERT INTO product ({val1}) values ({temp1});",frag1)
    # creating new database
    cur.execute('CREATE DATABASE ads2_2;')
    cur.execute('USE ads2_2;')
    # creating table for new database
    cur.execute(table2)
    # filling data
    cur.executemany(f"INSERT INTO product ({val2}) values ({temp2});",frag2)
    # commiting changes
    conn.commit()
    dictionary = {
            'alert' : True,
            'result' : "success",
            'outcome' : "Success",
            'outcome_message' : "Database fragmented."}
    return dictionary

def replication():
    # connceting to mysql
    conn, cur = connector()
    cur.execute("SHOW DATABASES LIKE 'ads2_%';")
    op = cur.fetchall()
    if len(op) <= 1:
        dictionary = {
            'alert' : True,
            'result' : "danger",
            'outcome' : "Failed",
            'outcome_message' : "Fragment the existing database first!"}
    else:
        cur.execute("create table ads2_1.pro_replica select * from ads2_2.product;")
        cur.execute("create table ads2_2.pro_replica select * from ads2_1.product;")
        conn.commit()
        dictionary = {
            'alert' : True,
            'result' : "success",
            'outcome' : "Success",
            'outcome_message' : "Database fully replicated!"
        }
    return dictionary

def info():
    # connecting to mysql
    conn, cur = connector()
    # fetching all related databases 
    cur.execute("SHOW DATABASES LIKE 'ads2_%';")
    temp = cur.fetchall()
    info = []
    size = 4
    counter = 0
    # building info object
    for i in temp:
        # db name
        db = i[0]
        # fetching table names
        cur.execute(f'use {db};')
        cur.execute('show tables;')
        tables = cur.fetchall()
        tables.reverse()
        for j in tables:
            counter+=1
            table = j[0]
            # fetching col names
            cur.execute(f'''SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table}' AND TABLE_SCHEMA='{db}';''')
            cols=cur.fetchall()
            cols = [j[0] for j in cols]
            # fetching first and last rows
            cur.execute(f"SELECT * FROM {db}.{table} order by id limit 1;")
            r1=cur.fetchone()
            cur.execute(f"SELECT * FROM {db}.{table} order by id desc limit 1;")
            r2=cur.fetchone()
            dots=['...']*len(r2)
            rows = [r1,dots,r2]
            # fetching row count
            cur.execute(f"SELECT count(id) FROM {db}.product;")
            records = cur.fetchone()[0]
            # json object
            att = {
                'size':size,
                'db':db,
                'table':table,
                'cols':cols,
                'rows':rows,
                'records':records
            }
            info.append(att)
    if counter==1:
        # if one db then big size, 1 row
        info[0]['size']=8
        return {
            "info":info
        }

    elif counter==2:
        # if two db, small size, 1 row
        return {
            "info":info
        }

    elif counter==4:
        # if four db, small size, 2 row
        tworows= True
        info, info2 = info[:2], info[2:]
        return {
            "tworows":tworows,
            "info":info,
            "info2": info2
        }
