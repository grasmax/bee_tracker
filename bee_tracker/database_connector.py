from __future__ import print_function
from __future__ import division

from time import sleep
from time import strftime

import datetime
import sqlite3
import threading

class DatabaseConnectionThread(threading.Thread):

    valueList = None
    system = "Windows"
    dbName = "bee_activity"
    tableName = "beeactivity"
    dbConnector = None
    dbCursor = None
    updateRate = 30

    def __init__(self, system, dbName, tableName, values, updateRate):
        threading.Thread.__init__(self)
        
        self.system = system
        self.dbName = dbName
        self.tableName = tableName
        self.valueList = values
        self.updateRate = updateRate

    def run(self):

        if self.system == "Windows":
            self.dbConnector = sqlite3.connect('//192.168.2.6/pishare/' + self.dbName)
        elif self.system == "Raspi":
            self.dbConnector = sqlite3.connect('/home/pi/shared/'+ self.dbName)

        self.dbCursor = self.dbConnector.cursor()

        while True:

            sleep(self.updateRate)

            now = datetime.datetime.now()

            self.valueList["date"] = strftime('\"%d.%m.%Y\"')
            self.valueList["time"] = strftime('\"%H:%M:%S\"')

            columns = "("
            values = "("

            for key, value in self.valueList.iteritems():
                if key != "pics":
                    columns += key + ","
                    values += str(value) + ","

            columns = columns[:-1] + ")"
            values = values[:-1] + ")"

            strSQLCmd = "INSERT INTO " + self.tableName + " " + columns + " VALUES " + values

            #print(strSQLCmd)

            # Insert a row of data
            self.dbCursor.execute(strSQLCmd)
            # Save (commit) the changes
            self.dbConnector.commit()

            
