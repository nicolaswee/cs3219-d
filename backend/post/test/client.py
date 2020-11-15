from psycopg2 import connect, extensions, sql

# declare a new PostgreSQL connection object
conn = connect(
dbname = "posts",
user = "root",
host = "localhost",
password = "password"
)

# object type: psycopg2.extensions.connection
print ("\ntype(conn):", type(conn))

# string for the new database name to be created

# get the isolation leve for autocommit
autocommit = extensions.ISOLATION_LEVEL_AUTOCOMMIT
print ("ISOLATION_LEVEL_AUTOCOMMIT:", extensions.ISOLATION_LEVEL_AUTOCOMMIT)

"""
ISOLATION LEVELS for psycopg2
0 = READ UNCOMMITTED
1 = READ COMMITTED
2 = REPEATABLE READ
3 = SERIALIZABLE
4 = DEFAULT
"""

# set the isolation level for the connection's cursors
# will raise ActiveSqlTransaction exception otherwise
conn.set_isolation_level( autocommit )

# instantiate a cursor object from the connection
cursor = conn.cursor()

# use the execute() method to make a SQL request
#cursor.execute('CREATE DATABASE ' + str(DB_NAME))

# use the sql module instead to avoid SQL injection attacks
# cursor.execute(sql.SQL(
# "CREATE DATABASE {}"
# ).format(sql.Identifier( DB_NAME )))
#

cursor.execute(
    """SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

CREATE TABLE public.posts (
    post_url text,
    date bigint,
    caption text,
    user_id integer,
    post_id integer NOT NULL
);


ALTER TABLE public.posts OWNER TO root;

CREATE SEQUENCE public.post_table_post_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.post_table_post_id_seq OWNER TO root;

ALTER SEQUENCE public.post_table_post_id_seq OWNED BY public.posts.post_id;

ALTER TABLE ONLY public.posts ALTER COLUMN post_id SET DEFAULT nextval('public.post_table_post_id_seq'::regclass);


ALTER TABLE ONLY public.posts
    ADD CONSTRAINT post_table_pkey PRIMARY KEY (post_id);


REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO root;
GRANT ALL ON SCHEMA public TO PUBLIC;
"""
)
# close the cursor to avoid memory leaks
cursor.close()

# close the connection to avoid memory leaks
conn.close()